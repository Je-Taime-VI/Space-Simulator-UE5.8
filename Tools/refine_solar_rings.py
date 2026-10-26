"""重建共用星环材质；保留程序化环形网格，不导入网页纹理或平面。"""
import importlib.util
from pathlib import Path
import unreal as u

ROOT=Path(u.Paths.project_dir()).resolve()
spec=importlib.util.spec_from_file_location('ring_asset_helpers',ROOT/'Tools/build_solar_system.py')
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)


def build():
    m=h.material('M_Rings',blend=u.BlendMode.BLEND_TRANSLUCENT)
    m.set_editor_property('two_sided',True)
    m.set_editor_property('use_translucency_vertex_fog',False)
    m.set_editor_property('translucency_pass',u.MaterialTranslucencyPass.MTP_BEFORE_DOF)
    view=h.node(m,u.MaterialExpressionCameraVectorWS)
    local=h.node(m,u.MaterialExpressionTransform,
        transform_source_type=u.MaterialVectorCoordTransformSource.TRANSFORMSOURCE_WORLD,
        transform_type=u.MaterialVectorCoordTransform.TRANSFORM_LOCAL)
    h.wire(view,local,'')
    def param(name,value):
        return h.node(m,u.MaterialExpressionScalarParameter,parameter_name=name,default_value=value)
    inputs={'UV':h.node(m,u.MaterialExpressionTextureCoordinate),'LocalView':local,
            'SunDirection':h.vector(m,'SunDirection',(1,0,0,1)),
            'BodyIndex':param('BodyIndex',7),'InnerRadiusKm':param('InnerRadiusKm',74400),
            'OuterRadiusKm':param('OuterRadiusKm',140600),'RadiusKm':param('RadiusKm',58232),
            'SolarIlluminance':param('SolarIlluminance',1200),'SunAngularRadius':param('SunAngularRadius',.0005)}
    node=h.custom(m,(ROOT/'Shaders/SolarRings.ush').read_text(encoding='utf-8'),inputs)
    opacity=u.CustomOutput();opacity.set_editor_property('output_name','Opacity')
    opacity.set_editor_property('output_type',u.CustomMaterialOutputType.CMOT_FLOAT1)
    node.set_editor_property('additional_outputs',[opacity])
    h.output(node,u.MaterialProperty.MP_EMISSIVE_COLOR)
    assert h.ML.connect_material_property(node,'Opacity',u.MaterialProperty.MP_OPACITY)
    return h.finish(m)


def main():
    assert not u.get_editor_subsystem(u.LevelEditorSubsystem).is_in_play_in_editor()
    m=build()
    manager=next(a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors() if isinstance(a,u.SolarSystemActor))
    manager.set_editor_property('ring_material',m);manager.rebuild_preview()
    assert u.get_editor_subsystem(u.LevelEditorSubsystem).save_current_level()
    print('PLANET_RINGS_MATERIAL_SAVED',m.get_path_name())


if __name__=='__main__':main()
