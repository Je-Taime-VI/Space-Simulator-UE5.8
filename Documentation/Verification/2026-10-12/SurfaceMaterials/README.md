# 示例地表材质接入验证

执行日期：2026年10月12日，Asia/Shanghai。环境为UE 5.8.2、SolarSystem地图、Win64编辑器实际Play会话。

## 最终实现

`M_Terrain` 保持Default Lit，四层颜色与法线使用以下插件资源的项目副本：

- 沙：`/WorldScape/Ressources/Textures/Sand/T_Sand_Far_C`、`T_Sand_Far_N`、`T_Sand_Far_ORMH`。
- 岩石：`/WorldScape/Ressources/Textures/Rock/T_Rock3`、`T_Rock3N`。
- 土壤：`/WorldScape/Ressources/Textures/Dirt/T_Dirt_Albedo`、`T_Dirt_Normal`。
- 雪：`/WorldScape/Ressources/Textures/Snow/T_Snow_Albedo`、`T_Snow_N`、`T_Snow_ORMH`。

项目副本位于 `/Game/SolarSystem/Textures/Surface`，没有改写插件原资源。最终活动资源共10张，最高2048且开启流式加载；较小原图不放大。岩石与土壤没有接入独立粗糙度/AO图，采用0.83/0.9固定粗糙度及AO=1。沙和雪组合图的R为AO、G为粗糙度，金属度统一为0。颜色均值在 `SourceAssets/SolarSystem/SurfaceTextureMeans.json`，来自原贴图逐像素sRGB转线性后的均值；用来保留天体宏观反照率，不把资源原色直接覆盖整颗星球。

材质使用世界空间三平面投影与法线，原生LWC节点先取相机纹理相位，Custom节点再处理相机相对位置。最终统计为2202条像素着色器指令、11个采样器；这些是编译统计，不是GPU时间或显存实测。

可调参数位于 `M_Terrain` 及其材质实例：`DetailStrength=1`、`NormalStrength=1`；`SandTileCm=300`、`RockTileCm=600`、`SoilTileCm=250`、`SnowTileCm=400`；`DetailFadeStartCm=30000`、`DetailFadeEndCm=250000`。淡出使用相机到像素的距离。`DebugLayerWeights=0` 为正常渲染，1只用于诊断。实例 `RadiusKm` 已按各自天体配置，巨行星/太阳的实例虽有此参数，但没有岩质近景地形。

## 报告与图像对应

- `Sites.json`：8个固定机位，包括地球沙地、土壤、高地、雪面、月球表土、火星沙土、金星岩地和地球整球。
- `before.json`：接入前原始记录；因早期截图回调重入，含4条额外重复的地球沙地记录，内容相同。按机位名称去重后为8个机位；未删改原报告。
- `after.json`：初次接入的中间记录，含1条额外重复记录。后续更换岩石资源、调整高地权重并消除非地球杂色，不能将其当作最终材质验证。
- `final.json`：最终8个机位，无重复且无检查错误。配对图片为 `Images/2026-10-12/SurfaceMaterials/*-before.png` 和 `*-final.png`。
- `PoseComparison.json`：前后8组位置、旋转、太阳照度及曝光补偿一致。不是像素完全相同的声明。
- `check.json`：最终材质的水星表土、火星极区两个额外机位。对应 `mercury-regolith-check.png` 和 `mars-polar-snow-check.png`，没有历史前图。
- `Motion.json`：地球原位、0.5 m平移、2 m平移、返回、临时关闭细节、升到10 km共6阶段的位姿。对应 `motion-*.png`。细节关闭只为诊断，结束后恢复。
- `MaterialAudit.json`：最终材质连接、10张纹理来源/默认引用/尺寸/流式/压缩设置、默认参数及10个实例半径检查。
- `ExamplePackedChannels.json`：原示例主材质中组合贴图通道读取的检查结果。
- `ImageMetrics.json`：固定图像区域的辅助差分，RGB范围0—255；返回原位约1.50、关闭细节约21.76、地球整球前后约1.15。时间重建与云会改变像素；此数值不能替代视觉检查、运动测试或画质评分。

截图均由UE `AutomationLibrary.take_high_res_screenshot` 直接保存为1280×720，没有修改像素。拍摄时暂停模拟并冻结巡视输入，HUD速度仍显示控制器设定，不能据此推断拍摄速度。海拔相对平均半径，地表机位净空约5 m。中间版本图片保留并在 [图片说明](../../../../Images/README.md) 中标明。

## 执行方式与验收边界

单独材质重建：退出PIE、保持SolarSystem编辑地图加载，在编辑器Python中执行 `Tools/refine_solar_ground.py`。完整 `Tools/refine_solar_materials.py` 也调用相同的构建逻辑。执行前应备份材质；材质生成工具会覆盖生成资产上的直接图表编辑。

图像采集工具为 `Tools/verify_surface_materials.py`，在实际Play会话中导入后运行 `SurfaceProbe('新阶段名')`；默认优先读取 `Saved/Diagnostics/SurfaceMaterials/Sites.json`，缺失时读取本归档的机位配置。`MotionProbe()` 为额外诊断。工具会移动巡视相机并冻结输入/时间，适合独立验证会话；完成后应退出PIE再继续编辑。重新检查使用新阶段名，避免覆盖历史截图。

本轮完成材质着色器编译、资产保存、重新运行PIE与上述机位检查；没有修改C++、原生重新构建或重启编辑器。最后退出PIE并恢复编辑器原机位，检查时无未保存地图或内容包。

验证覆盖指定机位与短距离平移，未覆盖所有地貌、速度、夜景或平台。尚未进行稳定前台帧率基准；三平面投影增加采样成本，最高2K与流式加载不能代替开销测量，距离淡出也不证明远处计算成本为零。现有平铺重复、clipmap几何/法线分界、真实高程缺失、岩石散布及完整海水效果均不属于已完成结果。

备份位于 `Saved/Backups/SurfaceMaterials_20261012`，包含修改前的材质目录、生成工具与地图副本。本轮没有修改地图、太阳照度、曝光或原生源码；回退材质及生成工具即可撤回本项，不要把上一轮受光校准一并撤回。
