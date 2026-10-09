# 技术问题与解决记录

最后整理日期：2026年10月08日。

状态含义：“已解决”指在注明范围内有验证；“已规避”指采用替代配置避免现象，原路径没有完成优化；“未解决/待验证”指尚缺修复实现或验证证据，不等同于已排期。

## T-001｜UE 版本和 C++ 工具链兼容

- **发现日期：** 2026年10月08日。
- **状态：** 项目接入及本次修复构建已通过；厂商代码警告仍存在。
- **问题：** 引擎目录与 EngineAssociation 只能表明 5.8 系列，需要确认实际补丁版本；项目插件需与当前引擎及编译工具链匹配。
- **处理：** 核实 Build.version 为 5.8.2 / CL 56702186，使用 VS 2022、MSVC 14.44.35228、Windows SDK 10.0.26100.0 和 UE 自带 .NET，编译项目及插件源码。
- **验证：** 项目正常加载；地形验证成功；地表渲染修复后的正式构建返回 `Result: Succeeded`。
- **剩余事项：** 浮点转换与弃用 API 警告未全面清理，未做 Shipping 和其他平台验证。
- **证据：** [TerrainVelocityFullBuild.log](<Documentation/Verification/2026-10-09/Logs/TerrainVelocityFullBuild.txt>)。

## T-002｜官方 MCP 连接与工具发现

- **发现日期：** 2026年10月08日。
- **状态：** 已解决并实际调用验证；连接需要随编辑器启动重新建立。
- **问题：** Epic 官方 Unreal MCP、第三方同名项目与 Python 桥接为独立实现；新增服务后，客户端工具列表可能需要重新连接才会刷新。
- **处理：** 检查本机 UE 5.8.2 插件和项目启用状态，确认 `ModelContextProtocol`、`AllToolsets`、8000 端口和 `/mcp` 路径；通过真实协议核实连接，而非只看配置文件。
- **验证：** HTTP 握手、工具集发现、读取关卡及截图均成功。工具搜索模式下的三个顶层入口是正常设计。
- **注意：** 官方插件是实验性功能；端口有人监听不等于 MCP 可用，应进一步握手和执行只读工具。部分自动启动设置在 Saved 下的编辑器配置中，清理目录后需恢复检查。
- **证据：** [官方验证报告](<Documentation/Verification/2026-10-09/Logs/OfficialMCPVerification.json>)、[只读调用报告](<Documentation/Verification/2026-10-09/Logs/OfficialMCPReadOnlyCall.json>)。

## T-003｜本机 MCP 请求因代理返回 502

- **发现日期：** 2026年10月08日。
- **状态：** 检查脚本中的问题已解决。
- **问题：** HTTP 客户端采用系统代理配置，将本应直连的回环服务请求转发，返回 502。
- **处理：** 官方 MCP 检查与截图脚本为本机客户端显式设置 `httpx.AsyncClient(..., trust_env=False)`。
- **验证：** 使用直连客户端后，握手、关卡读取和截图成功。
- **边界：** 没有全局关闭 Windows 代理；不能据此保证其他 MCP 客户端的代理行为也已调整。
- **文件：** [check_official_mcp.py](<Tools/check_official_mcp.py>)。

## T-004｜PowerShell 管道编码与 Python 桥接可靠性

- **发现日期：** 2026年10月08日。
- **状态：** 本次遇到的编码问题已解决。
- **问题：** 管道中的 UTF-8 BOM 会影响 JSON 解码；编辑器停止响应时，无限等待会妨碍判断执行结果。
- **处理：** 桥接输入使用 `utf-8-sig` 解码，设置发现及命令超时，只匹配项目路径；多个匹配实例时明确报错。
- **验证：** 桥接握手和四个工具调用通过。
- **注意：** 超时不保证修改没有执行。先检查实际状态，再决定是否重试；外层 MCP 成功也不能替代内部 Python `success` 检查。
- **文件：** [ue_bridge.py](<Tools/ue_bridge.py>)、[check_mcp.py](<Tools/check_mcp.py>)。

## T-005｜示例像固定机位、厂商步行角色不能移动

- **发现日期：** 2026年10月08日。
- **状态：** 自由飞行已解决；行星步行玩法未实施。
- **调查：** 初始 GameModeBase 已生成并控制 DefaultPawn，摄像机没有强制接管；GameGetsMouseControl 关闭、Play/Simulate 和视口焦点需要区分。项目没有轴映射，但 DefaultPawn 自带输入，因此“空映射导致默认 Pawn 完全不能动”不是可靠结论。
- **未采用的尝试：** 配置厂商 WorldScapeGamemode 和步行轴映射后，运行中的重力源列表为空、`IsOnGround=False`，没有得到有效步行位移。
- **最终处理：** 新增项目 GameMode，通过 Demonstration_ 前缀使用 FlyWorldScape；启用游戏鼠标捕获，撤回步行映射。
- **验证：** Pawn 控制和相机目标正确，注入前向、横向运动输入均产生位移。
- **限制：** 飞行升降沿世界 Z 轴；自动化检查没有模拟物理键盘；其他示例尚未逐一验证。
- **证据：** [DemoFlyMovementVerification.json](<Documentation/Verification/2026-10-09/Logs/DemoFlyMovementVerification.json>)。

## T-006｜VSM 非 Nanite 标记工作队列溢出

- **发现日期：** 2026年10月08日。
- **状态：** 已规避，未完成 VSM 路径本身的性能优化。
- **原因：** WorldScape 动态非 Nanite 网格覆盖阴影贴图的大面积，触发标记任务队列容量限制。
- **处理：** 项目使用 `r.Shadow.Virtual.Enable=0`，改用普通阴影贴图。
- **验证：** 后续对应测试期间未再记录该 VSM 告警。
- **代价：** 远处阴影的覆盖与质量变化，需要按最终场景需求评估。
- **重要区分：** 这是标记队列溢出，不等同于 VSM 物理页池耗尽；没有将增加 `r.Shadow.Virtual.MaxPhysicalPages` 当作本问题修复。
- **配置：** [DefaultEngine.ini](<Config/DefaultEngine.ini>)。

## T-007｜移动时地表整片消失、露出岩石底部

- **发现及解决日期：** 2026年10月08日。
- **状态：** 已解决，在 Demonstration_BarenLikePlanet 完成正式编译重启复测。
- **现象：** 玩家移动时地表闪烁或大片漏画，岩石原本埋在地下的部分可见；停下或冻结地形更新后表现不同。
- **证据：** 真实截图复现；相机离地高度采样为正，不能简单归因于穿地。详见 [开发日志中的前后截图](<DevelopmentLog.md>)。

**根因与修复：**

插件的 `FWorldScapeMeshSceneProxy::GetViewRelevance` 强制将 `bVelocityRelevance` 设为 `false`。UE 5.8 在深度阶段输出速度时，移动网格会从普通深度通道转交速度/深度通道。插件禁用了后一通道，导致更新帧缺少深度，地表漏画。

对齐引擎 ProceduralMeshComponent，恢复：

```cpp
Result.bVelocityRelevance = DrawsVelocity() && Result.bOpaque && Result.bRenderInMainPass;
```

修复文件：[WorldScapeMeshComponent.cpp](<Plugins/WorldScape/Source/WorldScapeCore/Private/WorldScapeMeshComponent.cpp#L404>)。

**已排除作为单独修复的方案：**

- 一次世界原点重定位：仍可复现。
- 关闭遮挡查询：仍可复现。
- 关闭一帧渲染线程延迟：仍可复现。
- 改用 FXAA：仍可复现。

冻结地形只用于对照，不是可持续探索方案。厂商旧文档中的 `r.UseVisibilityOctree` 不能直接当作 UE 5.8 有效开关使用；本机对应的 `r.Visibility.FrustumCull.UseOctree` 检查值已为 0。

**验证及回退：**

- 热编译后 18 张、正式编译重启后 12 张移动截图未再复现该地表漏画。
- 保留默认速度通道、TSR、遮挡查询和线程延迟，恢复地形生成；没有靠冻结地形或关掉正常渲染功能掩盖问题。
- 源码备份位于 `D:\BIG WORLD UE5.8\Saved\Backups\TerrainVelocityFix`；旧 DLL 和地图保存前副本位于 `Saved\Backups\TerrainVelocityRestart_20261008_163427`。
- 需要回退时先关闭编辑器，恢复相应源码后重新编译；不要只替换运行中被占用的 DLL。升级插件时重新检查该修复是否被覆盖。

## T-008｜Live Coding 成功不等同于正式 DLL 已更新

- **发现及处理日期：** 2026年10月08日。
- **状态：** 本次已解决。
- **问题：** 热编译补丁可修复当前运行实例，但不能把它等同于普通插件 DLL 的持久构建；关闭编辑器前还有未保存地图。
- **处理：** 完成可见效果验证后，备份磁盘地图和旧 DLL，保存当前改动，检查无剩余脏资产，正常退出编辑器，再正式构建并重新打开地图。
- **验证：** 正式构建 `Succeeded`；新旧 DLL 哈希不同；重启后复测成功。
- **附带记录：** Live Coding 控制台曾输出 `.voltbl` 查找错误，但同次补丁链接和应用报告成功。最终验收另以正常编译和重启结果为准；没有把这些控制台消息单独认定为根因。
- **证据：** [正式构建日志](<Documentation/Verification/2026-10-09/Logs/TerrainVelocityFullBuild.txt>)、[最终状态](<Documentation/Verification/2026-10-09/Logs/TerrainVelocityFixVerification.json>)。

## T-009｜启动时 13 条自动化自检错误

- **发现日期：** 2026年10月08日。
- **状态：** 未解决，已做空白项目对照。
- **现象：** 日志出现 13 条 `LogAutomationTest: Error: Condition failed`。
- **排查：** 不包含 WorldScape 的独立空白基线项目也出现相同数量的记录。
- **目前结论：** 不能仅凭这些记录归因于 WorldScape 接入；尚未定位到具体引擎或环境原因。
- **当前处理：** 未屏蔽或修改自检。项目加载、MCP、地形生成和渲染修复分别有自己的验证结果，不等同于整个引擎自动化测试全部通过。
- **证据：** [EngineBaseline.log](<Documentation/Verification/2026-10-09/Logs/EngineBaseline.txt>)。

## T-010｜部分示例的关卡重载覆盖飞行前缀规则

- **发现及解决日期：** 2026年10月08日。
- **状态：** 已同步全部 13 个 Demonstration 示例并重启后核查落盘。
- **问题：** Asteroid、CubeWorld、FlatWorld_legacy、LittlePlanet、PlanetaryHeightmap 五个地图的 DefaultGameMode 指向厂商步行角色。UE 仅在地图没有 GameMode 时才采用地图名前缀规则，所以只改前缀不足以覆盖所有示例。
- **处理：** 备份项目插件内的地图，把 13 张示例的 WorldSettings.DefaultGameMode 明确设为项目 BP_WorldScapeDemoGameMode。保留前缀规则作为后续同名前缀地图的默认值。
- **验证：** 重启后重新读取 13 图配置；EarthLikePlanet、LittlePlanet、FlatWorld_legacy 的 PIE 均实际生成 FlyWorldScape。其余地图没有逐一进行完整玩法验收。
- **范围：** 独立原始插件包、Blank、WorldScape_Test、L_NewMap、StartUp_WorldScape 没有被本次批量修改。
- **证据：** [DemoMapColdVerification.json](<Documentation/Verification/2026-10-09/Logs/DemoMapColdVerification.json>)。

## T-011｜无输入时在行星表面自动漂移

- **发现及解决日期：** 2026年10月08日。
- **状态：** 双星球复测已解决，配置同步 13 个自由巡视示例。
- **根因：** FloatingPawnMovement 的 LimitWorldBounds 会在 Pawn.Z 低于 KillZ 时主动赋予向上速度。默认 KillZ 为 -1,048,575 cm；本次位置在数亿厘米负 Z 处，持续被推向世界 Z 正方向，看上去像相机前移。
- **处理：** 示例的 Enable World Bounds Checks=False；不修改引擎源码，不通过移动星球或每帧强制归零掩盖问题。
- **验证：** 原配置无按键、输入向量为 0，仍以 120 m/s 上移；关闭检查后静止。重启后在地球和月球各离地约 15 米、低于 KillZ 的位置测试约 5.67 秒，位移和速度均为 0，星球位置和旋转也未变化。
- **代价：** 这些示例不再具备默认平面 KillZ 处理；未来真正的行星步行死亡/重生需按玩法实现。
- **证据：** [PlanetIdleVerification.json](<Documentation/Verification/2026-10-09/Logs/PlanetIdleVerification.json>)；引擎依据为 `Engine/Source/Runtime/Engine/Private/FloatingPawnMovement.cpp`。

## T-012｜EarthLikePlanet 远景地表出现矩形缺块

- **发现及解决日期：** 2026年10月08日。
- **状态：** 已普通编译、重启，并以同机位截图和数值回归验证。
- **根因：** RockyWorldsNoise 的河流遮罩对可能为负数的海床高度开平方。NaN 传播到顶点和包围盒，导致整个远景 LOD 无法正确绘制。不是纹理丢失，也不是此前速度通道补丁没有跨地图生效。
- **处理：** 仅将遮罩输入改为 `FMath::Sqrt(FMath::Max(0.0, Data.HeightNormalize))`；正常负海床高度仍保留。修改作用于所有使用 RockyWorldsNoise 的地图。
- **验证：** 同样 512 点中无效高度 439→0；原本正常的 73 点高度完全一致；修复后 436 点仍是负海床高度。双星球 43 个地形/海洋 LOD 的主顶点、包围盒均无无效数值，远景连续。
- **排除项：** 关闭遮挡查询没有改变缺块；临时隐藏海洋只用于辨认层次，未作为修复保留。
- **文件及证据：** [RockyWorlds.cpp](<Plugins/WorldScape/Source/WorldScapeNoise/Private/RockyWorlds.cpp#L113>)、[数值回归](<Documentation/Verification/2026-10-09/Logs/EarthNoiseColdPIE.json>)、[带截图开发日志](<DevelopmentLog.md>)。
- **回退：** 原源码与地图在 `Saved/Backups/EarthDiagnostics_20261008`；回退源码后需关闭编辑器重新构建。更新厂商插件时保留并复核该改动。

## T-013｜地球与月球转向时瞬间过亮或过暗

- **发现及处理日期：** 2026年10月08日。
- **状态：** 已改为固定曝光并核实重启后配置。
- **原因：** 原无界后处理没有覆盖曝光范围，采用直方图自动曝光。视野从暗宇宙/月球切换到明亮地球时沿用上一方向的曝光，再逐渐适应，反方向也会产生短暂变暗。
- **最初处理：** EarthLikePlanet 的无界 PostProcessVolume 开启最小/最大曝光亮度 Override，且两值均为 1。项目扩展亮度范围关闭，数值不是 EV100。
- **同日后续：** 将项目默认自动曝光关闭，13 张示例已有的 7 个无界后处理体均固定上下限为 1，其余 6 张图继承项目默认。保留曝光补偿和调色，设置读回符合目标。
- **限制：** 固定曝光取消日夜/洞穴之间的自动适应；未来相机/后处理仍能覆盖项目默认。静态截图不能证明瞬间亮度变化的完整过程，曝光路径依据设置及引擎规则核实。
- **依据：** [Epic 自动曝光说明](https://dev.epicgames.com/documentation/unreal-engine/auto-exposure-in-unreal-engine?lang=zh-CN)。

## T-014｜IceWorldPlanet 及其他低 LOD 示例的远山突然出现

- **发现及处理日期：** 2026年10月08日。
- **状态：** 已扩展低覆盖示例并验证 Ice；没有宣称消除所有 LOD 跳变。
- **根因：** Ice 只有 6 级地形 LOD，外围网格覆盖小，移动后生成边界移到远山，表现为大片加载。厂商 FAQ 也建议此症状使用 10–12 级。
- **处理：** 大型星球和普通平面至少 12 级，实际修改 6 个地形对象；小行星、LittlePlanet、CubeNoise 保留尺寸适配。海洋、分辨率、步长和噪声参数不变。
- **验证：** 同机位 6/12 级 A/B 画面显示山脉补足；Ice 共 22 个地形/海洋 LOD 主顶点与包围盒有效；短程前后运动 33 帧包围盒无无效数值，4 张运动样本留档。全图完成配置核查，其他图未逐一视觉验收。
- **代价：** Ice 地形主顶点 188,204→367,004，约增加 95%。增加生成、内存与绘制成本；未完成前台性能基准，不承诺 FPS 提升。
- **证据及回退：** 开发日志第 16 条、`Saved/Logs/DemoQualityApplied.json`、`IceQualityMeshes.json`、`IceQualityRuntime.json`；备份位于 `Saved/Backups/DemoQuality_20261008`。

## T-015｜行星表面呈现多层方形精度分界

- **发现日期：** 2026年10月08日。
- **状态：** 已定位主要机制，尚未消除视觉分界。
- **原因：** clipmap 围绕观察位置建立方形分级网格，外层以更大步长采样高度，各层独立计算法线；高空还有 HeightAnchor 分档缩放。材质细节也可能加重层级差。不是屏幕分辨率从中心向边缘降低。
- **本次边界：** 增加 MaxLOD 解决覆盖不足，不会让所有外层网格和中心一样精细。没有盲目成倍增加分辨率或开启高成本切线计算。
- **后续：** 几何渐变、法线一致性和材质过渡见 I-004，尚未实现；原始问题截图保存在 Images。

## T-016｜自由巡视相机不能自动判断行星局部上下

- **确认日期：** 2026年10月08日。
- **状态：** 当前控制器的已知能力边界，未实施行星控制器。
- **2026年10月09日补充：** 独立 SolarSystem 地图新增 SolarExplorer，地表升降按径向上方向，带地平线辅助；旧示例的 FlyWorldScape 未替换。新控制器仍是巡视相机，不含人物/飞船动力学。
- **原因：** DefaultPawn 前后/左右按控制器方向，MoveUp_World 使用世界 UpVector。没有基于行星中心的径向上方向和姿态更新。
- **影响：** 相对地表的升降、横移随所在半球与朝向变化；换人物或飞行器模型不会改变输入算法，飞行巡视也不等同于贴地避障。
- **后续：** 人物需要自定义重力源、局部切平面输入、碰撞落地和相机；飞船需要自身坐标系的姿态/推力控制，可选径向地平线辅助。关联 I-001。

## T-017｜自动化从球心启动导致网格变换无效

- **发现日期：** 2026年10月08日。
- **状态：** 当前测试实例已恢复；球心输入的源码边界未修复。
- **复现：** Ice 无 PlayerStart，调用 LevelEditorSubsystem.editor_request_begin_play() 会从 `(0,0,0)` 启动。该引擎函数没有填入开始位置，与从有效当前相机处运行不同。
- **证据：** 移回正常位置后，主顶点全部有限，但网格组件平移和包围盒仍为 NaN。日志出现 Invalid transform，第一段自动化运动中 32 帧包围盒无效。
- **临时恢复：** 将 Pawn 移回有效地表位置，再调用 PIE 根对象 ws_force_regenerate_ws(False)，重建后地形/海洋包围盒与顶点均有效；后续运动复测 0 无效帧。没有将此临时恢复保存为地图脚本。
- **限制：** 这不同于已修复的 RockyWorlds 负海床平方根；表面规则抽样未发现 NaN，不代表零向量球心输入也安全。后续自动化应提供有效出生点，并单独处理零长度径向坐标。
- **证据：** `Saved/Logs/IceQualityRuntimeSpawnAtCenter.json`、`Saved/Diagnostics/IceLod/spawn-at-center-invalid.png` 与恢复后的 `IceQualityMeshes.json`。

## T-018｜真实天文距离与近地表渲染精度

- **发现及实现日期：** 2026年10月09日。
- **状态：** 基础分尺度方案已实现；航天器参考系切换尚未实现。
- **问题：** 太阳系距离达到数十亿公里，不能直接用远景显示网格的坐标承担近地表物理精度与导航。
- **方案：** 双精度公里坐标维护天体轨道；当前天体采用固定地表坐标系，近景按厘米绘制；远处代理等比例缩小半径和到观察者的距离，保持角大小。其他天体及照明转换到当前局部系。
- **验证：** 轨道近远点、周期闭合、月球锁定与局部/惯性坐标往返检查保存在 `Saved/SolarModelValidation.json`。
- **限制：** 代理网格位置不是真实天文坐标；穿越参考系的速度、动量、重力积分、联机坐标和存档仍需单独设计。均值球体尚未加入巨行星扁率。

## T-019｜近地表大气呈现浓重灰雾

- **发现及解决日期：** 2026年10月09日。
- **状态：** 已修正太阳系场景参数。
- **原因：** Mie 散射强度误用 1，远大于地球近似散射系数，造成数百米内植被被灰雾覆盖。
- **修复：** 地球使用 0.003996，金星采用较浓的 0.04，火星采用 0.0002；水星和月球关闭大气。地球 Rayleigh 散射、真实半径与大气厚度配套设置。
- **验证：** 调整后地球近景可见天空、海面和植被；运行截图位于 `Images/2026-10-09/earth-surface-after.png`。
- **限制：** 当前为外观近似，未完成气压/密度/温度剖面、气动、热环境及物理光度标定。

## T-020｜切换地图时旧地图 Python 引用阻止清理

- **发现及处理日期：** 2026年10月09日。
- **状态：** 操作流程已规避；未修改引擎垃圾回收机制。
- **现象：** 保存 EarthLikePlanet 后切换空地图，旧地图仍被 Python 全局变量持有，触发旧包未能清理的错误并退出。
- **处理：** 保留地图保存前后副本；在干净进程中创建新地图；脚本把世界、Actor 和组件引用限制在函数或有明确结束流程的探针内，结束时释放。恢复包元数据另外备份，避免旧自动保存覆盖较新的磁盘地图。
- **证据：** `Saved/Backups/SolarSystem_20261009` 保存地图和恢复元数据；太阳系资产生成脚本在独立作用域执行。
- **维护要求：** 不在切换地图前长期保留编辑器世界、Actor、组件或 Package 的 Python 全局引用。

## T-021｜轨道远景代理与近景地形切换仍有视觉跳变

- **确认日期：** 2026年10月09日。
- **状态：** 已建立两层显示，平滑过渡尚未实现。
- **机制：** 岩质天体在低于 70 km 时启用 WorldScape，离开到 220 km 以上时返回轨道代理，采用不同阈值避免反复切换。G/O 可直接切换巡视机位。
- **限制：** 进入地形时存在生成等待，纹理细节与云层表示会切换；目前没有跨层级形变或淡入淡出。WorldScape 的方形 clipmap 精度分界仍可能出现。
- **后续：** 见 I-004、I-007；不能把新远景代理解释成已彻底修复全部地形 LOD 跳变。

## 待补充的验证范围

其他演示地图、不同位置与速度、行星步行、Shipping 打包、联机和其他平台尚未全面验证。后续只在对应需求展开时补充测试，不把当前单图验证外推成全项目无缺陷。

## 更新约定

每个独立技术问题单独编号，以客观现象、原因和验证结果描述。新问题按 `T-022` 起递增，保留发现日期、解决日期、状态、复现方法、根因、有效/无效尝试、验证与回退方式。结论被后续证据推翻时追加纠正并关联开发日志。
