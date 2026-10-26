# 开发日志

日期按 Asia/Shanghai 记录，精确到年月日。同日按实际工作先后分项；没有可靠时间证据的步骤不补写时分。

每条只记录一个独立问题、功能或验证事项，包含客观现象或目标、原因、实际改动、验证结果、限制和相关证据。尚未实施的方向记录于 [IdeaBacklog.md](<IdeaBacklog.md>)。

## 2026年10月08日

### 01｜建立 UE 5.8.2 空白项目并接入 WorldScape

**需求：** 将现有 WorldScape 插件包接入 UE 5.8.2 空白项目，并配置匹配的编译工具链。

**完成内容：**

- 创建 `D:\BIG WORLD UE5.8\BigWorld.uproject` 及 BigWorld C++ 游戏模块、游戏和编辑器构建目标。
- 使用 `E:\Epic Games\UE_5.8`，核实实际版本为 5.8.2 / CL 56702186。
- 将 WorldScape 放入项目插件目录，保留 `D:\WorldScape_5.8` 原始包。
- 配置 VS 2022、MSVC 14.44.35228、Windows SDK 10.0.26100.0 和 UE 自带 .NET 工具链，完成编译。
- 创建 `/Game/Maps/Blank` 和 `/Game/Maps/WorldScape_Test`，后者用于低开销地形生成检查。
- 创建构建、打开编辑器和初始化工具脚本。

**验证：** WorldScape 类可加载，资产注册表发现 653 个插件资产；测试地形记录了 3,108 个顶点、5,378 个三角形。验证范围为 Win64 编辑器接入。

证据：[BootstrapReport.json](<Documentation/Verification/2026-10-09/Logs/BootstrapReport.json>)、[TerrainVerification.json](<Documentation/Verification/2026-10-09/Logs/TerrainVerification.json>)。

**截图：** 未留存接入前后的成对截图，验证依据为资产与地形生成报告。

### 02｜配置 Python 桥接与 MCP

**需求：** 为后续自动化检查和编辑器操作提供工具连接。

**完成内容：**

- 建立项目内 Python 虚拟环境及锁定依赖。
- 使用 UE 官方 Python Remote Execution 实现按项目绑定的桥接。
- 建立 `unreal_bigworld` stdio MCP，提供编辑器状态、Actor 列表、资产列表和 Python 执行工具。
- 在项目中保留 MCP 配置副本，并注册客户端连接。
- 为 Windows 管道输入增加 `utf-8-sig` 解码，兼容 PowerShell 输出的 UTF-8 BOM。

**验证：** 完成 MCP 握手、四个工具的发现及实际编辑器调用；Python 执行结果需要进一步检查内层 `success` 字段。

证据：[MCPVerification.json](<Documentation/Verification/2026-10-09/Logs/MCPVerification.json>)。脚本：[ue_bridge.py](<Tools/ue_bridge.py>)、[unreal_mcp.py](<Tools/unreal_mcp.py>)、[check_mcp.py](<Tools/check_mcp.py>)。

### 03｜验证 Epic 官方 Unreal MCP 连接

**检查目标：** 核实内置 MCP 插件启用状态、工具发现和编辑器实际调用结果。

**配置与验证：**

- UE 5.8.2 内置 Epic 实验性 `ModelContextProtocol` 插件，项目已启用该插件与 `AllToolsets`。
- 服务在 `http://127.0.0.1:8000/mcp` 自动启动，HTTP 握手、工具集发现和当前关卡读取成功。
- 工具搜索模式提供 `list_toolsets`、`describe_toolset`、`call_tool` 三个顶层入口；验证时发现 52 个工具集，数量随启用插件变化。
- 官方 MCP 与 Python 桥接分别保留；第三方同名 UnrealMCP 未安装。

**限制：** 官方插件为实验性功能，连接依赖编辑器进程。部分服务设置位于 Saved 下的编辑器配置中，清理目录后需重新核查。

证据：[OfficialMCPVerification.json](<Documentation/Verification/2026-10-09/Logs/OfficialMCPVerification.json>)、[OfficialMCPReadOnlyCall.json](<Documentation/Verification/2026-10-09/Logs/OfficialMCPReadOnlyCall.json>)。

### 04｜修复本机 MCP 请求被系统代理转发后返回 502

**问题：** HTTP 客户端读取系统代理配置，将本应直连的回环请求转发，导致本机 MCP 调用返回 502。

**处理：** 检查与截图脚本使用 `httpx.AsyncClient(..., trust_env=False)`，对本机服务直接连接。

**验证：** 直连后的协议握手、关卡读取和截图成功。Windows 系统代理保持原配置，其他客户端的代理行为不在此次验证范围内。

文件：[check_official_mcp.py](<Tools/check_official_mcp.py>)。关联：T-003。

### 05｜规避 VSM 非 Nanite 标记工作队列溢出

**问题：** 打开 `Demonstration_BarenLikePlanet` 后，渲染日志出现 VSM 非 Nanite 标记工作队列溢出警告。

**原因：** WorldScape 使用动态非 Nanite 网格，大范围地形阴影覆盖超出标记任务队列容量。

**处理：** 项目设置 `r.Shadow.Virtual.Enable=0`，使用普通阴影贴图。

**验证与限制：** 对应测试期间未再出现该警告；远处阴影覆盖和质量与 VSM 不同。此项为替代配置，VSM 路径本身尚未完成性能优化，标记队列也不等同于物理页池。

配置：[DefaultEngine.ini](<Config/DefaultEngine.ini>)。修改前备份：`Saved/Backups/DemoControls_20261008_153942`。未留存此项的成对截图。关联：T-006。

### 06｜配置示例自由飞行与视口输入

**问题：** 示例运行时无法按预期自由移动，视口呈现固定机位。

**排查：**

- 初始 GameModeBase 已生成并控制 DefaultPawn，场景摄像机没有强制接管视角。DefaultPawn 自带输入，空 AxisMappings 不能单独解释无法移动。
- `GameGetsMouseControl` 未开启；Play/Simulate 模式与视口焦点影响输入接收。
- 厂商 WorldScapeGamemode 的步行角色没有获得所需重力源，`IsOnGround=False`，测试未产生有效步行位移。

**处理：** 新建 `/Game/Blueprints/BP_WorldScapeDemoGameMode`，默认玩家为 FlyWorldScape；通过 `Demonstration_` 地图名前缀应用，空白地图保留 GameModeBase。启用 `GameGetsMouseControl=True`，撤回临时步行轴映射，保留 DefaultPawn 内置飞行输入。

**验证：** 玩家控制和相机目标正确；注入移动输入得到前向约 93.33 米、横向约 226.67 米位移。该检查没有模拟物理键盘。关卡 GameMode 重载的覆盖问题后续单列处理。

**证据：** [DemoFlyMovementVerification.json](<Documentation/Verification/2026-10-09/Logs/DemoFlyMovementVerification.json>)。修改前备份：`Saved/Backups/DemoControls_20261008_153942`。未留存自由飞行添加前后的成对截图。关联：T-005。

### 07｜修复移动时地表消失、露出岩石地下模型

**问题：** 移动时画面频闪，地表整片消失，岩石原本埋在地下的部分可见。

**复现和排除：**

- 连续移动截图复现地表漏画。
- 初次检查时相机约在地表上方 12 米，后续复现采样也记录到正的离地高度；问题不能简单归因于相机穿地。
- 原点重定位后问题仍存在；关闭遮挡查询、关闭渲染线程延迟、切换 FXAA 也没有解决。
- 暂时冻结地形更新后画面较稳定，使排查进一步集中到移动网格的渲染路径。
- 厂商文档提及地表消失与速度通道设置；进一步对照 UE 5.8 源码确认具体兼容性缺口。

**根因：** 插件在 `FWorldScapeMeshSceneProxy::GetViewRelevance` 中把 `bVelocityRelevance` 强制设为 `false`。当 `r.VelocityOutputPass=0` 时，移动的网格会跳过普通深度通道，预期由速度/深度通道绘制；禁用该标记造成更新帧漏写深度，地表因而漏画。

**修复：** 在项目插件副本中恢复 UE 自带 ProceduralMeshComponent 对应的判断：

```cpp
Result.bVelocityRelevance = DrawsVelocity() && Result.bOpaque && Result.bRenderInMainPass;
```

文件：[WorldScapeMeshComponent.cpp](<Plugins/WorldScape/Source/WorldScapeCore/Private/WorldScapeMeshComponent.cpp#L404>)。

**修复前截图：** 实际诊断复现帧；地面大片漏画，岩石底部暴露。

![2026年10月08日修复前：移动时地表消失，露出岩石地下部分](<Images/2026-10-08/terrain-disappearance-before.png>)

**修复后截图：** 正式编译并重启编辑器后采集；地表正常绘制，岩石下半部被地面遮挡。

![2026年10月08日修复后：正式编译重启后地表恢复，岩石下半部被遮挡](<Images/2026-10-08/terrain-disappearance-after.png>)

两图来自同一示例的实际排查和验证过程，未加工画面，不是像素级固定机位对照。原始文件、诊断状态及归档规则见 [Images/README.md](<Images/README.md>)。

**编译与验证：**

- 热编译成功，18 张连续移动截图未再出现整片地表消失。
- 正式编译需要关闭 UE；关闭前存在未保存地图，先执行备份和保存。
- 备份地图磁盘版本、旧 DLL，保存当前改动，核实没有剩余未保存地图或内容，再关闭编辑器。
- 正式构建完成，结果为 `Succeeded`，更新插件 DLL；厂商原有弃用 API 警告仍存在。
- 重新打开相同地图，又采集 12 张移动截图，未复现地表漏画。修复共保留 30 张热编译/重启后样本，验证范围限于该示例与所采集路径。
- 恢复 TSR、遮挡查询、线程延迟、地形持续生成和 120 m/s 飞行速度，撤回原点重定位测试。未将临时诊断开关写成永久方案。

**留档：**

- 最终验证：[TerrainVelocityFixVerification.json](<Documentation/Verification/2026-10-09/Logs/TerrainVelocityFixVerification.json>)。
- 正式构建：[TerrainVelocityFullBuild.log](<Documentation/Verification/2026-10-09/Logs/TerrainVelocityFullBuild.txt>)。
- 诊断帧指标：[TerrainFlickerFrameMetrics.json](<Documentation/Verification/2026-10-09/Diagnostics/TerrainFlickerFrameMetrics.json>)。该黑像素比例指标只用于本次固定视口区域的辅助比较，不是通用自动判定。
- 源码备份：`D:\BIG WORLD UE5.8\Saved\Backups\TerrainVelocityFix\WorldScapeMeshComponent.cpp`。
- 地图保存前副本和旧 DLL：`D:\BIG WORLD UE5.8\Saved\Backups\TerrainVelocityRestart_20261008_163427`。

### 08｜建立项目文档和截图档案

**目标：** 建立中文项目接手说明、开发日志、想法清单、技术问题清单及 Images 截图档案。

**完成内容：**

- 新增 ContinuationGuide.md、DevelopmentLog.md、IdeaBacklog.md、TechnicalChallenges.md。
- 将地表消失问题的真实修复前后截图各一张复制到 Images，并嵌入本日志对应条目。
- 添加截图来源和命名规范；无历史截图的改动明确标注未留存。
- 在 README 添加文档入口，便于项目维护和交接。

**范围：** 本次为文件整理，不重新修改游戏行为、插件逻辑或渲染配置。

### 09｜修复关卡 GameMode 重载对飞行配置的覆盖

**问题：** 仅配置 `Demonstration_` 前缀不足以覆盖全部示例。Asteroid、CubeWorld、FlatWorld_legacy、LittlePlanet、PlanetaryHeightmap 共 5 张地图具有更高优先级的 GameMode 重载。

**处理：** 备份地图后，将全部 13 张 `Demonstration_*` 的 WorldSettings.DefaultGameMode 明确设置为 `BP_WorldScapeDemoGameMode`，保留前缀规则。

**验证：** 重启后重新读取 13 张地图，配置均已保存；EarthLikePlanet、LittlePlanet、FlatWorld_legacy 的 PIE 均生成 FlyWorldScape。其他地图完成配置核查，未逐图完成全部玩法测试。

**范围：** 插件共 15 张地图，此项只修改项目副本中的 13 张 Demonstration 地图。Blank、WorldScape_Test、L_NewMap、StartUp_WorldScape 及独立原始插件包保持原状。阴影与速度通道补丁原本已为共享配置或源码，无需逐图重复应用。

证据：[地图修改报告](<Documentation/Verification/2026-10-09/Logs/DemoMapFixReport.json>)、[重启后核查](<Documentation/Verification/2026-10-09/Logs/DemoMapColdVerification.json>)。备份：`Saved/Backups/EarthDiagnostics_20261008`。关联：T-010。

### 10｜修复行星表面无输入自动漂移

**问题：** 无移动键按下、输入向量为 0 时，Pawn 仍以世界 Z 方向 12,000 cm/s 移动。

**根因：** `FloatingPawnMovement::LimitWorldBounds` 会在 Pawn 低于默认 KillZ（-1,048,575 cm）时主动向上推角色。行星表面可位于数亿厘米负 Z 处，与平面边界检查不兼容。

**处理：** 全部 13 张自由巡视示例关闭 `Enable World Bounds Checks`，不修改引擎，不移动星球，也不通过每帧归零速度掩盖问题。

**验证：** 原配置静止约 3.34 秒漂移 400 米；临时关闭检查并停止残余速度后，连续 5 秒位移为 0。正式保存并重启后，两颗星球南侧、离地约 15 米且低于 KillZ 的位置各测约 5.67 秒，位移和速度均为 0，星球位置与旋转不变。

**代价：** 这些示例不再使用默认平面 KillZ 处理掉落，正式步行死亡与重生需另行实现。

证据：[PlanetIdleVerification.json](<Documentation/Verification/2026-10-09/Logs/PlanetIdleVerification.json>)。备份：`Saved/Backups/EarthDiagnostics_20261008`。关联：T-011。

### 11｜修复 EarthLikePlanet 远景地表矩形缺块

**问题：** 远距离观察地球风格星球时，大面积地表缺失，露出海洋，残余区域呈规则矩形。

**根因：** 地球使用的 `RockyWorlds.cpp` 在河流遮罩计算中执行 `pow(HeightNormalize, 0.5)`，海床高度为负时产生 NaN，进一步污染地形顶点和整级 LOD 包围盒。实际读取发现地球 LOD 4—11 的包围盒无效，部分更近 LOD 也有无效顶点；月球和海洋没有同类无效数值。

修复仅将河流遮罩的平方根输入限制为非负值，保留正常的海床负高度：`sqrt(max(0, HeightNormalize))`。改动位于 [RockyWorlds.cpp](<Plugins/WorldScape/Source/WorldScapeNoise/Private/RockyWorlds.cpp#L113>)，对所有使用该噪声算法的地图生效。

**修复前：** 同一远景机位仅剩中央矩形地表片，其他区域露出海洋。

![地球远景修复前，矩形地表缺口](<Images/2026-10-08/earth-distant-before.png>)

**修复后：** 正式编译、重启并恢复相同位置和朝向，地表恢复连续。

![地球远景修复后，地表连续](<Images/2026-10-08/earth-distant-after.png>)

前后图均为官方 MCP 采集的原始编辑器画面。前图为自动曝光稳定后，后图包含本次固定曝光；因此以几何连续性作为对照，不把亮度差异单独归因于噪声修补。截图说明见 Images/README.md。

**编译与验证：**

- 先备份磁盘地图，保存未保存改动，再保留保存后、修复前的地图副本；关闭编辑器前无脏地图或内容。
- 正式构建 `Result: Succeeded`，重启加载 WorldScapeNoise DLL；原有浮点转换警告仍存在。
- 同样 512 个固定点的无效高度由 439 降至 0；原本有效的 73 点高度差最大值为 0；修复后 436 点仍为负海床高度。
- 双星球合计 43 个地形/海洋 LOD 的主顶点与包围盒均为有限数值。

**证据：** [噪声修复前](<Documentation/Verification/2026-10-09/Logs/EarthNoiseBefore.json>)、[重启后噪声及网格](<Documentation/Verification/2026-10-09/Logs/EarthNoiseColdPIE.json>)、[正式构建日志](<Documentation/Verification/2026-10-09/Logs/EarthNoiseFixFullBuild.txt>)。

**回退：** 原地图与源码保存在 `Saved/Backups/EarthDiagnostics_20261008`，回退源码后需重新构建。关联：T-012。

### 12｜修复 EarthLikePlanet 转向时的曝光突变

**问题：** 视角从暗宇宙或月球转向地球时短暂刺白，反向转动时短暂发黑，随后亮度逐渐恢复。

**原因：** 自动曝光沿用上一视野的亮度估计，再逐渐适应新视野。

**处理：** EarthLikePlanet 的无界后处理体开启曝光亮度上下限 Override，两值均固定为 1。项目未开启扩展亮度范围，因此不是 EV100=1。此阶段只修改该关卡，其他示例的统一调整另列记录。

**验证与代价：** 保存重启后设置保持有效；固定曝光取消日夜、洞穴之间的自动适应。静态远景截图仅作为场景记录，不能单独验证瞬时亮度变化。

依据：[Epic 自动曝光说明](https://dev.epicgames.com/documentation/unreal-engine/auto-exposure-in-unreal-engine?lang=zh-CN)。备份：`Saved/Backups/EarthDiagnostics_20261008`。关联：T-013。

### 13｜核实 EarthLikePlanet 的双星球结构

**检查对象：** `Demonstration_EarthLikePlanet` 中可见两个独立球体。

**结果：** `Planet` 为 RockyWorldsNoise 地球风格对象，半径约 6,378 千米；`PlanetBp2` 为 Selenae 月球风格对象，半径约 3,189 千米。两者为独立地形对象，尺寸比例不对应现实地月系统。

**范围：** 此项只核查对象结构，不修改星球数量、尺寸、位置或旋转。

### 14｜核实星球内部水状层的来源

**现象：** 编辑器镜头穿过地表后，可见水或绸缎状的内层表面。

**原因：** EarthLikePlanet 的两个地形对象均开启 Ocean，使用 `MI_Planetary_Ocean` 动态材质。该内层是独立海洋网格；外部程序化地形是无实心厚度的表面，编辑器自由镜头可穿过。

**处理：** 保留海洋生成和材质。诊断期间隐藏海洋仅用于辨认层次，最终配置未删除海洋。

### 15｜统一全部示例的固定曝光

**问题：** EarthLikePlanet 已固定曝光，其他示例仍采用自动曝光，转向亮暗目标后存在亮度适应过程。

**配置核查：** 13 张演示地图中，7 个无界后处理体仅 EarthLikePlanet 已固定曝光，其余没有自定义曝光上下限 Override；另外 6 张图没有后处理体。

**处理：** `DefaultEngine.ini` 写入 `r.DefaultFeature.AutoExposure=False`；7 个无界后处理体均开启亮度上下限 Override，两值固定为 1。运行中的控制台变量同步为 0，保留曝光补偿、调色和灯光。

**范围与代价：** 无覆盖值的空白及其他地图也继承项目默认；新增相机或后处理仍能覆盖默认值。固定曝光改善巡视时的亮度稳定性，但夜面和洞穴不再自动提亮。自动曝光是光线适应效果，固定值不适合所有玩法。当前数值为亮度，不是 EV100。

**验证：** 13 图读回符合目标。曝光与远景配置调整共保存 9 张实际变化的地图，保存均成功，无剩余脏地图；仅修改资源和配置，无需编译 C++。

**证据与回退：** [修改报告](<Documentation/Verification/2026-10-09/Logs/DemoQualityApplied.json>)、[配置读回](<Documentation/Verification/2026-10-09/Logs/DemoQualityVerified.json>)；地图及配置备份位于 `Saved/Backups/DemoQuality_20261008`。调整前已依次保留 Ice 磁盘版本、保存现有改动、保留保存后且优化前的版本。

依据：[Epic 自动曝光说明](https://dev.epicgames.com/documentation/en-us/unreal-engine/auto-exposure-eye-adaptation?application_version=4.27)。关联：T-013。

### 16｜扩展 IceWorldPlanet 及其他低 LOD 示例的远山覆盖

**问题：** IceWorldPlanet 向前移动时，远处山体成片突然出现。

IceWorldPlanet 原 MaxLOD=6、分辨率 200、最小三角形步长 200 cm。在相同位置和朝向仅将 MaxLOD 临时增到 12，原先截断的山脉向远处连续展开。厂商 FAQ 将远山突然出现归因于 MaxLOD 太低，建议 10–12；本次复现也支持这个原因。[WorldScape FAQ](https://iolacorp-1.gitbook.io/worldscape-plugin/faq)。

已将大型星球和普通平面示例的地形 MaxLOD 补足到至少 12，实际改动如下：

- IceWorldPlanet：6→12。
- PlanetaryHeightmap：8→12。
- FlatWorld_Lava 的平面地形：9→12。
- EarthLikePlanet、TerraFormedMoon、FlatEarth 各自月球风格伴星：11→12。
- 其余本已达到 12 的大型对象不变。Asteroid 的微型小行星、LittlePlanet 和 CubeNoise 特例保留；未统一噪声、近景分辨率、三角形尺寸、HeightAnchor 或海洋设置。

**优化前：** 当前机位只有较小范围的山体，边界截断。

![2026年10月08日 IceWorldPlanet 远山覆盖优化前](<Images/2026-10-08/ice-lod-before.png>)

**优化后：** 相同位置和朝向，外围远山补足；该图也采用了最终固定曝光。

![2026年10月08日 IceWorldPlanet 远山覆盖优化后](<Images/2026-10-08/ice-lod-after.png>)

两张均为官方 MCP 获取的真实全编辑器画面。机位存于 `Saved/Logs/IceLodInitial.json`。只有 LOD 改动、仍用旧曝光的中间对照另存 `Saved/Diagnostics/IceLod/lod12-comparison.png`，用于区分几何和亮度变化。

**成本：** Ice 地形主顶点由 188,204 增至 367,004，约增加 95%，拼缝与海洋另计。此项扩大视距覆盖，同时增加生成、内存和绘制开销；未进行可用于承诺的前台 CPU/GPU 帧时间基准。

**验证：** Ice 的 12 级地形和 10 级海洋共 22 个 LOD，无无效主顶点或包围盒。恢复有效网格后的两段短程前后输入检查均无无效包围盒；最终一段记录 33 帧，最大离开起点约 231 米，结束后恢复位置、朝向和静止状态。另保留 4 张运动截图，所查样本未出现原先远山边界的大面积出现或消失。路径曾进入地形内部，不能作为贴地碰撞验收。

**范围：** 其他示例完成设置核查，未逐图进行视觉或性能验收；方形精度分界尚未消除，另列分析记录。

**工具与证据：** [configure_demo_quality.py](<Tools/configure_demo_quality.py>) 默认只读，`apply=True` 备份并保存地图；[运行检查脚本](<Tools/verify_demo_quality_runtime.py>) 只临时操作 PIE Pawn。[网格检查](<Documentation/Verification/2026-10-09/Logs/IceQualityMeshes.json>)、[移动检查](<Documentation/Verification/2026-10-09/Logs/IceQualityRuntime.json>)。备份：`Saved/Backups/DemoQuality_20261008`。关联：T-014。

### 17｜分析行星表面的多层方形精度分界

**问题：** 行星表面围绕观察位置出现多层方形区域，中心细节密集，外围逐级变稀。

**原因：** clipmap 按 2 倍步长分级采样地形，各级独立计算法线；高空还会按 HeightAnchor 分档扩大网格，材质细节可能加重观感差异。该现象不是屏幕分辨率从中心向外降低。

**状态：** 已定位主要机制，尚未消除视觉分界。增加 MaxLOD 只扩展覆盖，不会使远处等同于中心精度。几何渐变、法线一致性与材质过渡列入 I-004；未成倍提高全图分辨率。

**截图：** [方形精度分界原图](<Images/2026-10-08/planet-lod-rings-reported.png>)。问题未修复，暂无修复后配对图。关联：T-015。

### 18｜核实自由巡视相机的局部上下方向限制

**问题：** 在星球不同区域，升降与相对地表的上下方向不一致。

**原因：** FlyWorldScape 继承 DefaultPawn，前后按控制器方向移动，升降沿世界 Z；未使用径向向量 `(位置−星球中心)` 更新局部上方向或姿态。

**状态与后续：** 当前控制方式未改写。仅替换人物或飞行器模型无法改变输入算法；人物需要径向重力、切平面移动、地面碰撞及相机对齐，飞行器需要自身坐标系姿态控制，可增加地平线辅助。关联：T-016、I-001。

### 19｜抽检全部示例地形的噪声数值有效性

**检查目标：** 检查 Earth 噪声修复后的其他示例是否存在同类无效数值。

**方法：** 对 13 图的 19 个地形对象各取 256 点，球体按均匀方向采样，平面只在中心 20 km 区域取点，读取高度、归一化高度、温度和湿度。

**结果：** 合计 4,864 点均为有限数值。RockyWorlds 的共享源码修复适用于所有使用该算法的地图，没有统一替换其他星球的噪声或材质。

**限制：** 抽样不覆盖所有坐标、球心、任意自定义参数或完整生成过程；不能据此判定全部场景无缺陷。

证据：[DemoQualityApplied.json](<Documentation/Verification/2026-10-09/Logs/DemoQualityApplied.json>)。关联：T-012。

### 20｜复核全示例边界设置与 Ice 贴地静止状态

**检查目标：** 核实平面 KillZ 漂移修复是否完整覆盖示例。

**结果：** 13 张示例的 `Enable World Bounds Checks` 均为 False，无漏同步。Ice 测试机位位于负 Z，静止约 2.95 秒位移为 0。

**限制：** 其余地图仅核查配置，未逐一复测所有位置；新建地图需要单独检查边界设置。

证据：[设置读回](<Documentation/Verification/2026-10-09/Logs/DemoQualityVerified.json>)、[Ice 静止测量](<Documentation/Verification/2026-10-09/Logs/IceQualityRuntime.json>)。关联：T-011。

### 21｜定位程序化从球心出生导致的网格变换无效

**问题：** Ice 通过 `LevelEditorSubsystem.editor_request_begin_play()` 启动时缺少 PlayerStart，Pawn 出生于球心 `(0,0,0)`；随后移回地表，网格仍未正常显示。

**排查：** 该启动接口未填入出生位置，零长度径向坐标参与运算后产生 NaN。主顶点可保持有限值，但组件平移和包围盒无效，日志出现 Invalid transform；首段运动检查 32 帧包围盒无效。

**临时恢复：** 恢复有效地表位置，再对 PIE 根对象调用 `ws_force_regenerate_ws(False)` 重建，重新检查网格有效，后续运动无无效包围盒。

**状态：** 当前运行实例已恢复，球心输入的源码边界未修复。后续程序化测试需提供有效出生点。此问题不同于 RockyWorlds 的负海床平方根错误，也不由 MaxLOD 扩展解决。

证据：[首次失败检查](<Documentation/Verification/2026-10-09/Logs/IceQualityRuntimeSpawnAtCenter.json>)、[无效变换画面](<Documentation/Verification/2026-10-09/Diagnostics/IceLod/spawn-at-center-invalid.png>)、[恢复后网格检查](<Documentation/Verification/2026-10-09/Logs/IceQualityMeshes.json>)。关联：T-017。

### 22｜统一文档分项结构与客观记录规范

**问题：** 部分开发日志将独立问题和改动集中在同一条目中；项目文档混入沟通过程、请求来源和工具使用者叙述，影响按问题检索。

**处理：** 按独立问题、功能或验证事项拆分日志；各项分别保留原因、处理、验证、限制和证据。接手说明、技术问题清单、想法清单、项目说明及截图索引统一采用客观技术表述，并更新日志编号引用。

**范围：** 仅调整项目维护文档。原有图片、验证报告、问题状态和工程配置保持不变。

## 2026年10月09日

### 01｜建立真实尺度太阳系独立关卡

**目标与实现：** 新增 `/Game/SolarSystem/Maps/SolarSystem`，包含太阳、八大行星和月球；采用真实平均半径与轨道距离，天文状态以双精度公里存储。近景使用厘米单位，远景代理等比例调整距离与尺寸以保持角大小。设置为项目启动与游戏默认地图，保留 Blank、WorldScape_Test 和全部厂商示例。

**范围：** 这是航天模拟器的天体环境基础，不含航天器建造、推力、燃料、气动或飞行任务。远景显示代理的 UE 变换不是导航坐标。关联 T-018、I-005、I-006。

**添加前：** 新建空关卡，尚无天体。添加前为编辑器画面，添加后为运行视口，二者不是同机位画质对照。

![2026年10月09日太阳系添加前的空关卡](<Images/2026-10-09/solar-system-before.png>)

**添加后：** 真实半径的类地星球轨道视图。

![2026年10月09日类地星球轨道视图](<Images/2026-10-09/earth-orbit-after.png>)

### 02｜生成类地星球海陆、植被与极地冰盖

**实现：** 使用同一程序化高度函数生成轨道颜色贴图与 WorldScape 地形；加入海床、大陆、山地、小尺度丘陵和两极冰盖。近地表启用海洋、大气，并在巡视机位附近生成树木与草类实例。纹理与地形不是现实地球大陆的复刻。

**检查：** 球面 512 点均匀抽样的海洋比例为 65.625%，两极高度均大于海平面；地表机位生成 700 棵树和 800 个草类实例。原插件植被资源在太阳系中使用独立材质实例。

**限制：** 植被为局部演示性分布，暂无持久化生态、四季系统或资源玩法；海洋为第一版材质，未实现波浪模拟与水下环境。此功能没有独立的添加前近景截图，空关卡基线见第 01 条。

![2026年10月09日类地星球地表植被与海面](<Images/2026-10-09/earth-surface-after.png>)

### 03｜建立无大气月球与朝向锁定

**实现：** 月球平均半径 1737.4 km，地月轨道半长轴 384400 km；灰色程序化月海与陨坑地形，不生成海洋、植被或大气。月球局部正前方向持续指向地球中心。

**验证与限制：** 多个采样时刻的朝向点积检查通过。采用精确几何朝向锁定，尚未实现真实月球天平动和精密月面朝向。轨道外观与地表巡视均保存截图；无独立添加前月球截图，空关卡基线见第 01 条。

![2026年10月09日月球轨道外观](<Images/2026-10-09/moon-orbit-after.png>)

### 04｜加入可见太阳光球与恒星照明

**实现：** 太阳作为天体目录中的恒星实体，半径 695700 km，具有引力参数、可见自发光球面和程序化表面纹理。照明方向根据天文位置计算，随当前天体自转改变；照明强度包含距离平方反比因子。

**范围：** 平行光用于绘制远处恒星照明，可见太阳实体独立存在。曝光和强度经过显示归一化，未模拟核反应、太阳活动、物理光度或热辐射伤害。无独立添加前太阳截图，空关卡基线见第 01 条。

![2026年10月09日可见太阳实体](<Images/2026-10-09/sun-orbit-after.png>)

### 05｜生成其他行星外观与土星环

**实现：** 水星采用无大气陨坑外观，金星采用金黄色云层风格，火星采用锈红色地貌和极区冰色；木星包含条带与风暴色斑，土星包含条带、主要环区和卡西尼间隙，天王星和海王星采用不同蓝青色云顶。土星环按真实半径比例建立，并计算星球对环的近似遮蔽。

**范围：** 气体/冰巨星使用云顶外观，不提供固体着陆表面。各天体是均值球体；未实现巨行星扁率、其他卫星与完整环粒子系统。为避免明显多边形轮廓，新增 128×64 经纬网格球面资产。

**截图：** 全部行星轨道截图保存在 `Images/2026-10-09`。无独立添加前土星截图，空关卡基线见第 01 条。

![2026年10月09日土星条带与星环](<Images/2026-10-09/saturn-orbit-after.png>)

### 06｜实现简化自转、公转与时间倍率

**实现：** 使用固定 J2000 轨道元素求解开普勒方程，计算八大行星与月球位置；地月位置加入质心修正。加入各天体自转、倾斜轴、暂停、一至十万倍时间倍率和纪元复位。

**验证：** 对目录天体检查近远点距离和周期闭合；检查月球朝向及局部/惯性坐标转换，结果保存在 [SolarModelValidation.json](<Documentation/Verification/2026-10-09/SolarModelValidation.json>)。

**限制与依据：** 固定元素不含长期摄动；转轴方位、初始相位及月轨经过简化，不是精密星历。参数依据 [JPL 轨道元素](https://ssd.jpl.nasa.gov/planets/approx_pos.html)、[行星物理参数](https://ssd.jpl.nasa.gov/planets/phys_par.html)、[卫星物理参数](https://ssd.jpl.nasa.gov/sats/phys_par/)及[天文常数](https://ssd.jpl.nasa.gov/astro_par.html)。关联 I-007。

### 07｜新增径向地表巡视与天体切换

**实现：** SolarExplorer 提供 WASD、鼠标、Q/E、滚轮速度和 Shift 加速；0—9 切换天体，G 到岩质地表，O 返回轨道机位。地表上方向取行星径向，使用地平线辅助和解析高度净空，关闭平面世界边界检查。

**范围：** 仅新太阳系地图使用此控制器，旧示例的 FlyWorldScape 保留。相机没有惯性、地面碰撞、推力和飞船动力学。近景启用/退出阈值分别为 70/220 km，存在生成等待和视觉切换，未完成无缝渐变。关联 T-016、T-021。

### 08｜修正地表大气散射过强

**问题：** 地球地表曾被浓重灰雾覆盖，植被只剩暗色轮廓。

**原因与修复：** Mie 散射强度误设为 1；修正地球近似系数为 0.003996，并分别设置金星与火星的较浓/较稀散射值，月球和水星保持无大气。

**验证：** 调整后可以看清天空、海面、地形与植被。前图机位高于局部地表约 50 m，后图约 35 m；用于说明灰雾现象，不作为相同机位的性能或画质量化比较。关联 T-019。

![2026年10月09日大气散射修正前](<Images/2026-10-09/earth-atmosphere-before.png>)

![2026年10月09日大气散射修正后](<Images/2026-10-09/earth-surface-after.png>)

### 09｜保存地图并规避旧世界引用导致的切换崩溃

**问题：** EarthLikePlanet 保存后切换地图时，Python 全局强引用使旧世界未能清理，触发编辑器退出；随后启动被恢复包提示阻塞。

**处理：** 保留地图保存前后副本及恢复元数据；使用干净进程创建太阳系地图；将生成脚本中的 UObject 引用限制在局部作用域，探针结束后释放世界和 Actor 引用。恢复提示未覆盖更新的磁盘地图。

**证据与范围：** 备份位于 `Saved/Backups/SolarSystem_20261009`。这是引用生命周期与启动流程处理，没有修改引擎垃圾回收逻辑。关联 T-020。

### 10｜完成天体场景数值、地表和静止相机回归

**结果：** 正式 Development Editor 构建通过。10 个天体轨道视图和 5 个岩质地表共 15 项回归完成；相机坐标均为有限值，五个地表各生成 13 层 LOD，网格包围盒无无效值。地球测试机位包含 700 棵树、800 个草类实例，月球和水星不启用大气。

**净空与静止：** 设置 35 m 地表净空后，实测范围约 34.68—35.00 m；差异包括 WorldScape 单精度半径的取整。另在开启正常巡视输入与一倍时间的条件下记录约 6.19 秒，未检测到移动输入，位置变化为 0 cm。

**测试工具：** 截图会触发 Slate 重入，初版探针因此重复记录同一案例；已加入重入保护，重新完整执行后得到 15 项且通过。首次报告保存在 `Saved/Diagnostics/SolarRuntimeBeforeCallbackGuard.json`，没有把其失败状态当作通过。

**证据：** [正式构建](<Documentation/Verification/2026-10-09/Logs/SolarBuildFinal.txt>)、[模型验证](<Documentation/Verification/2026-10-09/SolarModelValidation.json>)、[15 项运行验证](<Documentation/Verification/2026-10-09/SolarRuntimeValidation.json>)、[静止相机记录](<Documentation/Verification/2026-10-09/SolarCameraValidation.json>)。

**边界：** 逐天体拍摄期间冻结相机输入，未模拟实际键盘驾驶；静止检查是短时单机位测量。未验证 Shipping 打包、联机、长时间高速巡航或航天器物理，不能据此推定所有位置均无问题。

### 11｜补充地图重开后的编辑预览与冷启动检查

**问题：** 天体显示组件为运行期临时组件，仅保存管理器和资源引用后，重新打开地图缺少可见预览。

**处理：** 在编辑器完成组件注册时重建天体显示；新增预览重建接口供资产生成工具使用，并在实时视口中继续刷新。关闭实时显示时可能保留尚未更新的材质画面，可开启 Ctrl+R 或进入 Play。

**验证：** 重启后默认打开 SolarSystem，检查到 23 个静态网格类组件（含两组植被组件），进入 PIE 后数量仍为 23，没有重复创建。冷启动后的地球轨道材质显示正常，模型检查继续通过。

**证据：** [启动检查](<Documentation/Verification/2026-10-09/SolarStartupValidation.json>)、[冷启动运行画面](<Documentation/Verification/2026-10-09/Diagnostics/solar-cold-play.png>)。实现前没有保存该问题的独立截图；第 01 条空关卡基线不是该问题的复现图。

### 12｜建立版本仓库与大型资源管理

**问题：** 工程包含超过 GitHub 普通文件大小限制的 UE 二进制资产，编译缓存和本机连接配置也不适合纳入版本库。

**处理：** 初始化 `main` 分支并配置远程仓库 `Je-Taime-VI/Space-Simulator-UE5.8`。使用 Git LFS 管理地图、UE 资产、纹理与截图；排除编译产物、缓存、虚拟环境、客户端本机配置和运行输出。配置文件中的 Android 文件服务访问令牌移出待提交内容，原文件保留在本机忽略目录的备份中。

**恢复方式：** README 补充 Git LFS 克隆、工具链恢复和首次编译步骤。本次仓库整理未改变游戏代码或地图内容，不作为新的场景测试结果。

### 13｜归档验证证据并修正文档链接

**问题：** 文档中的本机绝对路径无法直接用于仓库浏览，`Saved` 内的验证证据不会随源码克隆。

**处理：** 六份项目说明中的工程链接和截图链接改为相对路径；已引用的验证报告及相关截图单独归档到 `Documentation/Verification/2026-10-09`，保留原执行结果，构建日志以 `.txt` 保存。运行缓存、完整日志和备份继续留在本机。

**范围：** 归档日期不代表重新执行测试，报告里的本机路径保留用于追溯。无新增可见功能，不需要场景前后截图。

## 2026年10月10日

### 01｜取消轨道与地表巡视模式切换

**问题：** 接近地面时自动调用地表访问接口，改变相机位置、朝向和速度；G/O 也分别跳到两套机位。

**修改：** 移除 G/O 绑定与自动跳转，保留单一连续飞行相机。岩质天体在 1800 km 内预加载 WorldScape，16 层网格就绪后在 450—180 km 范围逐渐接替远景代理；远离到 2400 km 以上才释放。近地自动限速与限制单帧步长。靠近另一天体时转换局部坐标，保留同一逻辑位置与姿态。数字键仍可主动访问天体书签。

**验证方式：** 从地面净空 1200 km 连续下降到 35 m，逐帧检查加载期间的相机位置、朝向、速度设置和大气/云组件。最终结果见第 10 条。此过程没有调用地表跳转；开始布置测试位置使用一次访问接口。

**限制：** 淡入淡出不等于跨层几何形变，WorldScape 环间的高度/法线分界仍待处理；相机尚无航天器动力学。静态截图不能独立证明运动连续，轨迹报告为主要证据。

### 02｜消除整球贴图放大造成的低轨马赛克

**问题：** 1024×512 整球贴图在数百公里高度被大幅放大，陆地、海岸与云图显示为块状像素。

**修改：** 远近景使用对应的程序化高度和颜色函数；远景球面增加到 512×256 分段并按同一高度场位移。近地材质增加多尺度细节，不再靠放大整球颜色贴图表现地面。

**范围：** 作用于新太阳系全部天体材质；不修改原插件演示地图。程序化地貌仍为虚构大陆，近景使用简化解析光照，尚未完成完整地形阴影和反射标定。

![低轨马赛克修改前](Images/2026-10-10/earth-low-orbit-before.png)

![连续下降约489公里修改后](Images/2026-10-10/earth-descent-488p53km-after.png)

两图机位不同，用于观察贴图像素与近地细节机制，不作为逐像素画质或性能对照。

### 03｜地球云层从太空连续延伸到地面视角

**问题：** 原地球使用薄层云球，进入近景后隐藏，轨道云分布与地面晴空不一致。

**修改：** 活动地球使用 2—9 km 球形体积云，远处非活动地球的薄层表示使用同一覆盖函数；近地不再隐藏云层。材质补齐 `used_with_volumetric_cloud` 标记，消光系数按米设置；直接云追踪规避太空视角重投影黑屏。

**验证：** 采集整球、云下和穿云高度截图，并在下降期间检查组件持续存在。云下样点按实际覆盖函数选择，没有临时增大密度替代最终画面。尚未实现风场、天气演化、降水与云影完整联动。

![地球薄层云修改前](Images/2026-10-10/earth-orbit-before.png)

![地球体积云修改后](Images/2026-10-10/earth-orbit-after.png)

![最终云下仰视](Images/2026-10-10/earth-clouds-after.png)

### 04｜减弱低轨大气的硬边界

**问题：** 远景附加发光壳形成明显蓝色边框，近地又切换另一套大气。

**修改：** 当前天体保持同一个球形 SkyAtmosphere，按径向高度衰减；不同时叠加远景发光壳。非活动天体的远处壳层降低边缘亮度并平滑衰减。

**验证与限制：** 低轨、整球与地面分别检查。使用实时渲染近似，太阳光度、光谱和曝光没有完成物理标定；极端掠射角与大尺度精度仍需专项检查。

![大气硬边修改前](Images/2026-10-10/earth-low-orbit-before.png)

![球形散射大气修改后](Images/2026-10-10/earth-descent-488p53km-after.png)

### 05｜修正金星蓝色地表与缺少厚云的问题

**问题：** 日照地表色调偏蓝，与金星厚大气下的外观不符。

**修改：** 地表改为棕褐色岩石底色，调整大气为暖色散射，并加入 48—70 km 浓厚体积云层。地表暖色由材质和大气共同形成，不把所有岩石直接当成铁锈。

**共同光照修复：** 方向光启用逐像素大气透光率，避免整颗星球使用固定参考点的夜面透光率。大气遮蔽球底面移至平均半径下 12 km，以容纳低洼地形并补偿散射高度。

**范围：** 颜色和云层高度为外观近似，没有模拟 92 bar 地面气压、温度和化学组成。真实金星可见光外观通常接近浅色、低反差云球。[NASA 金星资料](https://science.nasa.gov/venus/venus-facts/)

![金星地表修改前](Images/2026-10-10/venus-surface-before.png)

![金星地表修改后](Images/2026-10-10/venus-surface-after.png)

### 06｜恢复火星日照侧的地面与天空

**问题：** 进入火星地表后，即使面向太阳，天空和地面仍接近全黑。

**原因与修改：** 低于平均半径的地形进入了大气遮蔽球，加上方向光的统一透光率取样不适合球面环境。降低大气底面、启用逐像素透光率，并设置稀薄含尘大气和赭红地表。

**限制：** 日照侧恢复可见；夜面保持黑暗。尚未实现随天气变化的尘埃、沙尘暴和准确的日落光谱。[NASA 火星资料](https://science.nasa.gov/mars/facts/)

![火星地表修改前](Images/2026-10-10/mars-surface-before.png)

![火星地表修改后](Images/2026-10-10/mars-surface-after.png)

### 07｜补充巨行星大气并明确参考面

**问题：** 四颗巨行星的大气高度原为零，球体边缘缺少散射表现。

**修改：** 四颗巨行星加入散射大气。HUD 使用“距1 bar参考层”，避免把平均半径称作可着陆地表。

**依据与限制：** 1 bar 是巨行星半径常用参考层；当前平均半径球体未体现扁率，渲染层高度不代表气体存在锐利边界。

**尚未实现：** 巨行星深层体积云、压强/温度剖面、内部穿行、精密云顶高度和天气系统；现有巡视边界仍限制进入参考球内部。这一限制不代表存在固体表面。

**截图：** 本项参数与色调同期改变，整球前后图见第11条，不把其差异单独归因于大气。

### 08｜校正自转轴方位及天王星姿态

**问题：** 原转轴由统一世界轴倾转生成，没有正确结合各自轨道法线及极轴方位；书签相机又把每个天体呈现为正立。

**修改：** 以 IAU/NAIF J2000 极轴方向提供方位，以各天体轨道法线和轴倾角构建角动量方向；金星、天王星的逆行符号统一处理。天王星轴倾角保持 97.77°，月球保留倾斜转轴和朝地经度锁定。书签视图以上黄道方向为参考。

**验证：** 20 个时间点检查转轴与各自轨道法线的夹角、月球朝地经度；另检查全部椭圆近远拱点、周期闭合和坐标往返。固定轨道元素以 [JPL 数据](https://ssd.jpl.nasa.gov/planets/approx_pos.html) 为依据，极轴取 [NAIF 行星常量](https://naif.jpl.nasa.gov/pub/naif/generic_kernels/pck/pck00011.tpc)。这不是含岁差、章动、本初子午线真实初相的精密星历。

![天王星姿态修改前](Images/2026-10-10/uranus-orbit-before.png)

![天王星姿态修改后](Images/2026-10-10/uranus-orbit-after.png)

### 09｜核查真实尺度并预留两条小天体带

**检查：** 保留真实平均半径和轨道公里数，地球半径 6371.0084 km、月地半长轴 384400 km、海王星半长轴约 30.0699 AU。远景显示压缩同时缩放半径和距离，不改变逻辑轨道。

**修改：** 定义主小行星带 2.1—3.3 AU、柯伊伯带 30—50 AU，加入火星/木星之间的空间检查及柯伊伯带外边界检查。海王星轨道与柯伊伯带内缘接近属于正常情况，不为制造空白间隔而移动行星。

**范围：** 只预留区域，未生成带内小天体、矮行星或引力扰动；本项没有新增可见对象，不提供虚构的添加后截图。[NASA 柯伊伯带资料](https://science.nasa.gov/solar-system/kuiper-belt/facts/)

### 10｜正式构建与连续飞行回归

**构建：** 关闭编辑器后完成 UE 5.8.2 Development Editor 构建并重启，结果 `Succeeded`；地图中的序列化星表已刷新并保存。

**检查范围：** 10 个天体整球、5 个岩质地表和1个地球云下样点；额外采集 1200 km 到35 m 的逐帧下降记录。数值检查和截图审阅分别进行，组件启用不直接视为画面正确。

**连续下降结果：** 16项视图与450帧下降检查通过。加载期间相机位置偏差为0 cm，朝向最大数值偏差约5.7×10⁻¹⁴度，速度设定未被改写，云和大气持续开启。最后的陨坑/条带材质细调另做6个受影响视图复查，不重复未改变的下降逻辑。

**补充回归：** 最终6个材质视图检查通过。连续转换10个天体参考系后的最大逻辑位置误差约4.54 mm，低于本次1 cm阈值；此检查不包含速度/动量守恒。

**证据：** [运行回归](Documentation/Verification/2026-10-10/Verification.json)、[最终材质及坐标转换](Documentation/Verification/2026-10-10/MaterialFinalVerification.json)、[正式构建](Documentation/Verification/2026-10-10/SeamlessBuildFinal.txt)，截图见 [Images 说明](Images/README.md)。结果及边界以归档报告为准。

**限制：** 没有模拟物理键盘驾驶、完成前台 FPS 基准、Shipping 打包、所有经纬度/天气的长期测试。地形和海洋各增加层级、体积云直接追踪都会增加开销；当前不宣称达到最终写实画质。

### 11｜校正海王星与天王星的可见光色调

**问题与修改：** 天王星、海王星的原有颜色区分不足。改为相近的浅蓝青色，海王星略偏蓝；保持天王星低反差条带，不直接套用饱和深蓝的增强色照片。

**依据与边界：** 两颗行星的天然色比常见增强色图更相似。[牛津大学颜色重建研究](https://www.ox.ac.uk/news/2024-01-05-new-images-reveal-what-neptune-and-uranus-really-look-0)。当前为程序化近似，未进行光谱或显示设备色彩标定。

![海王星色调修改前](Images/2026-10-10/neptune-orbit-before.png)

![海王星色调修改后](Images/2026-10-10/neptune-orbit-after.png)

### 12｜减弱木星和土星过密规则条纹

**问题：** 原有条带近似大量等宽细线，缺少较宽的主要带区。

**修改与验证：** 主带空间频率降低，保留低对比细纹和扰动，CPU导出与实时材质同步更新；重新采集两颗行星视图。没有增加流体天气模拟。

![木星条带修改前](Images/2026-10-10/jupiter-orbit-before.png)

![木星条带修改后](Images/2026-10-10/jupiter-orbit-after.png)

![土星条带修改前](Images/2026-10-10/saturn-orbit-before.png)

![土星条带修改后](Images/2026-10-10/saturn-orbit-after.png)

### 13｜保留水星、月球的陨坑明暗与灰色岩石

**问题与修改：** 切换程序化材质后，最初的GPU颜色函数遗漏CPU颜色中的陨坑明暗项；已补回并复查整球与地表。

**外观依据：** 两颗天体保持无大气黑色天空与强明暗反差，但岩石不应强制变成纯白、阴影也不由颜色二值化产生。表面灰度还取决于材质、入射角与曝光。[NASA 水星资料](https://science.nasa.gov/mercury/facts/)

![月球材质修改前](Images/2026-10-10/moon-orbit-before.png)

![月球材质修改后](Images/2026-10-10/moon-orbit-after.png)

前图来自本轮实施前版本，不是遗漏明暗项的中间诊断版；中间版没有另存历史证据。

### 14｜调整太阳可见光球的颜色

**问题：** 原光球偏橙黄色，不适合用作太空可见光的默认外观。

**修改：** 调整为近白色发光光球，保留真实半径与引力参数；固定曝光下光球接近白色饱和。没有把仅有方向光称作太阳实体，也没有实现恒星内部结构、耀斑和日冕。

![太阳修改前](Images/2026-10-10/sun-orbit-before.png)

![太阳修改后](Images/2026-10-10/sun-orbit-after.png)

### 15｜长按速度调节与贴地加速

**后续更正：** 本条记录当时的临时倍率版本；最终交互已由当日第18、19条替代。松开恢复、双键慢速和瞬时十倍不再适用。

**问题：** 贴近地面时，Shift 的加速倍率被自动速度上限和每帧位移上限抵消；左 Ctrl 原本同时承担下降。

**修改：** 左 Shift 长按使用滚轮设定基础速度的十倍，并绕过两项贴地限制。左 Ctrl 长按使用自动限速后的十分之一，松开恢复；两键同按时慢速优先。Ctrl 取消下降输入，Q/E 保留径向升降。HUD 更新按键提示。

**保护与范围：** 保留最低3 m解析地面净空、分段投影和100 ms长帧保护；只作用于 SolarExplorer，旧 Demonstration 控制不变。高速移动仍不是完整的飞船扫掠碰撞。

**验证：** 35 m净空、80 m/s基础速度样点：普通12.25 m/s、加速800 m/s、慢速1.225 m/s；100 ms位移分别1.225 m、80 m、0.1225 m。8项实际 C++ 移动入口检查通过，包括松开、两键优先级、空方向、长帧和向地下移动。未模拟物理键盘。证据见 [飞行与云回归](Documentation/Verification/2026-10-10/CloudPerformance/FlightCloudVerification.json)。

**截图说明：** 以下同一天体书签视图记录HUD按键提示前后变化，不作为移动速度证据；速度以数值回归为准。

![速度提示修改前](Images/2026-10-10/CloudPerformance/earth-orbit-before.png)

![速度提示修改后](Images/2026-10-10/CloudPerformance/earth-orbit-after.png)

### 16｜降低地球、金星体积云的渲染开销

**问题：** 切换到有云天体后出现严重卡顿。系统内存截图为83%—84%；仅凭该占用不能确定云耗尽内存。

**定位：** RTX3060 Laptop 6GB 上，原地球整球机位云通道775.417 ms、PIE场景801.912 ms；关闭云后场景27.557 ms。当时显存约2.9/6 GB、系统可用物理内存约2.5 GiB，主要瓶颈为云着色计算。原路径逐像素高采样执行多层 Perlin 噪声；只降低分辨率和采样后云仍约133 ms。

**修改：** 全球云覆盖改用现有1024×512线性灰度图，远景薄层与活动体积共享；近处云体保留两层轻量三维密度噪声。使用半分辨率追踪模式1、视线采样倍率0.5、阴影采样倍率0.25，4 km内不复用云历史以减轻穿云拖影。没有关闭体积云，也没有把地表恢复成整球低清贴图。

**结果：** 重启后地球整球云通道3次为1.466—2.173 ms，中位2.146 ms；金星为1.875—2.313 ms，中位2.095 ms。地球/金星云内样点分别4.814/6.665 ms。地球整场景仍约42—63 ms，说明其他渲染成本仍存在。往返切换、低轨、云内与地面共9个视图检查通过。

**测量边界：** GPU事件对应1376×808视口，截图为1280×720；编辑器存在额外视图，后台时钟变化会影响时间，不能折算成稳定前台FPS。原版地球仅1个有效GPU事件样本，没有原版金星同机位基准；不宣称所有切换尖峰、内存压力或风扇噪声已消除。

**画质取舍：** 云边缘较软，采样降低可能带来近处噪点和快速转向拖影；覆盖仍是静态近似。首次地形生成和着色器缓存仍可能产生短暂停顿。本项替代第03条及 T-024 中直接全分辨率追踪的临时规避设置。

**证据：** [GPU记录](Documentation/Verification/2026-10-10/CloudPerformance/GpuPerformance.json)、[原始事件](Documentation/Verification/2026-10-10/CloudPerformance/ProfileFinal.txt)、[构建](Documentation/Verification/2026-10-10/CloudPerformance/Build.txt)。源码和资产备份：`Saved/Backups/CloudPerf_20261010`。正式 Development Editor 构建成功；再次重启确认配置从磁盘读取为1/1/4（见 `RestartConfig.json`），仍有既存浮点转换警告。

![系统内存初始状态](Images/2026-10-10/CloudPerformance/system-memory-before.png)

![云优化前的地球](Images/2026-10-10/CloudPerformance/earth-orbit-before.png)

![云优化后的地球](Images/2026-10-10/CloudPerformance/earth-orbit-after.png)

![优化后连续云体内部](Images/2026-10-10/CloudPerformance/earth-inside-after.png)

截图只能说明外观和云体保留，不能显示帧耗时。金星本项修改前没有另拍同机位截图，不用诊断中间版充当原始版本。

### 17｜确定火星冰云与谷雾的后续范围

**事实：** 火星存在薄水冰云，以及更高、更冷处的二氧化碳冰云；云层受季节和地域影响。参考 [NASA 薄云资料](https://science.nasa.gov/blog/cloudy-sols-are-here-again/) 与 [Curiosity 云观测](https://www.nasa.gov/missions/mars-science-laboratory/nasas-curiosity-rover-captures-colorful-clouds-drifting-over-mars/)。

**决策：** 暂不增加火星云体，安排在天气精细化阶段，见 I-008。水冰云、高空干冰云、局部谷雾分别设计，不套用地球或金星厚云。谷雾的具体季节和空间分布需进一步核实后定参。

**当前状态：** 火星保留稀薄含尘散射大气；没有新增云、季节天气或谷雾，因此本项没有添加后截图。

### 18｜长按调速后保持，双键恢复自动

**问题：** 上一版 Shift/Ctrl 为临时倍率，松开恢复自动速度、两键同按进入慢速；无法保留调好的巡航速度。

**修改：** 单独长按左 Shift 逐渐提高速度、左 Ctrl 逐渐降低速度，从当前实际速度起调并进入手动模式。松开保持，海拔变化不重新限速。两键同按恢复自动限速；复位后要全部松开才接受新的单键调整，避免先后松键误触发。HUD显示自动/手动，低速改用m/s，Q/E继续升降。

**保护：** 手动模式持续绕过贴地速度和位移上限，保留解析最低3 m净空、分段投影及100 ms长帧保护。没有新增物理碰撞或飞船加速度模拟。

**验证：** 正式构建、重启后17项共用 C++ 入口检查通过；包括松开后移动、10 m净空保速、双键复位、单键先松、重新调速和向地下移动。按键读取仍使用左Shift/左Ctrl，测试注入共用函数参数，不等同于物理键盘测试。结果见 [调速验证](Documentation/Verification/2026-10-10/RetainedSpeed/Verification.json) 和 [正式构建](Documentation/Verification/2026-10-10/RetainedSpeed/Build.txt)。

**截图：** 原运行机位、天体及时间已记录并恢复；截图展示HUD和控制说明，时长与移动距离以数值报告为准。

![旧控制说明](Images/2026-10-10/RetainedSpeed/controls-before.png)

![新自动模式说明](Images/2026-10-10/RetainedSpeed/controls-auto-after.png)

![松开后保持手动速度](Images/2026-10-10/RetainedSpeed/controls-manual-after.png)

### 19｜降低持续调速和滚轮的灵敏度

**问题：** 瞬时十倍/十分之一倍率与滚轮每格翻倍会引起速度大幅跳变，难以微调。

**修改：** 按住调速改为随时间平滑累计，默认4秒翻倍/减半，0.1秒短按只变化约1.75%。`SpeedAdjustmentDoublingSeconds`可调整该时长。滚轮改为每格×1.2或÷1.2；自动模式调速度上限，手动模式调当前巡航速度。

**验证：** 30/60/144 Hz三种注入步长下按住4秒，速度均由12.25 m/s升至24.5 m/s；按住Ctrl4秒降回12.25 m/s，松开仍保持。10秒卡顿样本仅按100 ms调整，避免积累突变。滚轮分支已编译并核查，未进行物理滚轮注入。截图共用第18条，灵敏度不能由单张静态图证明。

## 2026年10月11日

### 01｜确认太阳系地表材质与示例存在细节差距

**问题：** 自制地球近地沙滩颜色平滑，缺少沙粒、岩石及细节明暗；插件示例具有更丰富的地表纹理和散布。

**核查：** 近景使用 WorldScape 网格，但高度与材质为项目自定义。最终生成脚本 `Tools/refine_solar_materials.py` 中 `M_Terrain` 使用 Unlit，并将程序化颜色和手工明暗输出到自发光，没有连接细节法线与粗糙度。`SolarSystemActor::EnsureTerrain` 清空插件原有散布列表；独立树草生成排除海拔低于15 m的区域，也没有岩石散布。

**状态：** 已定位实现差距，未修复。本日没有运行编辑器验证；素材可复用范围由源码与资源目录核查确定。关联 T-030。

![WorldScape荒芜行星示例近地细节](Images/2026-10-11/TerrainAssessment/demo-baren-beach-reference.png)

![WorldScape类地示例植被与地表](Images/2026-10-11/TerrainAssessment/demo-earth-vegetation-reference.png)

![自制地球当前沙滩与海面](Images/2026-10-11/TerrainAssessment/solar-earth-beach-before.png)

以上为2026年10月10日拍摄的不同场景参考与现状原图，不是同机位修复前后对照；暂无修复后截图。

### 02｜确认太阳系海洋缺少水面光学与近岸细节

**问题：** 自制地球海面表现为近乎均匀的蓝青色，岸线锯齿明显，缺少示例水面的细节与反射层次。

**核查：** 海洋有独立 WorldScape 网格，`SolarTerrainNoise` 的海洋高度为零基准；`M_Ocean` 则为 Unlit/Masked 材质，仅计算颜色和手工太阳明暗，没有波纹法线、反射、折射、深度吸收及泡沫。因此并非没有海洋几何，但当前水体外观仍是简化原型。岸线还依赖地形和海面几何精度，替换颜色贴图不能单独解决。

**状态：** 未修复。插件存在 `MI_Planetary_Ocean` 等可复用资源，仍需验证行星中心、真实尺度和近远景衔接。关联 T-031；当前太阳系截图共用第01条。

![WorldScape类地示例海面与湿润沙滩](Images/2026-10-11/TerrainAssessment/demo-earth-ocean-reference.png)

### 03｜确认真实山脉、盆地与海沟尚未接入

**问题：** 当前类地、类金星、类火星等天体没有指定经纬度的真实山脉、盆地、高原和海沟。

**核查：** `SolarModel::HeightKm` 使用噪声、脊线和程序化陨坑，不读取真实 DEM。地球高度另有 −10至8.5 km的硬裁剪。单纯增大噪声幅度不能得到喜马拉雅山、马里亚纳海沟、麦克斯韦山、卡洛里斯盆地、奥林匹斯山或水手谷的真实形状和位置。

**资料方向：** 地球采用 [NOAA ETOPO 2022](https://www.ncei.noaa.gov/products/etopo-global-relief-model) 的陆海高程，并参考 [NASA Blue Marble底图](https://science.nasa.gov/earth/earth-observatory/blue-marble-next-generation/base-map/)；火星采用 [USGS MOLA/HRSC融合DEM](https://astrogeology.usgs.gov/search/map/mars_mgs_mola_mex_hrsc_blended_dem_global_200m)；月球采用 [LOLA与SLDEM2015](https://pgda.gsfc.nasa.gov/products/54)，后者覆盖南北纬60°之间；水星参考 [MESSENGER全球地形产品](https://eros.usgs.gov/doi-remote-sensing-activities/2016/usgs/global-topographic-map-mercury)；金星参考 [Magellan地形档案](https://pds.nasa.gov/ds-view/pds/viewCollection.jsp?identifier=urn%3Anasa%3Apds%3Amagellan_gravity%3Atopo&version=1.0)。金星雷达影像不能直接作为可见光底色。

**状态与边界：** 尚未下载或接入这些数据。全球数据解决宏观形状，近地仍需要局部细节；产品网格间距不代表每处都具有相同观测精度。必须保留数据来源与许可，统一高程基准、经纬方向和单位，采用分级瓦片与缓存，不能直接让大型全球栅格全部常驻。关联 T-032、I-009。

### 04｜核查沙丘、侵蚀与细节素材复用范围

**已有资源：** 插件 `RockyWorlds.cpp` 有沙丘噪声，资源目录含沙、岩石、雪等贴图及法线/组合贴图、岩石模型、月球高度图、`BP_HeightMapVolume`、`HM_Montagne` 和 `WS_Heightmap_Editor` 的侵蚀脚本与滤镜。

**限制：** 这些资源不等同于指定行星的真实风蚀地貌，也不能仅由文件名断言已具备物理风蚀模拟。当前太阳系没有接入上述完整组合。后续可用真实宏观地形配合定向沙丘、区域笔刷和近地碎石补充观测分辨率以下的细节；程序化补充部分应与真实观测区分。关联 I-010。

![WorldScape荒芜行星丘陵参考](Images/2026-10-11/TerrainAssessment/demo-baren-hills-reference.png)

![WorldScape月球风格地表参考](Images/2026-10-11/TerrainAssessment/demo-moon-reference.png)

![WorldScape火星风格地表参考](Images/2026-10-11/TerrainAssessment/demo-mars-reference.png)

本日只完成资源核查和原图归档，未添加新地貌或替换运行资产，因此无添加后截图。

### 05｜核查表面高度场与洞穴能力边界

**现状：** WorldScape 使用表面高度场生成地形，同一径向位置只有一层高度，不能直接表示洞顶、洞底与多层地下通道。可见球壳不表示洞穴必须依赖整颗实体星球；独立洞穴网格可以构成可进入的地下空间。

**核查：** 插件已有 `TerrainHoleVolume`，在噪声结果设置 Hole，并写入地形顶点颜色 Alpha；接口标记为实验性，没有自动生成地下洞壁。当前太阳系材质尚未接入此标记。地表开洞配合洞穴网格为优先候选，任意挖掘另评估局部体积地形，关联 I-011。

**状态：** 仅完成源码核查，没有新增洞穴、安装插件或进行运行测试，暂无功能截图。

### 06｜确认巡视净空规则不适用于地下通行

**现状与原因：** `SolarExplorer.cpp` 根据 `GetGroundRadiusKm` 将移动位置保持在地表上方至少3 m，近景 WorldScape 碰撞也被关闭。即使补充洞穴模型，现有移动规则仍会把地下位置推回地面。

**处理方向：** 实施洞穴时同步接入洞口和地下碰撞，并在洞穴区域使用适合地下空间的移动检测；不能全局取消防穿地后视为洞穴功能完成。

**状态：** 尚未修改移动或碰撞逻辑，保持现有地表巡视行为；后续验收条件见 I-011。

### 07｜恢复太阳系地表与海面的正常受光

**问题：** 近景地表与海面使用 Unlit 自发光模拟明暗，不能正常响应太阳、天空光和材质高光。

**修改：** `M_Terrain`、`M_Ocean` 改为 Default Lit，颜色接入 Base Color，自发光归零。地表粗糙度0.85，海面粗糙度0.18、Specular为0.255。活动天体远景代理也接入真实方向光，非活动代理保留各自太阳方向的辐亮度近似。原有连续飞行、地形渐变与云性能设置保留。

**验证：** 正式编译并重启后，8个相关材质均有有效编译统计；地表/海洋连接检查通过。同机位关闭太阳与天空光后地表变暗，恢复后画面恢复。地球、月球、金星、火星地表均保留实际渲染截图。报告见 [受光校准验证](Documentation/Verification/2026-10-11/SurfaceLighting/README.md)。

**范围：** 本项仅恢复受光基础，没有新增沙石法线、岩石散布、海浪、折射、泡沫或真实高程。低轨的几何/法线分界与渐变采样仍可见，关联 T-030、T-031、I-004。

以下地球截图为相同机位的整体受光修改前后，包含第08—10条参数变化，不作为单独材质开关实验。

![地球受光修改前](Images/2026-10-11/SurfaceLighting/earth-surface-before.png)

![地球受光修改后](Images/2026-10-11/SurfaceLighting/earth-surface-final.png)

### 08｜统一太阳照度基准与固定曝光

**问题：** 原太阳方向光以1 AU处5 lux为基准，与自发光材质混用，无法作为正常受光材质的日照与摄影曝光基准。

**修改：** 1 AU处设为120000 lux，按日心距离平方反比衰减。太阳系局部后处理使用 Manual、ISO100、f/16、1/125秒，基准 EV100≈14.966；默认另加 `2*log2(日心距离AU)` 的确定性补偿。关闭局部曝光对比增强，恒星、星环与远景薄云同步调整到新亮度范围。

**验证：** 地球J2000样点太阳照度约124106 lux，月球约124348 lux，火星约62005 lux，金星约231334 lux。转向、关灯与恢复的8阶段记录中，曝光方式和补偿保持一致；地球与月球夜面不再自发亮。这里的距离补偿服务于外行星可见性，不是按画面亮度自动适应，也不表示所有天体采用完全相同曝光。

**边界：** 120000 lux为渲染校准值；恒星表面亮度和远景大气仍为视觉近似，未完成光谱、完整动态范围与专业摄影响应标定。通过管理器 `ExposureCompensation` 调整整体曝光，通过 `bCompensateExposureForSolarDistance` 开关距离补偿。厂商示例曝光没有改写。

以下月球同机位对照同时包含材质变化，不用于单独衡量曝光改动。

![月球受光与曝光修改前](Images/2026-10-11/SurfaceLighting/moon-surface-before.png)

![月球受光与曝光修改后](Images/2026-10-11/SurfaceLighting/moon-surface-after.png)

### 09｜补充有大气地表的天空照明

**问题：** 地表改用正常受光后，需要由天空散射提供环境照明，避免以材质自发光统一抬亮阴影和夜面。

**修改：** 新增64分辨率实时天空光，跟随观察位置；有大气的岩质天体在近地启用，20—120 km淡出，并根据太阳高度在夜侧关闭。取消固定世界Z下半球黑色设置，使球面各处的天空采集不依赖平面世界上下方向。

**验证：** 地球、金星、火星白昼地表样点天空光强度为1；月球、水星、地球轨道及夜面样点为0。金星地面保留暖色，火星受光地面可见。实际画面检查与运行记录归档，未完成新增天空光的稳定前台性能基准。

金星前后图包含本轮全部受光与曝光调整，不能将全部视觉差异归因于天空光一项。

![金星地表照明修改前](Images/2026-10-11/SurfaceLighting/venus-surface-before.png)

![金星地表照明修改后](Images/2026-10-11/SurfaceLighting/venus-surface-after.png)

### 10｜消除恢复受光后出现的地球海面暗格

**问题与定位：** 首次接入正常受光后，轨道海面出现规则暗格。球面三角形的内部位于顶点球面以内，与海平面重合的大气遮蔽底面将其误判为地下，逐像素透光率被截断。关闭高光或云层的对照不能消除暗格。

**修改：** 仅将地球大气遮蔽底面放到平均半径下1 km，补偿瑞利/米氏散射与米氏吸收的高度分布，云层底高同步补偿。实际地球半径、海平面和云层绝对高度保持原值，保留逐像素大气透光率。

**验证：** 正式构建成功后重启，地球轨道海面不再出现该规则暗格；300 km过渡视图、白昼地表与夜侧复查完成。云层采样纹理、clipmap环和近远景渐变噪点仍存在，不能与本项暗格混为一谈。关联 T-033。

下方前图是本轮首次受光版本中的问题状态，不是任务开始时的原始版本；后图来自最终正式构建。

![恢复受光后的海面暗格，修正前](Images/2026-10-11/SurfaceLighting/earth-grid-before-correction.png)

![大气遮蔽底面修正后的地球轨道画面](Images/2026-10-11/SurfaceLighting/earth-orbit-final.png)

**回退位置：** `Saved/Backups/SurfaceLighting_20261011`。源码、材质、地图需配套回退并重新编译，不能只恢复光强。

## 2026年10月12日

### 01｜接入示例沙地颜色、法线与表面参数

**问题：** 太阳系沙地已有基础受光，但近看主要是平滑的程序化颜色，缺少示例中的沙粒与凹凸层次。

**修改：** 将示例 `Sand/T_Sand_Far_C`、`T_Sand_Far_N`、`T_Sand_Far_ORMH` 复制到项目纹理目录并接入共享 `M_Terrain`。采用3 m尺度三平面投影；组合图 R 通道用于AO，G通道用于粗糙度，金属度保持0。地球海岸与沙漠使用沙层，火星沙土混合保留原宏观色调。

**验证：** 地球沙地同机位、同太阳照度及曝光前后对照完成，颗粒和法线明暗已出现。当前为干沙基础层，尚无随水位变化的湿沙、足迹或沙粒几何；本项没有修改海洋。

![地球沙地接入前](Images/2026-10-12/SurfaceMaterials/earth-sand-before.png)

![地球沙地接入后](Images/2026-10-12/SurfaceMaterials/earth-sand-final.png)

### 02｜接入岩石层并修正高地混合优先级

**问题：** 原地表缺少岩面纹理与细节法线；初版混合中，沙漠权重又覆盖了地球高地的岩石表现。

**修改：** 使用示例 `Rock/T_Rock3`、`T_Rock3N`，按6 m尺度投影，岩石粗糙度暂设0.83。地球按坡度和1.4—3.2 km高地范围增加岩石权重，同时减弱沙层；金星以岩石为主，月球、水星和火星按各自规则混合。保留天体宏观反照率与色调，非地球只复用纹理亮度变化，避免移植不合适的颜色。

**验证：** 地球高地与金星地表已拍摄前后对照，最终材质默认纹理确认引用 `T_Rock3`。下图为地球同机位整体材质替换，不是单独岩石层开关实验。岩面花纹与凹凸来自材质，未新增可碰撞岩石实体或改变山体几何。

![地球高地岩石材质接入前](Images/2026-10-12/SurfaceMaterials/earth-rock-before.png)

![地球高地岩石材质接入后](Images/2026-10-12/SurfaceMaterials/earth-rock-final.png)

### 03｜接入土壤与无大气天体表土细节

**问题：** 地球近地土壤原为大面积绿色宏观色块，月球和水星表土缺少颗粒细节。直接使用地球土壤颜色又会使月面出现不合适的杂色。

**修改：** 接入示例 `Dirt/T_Dirt_Albedo`、`T_Dirt_Normal`，按2.5 m尺度投影，粗糙度暂设0.9。地球近地土壤混入棕色基底；远处恢复原宏观颜色。月球、水星、金星与火星将资源色彩变化转为亮度变化，再乘各自的宏观颜色。

**验证：** 地球土壤、月球与火星完成同机位对照，另检查水星表土；近地已显示颜色与法线细节，月面保持中性灰。地球树草沿用已有散布规则，平铺重复仍可见，尚未建立真实地质分区或新增碎石网格。

![地球土壤接入前](Images/2026-10-12/SurfaceMaterials/earth-soil-before.png)

![地球土壤接入后](Images/2026-10-12/SurfaceMaterials/earth-soil-final.png)

### 04｜接入极地与高山雪层

**问题：** 原极地和高山白色区域只具备宏观颜色，近地缺少雪面颗粒与法线变化。

**修改：** 接入示例 `Snow/T_Snow_Albedo`、`T_Snow_N`、`T_Snow_ORMH`，按4 m尺度投影。地球按极区纬度及3.4—4.2 km海拔范围混入雪层，火星采用极区规则；月球、水星和金星不套用地球积雪分层。组合图读取 R 通道AO、G通道粗糙度。

**验证：** 地球雪面同机位前后与火星极区额外机位完成检查。当前表现为不透明积雪/冰盖表面，没有透明蓝冰、冰川几何、季节积雪或物质成分模拟，不能据此区分水冰与干冰的物理性质。

![地球雪面接入前](Images/2026-10-12/SurfaceMaterials/earth-snow-before.png)

![地球雪面接入后](Images/2026-10-12/SurfaceMaterials/earth-snow-final.png)

### 05｜适配真实尺度投影、远景淡出与纹理预算

**目标：** 在真实半径行星上使用米级纹理，保持移动时的纹理定位，并与原宏观远景衔接。

**实现：** 原生LWC节点先对相机坐标进行除法和取分数，再在材质Custom节点内加相机相对坐标；三平面法线采用带方向的表面梯度混合。细节按相机到像素距离在300—2500 m淡出。10张活动纹理开启流式加载并限制最高2048，原始较小贴图不放大；插件资源不改写。独立入口为 `Tools/refine_solar_ground.py`，完整材质工具同步调用同一构建逻辑。

**验证：** UE材质编译并保存成功，统计2202条像素指令、11个采样器；颜色、法线、粗糙度、AO、自发光及金属度连接检查通过。8组前后机位与太阳照度/曝光参数完全一致，额外检查2个地表机位。地球平移0.5 m、2 m、返回原位、暂时关闭细节和升到10 km共6阶段检查完成；关闭细节的诊断状态已恢复。返回固定区域平均像素差约1.50/255，仅用于辅助对照，不代表全部位置和速度均无滑动。整球远景没有新增可见细节贴图，原云层采样纹理仍存在。

**范围：** 本轮只编译材质并重新运行PIE，没有修改C++、地图或太阳曝光配置，没有执行原生重新构建。所有贴图层作用于 SolarSystem 的共享岩质近景；厂商示例地图不在本轮修改范围。材质淡出不是地形LOD平滑修复，也不保证远距离贴图采样成本归零；没有完成稳定前台帧率基准。

**证据与回退：** [验证归档](Documentation/Verification/2026-10-12/SurfaceMaterials/README.md)，备份 `Saved/Backups/SurfaceMaterials_20261012`。截图说明见 [Images/README.md](Images/README.md)，最终结果为 `*-final.png`，`*-after.png` 保留初次接入阶段。以下为原位与移动后返回原位的真实截图，不是添加前后图。

![纹理定位检查原位](Images/2026-10-12/SurfaceMaterials/motion-origin.png)

![纹理定位检查移动后返回](Images/2026-10-12/SurfaceMaterials/motion-returned.png)

### 06｜统一轨道颜色、近地材质和植被分区规则

**问题：** 宏观颜色、近地四层材质及植被分别判断噪声、海拔与纬度，海岸宽度、雪线和干旱区缺少统一依据。

**修改：** 新增 `SolarBiomeRules.inl` 作为共同规则源，C++直接调用，材质生成器将其嵌入HLSL。分区返回颜色、沙/岩/土/雪权重、温湿度指标、海水及植被适宜度，替换原有重复判断。新增可读取分区的编辑器接口和验证脚本。

**验证：** 正式构建并重启成功。5颗岩质天体各1024个方向的权重和类别约束通过；40个方向、3组输出的GPU浮点回读与C++最大差约0.00000195。8组前后机位、太阳照度、曝光及地面高度一致，`HeightKm`函数未改动。画面分别见第07—09条。

**范围与代价：** 仅重建表面材质及生态分布，大陆轮廓和山体几何保持原样。10张纹理仍最高2K、流式加载；地表材质统计2987条像素指令、11个采样器，不能据此承诺帧率不变。规则修改后需要同时编译C++和生成全部太阳系材质，避免两侧版本不一致。

证据：[分区验证](Documentation/Verification/2026-10-12/SurfaceRegions/README.md)。回退包：`Saved/Backups/SurfaceRegions_20261012`，须配套恢复源码、着色文件、工具及资产再编译。

### 07｜重建地球海岸、干旱区、植被区和雪线

**修改：** 海岸沙层在8—45 m高度区间渐退；程序化湿润度结合纬度及海拔温度指标决定干旱区、湿润植被区和寒冷土层。坡度与高地权重增加裸岩，雪线随纬度变化并平滑过渡，陡坡减弱积雪覆盖。

**验证：** 宏观零坡度1024点抽样中，海水643、沙地主导40、岩地主导24、土层主导185、雪层主导132；均为程序化模型的抽样分类，不是现实面积比例。整球及地表同机位对照完成，原海岸样点在收窄沙带后转为土层过渡区，文件名沿用旧机位名称。

**限制：** 温湿度仅为分布指标，没有季节、风场、雨影或真实气象。没有新增湿沙、水浪、侵蚀、真实山脉和海沟。

![地球分区重建前](Images/2026-10-12/SurfaceRegions/earth-orbit-before.png)

![地球分区重建后](Images/2026-10-12/SurfaceRegions/earth-orbit-final.png)

### 08｜区分其他岩质天体的表土、岩地和极区

**修改：** 火星采用尘土、沙地、裸岩与南北不同范围的极区雪层；金星采用干燥土层及岩地主导的高地；月球、水星采用明暗平原表土与露岩。海水只属于地球，火星之外的非地球岩质天体不套用雪层，所有非地球区域均不生成植被。

**验证：** 5天体抽样中没有非法海水/植被/雪层类别。月球、火星及金星地表有实际画面，GPU回读覆盖水星；水星本轮没有新增运行截图。近地实际坡度可提高裸岩权重，零坡度统计中月球和水星均以表土为主，不代表不存在岩石混合。

**限制：** 分区为视觉近似，没有真实地质位置、土壤成分或物理冰相数据。雪纹理不区分水冰与干冰，仍未新增实体岩石。

![火星分区重建前](Images/2026-10-12/SurfaceRegions/mars-soil-before.png)

![火星分区重建后](Images/2026-10-12/SurfaceRegions/mars-soil-final.png)

### 09｜使树草散布遵循地表分区

**问题：** 原树草散布只使用宽泛海拔和纬度条件，没有读取沙地、积雪和坡面权重。

**修改：** 根据共享植被适宜度与湿润度调节树草密度，候选点再按实际地形坡度筛选；排除海水、沙地主导区、明显积雪和陡坡。保留原有1500个候选点、近景范围与树草模型，没有扩大常驻资源预算。

**验证：** 额外森林样点实际生成374棵树、784组草，1158个实例均未落入禁用区域；干旱沙地样点为0棵树、0组草。地球旧机位有前后对照；额外森林和沙地样点只有最终图，不能作为历史前后证据。

**限制：** 使用原有少量树草模型，未建立温带/热带/寒带对应物种、持久化生态或完整碰撞。散布候选点增加坡度采样，尚无稳定前台性能基准。

![原海岸样点分区及植被修改前](Images/2026-10-12/SurfaceRegions/earth-sand-before.png)

![原海岸样点分区及植被修改后](Images/2026-10-12/SurfaceRegions/earth-sand-final.png)

## 2026年10月16日

本轮排查开始于2026年10月15日，跨日完成；图像统一保留在开始日期目录。

### 01｜恢复岩质天体远景的陨石坑与中尺度细节

**问题：** 水星、月球只剩大块灰白分区，火星呈模糊橙色色块。分区重建时移除了原有颜色细节；远景球面法线也没有反映对应高度变化。

**修改：** 在共享分区底色之上恢复中尺度明暗和陨石坑变化，细节噪声根据屏幕像素大小过滤；从既有高度场计算岩质天体远景法线。采样方向改由局部位置获得，避免插值顶点法线精度导致碎点。近景同样使用这层宏观外观变化，沙、岩、土、雪的分区与贴图继续保留。

**范围：** 太阳系共享代理/地表材质；没有重建大陆或导入真实地形，不能据此把程序化陨石坑、山地视为真实水星、月球、火星地貌。没有提高贴图尺寸或增加纹理资源。

**验证：** 三颗天体固定时刻与机位前后对照；最终报告与实际编译统计见[验证记录](Documentation/Verification/2026-10-16/OrbitalAppearance/README.md)。`*-after.png`为中间版本，最终结果使用`*-final.png`。

![水星远景修复前](Images/2026-10-15/OrbitalAppearance/Mercury-before.png)

![水星远景修复后](Images/2026-10-15/OrbitalAppearance/Mercury-final.png)

![月球远景修复前](Images/2026-10-15/OrbitalAppearance/Moon-before.png)

![月球远景修复后](Images/2026-10-15/OrbitalAppearance/Moon-final.png)

![火星远景修复前](Images/2026-10-15/OrbitalAppearance/Mars-before.png)

![火星远景修复后](Images/2026-10-15/OrbitalAppearance/Mars-final.png)

### 02｜修正远近景交接遮罩的共同漏画

**问题：** 地球315 km高度、近景混合权重0.5时，远近景使用同一抖动图案和互逆阈值，造成部分像素两层都不绘制，出现密集细网纹。关闭云层后仍存在。

**修改：** 近景保留`Dither(blend)`，远景改用`1-Dither(blend)`，使遮罩逐像素互补。作用于全部岩质天体的相同交接逻辑，没有调整加载距离或相机位置。

**验证边界：** 已记录地球315 km交接机位；不同几何LOD的色差、法线差异与运动中的残余抖动仍不能用单张截图排除。本条与高空云层棋盘格不同。

![交接遮罩修正前](Images/2026-10-15/OrbitalAppearance/Earth-transition-before.png)

![交接遮罩修正后](Images/2026-10-15/OrbitalAppearance/Earth-transition-final.png)

### 03｜修正高空云层的淡白色棋盘格

**问题：** 地球整球视角中，淡白色云层出现规则点阵，转动时伴随闪烁。关闭体积云后点阵消失；复现时地形混合权重为0，排除远近景交接。

**排查与修改：** 保持原位、原光照比较云重建模式。只改双线性合成无效，模式2仍有残余；模式0在已检视角消除了明显棋盘格。项目默认云渲染目标模式从1改为0，保留重投影距离4 km、组件采样倍率0.5与原云密度材质。没有关闭云层或改用表面云贴图。

**代价：** 模式0追踪分辨率更低、云边缘略软；未提高采样量、贴图大小或全局画质。效果验证不等于稳定前台帧率基准，也不能保证任意相机运动下完全无噪声。该控制台设置作用于项目内使用体积云渲染目标的场景。

**机位说明：** 整球书签HUD显示约21024 **km**；另补充20 km（20000 m）机位，避免单位差异造成遗漏。包含一次整球视角侧向移动和金星云层复查。

![高空云层修正前](Images/2026-10-15/OrbitalAppearance/Earth-orbit-cloud-before.png)

![高空云层修正后](Images/2026-10-15/OrbitalAppearance/Earth-orbit-cloud-final.png)

### 04｜修正金星云层轮廓的阶梯边缘

**问题：** 金星月牙外轮廓出现明显台阶；半分辨率重建后的云边缘与下方球面清晰度不一致。

**修改：** 云渲染目标改为模式3，在场景内部渲染分辨率上逐像素追踪，绕过云专用低分辨率重建。保留金星昼夜受光、厚云和可穿越体积，不把整球设为自发光。此设置替代本日第03条的模式0临时处理。

**验证：** 固定月牙机位及往返平移对照，正式编译重启后再采集正常视口画面；外轮廓明显平滑。截图不是超分辨率离线渲染。完整机位和开销见[云稳定性记录](Documentation/Verification/2026-10-16/CloudStability/README.md)。

![金星轮廓修复前](Images/2026-10-16/CloudStability/Venus-before.png)

![金星轮廓修复后](Images/2026-10-16/CloudStability/Venus-final.png)

### 05｜统一处理地球与金星移动时的云层网纹

**问题：** 模式0虽然减轻了已检整球棋盘格，低分辨率云层在相机移动时仍出现块状边缘和不稳定重建。单张静态截图不能排除这一问题。

**修改：** 两颗活动天体共用第04条的逐像素体积云路径，保留场景本身的时域抗锯齿。没有按轨道/地表切换云贴图或巡视模式；既有远近地形互补遮罩继续保留。

**验证范围：** 金星月牙、地球整球、地球20 km、地球5 km云内及金星58 km云内，各采集静止、四个移动阶段和返回原位的正常视口画面。原始帧保存在`Saved/Diagnostics/CloudStability`。规则重建网纹和月牙阶梯在已检图像中消除；任意帧率、急转、云地遮挡和全部高度仍不能用这些定向检查作无缺陷保证。

**依据：** UE 5.8源码确认模式3跳过云专用重建；Epic的[UE-388559](https://issues.unrealengine.com/issue/UE-388559)另记录远距离几何上的双边上采样砖块伪影，目标修复为6.0。该记录支持排查方向，不表示已证明本项目所有现象属于同一引擎缺陷。

![地球移动云层修复前](Images/2026-10-16/CloudStability/Earth-before.png)

![地球移动云层修复后](Images/2026-10-16/CloudStability/Earth-final.png)

### 06｜降低逐像素云追踪的密度计算成本

**问题：** 直接提高云渲染分辨率会显著增加GPU开销；旧三维噪声在每个光线采样点重复进行多次哈希计算。

**修改：** 用离线生成的64³、线性G8体积纹理替代两层运行时噪声，三轴周期连续，保留三维侵蚀和原全球覆盖图。视线采样倍率由0.5调整为0.25，在本机默认基数下每条光线最多24次基础采样；没有增加覆盖图尺寸、阴影采样或全局画质等级。

**验证与代价：** 新体积纹理运行资源记录为384 KB。模式3、倍率0.25下的地球20 km同机位单次云事件，烘焙前约20.92 ms、烘焙后约8.72 ms；旧模式0该机位约5.48 ms，说明稳定性改进仍有成本。重启后的事件另存验证报告；后台GPU时钟、首次使用和编辑器视图影响抽样，不能换算为稳定前台FPS。全分辨率渲染目标也增加显存，未完成显存峰值基准。

**维护：** 新增`Tools/bake_cloud_noise.py`，生成源图后由`Tools/refine_solar_clouds.py`建立体积纹理和材质。材质重建必须在退出PIE后执行；改动C++采样预算需关闭编辑器正式编译。备份为`Saved/Backups/CloudStability_20261016`，回退需配套恢复配置、源码、云材质及生成器并重新编译。原噪声与周期烘焙噪声并非逐点相同，云内部小尺度形状会改变。

## 2026年10月17日

### 01｜修正远距离地球云层成片间歇丢失

**问题：** 地球约21024 km高度、J2000+26.22日的整球视角，左下侧大片云层间歇消失。2026年10月16日模式3修正了低分辨率轮廓，但仍保留云深度渲染目标，前一轮稀疏截图没有发现这个残留问题。

**定位：** 本机UE 5.8.2的模式3把以公里表示的云深度写入`PF_G16R16F`，合成时与场景深度比较并丢弃被遮挡像素。约21024 km处半精度浮点相邻刻度相差16 km，超过地球7 km云层厚度；采样深度变化可能跨过量化边界，造成遮挡误判。同位姿、同一时刻，只绕过该中间目标后成片漏云消失，证据与深度精度不足的机制一致。

**修改：** `r.VolumetricRenderTarget=0`，使用原生逐像素直接云绘制路径，仍启用体积云。模式3参数保留但在目标关闭时不生效；继续使用0.25视线采样、0.25阴影采样及64³三维密度纹理，没有把云贴到地表或提高采样预算。本轮没有修改材质资产或C++执行逻辑，原生代码仅修正文案注释。

**验证：** 同机位对照112帧，涵盖每种路径的16帧静止、24帧小幅平移/转向、16帧返回；使用正常视口截图，冻结天文时间。固定区域中，亮度最大变化超过20/255的像素占比由4.42%降至约0.0024%，大面积漏云在对照中消除。该指标仅描述本机位的亮度波动，不代表其他位置无缺陷。重启后的连续帧与近云、金星回归见[验证记录](Documentation/Verification/2026-10-17/CloudDepth/README.md)。

**开销与边界：** 同机位单次云GPU事件约1.78→1.44 ms；不是稳定FPS基准。此前64³纹理和采样预算保持不变。直接路径与模式3的半透明表面云合成不同，后续真实水体、玻璃或其他半透明物体需单独验证云遮挡。

**回退：** `Saved/Backups/CloudDepth_20261017`保存原配置、工具、文档及原注释源码。恢复配置并重启即可恢复上一版渲染路径，但也会重新引入本项问题。

![远距离云层丢失](Images/2026-10-17/CloudDepth/Earth-before.png)

![重启后远距离云层修正](Images/2026-10-17/CloudDepth/Earth-after.png)

### 02｜核实金星共用远距云深度修复

**检查目标：** 金星厚云外观接近纯色，单靠颜色变化难以判断是否存在与地球相同的深度误判，需要核对实际渲染路径。

**结论：** 活动金星与地球复用同一`PlanetaryCloudVolume`组件和同一动态体积云材质，只切换天体参数。两者过去都经过中间云深度纹理，因此同属T-042风险路径；第01条的全局`r.VolumetricRenderTarget=0`已经同时覆盖两者。源码没有按金星重新开启渲染目标的分支。非活动金星使用远景材质中的云覆盖近似，不经过该体积云中间深度路径。

**验证：** 当前会话从地球切换金星，再恢复原天体、时间与相机，控制台值始终为0；确认组件、材质实例相同，金星参数为48—70 km云层、视线采样倍率0.25。约21024 km高度月牙机位采集56张截图，其中1张误采到编辑器预览，已剔除，55张有效游戏帧覆盖静止、移动和返回。31张静止/返回帧的固定区域亮度峰峰值第99百分位约1.33/255；抽查轮廓与返回画面未见成片漏云。纯色厚云的视觉敏感度有限，代码路径与运行参数核对是本项主要依据，不外推为所有高度和遮挡均无缺陷。

**改动范围：** 补充全局配置适用范围注释和验证记录；没有额外修改金星材质、云厚度或采样预算，无需重新编译。证据见[金星共用路径检查](Documentation/Verification/2026-10-17/CloudDepth/VenusAudit.md)。本项没有新的渲染前后差异，以下为现状验证图，不冒充修复前后对照。

![金星直接云路径远景检查](Images/2026-10-17/CloudDepth/Venus-path-check.png)

### 03｜修正穿越大气渲染上界时的地表颜色突变

**问题：** 地球在约100 km处由带蓝色散射的地表突然变成较浓的绿/蓝底色；火星在约80 km处出现较弱色调变化。两个高度对应本项目的大气渲染上界，并非地表材质分区或真实大气的颜色断层。

**原因：** UE 5.8.2在相机位于大气顶外时强制逐像素积分，进入顶内后默认切换为低分辨率空气透视体积查表。本机查表覆盖距离为96 km，超出距离沿用最后一层；从高空斜看地面的完整散射路径可能长得多，边界两侧因此不能得到一致结果。引擎切换还含极小安全边距，地球实际阈值约高于顶面10 m。

**处理：** 保存`r.SkyAtmosphere.AerialPerspectiveLUT.FastApplyOnOpaque=0`并同步当前运行会话，让不透明地表在大气内外都使用逐像素空气透视计算。保留`FastSkyLUT=1`、云直接绘制、云采样预算、曝光、地表材质和各天体的大气高度，没有扩大查表纹理来掩盖边界。

**地球与火星验证：** 冻结天文时间、保持视向，分别在大气顶上/下200 m采集旧路径和修正路径共8张游戏截图，均确认近景地形混合完成。固定地表区域的平均RGB绝对差，地球由19.79降至0.58、火星由1.75降至0.76（量程255）；高度差引起的视差、云采样与几何变化仍计入差异，不能将其解释为误差率。原先明显的地表颜色阶跃在已检机位消除。

**其他天体检查：** 金星、木星、土星、天王星和海王星分别在各自大气顶上下200 m补充10张游戏截图，新路径下固定区域平均RGB差为0.24—0.42/255，未见同类地表颜色阶跃。太阳、水星、月球没有启用该大气组件。验证只覆盖各固定朝向，不代表所有高度与光照条件。

**代价与维护：** 大气内的不透明地表像素增加积分计算，保留天空快速路径以限制开销；没有新增纹理资源，未完成稳定前台FPS基准。该设置为全局，厂商示例尚未逐一回归。当前会话已生效、配置已保存，本项未重启编辑器或执行不必要的原生编译。工具、其他天体检查范围和图像索引见[专项记录](Documentation/Verification/2026-10-17/AtmosphereBoundary/README.md)。备份为`Saved/Backups/AtmosphereBoundary_20261017`；回退该配置并同步控制台变量会恢复旧近似及其突变。

![地球99.8 km修正前](Images/2026-10-17/AtmosphereBoundary/Earth-before.png)

![地球99.8 km修正后](Images/2026-10-17/AtmosphereBoundary/Earth-after.png)

![火星79.8 km修正前](Images/2026-10-17/AtmosphereBoundary/Mars-before.png)

![火星79.8 km修正后](Images/2026-10-17/AtmosphereBoundary/Mars-after.png)

### 04｜核查星环远景参考并保存实现依据

**目标：** 星环远景参考 NASA Eyes 的环带层次、透光和阴影观感；保留适合项目的原有网格，实现不要求与网页相同。

**结果：** 读取公开前端脚本中的环组件与三颗行星配置，保存来源、哈希和参数。网页使用径向颜色/透明度和遮挡近似，所读木星配置未建立该组件。交互页面加载超时，未取得同机位画面对照，不能宣称精确复制网页外观。未复制网页程序或纹理进入运行资产。

**资料：** [星环资料与实现说明](SourceAssets/SolarSystem/Rings/README.md)。前期准备的100顶点/162三角形方形承载网格通过面积与绕序检查，但未导入运行；最终保留原有环形网格。此资料准备项没有独立画面变化。

### 05｜统一星环着色并更新土星主要环带

**问题：** 原土星环使用二值裁切和等强度正弦细纹，环带几乎不透光，密集条纹在远景缺少像素过滤。单个土星组件也不能直接服务其他巨行星。

**修改：** 保留程序化环形网格，扩展为每颗行星1024段并共用半透明材质。土星同步使用新实现，不保留单独旧路径。重建主要C/B/A/F环、卡西尼分界及恩克/基勒缝隙，增加密集环带颜色变化；窄环按屏幕像素覆盖计算，无法分辨的细纹逐渐衰减。太阳照度、正背面透射近似、行星软阴影共用统一逻辑。

**验证：** 正式C++构建成功，重启后编译保存材质并在PIE采集正光、背光、侧视和近环画面。既有模型校验通过；当前运行的四个组件共用同一个材质，真实尺度与行星姿态同步。详细结果见[星环专项记录](Documentation/Verification/2026-10-17/PlanetRings/README.md)。本版针对远景，靠近后仍是连续平面，不是颗粒群。

**开销与维护：** 四环合计8192三角形、四个绘制组件，无新增纹理或碰撞；增加半透明像素计算，未完成稳定FPS基准。材质资产由`refine_solar_rings.py`维护，两个总生成入口均调用它。备份位于`Saved/Backups/PlanetRings_20261017`，回退需配套恢复C++、材质和生成脚本并正式编译。

![土星环改动前](Images/2026-10-17/PlanetRings/Saturn-lit-before.png)

![土星环改动后](Images/2026-10-17/PlanetRings/Saturn-lit.png)

### 06｜加入木星主环与纱环远景

**原状：** 木星没有星环组件。

**修改：** 增加主环与两层纱环及淡延伸带，径向位置参考NASA环表。使用共用材质的低密度尘埃预设，逆光方向连续增强，不通过特定角度开关显示。颜色与密度经过巡视用途的视觉增强，不等于实际光学厚度或严格肉眼亮度。

**验证与边界：** 正光机位很淡，逆光机位可辨主环和薄纱；近环/侧视纳入专项检查。没有实现具有显著垂直厚度的立体晕环，也没有木星卫星阴影。以下前后图采用相同正光机位，逆光图仅作为新增功能检查。

![木星改动前](Images/2026-10-17/PlanetRings/Jupiter-lit-before.png)

![木星改动后同机位](Images/2026-10-17/PlanetRings/Jupiter-lit.png)

![木星环逆光检查](Images/2026-10-17/PlanetRings/Jupiter-back.png)

### 07｜加入天王星暗窄环与淡外环

**原状：** 天王星没有星环组件。

**修改：** 以主要窄环及淡外环的径向位置建立专用分布，保留暗色与窄宽度。环平面与天王星自转姿态共用变换，不固定在世界水平面；亚像素环以覆盖率衰减，不强制绘制成固定宽度亮线。

**验证与边界：** 整球正光、背光、侧视和近环机位均已采集，默认整球视角主要可辨最强外侧窄环，较弱环随分辨率及受光变淡。尚未实现环偏心、宽度随经度变化、岁差和卫星遮挡；颜色与密度是视觉预设。

![天王星改动前](Images/2026-10-17/PlanetRings/Uranus-lit-before.png)

![天王星改动后](Images/2026-10-17/PlanetRings/Uranus-lit.png)

### 08｜加入海王星主要径向环带

**原状：** 海王星没有星环组件。

**修改：** 建立Galle、Le Verrier、Lassell、Arago和Adams主要环带，沿用四行星共同的透明度、受光和像素覆盖过滤。普通正光机位非常淡，逆光中更易辨认，不将其处理成土星同样的宽亮环。

**验证与边界：** 四类机位已检查，深度遮挡和行星投影使用与土星相同路径。Adams局部环弧尚未加入，不能用整圈径向纹理宣称还原环弧。本轮没有真实颗粒、穿环碰撞或完整测光校准。前后对照仍使用相同正光机位，另附逆光检查。

![海王星改动前](Images/2026-10-17/PlanetRings/Neptune-lit-before.png)

![海王星改动后同机位](Images/2026-10-17/PlanetRings/Neptune-lit.png)

![海王星环逆光检查](Images/2026-10-17/PlanetRings/Neptune-back.png)

### 09｜确认天王星外环的蓝红分区参考

**对照日期：** 2026年10月17日。NASA Eyes原始截图中，最外层是较宽的暗蓝环带，次外层是较窄的暗红环带，内侧另有暗灰带和密集细环。[NASA天王星资料](https://science.nasa.gov/uranus/facts/)明确外侧μ环偏蓝、内侧ν环偏红。画面中带Miranda、Titania标签的亮青色细线是卫星轨道辅助线，不纳入星环外观目标。

**当前差异：** 项目已设置两条外环的径向范围，但ν环仍复用灰褐色，μ环只有很弱的蓝色倾向；现有正光验收图主要显出一条窄环，未达到参考中的蓝红宽带层次。本项只确认参考并归档，没有修改着色参数。截图曝光、视角和太阳方位未匹配，不能直接用像素亮度倒推材质反照率。

以下为网页参考原图，不是项目修复后截图；项目现状见第07条。

![天王星外环蓝红层次参考](Images/2026-10-17/PlanetRings/EyesReference/Uranus-detail-reference.png)

### 10｜确认土星细环层次与双向投影差异

**对照结果：** NASA Eyes截图呈现灰色宽环、深色缝隙和细密但不等强的条纹，同时可见行星遮住照向星环的光，以及星环在行星表面形成暗带。项目已实现前一种投影，尚未实现后一种；当前已存正光图中的环更亮、更暖，细纹更规则。由于双方机位与光照不同，本项不判定亮度差全部来自材质，也不直接整体压暗土星。

**状态：** 参考归档，未修改运行资产。下图为网页参考；项目现状见第05条。

![土星环层次及环在行星表面的阴影参考](Images/2026-10-17/PlanetRings/EyesReference/Saturn-reference.png)

### 11｜确认海王星淡宽环与细环的远景层次

**对照结果：** NASA Eyes截图中，受光星球周围仍可分辨暗灰色宽带及细线。项目已存正光图中的环几乎不可辨，背光图可见部分宽带和细线；与参考存在可见性差异，但尚未对齐太阳、相机和曝光，不能据此推断固定增亮倍数。

**状态：** 参考归档，未修改运行资产；环弧仍未实现。下图为网页参考，不作为修复前后证据；项目现状见第08条。

![海王星暗灰环带参考](Images/2026-10-17/PlanetRings/EyesReference/Neptune-reference.png)

## 2026年10月18日

### 01｜接入示例海洋的波浪与水上光学

**原状：** 自制地球海面仅有基础颜色和光泽，近岸缺少示例中的波纹与水深观感。

**修改：** 从`MI_Planetary_Ocean`读取实例参数，在项目目录复制其SingleLayerWater父材质，接入两层程序化波浪、波浪法线、吸收和散射。保留WorldScape球形海面；厂商材质、太阳曝光和云预算未修改。生成入口统一为`Tools/refine_solar_ocean.py`。

**验证：** 同一近岸位置、朝向及天文时间的原始截图如下，波浪材质时间没有冻结。正式编译重启成功，海面画面完成定向检查；这是海洋阶段一，尚未加入破碎浪、岸边泡沫、湿沙、潮汐或流体交互。证据与边界见[专项记录](Documentation/Verification/2026-10-18/Ocean/README.md)。

![近岸海面改动前](Images/2026-10-18/Ocean/coast-before.png)

![接入示例并完成尺度适配后的近岸海面](Images/2026-10-18/Ocean/coast-final.png)

### 02｜允许巡视相机穿过海面

**问题：** 海平面被移动约束当作固体地面，从海拔10 m向下移动时停在约3 m，无法入水。

**修改：** 防穿透改用真实程序化海底高度，保留海底上方3 m净空；自动速度仍参考海平面附近净空，手动调速松开保持、双键恢复自动的规则保持不变。地表书签仍从海面或陆地上方进入。

**验证：** 相同20 m/s下降输入运行3秒，改动后到达约−50 m；继续下降停在约−146.293 m海底上方3 m，随后可正常上浮。原持续调速17项回归全部通过。调用实际C++共用移动入口，没有注入实体键盘；约束不是航天器物理碰撞。改动前实际入水截图不存在，前后移动数据保留在专项JSON报告中。

![改动后海拔负20米的水下位置](Images/2026-10-18/Ocean/underwater-final.png)

### 03｜修正真实尺度海面上的规则细网纹

**问题：** 初次复制示例后，海面出现规则点阵与条纹。波浪噪声在数亿厘米世界坐标下进入普通浮点运算，局部精度不足。

**处理：** 波浪法线函数在项目副本中改用相机相对坐标求导；该步骤单独使用仍有网纹。进一步利用原梯度噪声的128单位周期，在高精度材质运算中折回相位，再进行噪声采样；近海对照中的规则细格消退。没有放大贴图或增加波浪噪声层数，也没有改引擎源文件。

**验证：** 下方“处理前”是本轮初次接入版本，不是最初纯色海面。最终图与其机位一致，波峰随材质时间变化；未据此认定所有运动和全球位置完全没有采样噪声。

![示例初次接入后的海面细网纹](Images/2026-10-18/Ocean/sea-initial-port.png)

![噪声相位适配后的海面](Images/2026-10-18/Ocean/sea-final.png)

### 04｜为近海水体建立独立的远景衔接

**问题：** 单层水体直接延伸到高空交接区域时，与原远景着色差异显出多边形边界；仅衰减波浪或匹配底色仍不足以消除。

**修改：** 海洋在相机到表面距离5—20 km内使用互补遮罩，逐步从近海材质过渡到原轨道海洋；相同权重同时衰减波浪和近景海底。仅同步海底仍有边界，隔离隐藏水面组件后边界消失；追加海拔20 km及以上隐藏已淡出水面，并保持远景海洋组件可见。陆地保留180—450 km交接，控制器仍为连续飞行。生成入口同步维护该规则。

**验证范围：** 正式构建重启后的300 km同机位画面中，本次新增的多边形色差消失。20 km检查点在改动前后均有大面积雾状遮盖，不能据此宣称所有云海合成问题已解决；其原图保留在专项目录中。近景复测另发现遮罩漏点，见第06条。

![初次接入版本的高空海面边界](Images/2026-10-18/Ocean/handoff-300km-initial-port.png)

![完成海面独立覆盖过渡后的同机位](Images/2026-10-18/Ocean/handoff-300km-final.png)

### 05｜避免海面背面遮黑水下视野

**问题：** 直接保留示例的双面单层水体后，从海下20 m向上看出现大面积黑色。水上单层水体路径不能替代水下体积光学。

**阶段处理：** 项目副本只绘制海面正面，避免不透明背面遮挡入水后的视野。当前可以入水、上浮和查看海底；水下尚无雾化、折射窗口与全反射，本项为阶段性处理，不记为完整水下视觉已完成，后续见I-013。

以下为本轮初次接入版本与最终版本的同机位水下仰视，均由脚本直接摆放相机，不用于证明旧移动逻辑能够入水。

![初次接入后的水下背面遮黑](Images/2026-10-18/Ocean/underwater-up-initial-port.png)

![移除不透明背面后的水下仰视](Images/2026-10-18/Ocean/underwater-up-final.png)

### 06｜修正远景球面透过近海显示的细网纹

**问题与隔离：** 远景球面在低空保持可见后，海拔12 m处的水面出现密集细网纹；隐藏该球面的诊断帧中网纹消失。它与第03条的波浪噪声精度问题不同。仅改为球形海面交点距离仍未消除网纹。

**修改：** 海面、海底和远景材质的互补遮罩改用0.5裁剪中点，并明确将全隐/全显端点置为0/1，避免时域抖动函数残留像素。距离计算保留球形海面交点适配。生成脚本同步维护这些规则，插件原资产不变。

**验证：** 专项记录分别保留原阈值、球面距离、0.5阈值、端点修正各版本，不将中间版本命名当作通过证据。最终12 m同机位中密集细网纹及零星青色漏点消失；19.99/20.01 km地平线对照未见明显退出跳变，300 km未再出现新增色差。以下前图为本轮正式构建后暴露的网纹；后图使用最终材质，远景球面保持启用。

![远景球面启用后的近海网纹](Images/2026-10-18/Ocean/sea-verified.png)

![遮罩端点修正后的同机位](Images/2026-10-18/Ocean/sea-final.png)

## 2026年10月19日

### 01｜岸线蓝色三角条纹与海床颜色分离

岸线附近出现规则蓝色三角条纹。隐藏近海水面和远景球体后，条纹仍在地形上；地表着色将负高程直接替换为轨道水色，使海平面附近的插值/浮点差异变成硬色界。近景地形改为连续沙土、岩石海床，水色由水面承担。生成入口刷新所有保留的地表代码节点，修正最初只更新未连接旧节点的失效改动。最终11 m机位中蓝色条纹消失，460 m机位另行归档；不能据此宣称全海岸均无几何接缝。对应T-051，完整记录见[海岸与深水验证](Documentation/Verification/2026-10-19/OceanCoverage/README.md)。

![岸线修复前](Images/2026-10-19/OceanCoverage/Before/shore.png)

![岸线修复后](Images/2026-10-19/OceanCoverage/Final/shore.png)

### 02｜地球大气虚拟底面与深水视点相交

原大气底面位于海拔−1 km，深水巡视会进入遮蔽球。底面下移到−12 km，并沿用高度分布补偿，保留2—9 km实际云层高度。−0.993 km和−1.126 km固定机位复查，前图中的黑色大气遮挡消失；水下仍缺少介质吸收与折射，天空可见，未当作完整水下效果验收。最终正式构建成功（16.42秒），重启后确认参数生效。对应T-052。

![深水遮挡修复前](Images/2026-10-19/OceanCoverage/Before/deep.png)

![深水遮挡修复后](Images/2026-10-19/OceanCoverage/Final/deep.png)

### 03｜高空海面弧形色差仍未通过验证

9.398 km机位仍出现大块弧形海色边界。统一三层覆盖权重及调整远景反光参数未消除边界，且网纹更明显；已撤回试验并正式重编译，保留原距离过渡。隐藏近海水面后弧形边界消失；关闭水体反射或隐藏大气均无效，尚未定位到唯一底层原因。下一阶段优先检查SingleLayerWater深度、遮罩及远景交接，不再重复已证实无效的参数替换。对应T-053；这也限定了10月18日T-048、T-050的“已检机位”结论，不能外推到全高度和全位置。

![仍待修复的高空海面](Images/2026-10-19/OceanCoverage/Final/handoff.png)

## 后续记录约定

- 按实际日期追加 `## YYYY年MM月DD日`，同日使用连续编号；多个独立事项分别成条，不按沟通批次合并。
- 直接描述问题事实、改动和验证，以问题和工程状态为记录主体。
- 一条日志中的排查、修复、验证和回退应围绕同一事项，相关事项以编号关联。
- 可见改动应在实施前、后各保留真实截图，归档至 Images 并嵌入对应条目；无成对截图时注明缺失。
- 新结论替代旧结论时注明原因和适用范围，保留历史证据；条目拆分或编号变化时同步更新引用。
