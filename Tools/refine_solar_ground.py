"""把示例沙、岩石、土壤、雪的贴图接入太阳系近景材质，不改写插件原资源。"""
import importlib.util
import json
from pathlib import Path
import unreal as u

ROOT=Path(u.Paths.project_dir()).resolve()
DEST='/Game/SolarSystem/Textures/Surface'
SOURCES={
    'SandColor':'Sand/T_Sand_Far_C','SandNormal':'Sand/T_Sand_Far_N','SandORMH':'Sand/T_Sand_Far_ORMH',
    'RockColor':'Rock/T_Rock3','RockNormal':'Rock/T_Rock3N',
    'SoilColor':'Dirt/T_Dirt_Albedo','SoilNormal':'Dirt/T_Dirt_Normal',
    'SnowColor':'Snow/T_Snow_Albedo','SnowNormal':'Snow/T_Snow_N','SnowORMH':'Snow/T_Snow_ORMH'}
TILES={'Sand':300.,'Rock':600.,'Soil':250.,'Snow':400.}


def helpers():
    spec=importlib.util.spec_from_file_location('solar_base_helpers',ROOT/'Tools/build_solar_system.py')
    h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
    return h


def refresh_shader(material,shader_source):
    """更新地表代码的所有保留节点，避免只改到未连接的旧节点。"""
    code=shader_source+(ROOT/'Shaders/SolarGroundDetail.ush').read_text(encoding='utf-8')
    for node in u.MaterialEditingLibrary.get_material_expressions(material):
        if isinstance(node,u.MaterialExpressionCustom) and 'GroundSampling detail;' in node.get_editor_property('code'):
            node.set_editor_property('code',code)


def textures():
    result={}
    for key,relative in SOURCES.items():
        source='/WorldScape/Ressources/Textures/'+relative
        path=DEST+'/T_'+key+('_Rock3' if key.startswith('Rock') else '')
        tex=u.load_asset(path) if u.EditorAssetLibrary.does_asset_exist(path) else u.EditorAssetLibrary.duplicate_asset(source,path)
        assert tex,source
        tex.set_editor_property('max_texture_size',2048)
        tex.set_editor_property('never_stream',False)
        u.EditorAssetLibrary.save_loaded_asset(tex)
        result[key]=tex
    return result


def build(material,macro_albedo,world_position,shader_source):
    h=helpers(); ML=u.MaterialEditingLibrary
    material.set_editor_property('tangent_space_normal',False)
    tex=textures()
    param=lambda name,value:h.node(material,u.MaterialExpressionScalarParameter,parameter_name=name,default_value=value)
    relative=h.node(material,u.MaterialExpressionWorldPosition,world_position_shader_offset=u.WorldPositionIncludedOffsets.WPT_CAMERA_RELATIVE_NO_OFFSETS)
    camera=h.node(material,u.MaterialExpressionCameraPositionWS)
    args={'WorldPosition':world_position,'RelativePosition':relative,
          'GeomNormal':h.node(material,u.MaterialExpressionVertexNormalWS),
          'BodyIndex':param('BodyIndex',3),'RadiusKm':param('RadiusKm',6371.0084),'MacroAlbedo':macro_albedo,
          'DetailStrength':param('DetailStrength',1),'NormalStrength':param('NormalStrength',1),
          'DebugLayerWeights':param('DebugLayerWeights',0),
          'DetailFadeStartCm':param('DetailFadeStartCm',30000),'DetailFadeEndCm':param('DetailFadeEndCm',250000)}
    # Dividing and wrapping the camera origin before entering a float Custom node
    # preserves sub-centimetre texture phase at planetary coordinates. Relative
    # positions carry derivatives without a per-pixel frac seam.
    for name,size in TILES.items():
        scale=param(name+'TileCm',size)
        divide=h.node(material,u.MaterialExpressionDivide);h.wire(camera,divide,'A');h.wire(scale,divide,'B')
        phase=h.node(material,u.MaterialExpressionFrac);h.wire(divide,phase,'')
        args[name+'TileCm']=scale;args[name+'Origin']=phase
    means=json.loads((ROOT/'SourceAssets/SolarSystem/SurfaceTextureMeans.json').read_text(encoding='utf-8'))
    for name in TILES:args[name+'Mean']=h.vector(material,name+'Mean',tuple(means[name+'Color'])+(1,))
    for name,texture in tex.items():
        sampler=u.MaterialSamplerType.SAMPLERTYPE_NORMAL if 'Normal' in name else u.MaterialSamplerType.SAMPLERTYPE_COLOR if 'Color' in name else u.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR
        args[name]=h.node(material,u.MaterialExpressionTextureObjectParameter,parameter_name=name,texture=texture,sampler_type=sampler)
    outputs=[]
    for name,kind in [('DetailNormal',u.CustomMaterialOutputType.CMOT_FLOAT3),('SurfaceRoughness',u.CustomMaterialOutputType.CMOT_FLOAT1),('SurfaceAO',u.CustomMaterialOutputType.CMOT_FLOAT1),('LayerWeights',u.CustomMaterialOutputType.CMOT_FLOAT4)]:
        output=u.CustomOutput();output.set_editor_property('output_name',name);output.set_editor_property('output_type',kind);outputs.append(output)
    pins=[]
    for name in args:
        pin=u.CustomInput();pin.set_editor_property('input_name',name);pins.append(pin)
    code=shader_source+(ROOT/'Shaders/SolarGroundDetail.ush').read_text(encoding='utf-8')
    node=h.node(material,u.MaterialExpressionCustom,code=code,output_type=u.CustomMaterialOutputType.CMOT_FLOAT3,inputs=pins,additional_outputs=outputs,description='WorldScape ground layers with LWC-anchored triplanar normals')
    for name,value in args.items():h.wire(value,node,name)
    for output,prop in [('',u.MaterialProperty.MP_BASE_COLOR),('DetailNormal',u.MaterialProperty.MP_NORMAL),('SurfaceRoughness',u.MaterialProperty.MP_ROUGHNESS),('SurfaceAO',u.MaterialProperty.MP_AMBIENT_OCCLUSION)]:
        assert ML.connect_material_property(node,output,prop),output
    h.output(h.scalar(material,0),u.MaterialProperty.MP_METALLIC)
    return node


def main():
    spec=importlib.util.spec_from_file_location('solar_materials',ROOT/'Tools/refine_solar_materials.py')
    ref=importlib.util.module_from_spec(spec);spec.loader.exec_module(ref)
    h=helpers();m=h.material('M_Terrain',lit=True,blend=u.BlendMode.BLEND_MASKED)
    position=h.node(m,u.MaterialExpressionWorldPosition,world_position_shader_offset=u.WorldPositionIncludedOffsets.WPT_EXCLUDE_ALL_SHADER_OFFSETS)
    body=h.node(m,u.MaterialExpressionScalarParameter,parameter_name='BodyIndex',default_value=3)
    source=ref.shader_source()
    macro=h.custom(m,source+'return saturate(field.color((int)BodyIndex,normalize(N)));',{'N':position,'BodyIndex':body})
    build(m,macro,position,source)
    h.output(h.scalar(m,0),u.MaterialProperty.MP_EMISSIVE_COLOR)
    h.output(h.scalar(m,.5),u.MaterialProperty.MP_SPECULAR)
    ref.visibility(m)
    ocean_spec=importlib.util.spec_from_file_location('solar_ocean_coverage',ROOT/'Tools/refine_solar_ocean.py')
    ocean=importlib.util.module_from_spec(ocean_spec);ocean_spec.loader.exec_module(ocean)
    ocean.adapt_seabed(m,h,source);h.finish(m)
    manager=next(a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors() if isinstance(a,u.SolarSystemActor))
    for body in manager.bodies:
        instance=u.load_asset('/Game/SolarSystem/Materials/MI_Terrain_'+body.key)
        if instance:
            u.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(instance,'RadiusKm',body.radius_km)
            u.MaterialEditingLibrary.update_material_instance(instance)
            u.EditorAssetLibrary.save_loaded_asset(instance)
    print('SOLAR_GROUND_MATERIAL_SAVED')


if __name__=='__main__':main()
