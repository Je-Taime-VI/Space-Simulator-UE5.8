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

## 后续记录约定

- 按实际日期追加 `## YYYY年MM月DD日`，同日使用连续编号；多个独立事项分别成条，不按沟通批次合并。
- 直接描述问题事实、改动和验证，以问题和工程状态为记录主体。
- 一条日志中的排查、修复、验证和回退应围绕同一事项，相关事项以编号关联。
- 可见改动应在实施前、后各保留真实截图，归档至 Images 并嵌入对应条目；无成对截图时注明缺失。
- 新结论替代旧结论时注明原因和适用范围，保留历史证据；条目拆分或编号变化时同步更新引用。
