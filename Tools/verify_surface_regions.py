"""在编辑器中抽样检查统一分区；截图复用地表材质验证工具。"""
import importlib.util
import json
import math
import uuid
from pathlib import Path
import unreal as u

ROOT=Path(u.Paths.project_dir()).resolve()
OUT=ROOT/'Saved/Diagnostics/SurfaceRegions'
OUT.mkdir(parents=True,exist_ok=True)


def manager():
    world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world()
    if not world:world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    return u.GameplayStatics.get_all_actors_of_class(world,u.SolarSystemActor)[0]


def sample_catalogue(count=1024):
    actor=manager();rows=[];failures=[];counts={};candidates={}
    for body in range(1,6):
        totals=dict.fromkeys(['water','sand','rock','soil','snow'],0)
        for i in range(count):
            z=1-2*(i+.5)/count;a=i*2.399963229728653
            d=u.Vector(math.sqrt(1-z*z)*math.cos(a),math.sqrt(1-z*z)*math.sin(a),z)
            row=json.loads(actor.get_surface_region(body,d,0))
            row['direction']=d.to_tuple()
            weights=[row[x] for x in ['sand','rock','soil','snow']]
            if any(not math.isfinite(v) or v<-.00001 or v>1.00001 for v in weights) or abs(sum(weights)-1)>.00001:
                failures.append(['weights',body,i])
            if body!=3 and (row['water']!=0 or row['vegetation']!=0):failures.append(['terrestrial_mask',body,i])
            if body not in (3,5) and row['snow']!=0:failures.append(['snow',body,i])
            if row['water'] and row['vegetation']!=0:failures.append(['underwater_vegetation',body,i])
            dominant='water' if row['water'] else max(['sand','rock','soil','snow'],key=lambda k:row[k])
            totals[dominant]+=1
            row['dominant']=dominant
            if body==3 and not row['water']:
                tag='forest' if row['vegetation']>.5 else dominant
                # Prefer the hemisphere currently illuminated at J2000.
                light=row['direction'][0]*.18+row['direction'][1]*.9+row['direction'][2]*.35
                if tag not in candidates or light>candidates[tag]['light']:
                    candidates[tag]={'light':light,**row}
            rows.append(row)
        counts[str(body)]=totals
    for layer in ['water','sand','soil','snow']:
        if counts['3'][layer]==0:failures.append(['earth_missing_zone',layer])
    for body in range(1,6):
        for d in [u.Vector(1,0,0),u.Vector(0,1,0),u.Vector(0,0,1),u.Vector(0,0,-1)]:
            flat=json.loads(actor.get_surface_region(body,d,0));steep=json.loads(actor.get_surface_region(body,d,.3))
            if steep['rock']+1e-5<flat['rock']:failures.append(['slope_rock',body,d.to_tuple()])
    report={'success':not failures,'failures':failures,'samples_per_body':count,'counts':counts,'candidates':candidates,'samples':rows,
            'scope':'固定种子的全球均匀方向抽样；分类使用零坡度以比较宏观分区，不是真实气候或地质观测。'}
    (OUT/'RegionSamples.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print('REGION_SAMPLES',report['success'],counts,failures[:10])
    return report


def start_views(stage='final',sites=None):
    spec=importlib.util.spec_from_file_location('surface_region_views',ROOT/'Tools/verify_surface_materials.py')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    mod.OUT=OUT;mod.IMAGES=ROOT/'Images/2026-10-12/SurfaceRegions'
    if sites is None:
        path=OUT/'Sites.json'
        if not path.exists():path=ROOT/'Documentation/Verification/2026-10-12/SurfaceRegions/Sites.json'
        sites=json.loads(path.read_text(encoding='utf-8'))
    class RegionProbe(mod.SurfaceProbe):
        def tick(self,dt):
            previous=len(self.rows)
            super().tick(dt)
            if len(self.rows)>previous:
                self.rows[-1]['vegetation_audit']=audit_vegetation(self.system)
    return RegionProbe(stage,sites)


def audit_vegetation(actor):
    invalid=[];counts={}
    for name,component in [('trees',actor.trees),('grass',actor.grass)]:
        counts[name]=component.get_instance_count()
        for index in range(counts[name]):
            position=component.get_instance_transform(index,True).translation
            sample=json.loads(actor.get_surface_region(3,position.normal(),-1))
            if sample['water'] or sample['snow']>.151 or sample['sand']>.501 or sample['slope']>.141 or sample['height_km']<.0149:
                invalid.append({'kind':name,'index':index,'sample':sample})
    return {'success':not invalid,'counts':counts,'invalid':invalid}


def gpu_parity(sample_rows):
    """读回浮点渲染目标，核对C++规则和实际HLSL输出，不经过曝光。"""
    spec=importlib.util.spec_from_file_location('region_materials',ROOT/'Tools/refine_solar_materials.py')
    ref=importlib.util.module_from_spec(spec);spec.loader.exec_module(ref)
    h=ref.h;original_dest=h.DEST;h.DEST='/Game/SurfaceRegionDiagnostics'
    material=h.material('M_RegionProbe')
    inputs={'N':h.vector(material,'N',(1,0,0,1)),
            'Body':ref.parameter(material,'Body',3),'H':ref.parameter(material,'H',0),
            'Slope':ref.parameter(material,'Slope',0),'Mode':ref.parameter(material,'Mode',0)}
    code=ref.shader_source()+'''FSolarSurfaceRegion r=field.biome((int)Body,normalize(N),H,Slope);
    if(Mode<.5)return float3(r.Sand,r.Rock,r.Snow);
    if(Mode<1.5)return float3(r.Moisture,r.Temperature,r.Vegetation);
    return r.Color;'''
    h.output(h.custom(material,code,inputs),u.MaterialProperty.MP_EMISSIVE_COLOR)
    h.finish(material);h.DEST=original_dest
    assert u.MaterialEditingLibrary.get_statistics(material).num_pixel_shader_instructions>0
    actor=manager();mid=u.MaterialLibrary.create_dynamic_material_instance(actor,material)
    target=u.RenderingLibrary.create_render_target2d(actor,4,4,u.TextureRenderTargetFormat.RTF_RGBA32F)
    rows=[];failures=[]
    try:
        for row in sample_rows:
            mid.set_vector_parameter_value('N',u.LinearColor(*row['direction'],1))
            for key,value in [('Body',row['body']),('H',row['height_km']),('Slope',row['slope'])]:mid.set_scalar_parameter_value(key,value)
            for mode,keys in [(0,['sand','rock','snow']),(1,['moisture_index','temperature_index','vegetation']),(2,[])]:
                mid.set_scalar_parameter_value('Mode',mode)
                u.RenderingLibrary.draw_material_to_render_target(actor,target,mid)
                c=u.RenderingLibrary.read_render_target_raw_pixel(actor,target,1,1,False)
                actual=[c.r,c.g,c.b];expected=[row[k] for k in keys] if keys else row['color']
                error=max(abs(a-b) for a,b in zip(actual,expected))
                rows.append({'body':row['body'],'direction':row['direction'],'mode':mode,'cpu':expected,'gpu':actual,'max_error':error})
                if error>.003:failures.append(len(rows)-1)
    finally:
        u.RenderingLibrary.release_render_target2d(target)
        path=material.get_path_name();package=material.get_package()
        u.EditorAssetLibrary.delete_asset(path)
        # A render-target probe may leave an empty dirty package after deletion.
        # Keep that orphan transient and remove only this tool's generated file.
        if package in u.EditorLoadingAndSavingUtils.get_dirty_content_packages():
            assert package.rename('/Temp/SurfaceRegionProbe_'+uuid.uuid4().hex)
        if not u.EditorAssetLibrary.does_asset_exist(path):
            (ROOT/'Content/SurfaceRegionDiagnostics/Materials/M_RegionProbe.uasset').unlink(missing_ok=True)
    report={'success':not failures,'failures':failures,'tolerance':.003,'max_error':max(x['max_error'] for x in rows),'rows':rows}
    (OUT/'GpuParity.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print('REGION_GPU_PARITY',report['success'],len(rows),report['max_error'])
    return report
