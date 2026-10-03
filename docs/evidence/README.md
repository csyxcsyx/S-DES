# 截图与测试证据

所有生成证据集中在本目录；操作指南、开发接口和课程报告位于上一级 `docs`。

## 界面

`screenshots/01`～`05` 对应五个页面，默认尺寸 1120 × 900；同名 `-compact` 文件为 880 × 600。均由实际 Qt 控件操作和离屏渲染生成。

- [二进制加解密](screenshots/01-binary.png)
- [ASCII 文本](screenshots/02-ascii.png)
- [暴力破解](screenshots/03-attack.png)
- [封闭测试](screenshots/04-collisions.png)
- [测试与说明](screenshots/05-testing.png)：CSV 为本地样例回读，组间记录仍待补充。
- [加载动效](screenshots/06-loading.gif)：真实 Qt 控件帧预览，计算和展示时长独立；不是桌面录像。
- [展开计算步骤](screenshots/07-trace.png)
- [下拉选项](screenshots/08-dropdown.png)
- [密钥分组页签](screenshots/09-key-groups.png) · [计算前的结果区域](screenshots/10-binary-empty.png)
- 150% 缩放：[破解](screenshots/11-attack-150.png) · [密钥分组](screenshots/11-groups-150.png) · [交叉表](screenshots/11-cross-150.png)
- [应用图标 PNG](../../sdes_app/ui/assets/app.png) · [SVG](../../sdes_app/ui/assets/app.svg) · [Windows ICO](../../sdes_app/ui/assets/app.ico)

## 实测数据

- [unittest 日志](results/unittest.txt) · [环境与实验汇总](results/summary.json)
- [本地交叉样例](results/local-vectors.csv)
- [256 种明文统计](results/collision-statistics.csv)
- [指定明文的全部密钥映射](results/collision-mapping-10011010.csv)

运行 `python tools/verify_project.py` 更新数据与报告；运行 `python tools/capture_screenshots.py` 更新截图。动图使用可选 Pillow 依赖和 `--animation`，步骤见 [开发手册](../developer-guide.md)。每次运行耗时可能不同。
