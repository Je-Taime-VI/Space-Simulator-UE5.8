"""复用WorldScape示例单层水体；只改项目副本，保留球形海洋与远近交接。"""
import importlib.util
from pathlib import Path
import unreal as u

ROOT=Path(u.Paths.project_dir()).resolve()
SOURCE='/WorldScape/Ressources/Materials/WorldScapeMaterials/Ocean/'
DEST='/Game/SolarSystem/Materials/M_Ocean_WorldScape'


def stable_mask(m,h,coverage):
    """保证全隐/全显端点精确，避免时域抖动函数漏出孤立像素。"""
    ml=u.MaterialEditingLibrary
    guard=next((e for e in ml.get_material_expressions(m) if e.get_editor_property('desc')=='SolarOceanMaskEndpoints'),None)
    if not guard:
        mask=ml.get_material_property_input_node(m,u.MaterialProperty.MP_OPACITY_MASK)
        guard=h.custom(m,'return Coverage<=0.00001 ? 0 : (Coverage>=0.99999 ? 1 : Mask);',{'Mask':mask,'Coverage':coverage},True)
        guard.set_editor_property('desc','SolarOceanMaskEndpoints')
        h.output(guard,u.MaterialProperty.MP_OPACITY_MASK)
    else:h.wire(coverage,guard,'Coverage')


def adapt_proxy(m,h,code):
    """海面5—20 km渐变到远景球面；陆地仍使用原180—450 km交接。"""
    ml=u.MaterialEditingLibrary
    expressions=ml.get_material_expressions(m)
    m.set_editor_property('opacity_mask_clip_value',.5)
    existing=next((e for e in expressions if e.get_editor_property('desc')=='SolarOceanProxyCoverage'),None)
    params={str(e.get_editor_property('parameter_name')):e for e in expressions if isinstance(e,u.MaterialExpressionScalarParameter)}
    if 'Visibility' not in params:return  # 初始生成器尚未建立完整远近景材质。
    # Complementary dither masks require a midpoint threshold. At the default
    # 0.333 threshold, nominally zero coverage can still leave a pixel pattern.
    coverage_code=code+'''if(BodyIndex!=3 || field.height(3,normalize(Local))>=0)return Visibility;
float3 cameraKm=CameraLocal*(RadiusKm/50.);
float altitude=length(cameraKm)-RadiusKm;
float nearWeight=1;
if(altitude>0)
{
    float3 ray=normalize(Local-CameraLocal);
    float b=-dot(cameraKm,ray);
    float c=altitude*(2*RadiusKm+altitude);
    float discriminant=b*b-c;
    float distanceKm=(b>0 && discriminant>=0) ? c/max(b+sqrt(max(0,discriminant)),1e-6) : 1e9;
    nearWeight=1-smoothstep(5.,20.,distanceKm);
}
return 1-(1-Visibility)*nearWeight;'''
    if existing:
        if 'CameraLocal' not in [str(i.get_editor_property('input_name')) for i in existing.get_editor_property('inputs')]:
            camera=h.node(m,u.MaterialExpressionCameraPositionWS)
            camera_local=h.node(m,u.MaterialExpressionTransformPosition,transform_source_type=u.MaterialPositionTransformSource.TRANSFORMPOSSOURCE_WORLD,transform_type=u.MaterialPositionTransformSource.TRANSFORMPOSSOURCE_LOCAL)
            h.wire(camera,camera_local,'')
            for name,node in [('CameraLocal',camera_local),('RadiusKm',params['RadiusKm'])]:
                pin=u.CustomInput();pin.set_editor_property('input_name',name)
                existing.set_editor_property('inputs',list(existing.get_editor_property('inputs'))+[pin]);h.wire(node,existing,name)
        existing.set_editor_property('code',coverage_code)
        stable_mask(m,h,existing)
        return
    mask=ml.get_material_property_input_node(m,u.MaterialProperty.MP_OPACITY_MASK)
    assert isinstance(mask,u.MaterialExpressionOneMinus),'Expected complementary planet coverage'
    dither=ml.get_inputs_for_material_expression(m,mask)[0]
    inverse=ml.get_inputs_for_material_expression(m,dither)[0]
    assert isinstance(inverse,u.MaterialExpressionOneMinus)
    local=h.node(m,u.MaterialExpressionTransformPosition,transform_source_type=u.MaterialPositionTransformSource.TRANSFORMPOSSOURCE_WORLD,transform_type=u.MaterialPositionTransformSource.TRANSFORMPOSSOURCE_LOCAL)
    world=h.node(m,u.MaterialExpressionWorldPosition,world_position_shader_offset=u.WorldPositionIncludedOffsets.WPT_EXCLUDE_ALL_SHADER_OFFSETS)
    h.wire(world,local,'')
    relative=h.node(m,u.MaterialExpressionWorldPosition,world_position_shader_offset=u.WorldPositionIncludedOffsets.WPT_CAMERA_RELATIVE_NO_OFFSETS)
    camera=h.node(m,u.MaterialExpressionCameraPositionWS)
    camera_local=h.node(m,u.MaterialExpressionTransformPosition,transform_source_type=u.MaterialPositionTransformSource.TRANSFORMPOSSOURCE_WORLD,transform_type=u.MaterialPositionTransformSource.TRANSFORMPOSSOURCE_LOCAL)
    h.wire(camera,camera_local,'')
    coverage=h.custom(m,coverage_code,{'Local':local,'Relative':relative,'CameraLocal':camera_local,'RadiusKm':params['RadiusKm'],'BodyIndex':params['BodyIndex'],'Visibility':params['Visibility']},True)
    coverage.set_editor_property('desc','SolarOceanProxyCoverage');h.wire(coverage,inverse,'')
    stable_mask(m,h,coverage)


def adapt_seabed(m,h,code):
    """远处海底与近海水面同步退出，避免粗层级海底穿出轨道海面。"""
    ml=u.MaterialEditingLibrary;expressions=ml.get_material_expressions(m)
    m.set_editor_property('opacity_mask_clip_value',.5)
    existing=next((e for e in expressions if e.get_editor_property('desc')=='SolarOceanSeabedCoverage'),None)
    if existing:
        existing.set_editor_property('code',code+'''if(BodyIndex!=3 || field.height(3,normalize(P))>=0)return Visibility;
return Visibility*(1-smoothstep(500000.,2000000.,length(Relative)));''')
        stable_mask(m,h,existing);return
    params={str(e.get_editor_property('parameter_name')):e for e in expressions if isinstance(e,u.MaterialExpressionScalarParameter)}
    if 'Visibility' not in params:return
    dither=ml.get_material_property_input_node(m,u.MaterialProperty.MP_OPACITY_MASK)
    assert isinstance(dither,u.MaterialExpressionMaterialFunctionCall)
    world=h.node(m,u.MaterialExpressionWorldPosition,world_position_shader_offset=u.WorldPositionIncludedOffsets.WPT_EXCLUDE_ALL_SHADER_OFFSETS)
    relative=h.node(m,u.MaterialExpressionWorldPosition,world_position_shader_offset=u.WorldPositionIncludedOffsets.WPT_CAMERA_RELATIVE_NO_OFFSETS)
    coverage=h.custom(m,code+'''if(BodyIndex!=3 || field.height(3,normalize(P))>=0)return Visibility;
return Visibility*(1-smoothstep(500000.,2000000.,length(Relative)));''',{'P':world,'Relative':relative,'BodyIndex':params['BodyIndex'],'Visibility':params['Visibility']},True)
    coverage.set_editor_property('desc','SolarOceanSeabedCoverage');h.wire(coverage,dither,'Alpha Threshold')
    stable_mask(m,h,coverage)


def build():
    spec=importlib.util.spec_from_file_location('ocean_helpers',ROOT/'Tools/build_solar_system.py')
    h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
    ml=u.MaterialEditingLibrary
    m=u.load_asset(DEST) if u.EditorAssetLibrary.does_asset_exist(DEST) else u.EditorAssetLibrary.duplicate_asset(SOURCE+'M_Water_WorldScape',DEST)
    assert m,'WorldScape ocean material copy failed'
    preset=u.load_asset(SOURCE+'MI_Planetary_Ocean')
    expressions=ml.get_material_expressions(m)
    # Bake the exact example instance values into the independent project parent.
    for e in expressions:
        if isinstance(e,u.MaterialExpressionScalarParameter) and str(e.get_editor_property('parameter_name'))!='Visibility':
            e.set_editor_property('default_value',ml.get_material_instance_scalar_parameter_value(preset,e.get_editor_property('parameter_name')))
        elif isinstance(e,u.MaterialExpressionVectorParameter):
            e.set_editor_property('default_value',ml.get_material_instance_vector_parameter_value(preset,e.get_editor_property('parameter_name')))
    m.set_editor_property('blend_mode',u.BlendMode.BLEND_MASKED)
    m.set_editor_property('opacity_mask_clip_value',.5)
    # SingleLayerWater is the above-water shading pass. Without a separate
    # underwater volume, its opaque backface blacks out the view from below.
    # Keep the surface front-facing; underwater volume optics are a later stage.
    m.set_editor_property('two_sided',False)
    m.set_editor_property('tangent_space_normal',False)
    # The original ocean remains a SingleLayerWater surface, with wave geometry,
    # world-space wave normals, absorption/scattering and the same depth response.
    assert m.get_editor_property('shading_model')==u.MaterialShadingModel.MSM_SINGLE_LAYER_WATER
    if not any(isinstance(e,u.MaterialExpressionScalarParameter) and str(e.get_editor_property('parameter_name'))=='Visibility' for e in expressions):
        fade=h.node(m,u.MaterialExpressionScalarParameter,parameter_name='Visibility',default_value=1.)
        dither=h.node(m,u.MaterialExpressionMaterialFunctionCall,material_function=u.load_asset('/Engine/Functions/Engine_MaterialFunctions02/Utility/DitherTemporalAA'))
        h.wire(fade,dither,'Alpha Threshold');h.output(dither,u.MaterialProperty.MP_OPACITY_MASK)
    # The old example uses CameraPosition + 50000000 to choose its wave axis.
    # Our frame is centred on the body; radial geometry provides the stable axis
    # at every latitude without changing the wave field as the camera translates.
    axis=next(e for e in expressions if e.get_name()=='MaterialExpressionNormalize_0')
    radial=next(e for e in expressions if e.get_name()=='MaterialExpressionVertexNormalWS_6')
    h.wire(radial,axis,'')
    # Normal reconstruction only needs position derivatives. Camera-relative
    # positions preserve centimetres at a 6371 km radius; translation cancels out.
    fn_path='/Game/SolarSystem/Materials/Functions/MF_OceanPerturbNormalHQ'
    fn=u.load_asset(fn_path) if u.EditorAssetLibrary.does_asset_exist(fn_path) else u.EditorAssetLibrary.duplicate_asset('/Engine/Functions/Engine_MaterialFunctions03/Procedurals/PerturbNormalHQ',fn_path)
    for e in ml.get_material_function_expressions(fn):
        if isinstance(e,u.MaterialExpressionWorldPosition):
            e.set_editor_property('world_position_shader_offset',u.WorldPositionIncludedOffsets.WPT_CAMERA_RELATIVE)
    ml.update_material_function(fn);u.EditorAssetLibrary.save_loaded_asset(fn)
    normal=next(e for e in expressions if e.get_name()=='MaterialExpressionMaterialFunctionCall_4')
    normal.set_editor_property('material_function',fn)
    # The example's gradient texture repeats every 128 noise units. Wrap in
    # material LWC arithmetic before Noise casts its input to float; all octave
    # multipliers are integers. This preserves both the field and local detail.
    for noise in [e for e in expressions if isinstance(e,u.MaterialExpressionNoise)]:
        tag='SolarOceanPhase_'+noise.get_name()
        wrapped=next((e for e in expressions if e.get_editor_property('desc')==tag),None)
        if not wrapped:
            source=ml.get_inputs_for_material_expression(m,noise)[0]
            divide=h.node(m,u.MaterialExpressionDivide,const_b=128.);h.wire(source,divide,'A')
            phase=h.node(m,u.MaterialExpressionFrac);h.wire(divide,phase,'')
            wrapped=h.node(m,u.MaterialExpressionMultiply,const_b=128.);h.wire(phase,wrapped,'A')
            wrapped.set_editor_property('desc',tag)
        h.wire(wrapped,noise,'World Position')
    # Unresolvable waves must not perturb the orbital normal or displace the
    # near/far complementary coverage. Keep the example waves near the observer.
    if not any(e.get_editor_property('desc')=='SolarOceanWaveDistance' for e in expressions):
        pos=h.node(m,u.MaterialExpressionWorldPosition,world_position_shader_offset=u.WorldPositionIncludedOffsets.WPT_CAMERA_RELATIVE_NO_OFFSETS)
        fade=h.custom(m,'return 1-smoothstep(500000.,2000000.,length(P));',{'P':pos},True)
        fade.set_editor_property('desc','SolarOceanWaveDistance')
        blended=h.custom(m,'return normalize(lerp(Radial,Wave,Fade));',{'Radial':radial,'Wave':normal,'Fade':fade})
        h.output(blended,u.MaterialProperty.MP_NORMAL)
        wpo=next(e for e in expressions if e.get_name()=='MaterialExpressionMultiply_23')
        h.output(h.custom(m,'return Wave*Fade;',{'Wave':wpo,'Fade':fade}),u.MaterialProperty.MP_WORLD_POSITION_OFFSET)
    # Match the established orbital ocean beyond resolvable surface detail.
    # Otherwise the clipmap's limited footprint shows dark polygonal islands
    # during its complementary transition to the planet proxy.
    if not any(e.get_editor_property('desc')=='SolarOceanOrbitalColor' for e in expressions):
        fade=next(e for e in ml.get_material_expressions(m) if e.get_editor_property('desc')=='SolarOceanWaveDistance')
        spec=importlib.util.spec_from_file_location('ocean_surface_helpers',ROOT/'Tools/refine_solar_materials.py')
        ref=importlib.util.module_from_spec(spec);spec.loader.exec_module(ref)
        world=h.node(m,u.MaterialExpressionWorldPosition,world_position_shader_offset=u.WorldPositionIncludedOffsets.WPT_EXCLUDE_ALL_SHADER_OFFSETS)
        base=next(e for e in expressions if e.get_name()=='MaterialExpressionLinearInterpolate_0')
        color=h.custom(m,ref.shader_source()+'if(Fade>=.999)return Near; return lerp(saturate(field.color(3,normalize(P))),Near,Fade);',{'P':world,'Near':base,'Fade':fade})
        color.set_editor_property('desc','SolarOceanOrbitalColor');h.output(color,u.MaterialProperty.MP_BASE_COLOR)
        for prop,far in [(u.MaterialProperty.MP_ROUGHNESS,.18),(u.MaterialProperty.MP_SPECULAR,.255),(u.MaterialProperty.MP_METALLIC,0),(u.MaterialProperty.MP_OPACITY,1)]:
            original=ml.get_material_property_input_node(m,prop)
            h.output(h.custom(m,'return lerp(%s,Near,Fade);'%far,{'Near':original,'Fade':fade},True),prop)
    expressions=ml.get_material_expressions(m)
    if not any(e.get_editor_property('desc')=='SolarOceanNearCoverage' for e in expressions):
        fade=next(e for e in expressions if e.get_editor_property('desc')=='SolarOceanWaveDistance')
        visibility=next(e for e in expressions if isinstance(e,u.MaterialExpressionScalarParameter) and str(e.get_editor_property('parameter_name'))=='Visibility')
        dither=ml.get_material_property_input_node(m,u.MaterialProperty.MP_OPACITY_MASK)
        coverage=h.custom(m,'return Visibility*Fade;',{'Visibility':visibility,'Fade':fade},True)
        coverage.set_editor_property('desc','SolarOceanNearCoverage');h.wire(coverage,dither,'Alpha Threshold')
    coverage=next(e for e in ml.get_material_expressions(m) if e.get_editor_property('desc')=='SolarOceanNearCoverage')
    coverage.set_editor_property('code','return Visibility*Fade;')
    stable_mask(m,h,coverage)
    for prop,far in [(u.MaterialProperty.MP_ROUGHNESS,.18),(u.MaterialProperty.MP_SPECULAR,.255)]:
        node=ml.get_material_property_input_node(m,prop)
        if isinstance(node,u.MaterialExpressionCustom):node.set_editor_property('code','return lerp(%s,Near,Fade);'%far)
    # A regular orbital BRDF must render the distant ocean, not the separate
    # SingleLayerWater pass. Complementary masks retain continuous coverage.
    spec=importlib.util.spec_from_file_location('ocean_proxy_helpers',ROOT/'Tools/refine_solar_materials.py')
    ref=importlib.util.module_from_spec(spec);spec.loader.exec_module(ref)
    proxy=u.load_asset('/Game/SolarSystem/Materials/M_Planet')
    if proxy:adapt_proxy(proxy,h,ref.shader_source());h.finish(proxy)
    terrain=u.load_asset('/Game/SolarSystem/Materials/M_Terrain')
    if terrain:
        ground_spec=importlib.util.spec_from_file_location('ocean_ground_helpers',ROOT/'Tools/refine_solar_ground.py')
        ground=importlib.util.module_from_spec(ground_spec);ground_spec.loader.exec_module(ground)
        ground.refresh_shader(terrain,ref.shader_source())
        adapt_seabed(terrain,h,ref.shader_source());h.finish(terrain)
    h.finish(m)
    return m


def main():
    assert not u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world(),'Stop PIE before rebuilding water'
    manager=next(a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors() if isinstance(a,u.SolarSystemActor))
    manager.set_editor_property('ocean_material',build())
    assert u.get_editor_subsystem(u.LevelEditorSubsystem).save_current_level()
    print('SOLAR_OCEAN_SAVED',manager.ocean_material.get_path_name())


if __name__=='__main__':main()
