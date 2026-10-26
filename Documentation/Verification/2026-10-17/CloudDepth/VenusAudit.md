# 金星共用云深度路径检查

日期：2026年10月17日，Asia/Shanghai。关联开发日志当日第02条、T-042。

## 源码与运行依据

- `SolarSystemActor::ConfigureAtmosphere`为活动地球、金星设置同一个`VolumeClouds`及`VolumeCloudMID`，差别是云高度、厚度、天体编号和大气参数。`SolarCloud.ush`的金星密度分支不选择渲染目标或深度格式。
- `Config/DefaultEngine.ini`中的全局`r.VolumetricRenderTarget=0`已在此前地球修复时保存。本次补充同时适用地球和金星的注释，没有改变执行参数。
- `VenusPathAudit.json`记录实际会话：地球、金星和恢复后均为0；组件及材质实例路径一致，金星`BodyIndex=2`、云可见、视线倍率0.25。
- 金星组件底面高度60 km相对于下移12 km的大气底面，实际云底仍为天体平均半径上48 km，厚度22 km，没有在本项改变云层高度。
- `UpdateVisuals`对非活动金星使用代理材质`VenusCloudCover`近似，不走同一个体积云中间深度纹理。

## 画面检查

复用`Tools/verify_cloud_depth.py`，冻结天文时间、设置金星月牙机位与21024.328 km高度，使用`start(values=(0,), stage='venus-shared-path')`采集。没有为此次核查重新开启已知有问题的旧路径。完成后恢复原天体、模拟时间、时间倍率、相机位姿和相机Tick状态。

- `VenusFrames.json`：56次正常Shot截图请求及位姿。
- `VenusMetrics.json`：55张有效游戏帧清单；`rt0-still-00100000.png`没有游戏HUD且实际显示编辑器中的地球预览，已排除，原文件保留在Saved。不把该批描述成无中断的56帧验收。
- 原分析工具因HUD检查拒绝此批；后续先按同一HUD区域均值阈值筛选，再仅对静止/返回帧计算相同固定区域(390,170)—(985,725)的亮度波动，未修改图像。31张有效静止/返回帧中平均时序标准差0.170，第99百分位峰峰值1.333/255，峰峰值超过20/255的像素占比约0.00303%。
- 精选静止、移动和返回原图在`Images/2026-10-17/CloudDepth/Venus-path-*.png`。完整原图在`Saved/Diagnostics/CloudDepth_20261017/venus-shared-path`。

抽查月牙轮廓与返回画面未见成片漏云。厚云纯色外观对局部变化不敏感，低波动不能单独证明每个像素的云都完整；主要结论是代码与实际运行均已绕过地球同款错误路径。其他高度、极端视点和半透明遮挡不在此次新增验收范围。未新增资源、提高采样或执行原生编译。
