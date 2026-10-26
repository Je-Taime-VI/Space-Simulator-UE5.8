"""检查长按调速、松开保持、双键恢复自动；调用实际 C++ 移动入口。"""
import json
import math
from pathlib import Path
import unreal as u


def verify_speed_controls(system,pawn):
    system.focus_body(3)
    assert system.visit_surface(25,0,35)
    origin=pawn.get_actor_location();rotation=pawn.get_actor_rotation();up=origin.normal()
    zero=u.Vector();rows=[];failures=[]
    automatic=.01225

    def apply(increase=False,decrease=False,dt=1/60,direction=None):
        pawn.apply_flight_input(zero if direction is None else direction,dt,increase,decrease)

    def reset():
        pawn.set_view_pose(origin,rotation);pawn.speed_km_per_second=.08
        apply(True,True,0);apply(False,False,0)

    def hold(seconds,increase,rate=60):
        for _ in range(round(seconds*rate)):apply(increase,not increase,1/rate)

    def check(name,speed,auto,distance=None):
        actual=pawn.effective_speed_km_per_second
        travel=(pawn.get_actor_location()-origin).length()/100
        row={'case':name,'speed_km_s':actual,'expected_km_s':speed,'automatic':pawn.automatic_speed,
             'distance_m':travel}
        rows.append(row)
        if abs(actual-speed)>max(1e-8,speed*1e-8) or pawn.automatic_speed!=auto or (distance is not None and abs(travel-distance)>.002):
            failures.append(name)

    reset();check('automatic_at_35m',automatic,True,0)
    for fps in [30,60,144]:
        reset();hold(4,True,fps)
        check('hold_4s_at_%dfps'%fps,automatic*2,False,0)
    # Release must preserve speed while moving and changing radial clearance.
    for _ in range(60):apply(direction=up)
    check('released_move_1s',automatic*2,False,24.5)
    near=up*(origin.length()-2500)
    pawn.set_view_pose(near,rotation);apply(dt=0)
    check('retained_at_10m_clearance',automatic*2,False)
    pawn.set_view_pose(origin,rotation)
    hold(4,False);check('decrease_4s',automatic,False,0)
    apply();check('decrease_release',automatic,False,0)
    apply(True,True);check('both_restore_automatic',automatic,True,0)
    apply(True,False);check('partial_chord_release',automatic,True,0)
    apply();check('full_chord_release',automatic,True,0)
    hold(4,False);check('new_decrease_after_reset',automatic/2,False,0)
    apply();check('new_decrease_retained',automatic/2,False,0)
    reset();apply(True,False,.1);check('short_tap_no_speed_jump',automatic*2**(.1/4),False,0)
    reset();apply(True,False,10);check('loading_stall_not_10s_adjustment',automatic*2**(.1/4),False,0)
    reset();hold(32,True)
    apply(dt=.1,direction=up)
    check('released_manual_bypasses_displacement_cap',automatic*256,False,313.6)
    pawn.set_view_pose(origin,rotation)
    apply(dt=.1,direction=u.Vector(-up.x,-up.y,-up.z))
    check('retained_manual_ground_projection',automatic*256,False,32)
    reset()
    return rows,failures


def main():
    world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world()
    system=u.GameplayStatics.get_all_actors_of_class(world,u.SolarSystemActor)[0]
    pawn=u.GameplayStatics.get_player_pawn(world,0)
    pawn.set_actor_tick_enabled(False);system.set_time_scale(0)
    try:
        rows,failures=verify_speed_controls(system,pawn)
        report={'success':not failures,'failures':failures,'cases':rows,
                'scope':'实际 C++ 共用入口的时长、状态转换和移动回归；30/60/144 Hz为注入步长，未注入物理键盘或测量渲染FPS。'}
        path=Path(u.Paths.project_saved_dir(),'Diagnostics/RetainedSpeed/Verification.json')
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        print('RETAINED_SPEED_CHECK',report['success'],len(rows),failures)
    finally:
        system.set_time_scale(1);pawn.set_actor_tick_enabled(True)


if __name__=='__main__':main()
