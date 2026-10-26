# 项目截图档案

2026年10月17日新增`2026-10-17/CloudDepth`：约21024 km机位的云层间歇丢失、重启后修正及金星轮廓回归。问题原图拍摄日期为10月16日；修复日期为10月17日。完整连续帧在Saved/Diagnostics/CloudDepth_20261017。

2026年10月16日新增`2026-10-16/CloudStability`：金星月牙轮廓、地球移动云层的同机位前后截图。使用正常视口Shot保留时域渲染；完整移动帧留在Saved/Diagnostics/CloudStability，验证范围见开发日志当日第04—06条。

建立日期：2026年10月08日。

用于保存真实问题和可见功能的修复前/后、添加前/后截图。这里只保存精选证据，不代替 Saved 中的完整运行日志和连续截图。

## 当前归档

### 2026年10月08日｜移动时地表消失

- 修复前：[terrain-disappearance-before.png](<2026-10-08/terrain-disappearance-before.png>)。
- 修复后：[terrain-disappearance-after.png](<2026-10-08/terrain-disappearance-after.png>)。
- 对应记录：[DevelopmentLog.md](<../DevelopmentLog.md>) 的“修复移动时地表消失、露出岩石地下模型”。

来源与说明：

- 前图原文件为 `D:\BIG WORLD UE5.8\Saved\Diagnostics\FlickerNoRenderLag\frame_01.png`，是实际移动复现帧；当时正在测试关闭渲染线程延迟，现象仍存在，因此该设置未保留。
- 后图原文件为 `D:\BIG WORLD UE5.8\Saved\Diagnostics\FlickerColdBuild\frame_03.png`，是在修复进入正式 DLL、重启编辑器后采集，正常渲染设置已恢复。
- 两图来自同一示例的相近观察方向，并非锁定同一帧、同一机位的像素比较。
- 文件按原始字节复制，没有裁剪、修图、补画或生成替代画面；归档时通过 SHA-256 核对与源文件一致。
- 此处采用本机连续采集中的复现截图，避免依赖临时剪贴板目录。

### 2026年10月08日｜EarthLikePlanet 远景地表缺块

- 修复前：[earth-distant-before.png](<2026-10-08/earth-distant-before.png>)，源码修补前由官方 MCP 直接采集。
- 修复后：[earth-distant-after.png](<2026-10-08/earth-distant-after.png>)，正式编译并重启后采集。
- 使用相同 PIE 相机位置与控制器朝向，记录在 `Saved/Logs/EarthInvestigationView.json`；两张均为原始全编辑器截图，没有裁剪或补画。
- 对比对象为地形几何是否连续。前图自动曝光已稳定，后图采用固定曝光；不是用于单独测量曝光算法的图片对。
- 此前阴影和速度通道修复在前后两图中都已存在。排查时的关闭遮挡查询、临时隐藏海洋未保留到最终配置。
- 瞬时曝光变化和无输入漂移主要依据配置、源代码和时间序列验证；没有把静态图伪称为这两种动态现象的完整证明。

### 2026年10月08日｜IceWorldPlanet 远山覆盖

- 优化前：[ice-lod-before.png](<2026-10-08/ice-lod-before.png>)，原始 6 级地形 LOD，自动曝光已稳定。
- 优化后：[ice-lod-after.png](<2026-10-08/ice-lod-after.png>)，已保存的 12 级地形 LOD 与最终固定曝光。
- 两图均为官方 MCP 的真实全编辑器截图；位置与朝向相同，记录于 `Saved/Logs/IceLodInitial.json`。差异用于说明远山覆盖，不单独用于曝光测量。
- 只调整 LOD 的中间对照为 `Saved/Diagnostics/IceLod/lod12-comparison.png`。前后截图没有裁剪、补画或生成替代画面。
- 对应开发日志第 16 条、技术问题 T-014。

### 2026年10月08日｜多层方形精度分界

- 原始截图：[planet-lod-rings-reported.png](<2026-10-08/planet-lod-rings-reported.png>)，从临时图像文件按原始字节归档。
- 分界尚未消除，暂无修复后配对图；远山覆盖截图不作为此问题已解决的证据。
- 对应开发日志第 17 条、技术问题 T-015。

### 2026年10月08日｜球心出生的无效变换

- 诊断原图：`Saved/Diagnostics/IceLod/spawn-at-center-invalid.png`，展示组件变换无效时的空画面。
- 当前运行实例通过恢复地表位置并重新生成恢复；球心输入的源码边界未修复，暂无永久修复后的配对图。
- 对应开发日志第 21 条、技术问题 T-017。该图未用作远山覆盖优化后的结果。

## 2026年10月09日｜太阳系基础场景

- `solar-system-before.png`：新建关卡尚无天体时的原始编辑器截图，关联当日开发日志第 01 条。
- `earth-orbit-after.png`、`earth-surface-after.png`：类地星球轨道与地表，关联第 01、02 条。
- `moon-orbit-after.png`、`moon-surface-after.png`：无大气月球，关联第 03 条。
- `sun-orbit-after.png`：可见太阳光球，关联第 04 条。
- `mercury-orbit-after.png`、`venus-orbit-after.png`、`mars-orbit-after.png`、`jupiter-orbit-after.png`、`saturn-orbit-after.png`、`uranus-orbit-after.png`、`neptune-orbit-after.png`：其余行星外观，关联第 05 条。
- `mercury-surface-after.png`、`venus-surface-after.png`、`mars-surface-after.png`：其余岩质天体地表回归截图。
- `earth-atmosphere-before.png`：散射强度修正前的灰雾原图；与 `earth-surface-after.png` 配对说明第 08 条。两张图机位净空约为 50/35 m，不能用于同机位性能比较。

运行结果截图由编辑器 `AutomationLibrary.take_high_res_screenshot` 直接保存，分辨率 1280×720；空关卡基线为官方编辑器截图接口的完整窗口图。逐天体拍摄时暂停时间并冻结巡视输入，结束后恢复。各新增天体没有单独的历史添加前图片，统一以新关卡基线说明添加前状态，没有生成或拼接模拟证据。

## 2026年10月10日｜连续飞行与天体校正

- `earth-low-orbit-before.png`：低轨马赛克与大气硬边的原始附图，按原始字节保存。
- `*-orbit-before.png`、`*-surface-before.png`：实施前在原版本中逐天体拍摄的真实视口截图。
- `*-orbit-after.png`、`*-surface-after.png`：正式编译并刷新已保存星表后的10个天体整球和5个岩质地表截图。
- `earth-clouds-after.png`：按实际覆盖函数选择阴天位置，在地面仰视体积云；近乎均匀灰白是该样点厚云遮盖的结果。没有用恒定密度诊断材质替代最终材质。
- `earth-descent-488p53km-after.png`、`earth-descent-220km-after.png`、`earth-descent-70km-after.png`、`earth-descent-10km-after.png`、`earth-descent-5km-after.png`、`earth-descent-1km-after.png`、`earth-descent-0p035km-after.png`：同一连续下降轨迹的分段记录，文件名是距起点局部地面净空；HUD海拔相对平均半径，因此数值略有差别。

运行画面均由 UE `AutomationLibrary.take_high_res_screenshot` 直接保存为1280×720，没有补画、生成替代画面或后期加工。前后部分机位因转轴和书签修正而不同，不用于逐像素比较、FPS测试或声明全部视角已达到最终写实效果。

关联开发日志2026年10月10日第01—14条；轨迹和数值报告见 `Documentation/Verification/2026-10-10`。两条小天体带只有逻辑区域，没有添加后截图。巨行星深层云海尚未实现，轨道截图不能当作其已完成的证据。

## 2026年10月10日｜速度调节与云性能

`2026-10-10/CloudPerformance/` 对应当日开发日志第15—17条：

- `system-memory-before.png`、`process-memory-before.png`：原始任务管理器附图，逐字节复制。
- `earth-orbit-before.png`：本项修改前同一书签机位截图；与 `earth-orbit-after.png` 对照云外观和HUD。速度与性能以数值记录为依据。
- `earth/venus-orbit-after.png`、`earth/venus-orbit-repeat-after.png`：正式编译后首次与往返切换机位。
- `earth-low-orbit-after.png`、`earth/venus-inside-after.png`、`earth/venus-surface-after.png`：低轨、云内和地表回归；`earth/venus` 表示分别两个文件前缀。
- 云内接近均匀灰白为高密度样点，地球地面样点为晴空；没有据此声称云层被关闭。金星本项没有新增原版同机位前图，火星云尚未实施。

上述运行截图为UE实际渲染1280×720图像，性能事件使用1376×808视口；没有后期编辑或生成替代证据。

## 2026年10月10日｜持续调速语义更正

`2026-10-10/RetainedSpeed/` 对应当日第18、19条：`controls-before.png` 为更正前原运行机位；`controls-auto-after.png` 为同机位的新自动模式，`controls-manual-after.png` 为在静止位置长按4秒并松开后的手动模式。运行画面为UE直接保存，没有修改像素；静态截图只验证HUD说明，持续速度行为见数值回归。

## 2026年10月11日｜地表实现差距核查

`2026-10-11/TerrainAssessment/` 保存七张2026年10月10日原始截图，按原始字节归档，没有裁剪或修改：

- `demo-baren-beach-reference.png`、`demo-baren-hills-reference.png`：原文件时间标记210032、210326，荒芜行星示例。
- `demo-earth-vegetation-reference.png`、`demo-earth-ocean-reference.png`：210427、210523，类地示例植被与海岸。
- `demo-moon-reference.png`、`demo-mars-reference.png`：210642、210732，月球和火星风格示例。
- `solar-earth-beach-before.png`：211100，自制太阳系地球现状。

原文件位于 `C:/Users/GrayRaveN/Pictures/Screenshots/屏幕截图 2026-10-10 HHMMSS.png`。来源与归档文件的SHA-256校验见同目录 `manifest.json`。对应2026年10月11日开发日志第01—04条。该核查阶段没有修复后截图；示例关卡和太阳系机位不同，不应作为同机位前后性能或画质测试。后续受光前后截图单列于下节。

## 2026年10月11日｜地表受光与曝光校准

`2026-10-11/SurfaceLighting/` 对应当日开发日志第07—10条：

- `*-before.png`：本轮实施前冻结时间、输入后采集的地表和轨道基线；与报告中的相同机位配对。
- `*-after.png`：首次正式受光版本。月球、火星、金星地表用于最终对照；地球轨道及过渡画面包含随后修复的大气遮蔽暗格，不能误当最终效果。
- `*-final.png`：加入地球遮蔽底面修正、再次正式编译并重启后的9个视点，包含昼夜与轨道过渡。
- `earth-grid-before-correction.png`：首次受光版的地球轨道暗格原图副本，配对 `earth-orbit-final.png`；不是任务开始时的原版画面。
- `earth-light-on.png`、`earth-light-off-diagnostic.png`、`earth-light-restored.png`：同机位诊断灯光开关，关灯仅为实验条件，完成后已恢复。`earth-opposite-view.png` 为相同位置反向视图，结合曝光记录验证转向设置。

所有图片为UE实际渲染的1280×720截图，没有后期改写像素。整体前后对照同时包含材质、太阳、曝光与天空光修改，不把全部变化归因于某一单项。截图中仍可见低轨LOD/法线分界和云采样纹理；本轮没有新增沙石细节贴图或完整海洋效果。

## 2026年10月12日｜沙、岩石、土壤与雪材质

`2026-10-12/SurfaceMaterials/` 对应当日开发日志第01—05条：

- `*-before.png`：修改前冻结模拟时间及输入后的8个机位，包含地球沙/岩石/土壤/雪、月球、火星、金星及地球整球。
- `*-final.png`：最终四层材质的8个相同机位；报告确认位置、方向、太阳照度和曝光补偿与前图一致。
- `*-after.png`：初次接入的中间结果。当时岩石选材与高地混合尚未完成，月面杂色随后纠正，不能当作最终版本。
- `earth-rock-rock-check.png`：更换岩石资源后、修正高地权重前的中间结果。
- `mercury-regolith-check.png`、`mars-polar-snow-check.png`：最终材质的额外水星表土与火星极区检查，没有同机位历史前图。
- `motion-origin.png`、`motion-offset-50cm.png`、`motion-offset-200cm.png`、`motion-returned.png`：地球固定时间下平移及返回检查。
- `motion-detail-disabled.png`：同机位临时关闭细节的诊断条件，检查后已恢复；不能作为修改前的历史画面。
- `motion-fade-10km.png`：升到平均海拔10 km后朝地检查，细节按相机到像素距离淡出。

全部为UE直接保存的1280×720真实渲染图，没有后期修改。HUD海拔相对平均半径；地表镜头离当地地面约5 m，因此高山截图可能显示数千米海拔。HUD速度是冻结输入前的控制器设定，不代表拍摄过程中以该速度运动。沙石颗粒主要来自颜色与法线，不能用截图推断已经新增几何、碰撞、岩石散布或完整海水。

验证报告见 [SurfaceMaterials](../Documentation/Verification/2026-10-12/SurfaceMaterials/README.md)。

## 2026年10月12日｜统一地表分区

`2026-10-12/SurfaceRegions/` 对应当日开发日志第06—09条：

- 8组 `*-before.png` / `*-final.png`：本项开始前及正式编译、重启并刷新材质后的同机位地表/轨道画面。位置、方向、采样高度、太阳照度和曝光均一致。
- 机位名称沿用旧标签，例如 `earth-sand` 表示原沙地机位；沙带收窄后该位置已主要为土层过渡，名称不代表当前分类。
- `earth-forest-region-check.png`、`earth-sand-region-check.png`：新规则下的森林与干旱沙地额外检查，只有最终图。前者1158个树草实例通过位置检查，后者没有树草；静态截图不代表整个区域实例总量或长期帧率。

所有截图为UE直接保存的1280×720画面。冻结时间及输入进行采集，HUD速度并非实际拍摄移动速度。实际高度保持不变，没有通过改变太阳或曝光制造前后差异。地形LOD、平铺重复和云采样纹理仍可见；完整证据见 [SurfaceRegions](../Documentation/Verification/2026-10-12/SurfaceRegions/README.md)。

## 后续归档规范

1. 按日期建立子目录，例如 `Images/2026-10-08/`。
2. 同一问题或功能使用共同主题名，分别加 `-before.png` 和 `-after.png`。
3. 实施前先采集一张，实施并验证后再采集一张；尽可能保持关卡、机位、分辨率和光照条件一致。
4. 在对应开发日志里分别插入两张图，写明日期、现象、前后状态和验证范围。
5. 如果仅有一侧截图或没有历史截图，明确说明缺失，不用后来生成或拍摄的画面伪装为历史证据。
6. 留下原始来源和临时诊断条件，不用开关造成的视觉差异冒充最终修复。
7. 每个独立问题或功能分别归档，并关联对应日志条目；新增问题使用新文件，替换旧文件时记录原因。

本目录不在项目 `.gitignore` 的 Saved 忽略范围中。复制或交接项目时应一并保留。仓库文档使用相对图片路径，迁移时保持目录结构即可。

- `2026-10-15/OrbitalAppearance`：10月15日至16日远景、交接遮罩和云层棋盘格的原图、前后对照；最终结果使用`-final.png`。

- `2026-10-17/AtmosphereBoundary`：地球100 km、火星80 km处颜色突变的原图、同高度修正前后图及其余五颗有大气行星的边界回归。

- `2026-10-17/PlanetRings`：四颗巨行星星环改动前后、背光/侧视/近环及移动抽样。木星和海王星的同机位正光环很淡，逆光图是附加检查，不冒充同机位对照。
- `2026-10-17/PlanetRings/EyesReference`：NASA Eyes外观参考原图，土星、海王星、天王星各一张，另有天王星局部图。原文件拍摄时间分别为20:46:17、20:47:41、20:46:44，局部图来自同日附件。文件逐字节复制，未调色；属于网页参考，不是项目修复后画面，双方机位与受光尚未匹配。

- `2026-10-18/Ocean`：海洋阶段一。6组`*-before.png`与`*-final.png`为原海面和最终材质的同机位对照；3张`*-initial-port.png`为本轮初次复制示例材质后、完成尺度适配前的中间版本，分别保留网纹、高空边界、水下背面遮黑。天文时间冻结，波浪材质时间未冻结。水下照片通过直接摆放相机获得，不能用改动前水下图证明旧移动规则可入水；实际进出测试数据见`Documentation/Verification/2026-10-18/Ocean`。原图逐字节归档，未做像素修改。
- 海洋附加图：`sea-verified.png`是远景覆盖启用后的网纹回归；`sea-grid-isolation.png`仅隐藏远景球面作诊断，不是最终实现。`*-boundary.png`为早期20 km俯视边界对照，`*-boundary-final.png`为最终19.99/20.01 km地平线视角。最终6机位报告是`endpoints.json`。
