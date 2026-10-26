# BigWorld / UE 5.8.2

WorldScape 已作为项目插件接入：`Plugins/WorldScape/`。原始包保留在 `D:\WorldScape_5.8`。本项目使用 `E:\Epic Games\UE_5.8`，其 Build.version 为 **5.8.2 / CL 56702186**。

## 从仓库恢复工程

仓库：[Space-Simulator-UE5.8](https://github.com/Je-Taime-VI/Space-Simulator-UE5.8)。UE 资源、纹理和截图通过 Git LFS 保存；下载 ZIP 不能替代完整的 LFS 克隆。

```powershell
git lfs install
git clone https://github.com/Je-Taime-VI/Space-Simulator-UE5.8.git
Set-Location Space-Simulator-UE5.8
git lfs pull
# 按实际引擎安装位置调整
$env:UE_ENGINE_ROOT = 'E:\Epic Games\UE_5.8'
New-Item -ItemType Directory -Force -Path Saved/Logs | Out-Null
& ./Tools/Build.ps1 -GenerateProjectFiles
& ./Tools/Build.ps1
& ./Tools/OpenEditor.ps1
```

需要 UE 5.8.2、Visual Studio 2022 C++ 游戏开发工具链和 Windows SDK；已通过构建的具体版本见下文。仓库包含项目内 WorldScape 插件源码和资源，编译产物、缓存、`Saved`、工具虚拟环境及本机客户端配置不入库。首次打开前应完成编译；构建时关闭编辑器。

需要 Python 工具时，安装 `uv` 后运行 `./Tools/SetupTools.ps1`，按 `Tools/uv.lock` 恢复依赖。MCP 客户端连接需在本机单独配置，不随仓库复制登录信息或访问令牌。文档中的 `D:\BIG WORLD UE5.8` 是原开发目录，在其他机器上应替换为实际克隆路径。

长期验证证据位于 [Documentation/Verification](Documentation/Verification/README.md)，开发截图位于 [Images](Images/README.md)。`Saved` 路径指本机运行输出或备份，克隆后不会自动包含它们；已归档证据的文档链接指向版本库内的副本。

## 项目记录与维护交接

- [ContinuationGuide.md：项目接手说明](<ContinuationGuide.md>)。
- [DevelopmentLog.md：按年月日记录的开发日志与前后截图](<DevelopmentLog.md>)。
- [IdeaBacklog.md：提及但尚未实施的想法](<IdeaBacklog.md>)。
- [TechnicalChallenges.md：技术问题、状态和解决方法](<TechnicalChallenges.md>)。
- [Images：截图来源与归档规范](<Images/README.md>)。

## 打开项目

双击 `BigWorld.uproject`，或运行：

```powershell
& 'D:\BIG WORLD UE5.8\Tools\OpenEditor.ps1'
```

- 默认关卡：`/Game/SolarSystem/Maps/SolarSystem`，航天模拟器的太阳系场景基础。
- 空白地图：`/Game/Maps/Blank`，继续保留。
- 地形接入测试：`/Game/Maps/WorldScape_Test`。固定种子 10，4 级 LOD、32 分辨率，无海洋和植被，使用基础材质，便于验证基础地形生成。
- 原插件演示：内容浏览器启用“显示插件内容”，打开 `WorldScape Content/Levels`。未逐一测试全部演示。

## 太阳系场景与巡视

2026年10月09日新增独立太阳系：太阳、水星、金星、地球、月球、火星、木星、土星、天王星和海王星。平均半径与轨道距离采用真实量级，程序化地貌和纹理不还原真实大陆。地球包含海洋、植被、两极冰盖及大气；月球无大气并保持朝向地球；土星有条带和环；太阳具有可见光球、半径和引力参数，同时驱动照明。

打开默认地图后选择 Play：

编辑视口关闭实时显示时，预览可能停留在尚未刷新的材质状态；可使用 Ctrl+R 开启实时显示，或直接 Play。天体组件会在地图加载时重建，不需要重新运行资产生成脚本。

- 数字 `0—9`：按上述顺序切换天体，`3` 是地球、`4` 是月球。
- WASD 连续飞行，鼠标转向，Q/E（或空格上升）沿行星径向升降。**按住左 Shift 逐渐加速，按住左 Ctrl 逐渐减速，松开保持手动速度**；从当前实际速度起调，默认4秒翻倍/减半。**两键同时按住恢复自动速度**，全部松开后才接受下一次单键调节。手动速度绕过贴地速度/位移上限，仍保留解析地面最低3 m净空及长帧保护。滚轮每格×1.2或÷1.2，手动时调当前速度，自动时调速度上限。HUD标明自动/手动，Ctrl不承担下降；这不是飞船碰撞或动力学。
- 已移除 G/O 巡视模式切换；从太空直接飞向地表，地形预加载和渐变不会重置相机。数字键仍是可选的天体机位书签。太阳和巨行星没有可着陆的固体地表。
- `,` / `.`：减小 / 增大时间倍率，最大十万倍；`P` 暂停 / 恢复一倍时间；Home 回到 J2000 起点。
- 地表巡视使用径向上方向及地平线辅助，按解析地形高度保留最低净空；这是巡视相机，不是带碰撞与动力学的人物或飞船。

天文位置采用双精度公里坐标。近处天体和地形按 1 UE 单位 = 1 cm 绘制；遥远天体的显示代理同时缩放距离与半径，保持视角大小，逻辑距离仍是真实公里数。切换天体会切换局部坐标系。这是分尺度渲染，不能把远景网格的 UE 坐标直接当作导航或引力计算坐标。

自转、公转已实现。轨道采用固定 J2000 元素的开普勒椭圆，月球保持朝地经度锁定。2026年10月10日按 IAU 极轴方位重建转轴，轴倾角相对各自轨道法线计算；天王星为 97.77°，金星和天王星使用逆行自转。仍未实现真实本初子午线初相、完整月球天平动、多体摄动、岁差、精密日期星历、航天器引力积分和气动。显示照明经过曝光归一化，尚未完成绝对光度标定。

2026年10月10日改为远近景共用程序化地表颜色与高度函数，近景增加细节；地球、金星使用可穿过的球形体积云，当前天体的大气从地面到太空连续保留。云层使用预计算覆盖图和64³周期三维密度纹理，采用逐像素直接绘制与0.25视线采样倍率（2026年10月17日关闭中间渲染目标，避免远距离云深度量化漏画），保留可穿越的体积。已定向检查金星轮廓、地球整球、20 km与云内平移；仍有额外计算和显存开销，不承诺任意急转均无噪点。火星冰云、季节云与谷雾留待天气细化（I-008）。巨行星已有散射大气，条带仍为云顶外观近似，1 bar 只作为半径参考；深层云海和压强剖面未实现，巡视相机仍限制进入参考球内部。海王星采用偏蓝的浅蓝青色，未采用常见增强色照片中的饱和深蓝。

主小行星带预留 2.1—3.3 AU，柯伊伯带预留 30—50 AU；只定义区域边界，尚未生成带内天体。地球半径 6371.0084 km，月地半长轴 384400 km，海王星半长轴约 30.0699 AU。全体仍采用平均半径球体，未加入扁率。

源码位于 [Source/BigWorld/SolarSystem](<Source/BigWorld/SolarSystem>)；资产位于 `Content/SolarSystem`；程序化材质函数位于 [SolarSurface.ush](Shaders/SolarSurface.ush)。完整生成工具 [build_solar_system.py](Tools/build_solar_system.py) 会调用 [refine_solar_materials.py](Tools/refine_solar_materials.py)，也可单独执行后者更新连续飞行材质；重新生成前应备份材质。当前验证工具 [verify_continuous_planets.py](Tools/verify_continuous_planets.py) 在 SolarSystem 的 PIE 中执行，暂时冻结巡视输入，采集逐天体视图与连续下降轨迹，结束后恢复输入。

参数依据：[JPL 行星轨道元素](https://ssd.jpl.nasa.gov/planets/approx_pos.html)、[行星物理参数](https://ssd.jpl.nasa.gov/planets/phys_par.html)、[天然卫星物理参数](https://ssd.jpl.nasa.gov/sats/phys_par/)。实际实现是游戏原型模型，不是 JPL 精密星历。

## 示例关卡与飞行配置

项目内全部 13 个 `Demonstration_*` 地图已明确设置 `/Game/Blueprints/BP_WorldScapeDemoGameMode`，默认玩家是插件自带的 `FlyWorldScape`。此前仅设置 `GameModeMapPrefixes`，会被 5 个厂商地图自带的 GameMode 重载覆盖；现已同步这些例外，前缀规则继续保留。独立原始插件包没有修改，空白地图仍使用 `GameModeBase`。

使用“在选定视口中运行 / Play”，不要选择“模拟 / Simulate”。已开启本项目的 `GameGetsMouseControl`；如果视口失去焦点，点击画面后再操作。

- WASD：前后左右飞行；鼠标：转动视角。
- E / Space：沿世界 Z 轴上升；Q / Ctrl / C：沿世界 Z 轴下降（不是始终沿行星地表法线）。
- Shift+F1：释放鼠标；F8：退出/恢复玩家控制；Esc：结束运行。
- `FlyWorldScape` 自带加速度，最高速度为 120 m/s，没有 Shift 冲刺绑定。

插件还有带重力的 `WorldScapePlayer` 步行角色，但它依赖重力源和地面检测。实测 `Demonstration_BarenLikePlanet` 没有提供该角色需要的重力源，直接套用 `WorldScapeGamemode` 会让角色处于未落地状态，无法正常步行。需要步行玩法时应另行配置重力、碰撞和该角色的旧式输入映射；自由飞行使用 UE DefaultPawn 自带输入，无需项目 AxisMappings。

检查记录：`Saved/Logs/DemoFlyMovementVerification.json`。可在示例的 PIE 运行实例中执行 `Tools/verify_demo_flight.py`，验证飞行 Pawn 的控制关系、视角与前后/横向移动输入；该检查不会修改地图，也不模拟物理键盘按键。

## 行星表面的自动漂移

这 13 个自由巡视示例均关闭 `Enable World Bounds Checks`，避免行星表面低于默认 `Kill Z` 时飞行组件持续向世界 Z 正方向推玩家。它们不再通过该平面边界处理掉落；未来加入步行死亡/重生玩法时应另行设计。

## 曝光

项目默认关闭自动曝光，13 个示例已有的无界后处理体将曝光亮度上下限固定为 1，保留曝光补偿和调色；没有后处理体的地图继承项目默认。转向亮暗物体后不再进行曝光适应，夜面和洞穴也不会自动提亮。新增相机或后处理可以覆盖默认设置。单图调整和全示例统一分别见开发日志第 12、15 条。

2026年10月11日起，SolarSystem 单独使用正常受光材质与局部 Manual 后处理：太阳照度以1 AU处120000 lux为基准，按距离平方反比衰减；相机ISO100、f/16、1/125秒。默认按日心距离补偿曝光，便于外行星巡视，转向不会触发明暗适应。管理器的 `ExposureCompensation` 可调整体亮度，`bCompensateExposureForSolarDistance` 可关闭距离补偿。近地天空光只用于有大气的岩质天体，夜面及无大气天体不补光。这些设置不改变厂商示例。验证见 [受光校准记录](Documentation/Verification/2026-10-11/SurfaceLighting/README.md)。

2026年10月12日接入示例的沙、岩石、土壤及雪资源，包含颜色、细节法线与基础粗糙度/AO，按天体、坡度、海拔和纬度混合。纹理最高2K并流式加载，以米级三平面投影贴合球面，300—2500 m视距内淡出。单独重建使用 [refine_solar_ground.py](Tools/refine_solar_ground.py)，完整材质生成也会保留这些层；应在SolarSystem编辑状态运行，重建前备份材质。具体参数、截图及验证见 [材质接入记录](Documentation/Verification/2026-10-12/SurfaceMaterials/README.md)。岩石实体散布、纹理去重复、湿沙、完整海水及真实高程仍未完成，不能将细节贴图等同于整体示例画质。

## 远景地形覆盖与 LOD

太阳系地表分区已统一到 [SolarBiomeRules.inl](Source/BigWorld/SolarSystem/SolarBiomeRules.inl)：地球使用程序化湿润度、纬度、海拔和坡度区分海岸、干旱区、植被区、岩地与雪区；其他岩质天体使用独立表土/岩石/极区规则。轨道颜色、近地材质和植被共享这份逻辑。修改分区后需编译C++并重新生成全部太阳系材质；只刷新近地材质不够。大陆轮廓与原有地形高度保持不变，当前分区不是观测数据复原。见 [分区验证记录](Documentation/Verification/2026-10-12/SurfaceRegions/README.md)。

大型星球和普通平面的远景地形 MaxLOD 已补足到至少 12；IceWorldPlanet 原为 6，因此改善最明显。小行星、LittlePlanet 及 CubeNoise 特例保留原设置，近景网格分辨率与各自噪声不变。增加远景层级会增加生成、显存/内存和绘制开销，不能等同于帧率优化。围绕观察位置的方形精度分界仍存在，平滑 LOD 过渡尚未实现。前后截图与验证范围见开发日志第 16 条。

## 地球远景缺块

EarthLikePlanet 包含地球风格与 Selenae 月球风格两个独立星球。地球远景矩形缺块由 `RockyWorlds.cpp` 对负高度开平方产生 NaN 导致，已修复并正式编译、重启验证；修复对所有使用该噪声算法的地图生效。详细回归结果见开发日志第 11 条。

## 非 Nanite 地形阴影

WorldScape 使用动态非 Nanite 地形网格。当前项目选择普通阴影贴图：`Config/DefaultEngine.ini` 中 `r.Shadow.Virtual.Enable=0`，避免大范围地形引发 VSM 非 Nanite 标记队列溢出。方向光仍投射阴影，但远处阴影的覆盖与质量不同于 VSM。若之后重新开启 VSM，需要针对非 Nanite 地形的阴影覆盖与 LOD 单独调优；这条警告不等同于虚拟阴影物理页池耗尽。

## 移动时地表漏画

移动时地表整片消失、露出岩石下半部是另一个渲染问题。此包的 `WorldScapeMeshComponent.cpp` 把 `FPrimitiveViewRelevance::bVelocityRelevance` 强制设为 `false`。在 UE 5.8 默认 `r.VelocityOutputPass=0` 下，移动的 clipmap 地形会跳过普通深度绘制，转入速度/深度通道；强制关闭速度相关性会使它漏写深度。项目副本已将该行恢复为 UE 自带 `ProceduralMeshComponent` 的实现：`DrawsVelocity() && Result.bOpaque && Result.bRenderInMainPass`。原始插件包保持不变，修改前文件另存于 `Saved/Backups/TerrainVelocityFix/`。

诊断工具 `Tools/capture_flicker_probe.py` 在已有 PIE 运行实例中暂时往返移动玩家并截图，同时对比地形更新/冻结状态，结束时恢复玩家位置和速度。截图与高度采样位于 `Saved/Diagnostics/`。原点重定位、关闭遮挡查询、关闭渲染线程延迟、切换 FXAA 的对照均未解决这次漏画问题；它们不作为永久修复配置。

2026-10-08 修复验证：热编译后同场景的 18 张连续移动截图未再出现整片地表消失，正常渲染设置均恢复。随后备份并保存当前未保存地图，关闭编辑器完成正式编译（`Saved/Logs/TerrainVelocityFullBuild.log`，`Result: Succeeded`）。地图保存前副本及旧 DLL 位于 `Saved/Backups/TerrainVelocityRestart_20261008_163427/`。`Saved/Diagnostics/TerrainFlickerFrameMetrics.json` 为相同视口区域的黑像素比例辅助记录，只适用于这次场景对照，不是所有场景的通用判定。

重启后又完成 12 张连续移动截图复测，未复现地表漏画。正式 DLL 已更新；无需依靠 Live Coding 补丁。最终状态记录在 `Saved/Logs/TerrainVelocityFixVerification.json`：地形持续生成，玩家速度恢复为 120 m/s，原点重定位测试已撤回，TSR、遮挡查询和渲染线程延迟均保持原设置。

## C++ 工具链

已验证 MSVC 14.44.35228、Windows SDK 10.0.26100.0 和 UE 自带 .NET 10。`BigWorld.sln` 为生成的 Visual Studio 2022 工程。

```powershell
& 'D:\BIG WORLD UE5.8\Tools\Build.ps1'
& 'D:\BIG WORLD UE5.8\Tools\Build.ps1' -GenerateProjectFiles
```

编译前关闭编辑器。插件源码有浮点精度转换及弃用 API 警告；以构建日志中的 `Result: Succeeded` 判断构建结果。

## MCP 与 Python

官方 Unreal MCP 已启用（`ModelContextProtocol`、`AllToolsets`），客户端注册的服务名为 `unreal`，地址 `http://127.0.0.1:8000/mcp`。编辑器启动后自动运行；关闭编辑器则服务停止。启用了工具搜索，因此顶层只有 `list_toolsets`、`describe_toolset`、`call_tool` 三个入口，其余操作按需发现。

2026-10-08 已直接通过官方 HTTP MCP 接口完成握手、工具集发现和 `SceneTools.get_current_level` 只读调用，返回 `/Game/Maps/Blank`。记录见 `Saved/Logs/OfficialMCPVerification.json` 与 `OfficialMCPReadOnlyCall.json`。客户端未显示官方入口时，保持 UE 项目打开并重新建立 MCP 连接。检查脚本 `Tools/check_official_mcp.py` 对本机服务采用直连，避免 Windows 系统代理将回环请求转发后返回 502。

以下 Python 桥接另行保留：

专用服务名：`unreal_bigworld`。使用 UE 官方 PythonScriptPlugin 的 Remote Execution 接口，MCP SDK 位于 `Tools/.venv`，依赖版本固定在 `Tools/uv.lock`。没有向 UE 的 Python 环境安装第三方包。

项目连接配置与客户端全局配置已同步。项目配置按客户端的目录信任设置加载；新增工具未显示时，重新连接服务或重启客户端，无需重装插件。

编辑器打开且 Python 初始化完成后，可使用：

- `editor_status`：引擎、项目、当前地图及 WorldScape 类状态。
- `list_level_actors`：当前关卡 Actor。
- `list_assets`：`/Game`、`/WorldScape` 资源。
- `execute_python`：执行编辑器 Python 操作，可修改场景与资源。

桥接只选择本目录的编辑器；UDP 发现为 `239.0.0.1:6766`，绑定 `127.0.0.1`、TTL 0；命令连接使用本机 `127.0.0.1:6778`。同一项目只打开一个编辑器实例。该接口能执行 Python，仅供本机开发使用。

```powershell
# 依赖恢复
& 'D:\BIG WORLD UE5.8\Tools\SetupTools.ps1'
# MCP 协议及实际编辑器连接验证
& 'D:\BIG WORLD UE5.8\Tools\.venv\Scripts\python.exe' 'D:\BIG WORLD UE5.8\Tools\check_mcp.py' --live
```

更换引擎位置时，为工具设置 `UE_ENGINE_ROOT`；移动项目目录后，更新 MCP 客户端配置中的绝对路径。

验证记录位于 `Saved/Logs/`：`BuildEditor.log`、`GenerateProjectFiles.log`、`BootstrapReport.json`、`MCPVerification.json`、`TerrainVerification.json`。实际地形测试生成了 3,108 个顶点、5,378 个三角形，完成后已切回空白关卡。当前验证范围是 Win64 编辑器接入；未进行 Shipping 打包或所有原厂演示的全面测试。

UE 启动日志出现 13 条 `LogAutomationTest: Error: Condition failed`。不含 WorldScape 的独立空白对照项目也复现相同 13 条记录（`Saved/Logs/EngineBaseline.log`），因此并非仅在此次插件接入中出现；未修改或屏蔽引擎自检。上述项目加载、MCP 和地形生成验证均通过，但不将其表述为整个引擎自动化测试通过。

配置依据：本机 UE 5.8.2 `PythonScriptPlugin/Content/Python/remote_execution.py`、[MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)。
