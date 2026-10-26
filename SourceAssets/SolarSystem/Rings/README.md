# 星环参考与实现资料

记录日期：2026年10月17日。

目标是接近 NASA Eyes 远景的环带层次与透光观感，不要求复刻其网格或着色代码。当前土星原有的程序化环形网格继续使用，四颗巨行星统一由 `SolarRings.ush` 着色。`SM_RingPlane.obj` 是前期准备的方形承载平面，**没有导入或用于运行**，不应误当成最终星环网格。

## 参考核查

- [NASA Eyes](https://eyes.nasa.gov/apps/solar-system/)公开分发的[前端脚本](https://eyes.nasa.gov/apps/solar-system/app.js)包含 `RingsComponent`。本次只读提取参数，不执行下载脚本；完整文件留在忽略版本控制的 `Saved/Reference/NasaEyes_20261017`。
- 已读版本采用双面透明网格、径向颜色/透明度、太阳与遮挡计算；土星有两套明暗纹理。土星、天王星、海王星主配置使用该组件，木星主配置未配置该组件。此结论只适用于所读版本。
- `EyesReference.json`记录来源、SHA256与外包范围。网页纹理的外包半径不等于完整科学环目录。未将网站 JavaScript 或 PNG 复制进运行资产，也未确认可直接移植的完整开源工程。
- 交互页面加载超时，本轮没有网页同机位截图，因此不能宣称逐像素还原。
- 2026年10月17日晚补充：已归档4张实际网页截图至`Images/2026-10-17/PlanetRings/EyesReference`，可以定性比较环带结构；尚未对齐相机、时间、太阳方位和曝光，仍不能宣称同机位或逐像素匹配。参见开发日志第09—11条。
- 截图可辨天王星外层暗蓝宽带、次外层暗红窄带；对应μ、ν环的颜色依据见[NASA天王星资料](https://science.nasa.gov/uranus/facts/)。当前ν环灰褐色需修正，μ环及海王星淡宽带的可见性尚需校准。土星截图还显示尚未接入的环对行星表面投影。所有截图只作参考资料，未嵌入运行材质。

## 运行实现

- C++为木星、土星、天王星、海王星分别建立1024段环形网格，每颗2048个三角形，无碰撞；共用`/Game/SolarSystem/Materials/M_Rings`。
- 环的位置、姿态和缩放与对应行星共用变换，包括天王星自转轴倾角、远距离压缩和当前天体的真实厘米尺度。太阳方向按各行星分别计算。
- 半透明替代原土星的二值裁切；采用连续正背面散射、行星投影和有限太阳角度的软阴影。窄环按像素覆盖率过滤，细条纹超过像素分辨能力时衰减，无相机角度开关。
- 保留正常深度测试；半透明不写入主深度。材质不接收低精度顶点雾，不改动云直接绘制或空气透视修复的全局设置。
- 不新增全局纹理、体积纹理或颗粒系统。相较单个土星环增加三个网格与半透明像素计算，实际成本取决于覆盖屏幕面积。

## 数据与视觉取舍

径向位置主要依据[NASA 木星环表](https://nssdc.gsfc.nasa.gov/planetary/factsheet/jupringfact.html)、[土星环表](https://nssdc.gsfc.nasa.gov/planetary/factsheet/satringfact.html)、[天王星环表](https://nssdc.gsfc.nasa.gov/planetary/factsheet/uranringfact.html)、[海王星环表](https://nssdc.gsfc.nasa.gov/planetary/factsheet/nepringfact.html)。这些表中也有测量范围与近似值，本轮没有处理环偏心率和岁差。土星细纹为程序化近似。

颜色、光学厚度和尘埃散射参数为便于巡视的视觉预设，尤其淡环经过增强，**不等于真实测量反照率、肉眼可见性或严格辐射传输**。它们会随受光、视角和像素覆盖连续变化，不会在任意角度都显示成亮线。木星尘埃在逆光下增强的方向参考[NASA 尘埃散射说明](https://science.nasa.gov/photojournal/jupiters-ring-halo/)。

当前只绘制木星主环/纱环、土星主要C/B/A/F环、天王星主要窄环及淡外环、海王星主要径向环带。木星立体晕环、土星广域E/G环、海王星局部环弧、卫星阴影、环投影到行星表面、真实颗粒与穿环碰撞均待后续实现。现有太阳系还没有这些巨行星的卫星，不能伪造已实现的卫星遮挡。

## 维护入口

1. 修改`Shaders/SolarRings.ush`后，退出PIE，在编辑器Python中调用`refine_solar_rings.main()`编译保存材质。总材质生成器`refine_solar_materials.refine()`也调用同一入口，不会恢复旧土星材质。
2. 修改C++组件或网格后关闭编辑器正式编译，再重建材质与预览。备份见`Saved/Backups/PlanetRings_20261017`。
3. 使用`Tools/verify_planet_rings.py`采集前后、正背光、侧视与近环机位。实际验收结果见`Documentation/Verification/2026-10-17/PlanetRings`，源码存在不代表运行已验证。
