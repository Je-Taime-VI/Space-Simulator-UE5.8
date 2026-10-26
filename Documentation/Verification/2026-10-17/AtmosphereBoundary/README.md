# 大气顶颜色连续性验证

日期：2026年10月17日（Asia/Shanghai），关联T-043及开发日志当日第03条。

## 原因与处理

本机UE 5.8.2源码`Engine/Source/Runtime/Renderer/Private/SkyAtmosphereRendering.cpp`约1973—2008行：相机半径达到`TopRadiusKm * 1.00000155763`时，强制关闭快速天空与快速空气透视分支。`Engine/Shaders/Private/SkyAtmosphere.usf`约1041—1077行分别实现空气透视体积查表与直接积分。查表深度本机为96 km，源码说明超出距离使用最后一层。

地球、火星在顶面以内切回查表，斜看远地表时可能没有覆盖到低空散射较强的路径，造成色调突然改变。配置`r.SkyAtmosphere.AerialPerspectiveLUT.FastApplyOnOpaque=0`使不透明地表一直采用直接积分。`FastSkyLUT=1`及`r.VolumetricRenderTarget=0`保留。本项没有修改引擎、材质、真实天体尺寸或大气顶高度。

## 方法与数据

复用固定天文时间、正常游戏视口Shot，禁用相机输入Tick，使用同一视向在大气顶上下200 m拍摄，结束恢复天体、时间、相机与速度设置。地球/火星各对照快速空气透视开启/关闭两种状态。

- `Comparison.json`和`ComparisonMetrics.json`：地球100.2/99.8 km、火星80.2/79.8 km共8张有效游戏截图；每张地形混合系数均为1、云直接绘制值为0。
- `OtherPlanets.json`与`OtherPlanetsMetrics.json`：金星150 km、木星300 km、土星600 km、天王星350 km、海王星300 km的大气顶各上下200 m，共10张游戏截图。新路径下固定区域平均RGB差为0.24—0.42/255，第95百分位均为1/255；画面抽查及数值未见相同地表颜色阶跃。仅覆盖各一个固定朝向，不代表完整大气真实性验收。太阳、水星、月球未启用此大气组件，无对应切换点。
- 固定地表区域(100,300)—(1250,650)平均RGB绝对差：地球19.7895→0.5787，火星1.7511→0.7600，量程255。第95百分位分别59→2、4→2。相差400 m的画面存在合理视差及采样差异，数值不是物理准确度或视觉误差率。
- 原始截图位于`Saved/Diagnostics/AtmosphereBoundary_20261017/comparison-final`，精选同高度前后图及原始问题截图位于`Images/2026-10-17/AtmosphereBoundary`。
- 首次诊断脚本在切换天体后未等太阳方向更新，已中止，`comparison`目录不用于结论。最终版延迟设置机位；分析工具验证同一天体上下两张旋转一致、游戏HUD存在、云配置正确和地形混合完成。
- 地球/火星对照的阶段最小等待为32个回调帧；其余天体回归为16帧，仍保留切换后的12秒场景等待及机位变更后的2秒等待。工具快照为回归结束版本。

工具为工程`Tools/verify_atmosphere_boundary.py`与`Tools/analyze_atmosphere_boundary.py`，采集完成与实际图像检查分开。本项当前会话已生效、默认配置已保存，但未重启；没有执行原生编译。

## 限制与回退

地表像素的大气积分开销增加，没有增加云采样或运行时贴图；未完成稳定前台FPS基准。天空快速路径、半透明表面空气透视与厂商示例不在本项全面验收范围。

备份为`Saved/Backups/AtmosphereBoundary_20261017`。回退只撤销不透明空气透视设置，并同步当前控制台变量或重启；保留云直接绘制修复。
