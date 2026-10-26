"""在编辑器内生成独立太阳系资产。重复运行会更新本工具生成的材质。"""
import json
import math
from pathlib import Path
import unreal as u

ROOT = Path(u.Paths.project_dir()).resolve()
DEST = '/Game/SolarSystem'
KEYS = ['Sun', 'Mercury', 'Venus', 'Earth', 'Moon', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune']
ML = u.MaterialEditingLibrary
AL = u.EditorAssetLibrary


def material(name, lit=False, blend=None):
    path = DEST + '/Materials/' + name
    m = u.load_asset(path)
    if m:
        ML.delete_all_material_expressions(m)
    else:
        m = u.AssetToolsHelpers.get_asset_tools().create_asset(name, DEST + '/Materials', u.Material, u.MaterialFactoryNew())
    m.set_editor_property('shading_model', u.MaterialShadingModel.MSM_DEFAULT_LIT if lit else u.MaterialShadingModel.MSM_UNLIT)
    if blend is not None:
        m.set_editor_property('blend_mode', blend)
    return m


def node(m, cls, **props):
    n = ML.create_material_expression(m, cls)
    for k, v in props.items():
        n.set_editor_property(k, v)
    return n


def wire(a, b, pin, out=''):
    if not ML.connect_material_expressions(a, out, b, pin):
        raise RuntimeError('Material connection failed: ' + pin)


def custom(m, code, inputs, scalar=False):
    pins = []
    for k in inputs:
        pin = u.CustomInput()
        pin.set_editor_property('input_name', k)
        pins.append(pin)
    n = node(m, u.MaterialExpressionCustom, code=code,
             output_type=u.CustomMaterialOutputType.CMOT_FLOAT1 if scalar else u.CustomMaterialOutputType.CMOT_FLOAT3,
             inputs=pins)
    for k, v in inputs.items():
        wire(v, n, k)
    return n


def output(n, prop):
    if not ML.connect_material_property(n, '', prop):
        raise RuntimeError('Material property connection failed')


def vector(m, name, color):
    return node(m, u.MaterialExpressionVectorParameter, parameter_name=name, default_value=u.LinearColor(*color))


def scalar(m, value):
    return node(m, u.MaterialExpressionConstant, r=value)


def local_normal(m):
    world = node(m, u.MaterialExpressionVertexNormalWS)
    local = node(m, u.MaterialExpressionTransform,
                 transform_source_type=u.MaterialVectorCoordTransformSource.TRANSFORMSOURCE_WORLD,
                 transform_type=u.MaterialVectorCoordTransform.TRANSFORM_LOCAL)
    wire(world, local, '')
    return local


UV = 'float3 n=normalize(N); float2 uv=float2(atan2(n.y,n.x)*0.159154943+0.5,acos(clamp(n.z,-1,1))*0.318309886); '


def finish(m):
    ML.layout_material_expressions(m)
    ML.recompile_material(m)
    AL.save_loaded_asset(m)
    return m


def instance(name, parent, texture):
    path = DEST + '/Materials/' + name
    mi = u.load_asset(path) or u.AssetToolsHelpers.get_asset_tools().create_asset(name, DEST + '/Materials', u.MaterialInstanceConstant, u.MaterialInstanceConstantFactoryNew())
    ML.set_material_instance_parent(mi, parent)
    ML.set_material_instance_texture_parameter_value(mi, 'Albedo', texture)
    ML.update_material_instance(mi)
    AL.save_loaded_asset(mi)
    return mi


def build_sphere(source, nx=128, ny=64, name='SM_PlanetSphere'):
    """规则经纬网格，半径 50 cm；避免近景使用低面数预览球。"""
    lines = []
    for y in range(ny + 1):
        lat = math.pi * y / ny
        for x in range(nx + 1):
            lon = 2 * math.pi * x / nx
            n = (math.sin(lat)*math.cos(lon), math.sin(lat)*math.sin(lon), math.cos(lat))
            lines.append('v %.8f %.8f %.8f' % tuple(c*50 for c in n))
            lines.append('vn %.8f %.8f %.8f' % n)
            lines.append('vt %.8f %.8f' % (x/nx, 1-y/ny))
    for y in range(ny):
        for x in range(nx):
            a=y*(nx+1)+x+1; b=a+nx+1
            for tri in ((a,b,a+1),(a+1,b,b+1)):
                lines.append('f '+' '.join('%d/%d/%d'%(v,v,v) for v in tri))
    obj = source / (name+'.obj')
    obj.write_text('\n'.join(lines), encoding='ascii')
    t = u.AssetImportTask()
    for k,v in {'filename': str(obj), 'destination_path': DEST+'/Meshes', 'automated':True, 'replace_existing':True, 'save':True}.items():
        t.set_editor_property(k,v)
    options=u.FbxImportUI()
    options.set_editor_property('import_mesh',True)
    options.set_editor_property('import_materials',False)
    options.set_editor_property('import_textures',False)
    options.set_editor_property('automated_import_should_detect_type',False)
    options.set_editor_property('mesh_type_to_import',u.FBXImportType.FBXIT_STATIC_MESH)
    options.static_mesh_import_data.set_editor_property('auto_generate_collision',False)
    t.set_editor_property('options',options)
    u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
    mesh=u.load_asset(DEST+'/Meshes/'+name)
    assert mesh
    return mesh


def temperate_materials(manager):
    for component, mesh_path in [(manager.trees,'/WorldScape/Ressources/Mesh/Tree/SM_Tree_1'),(manager.grass,'/WorldScape/Ressources/Mesh/Grass/SM_Grass_Temp')]:
        mesh=u.load_asset(mesh_path)
        component.set_static_mesh(mesh)
        for i,slot in enumerate(mesh.static_materials):
            parent=slot.material_interface
            names=[str(n) for n in ML.get_scalar_parameter_names(parent)]
            if 'SeasonAffect' not in names:
                continue
            name='MI_Temperate_'+mesh.get_name()+'_'+str(i)
            mi=u.load_asset(DEST+'/Materials/'+name) or u.AssetToolsHelpers.get_asset_tools().create_asset(name, DEST+'/Materials',u.MaterialInstanceConstant,u.MaterialInstanceConstantFactoryNew())
            ML.set_material_instance_parent(mi,parent)
            for p,v in [('SeasonAffect',0),('SeasonShift',0),('Humidity',.65),('Temprature',.65)]:
                ML.set_material_instance_scalar_parameter_value(mi,p,v)
            ML.update_material_instance(mi)
            AL.save_loaded_asset(mi)
            component.set_material(i,mi)


def build_assets(manager):
    source = ROOT / 'SourceAssets' / 'SolarSystem'
    source.mkdir(parents=True, exist_ok=True)
    sphere=u.load_asset(DEST+'/Meshes/SM_PlanetSphere') or build_sphere(source)
    manager.set_editor_property('planet_mesh',sphere)
    stamp=source / 'T_Clouds.tga'
    if not stamp.exists() or stamp.stat().st_mtime < (ROOT/'Source/BigWorld/SolarSystem/SolarModel.cpp').stat().st_mtime:
        assert manager.export_procedural_textures(str(source), 1024)
    tasks = []
    for key in KEYS + ['Clouds']:
        task = u.AssetImportTask()
        task.set_editor_property('filename', str(source / ('T_' + key + '.tga')))
        task.set_editor_property('destination_path', DEST + '/Textures')
        task.set_editor_property('automated', True)
        task.set_editor_property('replace_existing', True)
        task.set_editor_property('save', True)
        tasks.append(task)
    u.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
    textures = {key: u.load_asset(DEST + '/Textures/T_' + key) for key in KEYS + ['Clouds']}
    for t in textures.values():
        assert t
        t.set_editor_property('never_stream', True)
        AL.save_loaded_asset(t)

    proxy = material('M_Planet')
    n = local_normal(proxy)
    tex = node(proxy, u.MaterialExpressionTextureObjectParameter, parameter_name='Albedo', texture=textures['Earth'])
    sun = vector(proxy, 'SunDirection', (1, 0, 0, 1))
    color = custom(proxy, UV + 'float3 c=Texture2DSample(Albedo,AlbedoSampler,uv).rgb; float light=saturate(dot(n,normalize(SunDirection))); return c*(0.009+1.55*pow(light,0.75));', {'N': n, 'Albedo': tex, 'SunDirection': sun})
    output(color, u.MaterialProperty.MP_EMISSIVE_COLOR)
    finish(proxy)

    star = material('M_Star')
    tex = node(star, u.MaterialExpressionTextureObjectParameter, parameter_name='Albedo', texture=textures['Sun'])
    color = custom(star, UV + 'return Texture2DSample(Albedo,AlbedoSampler,uv).rgb*3.0;', {'N': local_normal(star), 'Albedo': tex})
    output(color, u.MaterialProperty.MP_EMISSIVE_COLOR)
    finish(star)

    terrain = material('M_Terrain', lit=True)
    pos = node(terrain, u.MaterialExpressionWorldPosition)
    tex = node(terrain, u.MaterialExpressionTextureObjectParameter, parameter_name='Albedo', texture=textures['Earth'])
    color = custom(terrain, UV + 'float3 c=Texture2DSample(Albedo,AlbedoSampler,uv).rgb; float detail=0.94+0.06*sin(N.x*0.021)*sin(N.y*0.017)*sin(N.z*0.019); return c*detail;', {'N': pos, 'Albedo': tex})
    output(color, u.MaterialProperty.MP_BASE_COLOR)
    output(scalar(terrain, .88), u.MaterialProperty.MP_ROUGHNESS)
    finish(terrain)

    atmo = material('M_Atmosphere', blend=u.BlendMode.BLEND_ADDITIVE)
    n = local_normal(atmo)
    wn = node(atmo, u.MaterialExpressionPixelNormalWS)
    view = node(atmo, u.MaterialExpressionCameraVectorWS)
    tint = vector(atmo, 'Tint', (.07, .28, .75, 1))
    sun = vector(atmo, 'SunDirection', (1, 0, 0, 1))
    color = custom(atmo, 'float rim=pow(1-saturate(dot(normalize(WN),normalize(View))),3.5); float day=saturate(dot(normalize(N),normalize(SunDirection))*3+0.25); return Tint*rim*day*0.65;', {'N': n, 'WN': wn, 'View': view, 'Tint': tint, 'SunDirection': sun})
    output(color, u.MaterialProperty.MP_EMISSIVE_COLOR)
    output(scalar(atmo, 1), u.MaterialProperty.MP_OPACITY)
    finish(atmo)

    cloud = material('M_Clouds', blend=u.BlendMode.BLEND_TRANSLUCENT)
    n = local_normal(cloud)
    tex = node(cloud, u.MaterialExpressionTextureObjectParameter, parameter_name='Albedo', texture=textures['Clouds'])
    sun = vector(cloud, 'SunDirection', (1, 0, 0, 1))
    opacity = custom(cloud, UV + 'return Texture2DSample(Albedo,AlbedoSampler,uv).r*0.82;', {'N': n, 'Albedo': tex}, True)
    color = custom(cloud, 'return float3(0.83,0.89,1)*(0.006+1.55*saturate(dot(normalize(N),normalize(SunDirection))));', {'N': n, 'SunDirection': sun})
    output(color, u.MaterialProperty.MP_EMISSIVE_COLOR)
    output(opacity, u.MaterialProperty.MP_OPACITY)
    finish(cloud)

    import importlib.util
    ring_spec=importlib.util.spec_from_file_location('solar_ring_assets',ROOT/'Tools/refine_solar_rings.py')
    ring_helpers=importlib.util.module_from_spec(ring_spec)
    ring_spec.loader.exec_module(ring_helpers)
    ring=ring_helpers.build()

    ocean_spec=importlib.util.spec_from_file_location('solar_ocean_assets',ROOT/'Tools/refine_solar_ocean.py')
    ocean_helpers=importlib.util.module_from_spec(ocean_spec)
    ocean_spec.loader.exec_module(ocean_helpers)
    ocean=ocean_helpers.build()

    manager.set_editor_property('body_materials', [instance('MI_' + k, star if k == 'Sun' else proxy, textures[k]) for k in KEYS])
    manager.set_editor_property('terrain_materials', [instance('MI_Terrain_' + k, terrain, textures[k]) for k in KEYS])
    manager.set_editor_property('atmosphere_material', atmo)
    manager.set_editor_property('cloud_material', cloud)
    manager.set_editor_property('ring_material', ring)
    manager.set_editor_property('ocean_material', ocean)
    temperate_materials(manager)


def main():
    levels = u.get_editor_subsystem(u.LevelEditorSubsystem)
    actors = u.get_editor_subsystem(u.EditorActorSubsystem)
    cls = u.load_class(None, '/Script/BigWorld.SolarSystemActor')
    # New map is created before any world or actor references are acquired.
    map_path = DEST + '/Maps/SolarSystem'
    if not AL.does_asset_exist(map_path):
        assert levels.new_level(map_path)
    elif u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world().get_path_name() != map_path + '.SolarSystem':
        assert levels.load_level(map_path)
    manager = next((a for a in actors.get_all_level_actors() if a.get_class() == cls), None)
    if manager is None:
        manager = actors.spawn_actor_from_class(cls, u.Vector())
    manager.set_actor_label('SolarSystem')
    manager.set_actor_location(u.Vector(0, 0, 0), False, True)
    build_assets(manager)
    # Keep a full rebuild consistent with the continuous-flight material pipeline.
    import importlib.util
    refinement_spec=importlib.util.spec_from_file_location('solar_refinement',ROOT/'Tools/refine_solar_materials.py')
    refinement=importlib.util.module_from_spec(refinement_spec)
    refinement_spec.loader.exec_module(refinement)
    refinement.refine(manager)
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    ws = world.get_world_settings()
    ws.set_editor_property('default_game_mode', u.load_class(None, '/Script/BigWorld.SolarExplorerGameMode'))
    ws.set_editor_property('enable_world_bounds_checks', False)
    if not any(isinstance(a, u.PlayerStart) for a in actors.get_all_level_actors()):
        start = actors.spawn_actor_from_class(u.PlayerStart, u.Vector(1975012604, 0, 0))
        start.set_actor_label('ExplorerStart')
    manager.rebuild_preview()
    u.get_editor_subsystem(u.UnrealEditorSubsystem).set_level_viewport_camera_info(u.Vector(1900000000, 0, 500000000), u.Rotator(-14.7, 180, 0))
    validation = json.loads(manager.validate_model())
    (ROOT / 'Saved' / 'SolarModelValidation.json').write_text(json.dumps(validation, ensure_ascii=False, indent=2), encoding='utf-8')
    assert validation['success'], validation
    assert levels.save_current_level()
    AL.save_directory(DEST, only_if_is_dirty=True, recursive=True)
    (ROOT / 'Saved' / 'SolarAssetBuild.json').write_text(json.dumps({'success': True, 'map': map_path, 'validation': validation}, indent=2), encoding='utf-8')
    print('SOLAR_BUILD_SUCCESS', validation)


if __name__ == '__main__':
    main()
