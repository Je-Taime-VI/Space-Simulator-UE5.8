"""仅重建太阳系云材质，保留地表、地图和其余材质设置。"""
from pathlib import Path
import importlib.util
import unreal as u

ROOT=Path(u.Paths.project_dir()).resolve()
spec=importlib.util.spec_from_file_location('cloud_asset_helpers',ROOT/'Tools/build_solar_system.py')
h=importlib.util.module_from_spec(spec)
spec.loader.exec_module(h)


def refine_clouds():
    # Small periodic 3D density lookup replaces sixteen lattice hashes per ray step.
    detail_path=h.DEST+'/Textures/T_CloudDetailVolume'
    detail=u.load_asset(detail_path)
    if not detail:
        task=u.AssetImportTask()
        task.filename=str(ROOT/'SourceAssets/SolarSystem/T_CloudDetailAtlas.png')
        task.destination_path=h.DEST+'/Textures'
        task.automated=True
        task.save=True
        u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        atlas=u.load_asset(h.DEST+'/Textures/T_CloudDetailAtlas')
        assert atlas, 'Run Tools/bake_cloud_noise.py first'
        atlas.set_editor_property('srgb',False)
        atlas.set_editor_property('compression_settings',u.TextureCompressionSettings.TC_GRAYSCALE)
        h.AL.save_loaded_asset(atlas)
        factory=u.VolumeTextureFactory()
        detail=u.AssetToolsHelpers.get_asset_tools().create_asset('T_CloudDetailVolume',h.DEST+'/Textures',u.VolumeTexture,factory)
        detail.set_editor_property('source2d_texture',atlas)
        detail.set_editor_property('source2d_tile_size_x',64)
        detail.set_editor_property('source2d_tile_size_y',64)
    assert detail
    detail.set_editor_property('srgb',False)
    detail.set_editor_property('compression_settings',u.TextureCompressionSettings.TC_GRAYSCALE)
    detail.set_editor_property('filter',u.TextureFilter.TF_TRILINEAR)
    detail.set_editor_property('address_mode',u.TextureAddress.TA_WRAP)
    h.AL.save_loaded_asset(detail)
    texture=u.load_asset(h.DEST+'/Textures/T_Clouds')
    assert texture
    # The source stores a linear coverage mask, not an sRGB colour.
    texture.set_editor_property('srgb',False)
    texture.set_editor_property('compression_settings',u.TextureCompressionSettings.TC_GRAYSCALE)
    texture.set_editor_property('filter',u.TextureFilter.TF_BILINEAR)
    texture.set_editor_property('address_x',u.TextureAddress.TA_WRAP)
    texture.set_editor_property('address_y',u.TextureAddress.TA_CLAMP)
    h.AL.save_loaded_asset(texture)

    def scalar(m,name,value):
        return h.node(m,u.MaterialExpressionScalarParameter,parameter_name=name,default_value=value)
    def tex(m):
        return h.node(m,u.MaterialExpressionTextureObjectParameter,parameter_name='CloudMap',texture=texture)

    volume=h.material('M_PlanetCloudVolume',lit=True,blend=u.BlendMode.BLEND_ADDITIVE)
    volume.set_editor_property('material_domain',u.MaterialDomain.MD_VOLUME)
    volume.set_editor_property('used_with_volumetric_cloud',True)
    args={'Position':h.node(volume,u.MaterialExpressionWorldPosition),
          'RadiusKm':scalar(volume,'RadiusKm',6371.0084),
          'BodyIndex':scalar(volume,'BodyIndex',3),
          'CloudBottomKm':scalar(volume,'CloudBottomKm',2),
          'CloudThicknessKm':scalar(volume,'CloudThicknessKm',7),
          'CloudMap':tex(volume),
          'CloudDetail':h.node(volume,u.MaterialExpressionTextureObjectParameter,parameter_name='CloudDetail',texture=detail)}
    h.output(h.custom(volume,(ROOT/'Shaders/SolarCloud.ush').read_text(encoding='utf-8'),args,True),u.MaterialProperty.MP_SUBSURFACE_COLOR)
    h.output(h.custom(volume,'return BodyIndex==2?float3(.96,.90,.73):float3(.98,.985,1);',{'BodyIndex':args['BodyIndex']}),u.MaterialProperty.MP_BASE_COLOR)
    h.node(volume,u.MaterialExpressionVolumetricAdvancedMaterialOutput,
           multi_scattering_approximation_octave_count=1,
           ground_contribution=True,ray_march_volume_shadow=False)
    h.finish(volume)

    cloud=h.material('M_Clouds',blend=u.BlendMode.BLEND_TRANSLUCENT)
    n=h.local_normal(cloud)
    h.output(h.custom(cloud,h.UV+'return Texture2DSampleLevel(CloudMap,CloudMapSampler,uv,0).r*.9;',
                      {'N':n,'CloudMap':tex(cloud)},True),u.MaterialProperty.MP_OPACITY)
    sun=h.vector(cloud,'SunDirection',(1,0,0,1))
    h.output(h.custom(cloud,'return float3(.95,.97,1)*SolarIlluminance*0.318309886*saturate(dot(normalize(N),normalize(SunDirection)));',
                      {'N':n,'SunDirection':sun,'SolarIlluminance':scalar(cloud,'SolarIlluminance',120000)}),u.MaterialProperty.MP_EMISSIVE_COLOR)
    h.finish(cloud)
    return volume,cloud


if __name__=='__main__':
    refine_clouds()
    print('CLOUD_MATERIALS_SAVED')
