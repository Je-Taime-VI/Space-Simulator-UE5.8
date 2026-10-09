# 项目接手说明

最后整理日期：2026年10月09日（Asia/Shanghai）。

本文记录项目目标、当前实现、配置依据、验证范围和维护流程。进度以工程文件及验证报告为依据；编辑器进程、当前地图和运行状态需在接手时重新核查。

## 1. 项目目标与当前成果

项目使用 UE 5.8.2 和 WorldScape，目标是开发类似 KSP、Juno 的航天模拟器。当前阶段建立真实尺度天体场景、地表巡视和简化天体运动；航天器动力学与建造玩法尚未实现。

当前已完成：

- 建立 BigWorld C++ 空白项目并接入 WorldScape 项目插件，保留独立原始插件包。
- 配置 C++ 编译工具链、Python 工具环境、Epic 官方 Unreal MCP 和项目专用 Python 桥接 MCP。
- 创建空白地图和低开销地形验证地图。
- 为 `Demonstration_*` 示例配置飞行 GameMode，支持 WASD 和鼠标操作。
- 使用普通阴影贴图规避非 Nanite 地形的 VSM 标记工作队列溢出。
- 修复插件程序化地形的速度通道相关性，解决移动时整片地表漏画；已正式编译、重启并复测。
- 正式编译前已备份并保存示例地图的未保存改动。

2026年10月08日后续又修复了 EarthLikePlanet 的曝光、漂移与远景缺块，并同步全部 13 个演示地图。随后统一固定曝光并扩展不足的远景 LOD，各项改动见开发日志第 09—21 条；编辑器瞬时状态需在接手时重新核查。

### 2026年10月09日太阳系实现

- 新入口为 `/Game/SolarSystem/Maps/SolarSystem`，已设置为编辑器和游戏默认地图；旧 Blank 与全部示例继续保留。
- 原生类：`SolarSystemActor` 管理天体与坐标系，`SolarModel` 计算轨道/自转/地形/颜色，`SolarTerrainNoise` 接入 WorldScape，`SolarExplorerPawn` 与 `SolarExplorerGameMode` 提供巡视控制。
- 太阳、八大行星和月球共 10 个天体。地球有海洋、植被、极地冰盖和大气；月球无大气并朝向锁定；土星环含主要间隙；太阳有可见光球和引力参数。
- 天文位置为双精度公里，近处天体为厘米单位。远景代理按相同倍率缩放半径与距离以保留角大小。导航、引力与存档必须使用逻辑坐标，不能读取显示代理的变换代替。
- 当前天体采用固定地表坐标系；自转体现在其他天体和太阳方向的变化中，避免每帧搬动 WorldScape 地形。切换天体重建近景环境，不是多个完整地表同时常驻。
- 默认一倍时间，可暂停与加速；固定轨道元素、转轴方位和初始相位为简化模型，未实现 N 体动力学或精密星历。
- 新地图的径向巡视控制只作用于 SolarExplorer，旧示例仍使用 FlyWorldScape。WorldScape 原有 clipmap 方形 LOD 分界尚未根治。
- 地表近景使用解析高度保持净空，没有开启 WorldScape 碰撞或车辆物理；植被以玩家附近 HISM 实例生成，尚无持久化生态或资源采集。
- 生成与验证脚本位于 `Tools/build_solar_system.py`、`Tools/verify_solar_system.py`；原始资源在 `SourceAssets/SolarSystem`，编辑器资产在 `Content/SolarSystem`。按键与模型限制见 README 的“太阳系场景与巡视”。
- 备份目录：`Saved/Backups/SolarSystem_20261009`。保留 EarthLikePlanet 保存前后地图及原配置；保存时间晚于恢复包，因此恢复提示中的旧自动保存不应覆盖已保存的新地图。
- 验证报告：`Saved/SolarModelValidation.json`、`Saved/SolarRuntimeValidation.json`、`Saved/SolarCameraValidation.json`；10 个天体与 5 个地表的回归通过，地表静止约 6.19 秒位移为 0。正式构建日志为 `Saved/Logs/SolarBuildFinal.log`，截图位于 `Images/2026-10-09`。

## 2. 重要位置

- 远程仓库：[Space-Simulator-UE5.8](https://github.com/Je-Taime-VI/Space-Simulator-UE5.8)，默认分支 `main`。克隆需安装 Git LFS；首次打开前按 README 编译。客户端本机配置、访问令牌、编译缓存和 `Saved` 不入库。
- 长期验证证据：[Documentation/Verification](Documentation/Verification/README.md)。已归档报告为当时执行结果，不能代替接手后的重新检查。
- 项目根目录：`D:\BIG WORLD UE5.8`。
- 项目入口：[BigWorld.uproject](<BigWorld.uproject>)。
- 引擎：`E:\Epic Games\UE_5.8`，实际版本 **5.8.2 / CL 56702186**；不要仅凭目录名或 `EngineAssociation=5.8` 判断补丁版本。
- 原始 WorldScape 包：`D:\WorldScape_5.8`。保留原样，不作为日常修复目录。
- 项目插件副本：`D:\BIG WORLD UE5.8\Plugins\WorldScape`。
- 项目源码：`D:\BIG WORLD UE5.8\Source\BigWorld`。
- 配置目录：`D:\BIG WORLD UE5.8\Config`。
- 工具目录：`D:\BIG WORLD UE5.8\Tools`。
- 本地证据及备份：`D:\BIG WORLD UE5.8\Saved\Logs`、`Saved\Diagnostics`、`Saved\Backups`。
- 长期保留的截图：[Images](<Images/README.md>)。

配套文档：

- [DevelopmentLog.md：按日期记录改动与截图](<DevelopmentLog.md>)。
- [TechnicalChallenges.md：问题、解决方法及未解决项](<TechnicalChallenges.md>)。
- [IdeaBacklog.md：讨论过但未实施的方向](<IdeaBacklog.md>)。
- [README.md：日常打开、构建和操作说明](<README.md>)。

## 3. 地图与玩家控制的最终方案

### 3.1 地图入口与飞行 GameMode

- `/Game/Maps/Blank`：保留的空白地图。2026年10月09日起默认入口改为 `/Game/SolarSystem/Maps/SolarSystem`。
- `/Game/Maps/WorldScape_Test`：基础地形接入验证。种子 10、MaxLod 4、分辨率 32，不生成海洋和植被；曾验证生成 3,108 个顶点、5,378 个三角形。
- `/WorldScape/Levels/Planets_Levels/Demonstration_BarenLikePlanet`：本次移动和地表漏画的主要复现、验证地图。资源名确实拼写为 `BarenLikePlanet`，不要擅自改成 `BarrenLikePlanet`。
- `/Game/Blueprints/BP_WorldScapeDemoGameMode`：本项目新增 GameMode，默认 Pawn 为 `/WorldScape/Blueprints/PlayerLogic/FlyWorldScape.FlyWorldScape_C`。

[DefaultEngine.ini](<Config/DefaultEngine.ini>) 保留 `GameModeMapPrefixes`。后来逐图检查发现 Asteroid、CubeWorld、FlatWorld_legacy、LittlePlanet、PlanetaryHeightmap 共 5 个示例的关卡重载优先，已将项目内全部 13 个 Demonstration 地图的 WorldSettings 明确设置为该飞行 GameMode。重启后重新读取 13 张地图确认落盘；空白地图、L_NewMap 和 StartUp_WorldScape 未被此次批量改动。

### 3.2 行星平面边界检查

13 个演示地图还关闭了 `Enable World Bounds Checks`：DefaultPawn 的 FloatingPawnMovement 会在低于 KillZ 时主动向上推玩家，这正是双星球表面自动漂移的原因。不能再把默认平面 KillZ 用作行星巡视的掉落边界。步行死亡/重生机制仍未实现。

### 3.3 输入与移动能力

操作方式：选择 Play，而非 Simulate；WASD 移动、鼠标转向、E/空格上升、Q/Ctrl/C 下降。升降沿世界 Z 轴，不保证沿行星地表法线。Shift+F1 释放鼠标，F8 退出/恢复玩家控制，Esc 停止。当前飞行角色最高速度为 120 m/s，没有 Shift 冲刺绑定。

已启用本项目 `GameGetsMouseControl=True`。如果焦点切走，仍需点击运行视口。

**不要重新把所有示例直接换成厂商的 WorldScapeGamemode。** 其默认 `WorldScapePlayer` 为步行角色；在本次地图中没有获得所需重力源，地面检测为未落地，步行输入不能正常推动角色。旧式输入映射曾用于诊断，最终已撤回；现用 FlyWorldScape 继承 DefaultPawn 内置输入，无需额外 AxisMappings。

## 4. 渲染修复与必须保留的状态

地表漏画修复位于 [WorldScapeMeshComponent.cpp](<Plugins/WorldScape/Source/WorldScapeCore/Private/WorldScapeMeshComponent.cpp#L404>) 的 `FWorldScapeMeshSceneProxy::GetViewRelevance`：

```cpp
Result.bVelocityRelevance = DrawsVelocity() && Result.bOpaque && Result.bRenderInMainPass;
```

原代码强制赋值 `false`。UE 5.8 在默认速度/深度通道路径下会让移动网格跳过普通深度绘制；插件又排除了速度通道，造成地形更新帧漏写深度。修复对齐 UE 自带 ProceduralMeshComponent 的实现。

该改动已进入正式 `UnrealEditor-WorldScapeCore.dll`，不是仅存在于 Live Coding 内存补丁。升级或重新覆盖 WorldScape 时，应检查该修复是否被上游保留。

最近一次重启验证时的关键值：

- `r.Shadow.Virtual.Enable=0`：普通阴影贴图，用于规避此前 VSM 队列溢出。
- `r.VelocityOutputPass=0`：保留 UE 默认的深度阶段输出方式。
- `r.AntiAliasingMethod=4`：TSR。
- `r.AllowOcclusionQueries=1`：遮挡查询正常启用。
- `r.OneFrameThreadLag=1`：恢复正常渲染线程设置。
- 地形 `freeze_generation=False`，原点为 `(0, 0, 0)`；持续原点跟随没有实现。

原点重定位、关闭遮挡查询、关闭渲染线程延迟、改用 FXAA 均未解决本次漏画。不要把这些临时诊断状态当作最终修复，也不要把问题归因于“相机一定穿地”或单纯 VSM 警告。

### 4.1 地球远景地表缺块

另一个独立的远景地表缺块问题已在 [RockyWorlds.cpp](<Plugins/WorldScape/Source/WorldScapeNoise/Private/RockyWorlds.cpp#L113>) 修复：河流遮罩原先对可为负数的海床高度执行平方根，NaN 污染顶点和整个 LOD 包围盒。现在仅对遮罩输入使用 `sqrt(max(0, HeightNormalize))`，保留真实负海床高度。修复对所有使用 RockyWorldsNoise 的地图生效，不只 EarthLikePlanet；已普通编译并重启编辑器验证。

验证结果：512 个固定地球噪声点的无效样本由 439 降至 0，原来正常的 73 点高度完全一致；双星球 43 个地形/海洋 LOD 的主顶点和包围盒均为有限值。源码与地图备份位于 `Saved/Backups/EarthDiagnostics_20261008`，开发日志第 11 条记录前后截图与正式构建证据。

### 4.2 固定曝光

EarthLikePlanet 最初单独固定曝光，后续扩展为项目默认：项目 `r.DefaultFeature.AutoExposure=False`，全部 13 个演示地图中的 7 个无界后处理体均固定 `auto_exposure_min_brightness=auto_exposure_max_brightness=1`，两个 Override 开启；另外 6 张图继承项目默认。当前项目扩展曝光亮度范围关闭，这些是亮度值，不是 EV100。保留各图曝光补偿和调色。以后新增的相机/后处理仍能覆盖默认值；固定曝光会取消夜面、洞穴的自动提亮。

单图调整见开发日志第 12 条，全示例统一见第 15 条。

### 4.3 双星球结构与海洋层

EarthLikePlanet 中的 Planet 与 PlanetBp2 是两个独立地形对象，半径分别约 6,378 千米和 3,189 千米，不对应现实地月尺寸比例。

双星球的海洋生成均为开启，材质为 `MI_Planetary_Ocean` 的动态实例。地表内部看见的水/绸缎状层是海洋网格，并非实心星球内部；编辑器自由镜头能够穿过没有厚度的地表外壳。未删除海洋层。

对象结构和海洋层分别见开发日志第 13、14 条。

### 4.4 远景地形覆盖

大型行星、普通平面地形采用至少 12 级地形 MaxLOD。实际补足 6 个对象：IceWorldPlanet 6→12、PlanetaryHeightmap 8→12、FlatWorld_Lava 的平面 9→12，以及 EarthLikePlanet、TerraFormedMoon、FlatEarth 各自的月球风格伴星 11→12。原来达到 12 的对象不变；Asteroid 小行星、LittlePlanet 和 CubeNoise 特例保留。海洋 LOD、地形分辨率、三角形尺寸、HeightAnchor、噪声资产没有改成统一数值。

Ice 同机位前后截图证明原先被截断的远山已补足。地形主顶点 188,204→367,004，约增加 95%；不是帧率提升。增加远景范围会增加内存、生成、绘制和阴影开销。

配置范围与前后截图见开发日志第 16 条。

### 4.5 跨示例噪声数值检查

13 图共 19 个地形对象各抽检 256 个噪声点，4,864 点均为有效数值。平面只抽样中心 20 km 区域；不能外推为任意位置和参数无缺陷。Ice 的 12 级地形与 10 级海洋检查无无效主顶点/包围盒。

完整抽样范围见开发日志第 19 条。表面抽样不包含球心输入边界。

### 4.6 方形 LOD 精度分界

截图的同心方块来自 clipmap 网格按 2 倍步长分级、各级独立采样和计算法线；升高时网格还会按 HeightAnchor 分档缩放。增加 MaxLOD 扩展覆盖，不等同于消除精度分界。平滑过渡/法线一致性仍未实现，见 I-004、T-015。

### 4.7 行星局部上下方向

当前 FlyWorldScape 沿控制器方向前后飞行，升降沿世界 Z，不自动采用 `(位置−星球中心)` 作为局部上方向。换模型不会补全重力/姿态逻辑。人物需要径向重力、落地/碰撞和切平面输入；飞船需要自身姿态控制，可另外选择地平线辅助。

### 4.8 球心出生的无效变换

本机 `LevelEditorSubsystem.editor_request_begin_play()` 未提供出生位置；Ice 没有 PlayerStart 时会从球心 `(0,0,0)` 启动，导致网格变换 NaN。不是本次 MaxLOD 导致，也不同于已修复的 RockyWorlds 海床平方根。恢复地表位置后调用 PIE 根对象 `ws_force_regenerate_ws(False)` 可重建恢复；球心输入边界尚未通过源码修复。后续自动化应提供有效出生点，交互运行可从有效当前相机位置开始。

复现、恢复和未解决状态见开发日志第 21 条、T-017。

### 4.9 验证脚本与备份

- `Tools/audit_demo_maps.py` 的 `apply=True` 会备份并保存地图；`verify_planet_noise.py` 检查噪声和网格；`verify_planet_idle.py` 临时移动 PIE Pawn 后恢复。
- `Tools/configure_demo_quality.py` 默认只读，`apply=True` 会备份并保存地图；`verify_demo_quality_runtime.py` 临时移动 PIE Pawn，完成后恢复位置和朝向。
- 控制及地球噪声修复证据位于 `Saved/Logs/Earth*`、`DemoMap*`、`PlanetIdleVerification.json`，对应备份在 `Saved/Backups/EarthDiagnostics_20261008`。
- 曝光与远景调整证据位于 `Saved/Logs/DemoQuality*`、`IceQuality*`，对应备份在 `Saved/Backups/DemoQuality_20261008`。修改类脚本不宜无目的重跑，以免覆盖后续艺术设置。

## 5. 工具链与常用命令

已验证工具链：Visual Studio 2022 Community、MSVC 14.44.35228、Windows SDK 10.0.26100.0、UE 自带 .NET 10。Python 工具环境在 `D:\BIG WORLD UE5.8\Tools\.venv`，依赖由 `pyproject.toml` 和 `uv.lock` 管理。

打开项目：

```powershell
& 'D:\BIG WORLD UE5.8\Tools\OpenEditor.ps1'
```

普通编译前先保存必要改动并关闭编辑器，避免 DLL 占用。重新生成工程与构建：

```powershell
& 'D:\BIG WORLD UE5.8\Tools\Build.ps1' -GenerateProjectFiles
& 'D:\BIG WORLD UE5.8\Tools\Build.ps1'
```

恢复 Python 工具依赖（需要 `uv` 可用）：

```powershell
& 'D:\BIG WORLD UE5.8\Tools\SetupTools.ps1'
```

`bootstrap_project.py` 用于创建初始化资产，已执行完成，不作为常规启动脚本重复运行。

## 6. MCP：两条连接都保留

### Epic 官方 Unreal MCP

- UE 5.8.2 自带实验性 `ModelContextProtocol` 插件；本项目还启用了 `AllToolsets`。
- MCP 客户端注册的服务名为 `unreal`，地址为 `http://127.0.0.1:8000/mcp`。
- 编辑器设置中端口为 8000、路径为 `/mcp`、自动启动和工具搜索均开启。
- 工具搜索模式下顶层只有 `list_toolsets`、`describe_toolset`、`call_tool`，不代表连接失败。
- 已验证 HTTP 握手、工具发现、关卡读取和后续截图调用。此前发现 52 个工具集，但数量会随启用插件变化。
- 官方 MCP 设置目前还依赖 `D:\BIG WORLD UE5.8\Saved\Config\WindowsEditor\EditorPerProjectUserSettings.ini`。清理 Saved 或换机器时需要重新检查，不能认为全部设置都随项目配置迁移。

检查官方服务：

```powershell
& 'D:\BIG WORLD UE5.8\Tools\.venv\Scripts\python.exe' 'D:\BIG WORLD UE5.8\Tools\check_official_mcp.py'
```

该脚本为本机 HTTP 客户端设置 `trust_env=False`，避免 Windows 系统代理把回环请求转发后产生 502。没有为此关闭系统代理。

### 项目专用 Python 桥接 MCP

- 服务名为 `unreal_bigworld`，使用 stdio、官方 MCP Python SDK 和 UE 官方 PythonScriptPlugin Remote Execution。
- 启动程序为 `D:\BIG WORLD UE5.8\Tools\.venv\Scripts\python.exe`，服务脚本为 `D:\BIG WORLD UE5.8\Tools\unreal_mcp.py`。
- 提供 `editor_status`、`list_level_actors`、`list_assets`、`execute_python`。
- 按项目路径筛选编辑器，只连接本项目；避免同时打开多个 BigWorld 实例。
- 发现地址 `239.0.0.1:6766`，绑定 `127.0.0.1`、TTL 0；命令连接为本机 `127.0.0.1:6778`。
- 项目连接配置与客户端全局配置已同步。启动客户端后需核实服务实际加载状态；迁移机器时按上述启动程序、脚本和端点恢复连接。

检查桥接协议及编辑器连接：

```powershell
& 'D:\BIG WORLD UE5.8\Tools\.venv\Scripts\python.exe' 'D:\BIG WORLD UE5.8\Tools\check_mcp.py' --live
```

Epic 官方插件、第三方同名 UnrealMCP 项目与项目 Python 桥接是独立实现。当前保留已验证的官方插件和 Python 桥接，未安装第三方同名项目。

## 7. 项目接手流程

1. 阅读本文与最新开发日志，再查看技术问题清单。
2. 核定当前开发范围；IdeaBacklog 为候选方向，不等同于已排期任务。
3. 检查引擎版本、项目目录和编辑器实例；需要操作 UE 时再测试 MCP。
4. 先判断是否处于 PIE。使用 `get_game_world()` 读取运行世界；没有运行世界时再使用 `get_editor_world()`，不要在 PIE 中假定后者一定返回有效对象。
5. 优先使用已发现的工具和已验证脚本。UE Python 名称可能与 C++ 名称不同，先查签名再调用；`execute_python` 外层 `isError=False` 也可能包着内部 `success=False`，必须检查实际结果。
6. 修改插件前备份项目副本。遇到超时先检查是否已执行，避免盲目重复修改。
7. 关闭编辑器前检查未保存地图和资产，先备份磁盘版本并保存现有改动，禁止直接丢弃未保存内容。
8. 完成工作后同步维护项目文档。每个独立问题、功能和验证事项分别记录，采用客观技术表述；可见变化的前后截图归档至 Images 并嵌入对应日志。

## 8. 已知边界与后续检查

- 尚未逐一验证全部演示地图，也未进行 Shipping 打包、多人联机和目标平台验证。
- 飞行移动验证通过向 Pawn 注入移动输入完成，不等同于自动化按下物理键盘进行测试。
- 本次地表修复验证包含热编译后的 18 张移动截图、正式编译重启后的 12 张移动截图；不能扩展为所有地图和所有摄像机路径均无问题。
- UE 启动时的 13 条 `LogAutomationTest: Error: Condition failed` 在不含 WorldScape 的空白基线项目也复现，尚未解决；不能声称引擎所有自动化测试通过。
- 厂商代码仍有浮点转换和弃用 API 警告；本次构建成功不表示这些警告已全部清理。
- `Saved` 被 `.gitignore` 排除。若迁移项目且需要完整证据、备份及本机编辑器配置，应额外保留；精选截图已复制到不在该忽略项中的 `Images`。
- 配置可能含本机服务凭据。后续日志、文档只记录必要设置，不整段复制可能含令牌的配置文件。
- 本文链接使用当前项目绝对路径；项目搬迁后需要更新链接及 MCP 路径。

## 9. 接手检查要点

- 阅读本说明、最新开发日志和技术问题清单，按独立事项核查状态。
- 工程采用 UE 5.8.2；WorldScape、官方 MCP 和 Python 桥接已有实际验证记录。
- Demonstration 示例使用 FlyWorldScape；速度通道和 RockyWorlds 噪声修复已正式编译并重启验证。
- 固定曝光和远景层级已保存；方形 LOD 分界、局部上下控制和球心输入边界仍有未完成项。
- 继续开发前核实当前编辑器、地图及未保存内容，保留既有修复并同步更新文档和图片档案。
