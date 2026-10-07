# 截图与测试证据

所有生成证据集中在本目录；操作指南、开发接口和课程报告位于上一级 `docs`。

## 界面

`screenshots/01`～`05` 对应五个页面，默认尺寸 1120 × 900；同名 `-compact` 文件为 880 × 600。均由实际 Qt 控件操作和离屏渲染生成。

- [二进制加解密](screenshots/01-binary.png)
- [ASCII 文本](screenshots/02-ascii.png)
- [暴力破解](screenshots/03-attack.png)
- [封闭测试](screenshots/04-collisions.png)
- [测试与说明](screenshots/05-testing.png)：8 条本地样例的 CSV 回读验证。
- [加载动效](screenshots/06-loading.gif)：真实 Qt 控件帧预览，计算和展示时长独立；不是桌面录像。
- [展开计算步骤](screenshots/07-trace.png)
- [下拉选项](screenshots/08-dropdown.png)
- [密钥分组页签](screenshots/09-key-groups.png) · [计算前的结果区域](screenshots/10-binary-empty.png)
- 150% 缩放：[破解](screenshots/11-attack-150.png) · [密钥分组](screenshots/11-groups-150.png) · [交叉表](screenshots/11-cross-150.png)
- 组间交叉测试：[CSV 第 2～6 行](screenshots/12-peer-cross-top.png) · [CSV 第 6～10 行](screenshots/12-peer-cross-bottom.png)，1280 × 1100，另一小组的 9 条数据全部通过。
- [应用图标 PNG](../../sdes_app/ui/assets/app.png) · [SVG](../../sdes_app/ui/assets/app.svg) · [Windows ICO](../../sdes_app/ui/assets/app.ico)

## 组间交叉测试

2026-10-07 对另一小组提供的 `vectors.csv` 完成加密一致性与解密恢复验证，两项均为 9/9。原始文件按字节保存，导入文件仅调整列顺序。完整过程见[组间交叉测试报告](../cross-test-record.md)。

- [对方原始 CSV](cross-test/peer-vectors-original.csv)：表头为 `key,plaintext,ciphertext`，保留全部原始内容。
- [导入用 CSV](cross-test/peer-vectors-import.csv)：表头为 `plaintext,key,ciphertext`，位串与行顺序保持一致。
- [逐行验证结果](cross-test/cross-test-results.csv)：记录本组加密、本组解密及两项比较结果。
- [验证汇总 JSON](cross-test/cross-test-summary.json)：记录时间、环境、文件 SHA-256、统计结果和界面截图信息。

## 桌面录屏

- [暴力破解桌面录屏](video/bruteforce.mp4)：2026-10-03 录制，约 28 秒，1408 × 1032；展示一组已知对搜索，以及加入第二组后的再次搜索。
- 两次均检查全部 1024 个密钥，得到 `1010000010`、`1110000010` 两个候选；录像显示计算耗时依次为 9.609 ms、1.361 ms。
- [录像与实测记录](../demo-recording.md)包含输入数据、运行环境、结果和复现步骤。

## 实测数据

- [unittest 日志](results/unittest.txt) · [环境与实验汇总](results/summary.json)
- [本地交叉样例](results/local-vectors.csv)
- [256 种明文统计](results/collision-statistics.csv)
- [指定明文的全部密钥映射](results/collision-mapping-10011010.csv)
- [录屏第二次搜索的候选密钥与原始计时](results/key_candidates.csv)：`completed=True`、`checked=1024`、`elapsed_seconds=0.001361000`，对应录像中的 1.361 ms。

运行 `python tools/verify_project.py` 更新数据与报告；运行 `python tools/capture_screenshots.py` 更新截图。动图使用可选 Pillow 依赖和 `--animation`，步骤见 [开发手册](../developer-guide.md)。每次运行耗时可能不同。

`verify_project.py` 会重写五关测试报告，其模板仅包含基础自动实验内容。组间测试与桌面录屏分别独立保存于[组间交叉测试报告](../cross-test-record.md)和[录像与实测记录](../demo-recording.md)，重新生成总报告后，第2关与第4关实测内容由上述记录合并恢复。
