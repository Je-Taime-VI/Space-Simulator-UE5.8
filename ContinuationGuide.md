# 项目接手说明

最后整理日期：2026年10月19日（Asia/Shanghai）。

本文记录项目目标、当前实现、配置依据、验证范围和维护流程。进度以工程文件及验证报告为依据；编辑器进程、当前地图和运行状态需在接手时重新核查。

### 当前接续重点：2026年10月19日海岸与深水

- 本轮保留两项修正：地表海床不再使用轨道水色，固定岸线11 m机位的蓝色三角条纹消失；地球大气虚拟底面下移至−12 km，避免深水相机在−1 km附近进入遮蔽球。正式构建、重启及六机位采集完成。
- **下一步先处理T-053：约9 km的弧形海色边界仍在。** 统一海拔覆盖权重与远景反光参数的试验已撤回，不要把`connected/after`等中间截图当完成结果；最终状态以`final.json`和`Final`照片为准。
- 隐藏近海水面可消除该大边界；关闭水体反射和隐藏大气均无效。需要检查SingleLayerWater深度、遮罩及球面代理交接，保留现有遮罩端点钳制。不要重复只改参数的无效试验。
- `refine_solar_ocean.py`现在调用`refine_solar_ground.refresh_shader()`，刷新保留的地表着色节点。历史材质有未连接的旧节点，检查必须从材质输出反向追踪，不能只取第一个Custom节点。
- 机位、前后照片、构建、有效/无效隔离说明及限制见[本轮验证](Documentation/Verification/2026-10-19/OceanCoverage/README.md)。备份位于`Saved/Backups/OceanCoverage_20261019`。
- 完整水下介质、折射窗口、全反射、泡沫和湿沙仍待实现。深水可见天空尚未处理。为控制单轮工作量，本轮在两项已验证修正处收尾，没有将水体整体标为完成。

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

### 2026年10月10日连续飞行与天体校正

以下状态替代上一版 G/O 与 70/220 km 切换方案，仅适用于独立 SolarSystem 地图。

- 取消 G/O 控制与自动 VisitSurface 调用。岩质天体距平均半径 1800 km 内预加载，450—180 km 渐变；必须等待 16 层地形生成后才淡出球面代理。相机和速度设置不由地形加载重置。超过 2400 km 后释放近景。
- 远近景共享 CPU/HLSL 高度及颜色规则，球体网格提高到 512×256 分段；近景增加程序化细节。外层 clipmap 环的几何/法线衔接仍需 I-004 的独立工作。
- 地球 2—9 km、金星 48—70 km 为本版体积云的渲染层。必须保留材质 `used_with_volumetric_cloud=True`；没有该标记会出现组件存在却不显示的情况。活动天体从太空到地面使用同一云体，远处非活动地球仍使用同一覆盖函数的薄层近似。
- 云渲染最终采用 `r.VolumetricRenderTarget=1`、`Mode=1`、`MinimumDistanceKmToEnableReprojection=4`，视线采样倍率 0.5。此前直接追踪的临时规避方案已由当日第16条优化替代；材质用途标记完整后，半分辨率路径的已检机位可正常显示。仍未进行稳定前台 FPS 基准。
- 方向光使用逐像素大气透光率；金星与火星大气底面放到平均半径下 12 km，并补偿散射高度分布，避免低洼地形进入大气遮蔽球。巨行星已有散射大气，但没有可进入的完整深层云海。
- 旋转轴以各自轨道法线为基准，IAU 极轴方位转换到黄道坐标。金星与天王星统一使用正周期绕角动量方向旋转；天王星轴倾角为 97.77°。相机书签保留黄道上方向，避免把每颗星球看成正立。
- 主带 2.1—3.3 AU、柯伊伯带 30—50 AU 已定义边界，没有生成小天体；半径和轨道仍采用真实公里尺度，巨行星使用平均半径球体近似。
- 构建：`Saved/Logs/SeamlessBuildFinal.log`。运行检查：`Tools/verify_continuous_planets.py`；输出 `Saved/Diagnostics/ContinuousPlanets/Verification.json`，长期证据另行归档至 `Documentation/Verification/2026-10-10`。截图位于 `Images/2026-10-10`。
- 运行结果：16项视图与450帧下降检查通过，加载引起的位置偏差0 cm。最后6个受影响材质视图与10天体参考系转换补充检查通过，报告 `MaterialFinalVerification.json`；坐标转换最大误差约4.54 mm。没有完成前台性能基准或飞船物理验证。
- 更新已保存地图中的星表需要执行 `reset_catalogue()` 并 `rebuild_preview()` 后保存，单独修改 C++ 默认值不会覆盖旧地图中的序列化参数。2026年10月11日起，材质刷新不再自动重置星表，避免覆盖独立的天体参数调整。
- 备份：`Saved/Backups/SeamlessPlanets_20261010`；回退须配套恢复源代码、配置、材质和地图，不能只恢复其中一个层面。

### 2026年10月10日速度控制与云性能修复

- SolarExplorer 调速语义已按当日第18条更正：左 Shift 长按渐增、左 Ctrl 长按渐减，松开保持手动速度；两键同时按住恢复自动，全部松开后才接受下一次单键调节。默认4秒翻倍/减半，从当前实际速度起调；滚轮每格×1.2或÷1.2。手动时绕过贴地速度/位移限制，HUD显示自动/手动。Ctrl不下降，Q/E径向升降；旧 Demonstration 控制不变。
- `ApplyFlightInput` 是键盘和脚本共用入口，保留解析最低3 m净空、分段高度投影和100 ms长帧保护。没有完整扫掠碰撞，不能直接作为飞船物理使用。
- 地球云通道原始 GPU 抽样约775 ms；关闭云后同场景约28 ms，主要瓶颈为逐采样噪声计算，不能仅凭系统84%内存占用归因为内存耗尽。
- `T_Clouds` 为1024×512线性灰度覆盖图，双线性过滤，横向重复/纵向夹紧。轨道薄层与活动体积云共享此图；近处仍计算三维密度，不把地表颜色改回低分辨率贴图。
- 云材质源在 `Shaders/SolarCloud.ush`，单独重建使用 `Tools/refine_solar_clouds.py`；完整材质重建也调用此脚本，避免旧慢路径复活。金星保持独立厚云参数。
- 正式构建及回归证据见 `Documentation/Verification/2026-10-10/CloudPerformance`；前后截图在 `Images/2026-10-10/CloudPerformance`。备份在 `Saved/Backups/CloudPerf_20261010`。
- 云优化阶段保留的8项旧输入检查只对应当时临时倍率语义；最新调速改用 `Tools/verify_retained_speed.py`，云验证脚本也引用它。9个云视图保持原验证记录；整球云通道地球/金星各3次样本中位约2.15/2.10 ms，重启读取配置1/1/4通过。这是GPU事件抽样，不是稳定前台帧率保证。
- 新调速备份在 `Saved/Backups/RetainedSpeed_20261010`，验证归档在 `Documentation/Verification/2026-10-10/RetainedSpeed`；正式重启后17项调速检查通过，涵盖保持、复位和不同输入步长。`SpeedAdjustmentDoublingSeconds` 可调灵敏度，默认4秒。手动速度保持到双键复位，不会因海拔或天体书签变化恢复自动。
- 火星薄冰云、季节变化及局部谷雾暂未加入，设计和验收边界见 I-008。

### 2026年10月11日地表实现核查

- 近景确实由 `AWorldScapeRoot` 生成；高度来自自定义 `SolarTerrainNoise` / `SolarModel::HeightKm`，远景为球面代理。真实天体尺寸与连续飞行已建立，但没有导入真实全球高程，不能把当前噪声地貌视为现实山脉、盆地或海沟的复原。
- 本节核查时，材质生成入口 `Tools/refine_solar_materials.py` 将 `M_Terrain` 和 `M_Ocean` 生成为 Unlit 材质，主要输出程序化颜色与手工明暗到自发光。地表缺少细节法线、粗糙度及完整受光；海洋有独立网格，但尚无水面波纹法线、反射、折射、深度吸收及岸边泡沫。先前“有海洋”指几何与覆盖范围，不代表完成写实水体。后续受光改动见下节。
- `EnsureTerrain` 清空原插件的 Foliages 列表，另行生成少量地球树草实例；当前没有岩石散布，海拔低于15 m不布置树草。示例中的材质、水体与生态组合没有完整接入太阳系。
- 插件现有海洋材质、沙石法线与组合贴图、月球高度图、高度图体积及侵蚀工具可作为后续基础；是否适配真实尺度、局部坐标及远近景过渡仍需实际验证。
- 后续方向为真实宏观高程、重点区域瓦片和近景材质细节三层组合，详见 I-009、I-010；地表与水体缺陷见 T-030、T-031，数据接入限制见 T-032。本节所述核查阶段未修改运行材质；后续修改与验证单列于下节。
- 七张对照原图归档至 `Images/2026-10-11/TerrainAssessment`，拍摄日期为2026年10月10日。示例与太阳系机位不同，不构成同机位前后对照。
- 洞穴能力另见 I-011：插件有实验性 TerrainHoleVolume，但当前材质未接入开洞标记、没有地下网格，巡视相机的3 m地表净空规则也不支持地下通行。固定洞穴可采用地表开洞加局部洞穴网格，自由挖掘另评估局部体积地形；尚未实施或选购插件。

### 2026年10月11日地表受光与曝光校准

以下实现替代上节核查时的 Unlit 状态；当日尚未完成细节材质、写实海洋和真实地形。细节材质的后续进展见2026年10月12日小节。

- `M_Terrain`、`M_Ocean` 已改为 Default Lit，颜色接入 Base Color，自发光为零。活动天体的远景代理与近景共用太阳光；非活动远景代理仍按各自太阳方向和照度计算辐亮度近似，避免局部方向光错误照亮其他天体。恒星、薄云和星环输出同步调整。
- `SolarSystemActor` 新增 `SolarIlluminanceAtOneAU=120000` lux，按日心距离平方反比衰减。这是大气消光前的渲染基准，并非精密太阳光谱标定。
- 太阳系自身的无界后处理使用 Manual：ISO100、f/16、1/125秒，基准 EV100≈14.966。默认曝光补偿为 `2*log2(日心距离AU)`，保证外行星巡视可见，不读取画面亮度；同一天体转向不会触发明暗适应。`bCompensateExposureForSolarDistance` 可关闭距离补偿，`ExposureCompensation` 控制整体偏置。不同天体不等同于同一固定摄影曝光。
- 新增64分辨率实时天空光，随观察位置采集有大气的岩质天体天空，20—120 km逐步淡出，并在夜侧关闭。月球、水星不补天空光；不是完整地表间接光照或洞穴遮蔽方案。
- 地球大气遮蔽底面下移1 km，并补偿散射密度和云层高度，解决球面三角形内部落入遮蔽球产生的海面暗格。地球实际半径、海平面及云层绝对高度不变，逐像素大气透光率保留。未验证水下漫游。
- 正式编译并重启后完成材质检查、地表/轨道/昼夜视图及关灯恢复对照。脚本为 `Tools/verify_surface_lighting.py`，证据在 `Documentation/Verification/2026-10-11/SurfaceLighting`，截图在 `Images/2026-10-11/SurfaceLighting`。低轨仍可见原有 LOD/法线和渐变采样分界，不能把受光修复描述成已达到示例全部画质。
- 本次作用于 SolarSystem 的共享材质和管理组件；没有修改厂商 Demonstration 地图或全项目默认曝光。备份为 `Saved/Backups/SurfaceLighting_20261011`，回退需配套恢复源码、材质与地图并重新编译。

### 2026年10月12日接入示例地表材质资源

- SolarSystem 的共享 `M_Terrain` 已接入沙、岩石、土壤/表土、雪四层颜色与法线；沙和雪读取示例组合贴图的 R 通道遮蔽、G 通道粗糙度，岩石和土壤暂用固定粗糙度。地表金属度仍为0、Default Lit、自发光为0，保留上一轮太阳与曝光设置。
- 复用 `/WorldScape/Ressources/Textures` 中 Sand、Rock、Dirt、Snow 资源，复制至 `/Game/SolarSystem/Textures/Surface`，没有改写插件原资源或直接替换整个示例主材质。岩石最终使用 `T_Rock3/T_Rock3N`，不是调试初版的 Desert 贴图。
- 地球按海岸/沙漠、坡度/高地、土壤、极区/高山雪混合；火星保留橙色沙土并在极区混雪；金星以岩石为主；月球、水星使用去除杂色后的灰色表土与岩石。太阳与巨行星没有固体近景地形，不应用这些地表层。
- 地面尺度为沙3 m、岩石6 m、土壤2.5 m、雪4 m重复一次。采用三平面投影与世界空间法线，原生 LWC 节点先计算相机坐标除以纹理尺度的分数部分，再加相机相对坐标，避免先将行星坐标降为单精度。细节从相机到像素300 m开始淡出，2500 m完全回到宏观颜色和几何法线。
- 10张活动纹理均开启流式加载、最高2048，较小原图不放大。材质统计为2202条像素着色器指令、11个采样器；三平面投影增加采样开销，不能把纹理尺寸上限等同于性能验收，尚无稳定前台帧率基准。
- 地表单独重建入口为 `Tools/refine_solar_ground.py`，着色代码为 `Shaders/SolarGroundDetail.ush`，颜色均值来源为 `SourceAssets/SolarSystem/SurfaceTextureMeans.json`。完整 `refine_solar_materials.py` 同样调用该层，避免完整重建回到无细节版本。应在 SolarSystem 编辑状态、退出 PIE 后执行重建，先备份材质；修改脚本/着色代码后须执行重建才会更新资产。
- `Tools/verify_surface_materials.py` 完成8组同机位前后对照、另外2个地表机位和6阶段移动/细节开关/高空检查；太阳照度与曝光补偿保持一致。证据见 `Documentation/Verification/2026-10-12/SurfaceMaterials`，图像以 `*-final.png` 为最终结果，`*-after.png` 是中间版本。此次只重编译并保存材质、重新运行 PIE，没有修改 C++ 或执行原生构建。
- 仍有重复纹理、clipmap几何/法线分界；没有增加岩石实体散布、真实高程、透明冰体、湿沙或完整海水效果。不能据此认定已达到示例的整体场景质量。T-030 部分解决，投影适配见 T-034。
- 备份：`Saved/Backups/SurfaceMaterials_20261012`，保存修改前材质目录、地图和材质工具。回退本项时恢复旧材质和旧 `refine_solar_materials.py`；本项未修改地图、光照源码或配置，无需撤回受光校准。

### 2026年10月12日重建统一地表分区

以下分区规则替代同日首次接入纹理时的独立判断；仍沿用那10张纹理及2K流式预算。

- 唯一规则源为 `Source/BigWorld/SolarSystem/SolarBiomeRules.inl`。C++通过适配器调用，材质生成时将同一文件嵌入 `SolarSurface.ush`；轨道颜色、近地四层权重、WorldScape温湿度/植被掩码和树草散布共同读取。新增 `GetSurfaceRegion` 可从编辑器读取某个方向的分区数值。
- 地球采用程序化湿润度、纬度/海拔温度指标、海岸高度、坡度与随纬度变化的雪线。海岸沙层在8—45 m高度范围渐退，干旱沙地由低湿润度及温度共同确定，高地/陡坡增加岩石，极区及高山增加雪；指标不是气候模拟或真实地理分类。
- 火星使用尘土、裸岩及南北不同范围的极区雪层；金星使用干燥岩地与土层；月球、水星使用明暗平原表土与露岩。月球/水星没有积雪、海水或植被，火星/金星也不使用地球植物分布。真实地质位置仍未导入。
- 树草密度改用同一分区的植被适宜度和湿润度，排除海水、沙地主导区、明显积雪和陡坡；保留原有树草模型、实例数量上限与近景生成范围。没有新增热带树种、真实生态群落或持久化生态。
- 已正式编译并重启。5颗岩质天体各1024个方向的宏观抽样通过；40个方向、3组输出的GPU浮点回读与C++最大差约0.00000195。8组同机位前后检查通过，另检查森林和干旱沙地的1158个植被实例，未发现落入禁用区域。`HeightKm`函数未改动，前后采样高度、太阳照度和曝光一致。
- 地形材质最终统计为2987条像素指令、11个采样器，原始纹理数量和尺寸未增加。规则与坡度检查有额外CPU/GPU成本，未完成稳定前台性能基准。原有平铺重复、clipmap分界、云层采样纹理与真实地形缺失仍存在。
- 修改规则后须正式编译C++并重新执行 `Tools/refine_solar_materials.py`；只更新其中一侧会重新造成不一致。单独 `refine_solar_ground.py` 只刷新近景，不能作为分区规则变更的完整构建步骤。
- 验证工具为 `Tools/verify_surface_regions.py`，归档在 `Documentation/Verification/2026-10-12/SurfaceRegions`，图片在 `Images/2026-10-12/SurfaceRegions`。完整回退包在 `Saved/Backups/SurfaceRegions_20261012`；必须配套恢复源码、着色文件、材质生成工具及材质资产，再编译并重启。

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

### 2026年10月16日远景细节与云层网格修正

本轮于2026年10月15日开始排查，跨日完成；截图目录按开始日期归档。

- 岩质天体远景曾因分区重建直接返回分区底色，丢失中尺度色差与陨石坑变化。`SolarSurface.ush` 新增独立外观细节层，CPU/HLSL共享的分区权重、高度及植被规则保持不变。CPU `SurfaceColor` 仍是分区底色，不能再用它与最终带细节的着色像素逐值比较。
- `SolarOrbitalDetail.ush` 从现有高度场恢复水星、月球、金星及火星的受光法线；采用局部位置计算方向，避免把低精度插值顶点法线当作地形坐标后产生碎点。没有导入真实天体高程或提高全球贴图尺寸。地球的高频高度和海洋暂不使用这一代理法线。
- 180—450 km交接改为互补遮罩：近景 `Dither(blend)`，远景 `1-Dither(blend)`。原有地形加载就绪条件、速度和连续飞行逻辑保持不变。
- 云层棋盘格与上述交接是两件事。整球视角关闭体积云后网格消失；改变合成插值无效，模式2仍有残余，最终选用 `r.VolumetricRenderTarget.Mode=0`。保持渲染目标开启、重投影距离4 km及云组件采样倍率0.5；默认模式由此前的1改为0，旧配置说明以本节为准。模式0采用四分之一分辨率追踪、半分辨率重建，云边缘会略软；未据此宣称所有视角和运动均无噪点。
- 定向验证入口 `Tools/verify_orbital_appearance.py`，长期证据 `Documentation/Verification/2026-10-16/OrbitalAppearance`，图像 `Images/2026-10-15/OrbitalAppearance`。仅改材质与配置，无需C++构建；只重建地表/代理可调用 `refine_solar_materials.refine_surface_materials()`，避免重建无关资产。
- 备份 `Saved/Backups/OrbitalAppearance_20261015`。回退材质需同时恢复生成脚本与着色源；回退云模式需恢复DefaultEngine.ini并重新启动或同步运行中的控制台变量。

### 2026年10月16日云层移动稳定性与金星轮廓

- **当前配置以本节为准：** `r.VolumetricRenderTarget=1`、`Mode=3`；两颗活动天体视线倍率0.25、阴影倍率0.25。重投影距离4 km保留，但模式3跳过云专用重建。前文模式1/0为历史版本。全分辨率指场景内部渲染分辨率。
- `SolarCloud.ush`读取64³周期三维密度纹理`T_CloudDetailVolume`，替代逐采样哈希噪声。仍是可进入的球形体积云；地球2—9 km、金星48—70 km和全球覆盖保留。内部小尺度形状会改变，没有实现真实天气。
- `Tools/bake_cloud_noise.py`使用NumPy/Pillow生成源图；退出PIE后调用`refine_solar_clouds.refine_clouds()`创建资产。已有体积纹理会被复用；修改烘焙源图后需要重导入`T_CloudDetailAtlas`并更新体积纹理源图，仅重建材质不会重新导入。
- 正式构建`Saved/Logs/CloudStabilityBuild.log`成功，重启读取1/3配置；5个机位各6个静止/平移/返回截图采集完成。工具为`Tools/verify_cloud_stability.py`，归档见`Documentation/Verification/2026-10-16/CloudStability`。不把定向检查外推为任意急转、遮挡及所有高度均无缺陷。
- 新体积纹理运行资源记录384 KB；逐像素追踪和渲染目标仍有额外计算/显存成本。旧模式0、未烘焙模式3与最终方案的事件分开记录，不把后台抽样当稳定FPS。
- 全局云渲染目标配置改变；材质与采样预算优化属于SolarSystemActor。厂商示例未逐一复测。回退包`Saved/Backups/CloudStability_20261016`，需恢复配置、源码、云资产并正式编译。
- UE Python的`-Vector`会修改原对象；测试反转方向使用`vector * -1.`。首次无效黑屏采集仅留在Saved，未列为通过证据。

### 2026年10月17日远距云深度修正（当前配置）

- **当前使用`r.VolumetricRenderTarget=0`直接绘制体积云。** 模式3仍保留在配置中，但只在渲染目标启用时生效。此前模式3仍使用半精度公里深度，在约21024 km处刻度间隔16 km，会把薄云误判到地表后方；同机位直接路径对照有效。
- 0.25视线/阴影倍率、64³密度资源、全球覆盖、云层物理高度保持不变。没有修改引擎或重新生成材质。本轮C++仅改解释注释，没有执行原生构建。
- 增加`verify_cloud_depth.py`连续帧诊断和`analyze_cloud_depth.py`波动统计；本轮输出在`Saved/Diagnostics/CloudDepth_20261017`，长期记录在`Documentation/Verification/2026-10-17/CloudDepth`。两个旧云验证工具已改为检查直接路径。
- 直接绘制不等于关闭云；仍用场景深度限制云光线追踪。模式3的半透明云合成路径不再使用，真实海水、玻璃等后续接入时需另验云遮挡。厂商示例没有在本轮逐一复测。
- 备份`Saved/Backups/CloudDepth_20261017`；按本节配置接手，避免根据历史记录重新开启模式3渲染目标。
- 金星与地球共用上述直接云路径，没有独立启用旧渲染目标的分支；2026年10月17日核对运行时同组件、同动态材质与切换前后`r.VolumetricRenderTarget=0`。金星55张有效远景游戏帧检查见`Documentation/Verification/2026-10-17/CloudDepth/VenusAudit.md`；1张误采到编辑器预览的帧已排除。本次仅补充范围注释和证据，不需要额外构建。

### 2026年10月17日大气顶地表颜色连续性

- 地球100 km、火星80 km附近的地表变色由空气透视积分/快速查表切换造成，与云深度、曝光和180—450 km地形交接不同。当前`r.SkyAtmosphere.AerialPerspectiveLUT.FastApplyOnOpaque=0`，不透明地表在大气内外均逐像素积分；天空仍为`FastSkyLUT=1`。
- 已保存默认配置并同步当前会话，无C++/材质改动，不需正式编译；本项没有重启编辑器。不要重新开启快速不透明空气透视，也不要只增大大气高度把突变推到另一位置。
- 工具为`Tools/verify_atmosphere_boundary.py`与`Tools/analyze_atmosphere_boundary.py`，证据见`Documentation/Verification/2026-10-17/AtmosphereBoundary`。地球/火星旧/新路径两侧对照需保持相同朝向、时间并等待地形完全混合；新增天体时按其大气顶检查。
- 增加不透明像素的大气积分成本，未完成稳定FPS基准；半透明水体/玻璃与天空查表仍需各自验证。备份为`Saved/Backups/AtmosphereBoundary_20261017`，回退本项不应撤销此前云直接绘制配置。


### 2026年10月17日四巨行星星环

- 目标是接近NASA Eyes的远景观感，实现沿用原土星的程序化环形网格；前期`SourceAssets/SolarSystem/Rings/SM_RingPlane.obj`没有导入运行，不要另建第二套。
- `SolarSystemActor`改为四颗巨行星分别持有环组件与MID，各1024段，均使用`M_Rings`。土星已经同步替换旧着色路径；环跟随本天体姿态、真实半径和远景压缩。
- `Shaders/SolarRings.ush`处理径向分布、连续透明度、正背面散射近似、行星阴影及像素过滤，无新增纹理。颜色与密度为巡视视觉预设，不能作为真实光学厚度或肉眼可见性依据。
- 材质维护入口`Tools/refine_solar_rings.py`；`build_solar_system.py`与`refine_solar_materials.py`均调用它。只改星环应退出PIE调用`refine_solar_rings.main()`，不要重建无关地表/云资产。
- 已正式编译、重启和保存材质/地图。专项工具为`verify_planet_rings.py`、`archive_planet_ring_checks.py`；验证、限定范围与截图见`Documentation/Verification/2026-10-17/PlanetRings`、`Images/2026-10-17/PlanetRings`。
- 当前仍是远景平面；木星立体晕环、土星广域淡环、海王星环弧、环对地表阴影和卫星遮挡、真实颗粒与碰撞尚未做，见I-012。网页交互视图加载超时，未完成同机位视觉匹配，不声称精确复刻。
- 继续保留`r.VolumetricRenderTarget=0`和`r.SkyAtmosphere.AerialPerspectiveLUT.FastApplyOnOpaque=0`；后续近大气、云、水体与环的半透明合成仍需专门验证。回退包`Saved/Backups/PlanetRings_20261017`。

### 2026年10月17日星环参考截图补充

- 已获得并归档4张NASA Eyes截图到`Images/2026-10-17/PlanetRings/EyesReference`，与现有项目验收图完成定性对照，见当日开发日志第09—11条。此前交互连接失败的记录保留；尚未完成相同太阳方位、视向和曝光下的匹配。
- 天王星下一步优先校正μ环暗蓝宽带、ν环暗红窄带与内圈细环的层次。当前ν环颜色仍复用灰褐色，不能称已匹配参考；带卫星名称的亮青轨道辅助线不要当作环。
- 土星环投影到星球表面的暗带尚未实现；海王星正光下淡宽带的可见性尚需匹配条件后校准。参考截图不证明网页亮度等于严格肉眼亮度。
- 本次仅整理参考与差异，没有改着色代码、材质资产或曝光，没有运行新的渲染回归。

### 2026年10月18日海洋阶段一

- 自制SolarSystem地球已接入示例`MI_Planetary_Ocean`参数及其SingleLayerWater父材质的项目副本`M_Ocean_WorldScape`，保留波浪、法线、吸收与散射。未覆盖插件原资产；太阳、曝光、云预算保持原值。
- `Tools/refine_solar_ocean.py`是维护入口。退出PIE运行`main()`，只更新海洋及必要的远景覆盖；总生成器和`refine_surface_materials()`均已接入，避免重建后复活纯色水面或失去海面交接。
- 波浪噪声按128单位周期在高精度域折回，再进入浮点噪声；`MF_OceanPerturbNormalHQ`仅修改项目内函数副本的求导坐标。初次移植有规则网纹，修正后的近海截图更连续。
- 海水与近景海底在相机至表面5—20 km范围内同步退出，原远景海面互补覆盖；陆地仍在180—450 km交接。单改底色、波浪法线或同步海底均不足以消除边界；隔离隐藏水面组件后边界消失，不能只归因于海底。
- 相机Q/E可穿过海面，按实际海底高度维持3 m净空。自动近海减速与手动保持规则保留，地表书签仍在水上生成。正式构建及重启完成，下降到−50 m、海底约束和上浮通过；17项持续调速回归通过。
- **未完成：** 水下体积雾、折射窗口、全反射、泡沫/湿沙、潮汐、浮力和尾流。当前关闭海面背面绘制避免入水遮黑，水下仰视仍是基础天空，不应宣称完整水下效果已经还原。20 km机位原有雾状遮盖也未定位，不能用其作为全面高空验收。
- 验证工具`verify_solar_ocean.py`，最终报告`Documentation/Verification/2026-10-18/Ocean/endpoints.json`，照片`Images/2026-10-18/Ocean/*-final.png`。此前包括`verified/spherical/threshold.json`在内均为中间版本，文件名不代表通过，以专项说明为准。
- 保持海面、海底和远景的裁剪阈值0.5及`SolarOceanMaskEndpoints`端点钳制。正式构建后近海复测的细网纹来自仍漏像素的远景遮罩；只换球形交点距离无效，只改阈值仍有孤立漏点。最终在材质输出上明确全隐/全显，不能撤掉端点保护。
- 水面遮罩归零后独立水体绘制仍会留下边界，隔离隐藏水面组件后消失。当前在海拔20 km及以上隐藏完全淡出的水面组件，同时让有海洋天体的远景球面保持可见，由材质遮罩控制覆盖；否则海拔低于180 km时整球组件会被旧逻辑关闭。该C++适配已追加正式构建，日志`OceanCoverageBuild.log`。
- 备份`Saved/Backups/Ocean_20261018`。回退时同步恢复C++、生成脚本、地图、`M_Planet`与`M_Terrain`；旧`M_Ocean`保留。保持云直接绘制和不透明空气透视积分修复，下一阶段优先I-013水下视觉。
