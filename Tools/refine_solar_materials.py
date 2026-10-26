"""生成连续远近景材质与球形体积云；在编辑器中执行，不依赖截图贴图。"""
import importlib.util
import re
from pathlib import Path
import unreal as u

ROOT = Path(u.Paths.project_dir()).resolve()
spec = importlib.util.spec_from_file_location('solar_asset_helpers', ROOT/'Tools/build_solar_system.py')
h = importlib.util.module_from_spec(spec)
spec.loader.exec_module(h)
ML, AL = h.ML, h.AL


def parameter(m, name, value):
    return h.node(m, u.MaterialExpressionScalarParameter, parameter_name=name, default_value=value)


def shader_source():
    engine = Path(u.Paths.engine_dir()).resolve()
    math_source = (engine/'Source/Runtime/Core/Private/Math/UnrealMath.cpp').read_text(encoding='utf-8-sig')
    table = re.search(r'Permutation\[512\]\s*=\s*\{([^}]+)', math_source).group(1)
    values = re.findall(r'\d+', table)[:256]
    assert len(values) == 256 and len(set(values)) == 256
    rules=(ROOT/'Source/BigWorld/SolarSystem/SolarBiomeRules.inl').read_text(encoding='utf-8')
    return (ROOT/'Shaders/SolarSurface.ush').read_text(encoding='utf-8').replace('@PERMUTATION@', ','.join(values)).replace('@BIOME_RULES@',rules)


def visibility(m, complementary=False):
    m.set_editor_property('opacity_mask_clip_value',.5)
    function = u.load_asset('/Engine/Functions/Engine_MaterialFunctions02/Utility/DitherTemporalAA')
    call = h.node(m,u.MaterialExpressionMaterialFunctionCall,material_function=function)
    alpha=parameter(m,'Visibility',1)
    if complementary:
        inverse=h.node(m,u.MaterialExpressionOneMinus);h.wire(alpha,inverse,'');alpha=inverse
    h.wire(alpha,call,'Alpha Threshold')
    mask=call
    if complementary:
        mask=h.node(m,u.MaterialExpressionOneMinus);h.wire(call,mask,'')
    h.output(mask,u.MaterialProperty.MP_OPACITY_MASK)


def refine_surface_materials():
    code=shader_source()
    proxy=h.material('M_Planet',lit=True,blend=u.BlendMode.BLEND_MASKED)
    terrain=h.material('M_Terrain',lit=True,blend=u.BlendMode.BLEND_MASKED)
    for m,is_terrain in [(proxy,False),(terrain,True)]:
        n=h.node(m,u.MaterialExpressionWorldPosition,world_position_shader_offset=u.WorldPositionIncludedOffsets.WPT_EXCLUDE_ALL_SHADER_OFFSETS)
        if not is_terrain:
            local=h.node(m,u.MaterialExpressionTransformPosition,
                transform_source_type=u.MaterialPositionTransformSource.TRANSFORMPOSSOURCE_WORLD,
                transform_type=u.MaterialPositionTransformSource.TRANSFORMPOSSOURCE_LOCAL)
            h.wire(n,local,'');n=local
        body=parameter(m,'BodyIndex',3)
        args={'N':n,'BodyIndex':body,
              'VenusCloudCover':parameter(m,'VenusCloudCover',0)}
        shade=code+'''float3 n=normalize(N);
float3 c=field.color((int)BodyIndex,n);
if(BodyIndex==2 && VenusCloudCover>.5)c=float3(.78,.69,.48)*(1+field.noise(n*24,4)*.16);
return saturate(c);'''
        albedo=h.custom(m,shade,args)
        if not is_terrain:
            radius=parameter(m,'RadiusKm',6371.0084)
            pin=u.CustomInput();pin.set_editor_property('input_name','RadiusKm')
            albedo.set_editor_property('inputs',list(albedo.get_editor_property('inputs'))+[pin])
            h.wire(radius,albedo,'RadiusKm')
            normal_out=u.CustomOutput()
            normal_out.set_editor_property('output_name','ReliefNormal')
            normal_out.set_editor_property('output_type',u.CustomMaterialOutputType.CMOT_FLOAT3)
            albedo.set_editor_property('additional_outputs',[normal_out])
            albedo.set_editor_property('code',code+(ROOT/'Shaders/SolarOrbitalDetail.ush').read_text(encoding='utf-8'))
            m.set_editor_property('tangent_space_normal',False)
            normal_world=h.node(m,u.MaterialExpressionTransform,
                transform_source_type=u.MaterialVectorCoordTransformSource.TRANSFORMSOURCE_LOCAL,
                transform_type=u.MaterialVectorCoordTransform.TRANSFORM_WORLD)
            h.wire(albedo,normal_world,'',out='ReliefNormal')
            h.output(normal_world,u.MaterialProperty.MP_NORMAL)
        if is_terrain:
            h.output(albedo,u.MaterialProperty.MP_BASE_COLOR)
            h.output(h.scalar(m,0),u.MaterialProperty.MP_EMISSIVE_COLOR)
            h.output(h.scalar(m,.5),u.MaterialProperty.MP_SPECULAR)
        else:
            # The active body shares UE lighting with its terrain. Distant bodies
            # retain their own stellar direction and illuminance in the local frame.
            active=parameter(m,'ActiveBody',1)
            sun=h.vector(m,'SunDirection',(1,0,0,1))
            lux=parameter(m,'SolarIlluminance',120000)
            h.output(h.custom(m,'return Albedo*ActiveBody;',{'Albedo':albedo,'ActiveBody':active}),u.MaterialProperty.MP_BASE_COLOR)
            h.output(h.custom(m,'return .5*ActiveBody;',{'ActiveBody':active},True),u.MaterialProperty.MP_SPECULAR)
            radiance=h.custom(m,'return (1-ActiveBody)*Albedo*SolarIlluminance*0.318309886*saturate(dot(normalize(N),normalize(SunDirection)));',
                {'Albedo':albedo,'ActiveBody':active,'N':n,'SunDirection':sun,'SolarIlluminance':lux})
            h.wire(albedo,radiance,'N',out='ReliefNormal')
            h.output(radiance,u.MaterialProperty.MP_EMISSIVE_COLOR)
        h.output(h.scalar(m,.85),u.MaterialProperty.MP_ROUGHNESS)
        h.output(h.scalar(m,0),u.MaterialProperty.MP_METALLIC)
        if is_terrain:
            ground_spec=importlib.util.spec_from_file_location('solar_ground_assets',ROOT/'Tools/refine_solar_ground.py')
            ground=importlib.util.module_from_spec(ground_spec)
            ground_spec.loader.exec_module(ground)
            ground.build(m,albedo,n,code)
        # The far surface must cover exactly the pixels discarded by the near one.
        # Dither(1-blend) is NOT the complement of Dither(blend).
        visibility(m,complementary=not is_terrain)
        if not is_terrain:
            wn=h.node(m,u.MaterialExpressionVertexNormalWS)
            displacement=code+'''float height=field.height((int)BodyIndex,normalize(N));
if(BodyIndex==3)height=max(0,height);
return normalize(WN)*height*100000*DisplayScale;'''
            h.output(h.custom(m,displacement,{'N':n,'WN':wn,'BodyIndex':body,
                     'DisplayScale':parameter(m,'DisplayScale',1)}),u.MaterialProperty.MP_WORLD_POSITION_OFFSET)
        ocean_spec=importlib.util.spec_from_file_location('solar_ocean_coverage',ROOT/'Tools/refine_solar_ocean.py')
        ocean_helpers=importlib.util.module_from_spec(ocean_spec);ocean_spec.loader.exec_module(ocean_helpers)
        if is_terrain:ocean_helpers.adapt_seabed(m,h,code)
        else:ocean_helpers.adapt_proxy(m,h,code)
        h.finish(m)

    return proxy,terrain


def refine(manager):
    code = shader_source()
    source=ROOT/'SourceAssets/SolarSystem'
    # More even curvature at low altitude; the near clipmap carries metre detail.
    mesh=u.load_asset(h.DEST+'/Meshes/SM_PlanetSphere_HiRes')
    if not mesh:
        mesh=h.build_sphere(source,512,256,'SM_PlanetSphere_HiRes')
    manager.set_editor_property('planet_mesh',mesh)
    bodies=manager.get_editor_property('bodies')

    star=h.material('M_Star')
    star_color=code+'''float3 n=normalize(N);float grain=field.noise(n*110,4);
return float3(1,.96,.89)*(120000+grain*14400);'''
    h.output(h.custom(star,star_color,{'N':h.local_normal(star)}),u.MaterialProperty.MP_EMISSIVE_COLOR)
    h.finish(star)

    proxy,terrain=refine_surface_materials()

    ocean_spec=importlib.util.spec_from_file_location('solar_ocean_assets',ROOT/'Tools/refine_solar_ocean.py')
    ocean_helpers=importlib.util.module_from_spec(ocean_spec)
    ocean_spec.loader.exec_module(ocean_helpers)
    ocean=ocean_helpers.build()

    cloud_spec=importlib.util.spec_from_file_location('solar_cloud_assets',ROOT/'Tools/refine_solar_clouds.py')
    cloud_helpers=importlib.util.module_from_spec(cloud_spec)
    cloud_spec.loader.exec_module(cloud_helpers)
    volume,cloud=cloud_helpers.refine_clouds()

    atmo=h.material('M_Atmosphere',blend=u.BlendMode.BLEND_ADDITIVE)
    normal=h.local_normal(atmo)
    view=h.node(atmo,u.MaterialExpressionCameraVectorWS)
    wn=h.node(atmo,u.MaterialExpressionPixelNormalWS)
    tint=h.vector(atmo,'Tint',(.09,.25,.6,1))
    sun=h.vector(atmo,'SunDirection',(1,0,0,1))
    lux=parameter(atmo,'SolarIlluminance',120000)
    h.output(h.custom(atmo,'''float mu=abs(dot(normalize(WN),normalize(View)));
float tangent=sqrt(saturate(1-mu*mu));
float outside=saturate((tangent-.982)/.018);
float optical=exp(-outside*7)*(1-smoothstep(.65,1,outside));
float rim=pow(tangent,24)*optical;
float day=saturate(dot(normalize(N),normalize(SunDirection))*3+.3);
return Tint*rim*day*.45*(SolarIlluminance/5);''',{'N':normal,'WN':wn,'View':view,'Tint':tint,'SunDirection':sun,'SolarIlluminance':lux}),u.MaterialProperty.MP_EMISSIVE_COLOR)
    h.output(h.scalar(atmo,1),u.MaterialProperty.MP_OPACITY)
    h.finish(atmo)

    ring_spec=importlib.util.spec_from_file_location('solar_ring_assets',ROOT/'Tools/refine_solar_rings.py')
    ring_helpers=importlib.util.module_from_spec(ring_spec)
    ring_spec.loader.exec_module(ring_helpers)
    ring=ring_helpers.build()
    manager.set_editor_property('ring_material',ring)

    mats=[];lands=[]
    for i,key in enumerate(h.KEYS):
        tex=u.load_asset(h.DEST+'/Textures/T_'+key)
        m=h.instance('MI_'+key,u.load_asset(h.DEST+'/Materials/M_Star') if i==0 else proxy,tex)
        land=h.instance('MI_Terrain_'+key,terrain,tex)
        for instance in [m,land]:
            ML.set_material_instance_scalar_parameter_value(instance,'BodyIndex',i)
            ML.set_material_instance_scalar_parameter_value(instance,'RadiusKm',bodies[i].radius_km)
            ML.update_material_instance(instance)
            AL.save_loaded_asset(instance)
        mats.append(m);lands.append(land)
    manager.set_editor_property('body_materials',mats)
    manager.set_editor_property('terrain_materials',lands)
    manager.set_editor_property('volume_cloud_material',volume)
    manager.set_editor_property('cloud_material',cloud)
    manager.set_editor_property('atmosphere_material',atmo)
    manager.set_editor_property('ocean_material',ocean)
    manager.rebuild_preview()


def main():
    actors=u.get_editor_subsystem(u.EditorActorSubsystem)
    manager=next(a for a in actors.get_all_level_actors() if isinstance(a,u.SolarSystemActor))
    refine(manager)
    assert u.get_editor_subsystem(u.LevelEditorSubsystem).save_current_level()
    AL.save_directory(h.DEST,only_if_is_dirty=True,recursive=True)
    print('CONTINUOUS_MATERIALS_SAVED')


if __name__=='__main__':
    main()
