# 海岸条纹与深水遮挡检查

2026年10月19日，UE 5.8.2，`/Game/SolarSystem/Maps/SolarSystem`。

## 本轮保留的修正

- 地表材质将海底作为沙土/岩石处理，不再把水面远景的蓝色直接涂到海床。此前低于海平面的硬色界，在岸边形成规则蓝色三角条纹；隐藏海面和远景球体后仍可见。修正应用到实际连接的地表着色节点；生成脚本同步刷新所有保留的同类节点，避免改到未连接旧节点。
- 地球大气的虚拟底面从平均半径下1 km移至12 km。沿用高度分布补偿，保持海平面处的Rayleigh/Mie密度参数；云层实际高度仍为2—9 km。它避免巡视相机在约−1 km处穿入大气遮蔽球，不代表实现了水下介质。
- 正式构建成功，最终构建耗时16.42秒，见`BuildFinal.log`。已有浮点截断警告仍存在。曾因编辑器尚未完全退出而被Live Coding阻止构建，等待正常退出后重试成功。

## 机位与证据

`Sites.json`保存基线机位，纬度约23.261616°；岸线经度约89.834089°。深水机位经度85°，解析海床高度约−1.787562 km。`before.json`与`final.json`记录实际位置、姿态、海床高程和可见状态。

最终采集包括岸线11 m、岸上460 m、深水−0.993/−1.126 km、交接9.398 km与25 km高空。最终截图归档于`Images/2026-10-19/OceanCoverage/Final`；前图位于`Before`，原始五张问题截图位于`Reported`。波浪动画时间没有锁定，截图用于检查空间条纹与覆盖边界，不做逐像素误差比较。

修正前岸边：

![岸边前图](../../../../Images/2026-10-19/OceanCoverage/Before/shore.png)

最终岸边：

![岸边最终图](../../../../Images/2026-10-19/OceanCoverage/Final/shore.png)

−0.993 km遮挡前后：

![深水前图](../../../../Images/2026-10-19/OceanCoverage/Before/deep.png)

![深水最终图](../../../../Images/2026-10-19/OceanCoverage/Final/deep.png)

## 未通过的部分与下一步

**约9 km海面的大块弧形色差仍未解决。** 统一海拔覆盖权重、匹配远景反光参数的试验没有消除边界，并加重可见网纹，已经撤回。最终保留原5—20 km表面距离过渡和20 km水面组件退出规则，不将中间版本称为完成。

隔离检查中，隐藏近海水体后大弧形边界消失；关闭水体反射、隐藏大气均不能消除。最终需要继续检查SingleLayerWater绘制、深度/遮罩与远景球面的交接，不能只凭本次证据认定某个引擎通道就是唯一原因。试验代码保存于`Saved/Diagnostics/OceanCoverage_20261019/RejectedUniformCoverage.*`，不参与运行。

早期`before`中的`shore-no-water`被运行时可见性写入覆盖；`after-isolation`首帧地形混合为0。两者均不能作为有效隔离证据。后续`isolated-settled`先等待地形就绪再暂停管理器Tick，记录了混合权重和实际隐藏状态。

完整水下吸收、散射、折射窗口、全反射，以及泡沫、湿沙、浮力和尾流仍未完成。深水图仍可看见天空，不能作为完整水下效果验收。没有进行全海岸、全纬度、高速连续飞行或性能基准测试。

## 维护与回退

源文件：`SolarGroundDetail.ush`、`refine_solar_ground.py`、`refine_solar_ocean.py`和`SolarSystemActor.cpp`；采集脚本为`verify_ocean_coverage.py`。运行时与材质状态见`RuntimeFinal.json`和`MaterialFinal.json`。

备份位于`Saved/Backups/OceanCoverage_20261019`。回退应同步恢复源文件和材质，C++恢复后重新编译。原WorldScape示例及引擎资源没有修改。`SHA256.json`记录归档文件校验值。
