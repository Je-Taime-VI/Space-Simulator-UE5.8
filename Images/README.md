# 项目截图档案

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

## 后续归档规范

1. 按日期建立子目录，例如 `Images/2026-10-08/`。
2. 同一问题或功能使用共同主题名，分别加 `-before.png` 和 `-after.png`。
3. 实施前先采集一张，实施并验证后再采集一张；尽可能保持关卡、机位、分辨率和光照条件一致。
4. 在对应开发日志里分别插入两张图，写明日期、现象、前后状态和验证范围。
5. 如果仅有一侧截图或没有历史截图，明确说明缺失，不用后来生成或拍摄的画面伪装为历史证据。
6. 留下原始来源和临时诊断条件，不用开关造成的视觉差异冒充最终修复。
7. 每个独立问题或功能分别归档，并关联对应日志条目；新增问题使用新文件，替换旧文件时记录原因。

本目录当前不在项目 `.gitignore` 的 Saved 忽略范围中。复制或交接项目时应一并保留。Markdown 里的图片链接使用当前项目绝对路径，迁移项目后应同步更新。
