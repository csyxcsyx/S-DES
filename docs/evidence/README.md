# 实验材料索引

本目录保存五关实验的测试日志、CSV 数据、统计结果、程序截图和演示录像。实验方法与结论见[五关测试报告](../test-report.md)。

## 五关实验材料

| 实验 | 界面与记录 | 数据文件 |
|---|---|---|
| 第1关：基本测试 | [加解密窗口](screenshots/01-binary.png)、[计算步骤](screenshots/07-trace.png) | [测试日志](results/unittest.txt)、[实验汇总](results/summary.json) |
| 第2关：交叉测试 | [结果表上半部分](screenshots/12-peer-cross-top.png)、[结果表下半部分](screenshots/12-peer-cross-bottom.png)、[实验记录](../cross-test-record.md) | [原始向量](cross-test/peer-vectors-original.csv)、[导入向量](cross-test/peer-vectors-import.csv)、[逐行结果](cross-test/cross-test-results.csv)、[验证汇总](cross-test/cross-test-summary.json) |
| 第3关：ASCII 扩展 | [文本加解密窗口](screenshots/02-ascii.png) | [文本与密文记录](results/summary.json) |
| 第4关：暴力破解 | [搜索窗口](screenshots/03-attack.png)、[实验录像](video/bruteforce.mp4)、[实验记录](../demo-recording.md) | [候选密钥与计时](results/key_candidates.csv)、[多组已知对结果](results/summary.json) |
| 第5关：封闭测试 | [统计窗口](screenshots/04-collisions.png)、[密钥分组](screenshots/09-key-groups.png) | [256 种明文统计](results/collision-statistics.csv)、[指定明文密钥映射](results/collision-mapping-10011010.csv) |

## 界面验证材料

五个页面的完整截图为 `screenshots/01`～`05`，尺寸为 1120 × 900；同名 `-compact` 文件为 880 × 600。交叉测试结果表截图为 974 × 264，演示录像为 1408 × 1032。

- [自检与 CSV 交换页面](screenshots/05-testing.png)、[本地交换样例](results/local-vectors.csv)
- [界面加载动效](screenshots/06-loading.gif)、[下拉选项](screenshots/08-dropdown.png)、[计算前的结果区域](screenshots/10-binary-empty.png)
- 150% 缩放：[破解页面](screenshots/11-attack-150.png)、[密钥分组](screenshots/11-groups-150.png)、[交叉表](screenshots/11-cross-150.png)
- [应用图标 PNG](../../sdes_app/ui/assets/app.png)、[SVG](../../sdes_app/ui/assets/app.svg)、[Windows ICO](../../sdes_app/ui/assets/app.ico)

## 项目文档

- [五关测试报告](../test-report.md)
- [用户指南](../user-guide.md)
- [开发手册](../developer-guide.md)
- [界面设计说明](../ui-design.md)
