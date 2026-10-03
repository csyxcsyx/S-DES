"""由真实实验 JSON 生成 Markdown 报告，避免手工抄写过时数据。"""
from pathlib import Path


def write_report(root: Path, summary: dict) -> None:
    tests = summary["tests"]
    environment = summary["environment"]
    statistics = summary["collisions"]
    selected = statistics["selected_summary"]
    search_rows = "\n".join(
        f"| {item['pair_count']} | {len(item['candidates'])} | {'、'.join(item['candidates'])} | {item['elapsed_seconds']:.9f} |"
        for item in summary["searches"])
    body = f"""# 五关测试报告

本报告由 `tools/verify_project.py` 根据实际执行结果生成。记录时间：{summary['generated_at']}（UTC+8）。截图来自实际 Qt 离屏渲染，另一个进程中的耗时可能不同。

## 环境与总体验证

- 系统：{environment['platform']}。
- Python：{environment['python']}；PySide6 / Qt：{environment['pyside6']}。
- 处理器信息：{environment['processor']}。
- 自动测试：{tests['run']} 项，失败 {tests['failures']}，错误 {tests['errors']}，本次执行 {tests['elapsed_seconds']:.6f} 秒。
- 核心全空间：{tests['round_trip_combinations']} 组加解密往返全部通过，每个密钥下 256 个密文均不同。
- 独立字符串实现：{tests['independent_reference_combinations']} 组对照全部通过，覆盖全部主密钥及 8 种代表性明文；它不引用产品的位运算或参数常量。
- Qt 验证：按钮、Enter、导航、复制、格式转换、后台任务完成 / 异常 / 取消、运行中关闭、CSV 导入导出和中文字体。两个尺寸的截图为 1120 × 900、880 × 600。

原始证据：[测试日志](evidence/results/unittest.txt)、[完整汇总 JSON](evidence/results/summary.json)。界面检查为程序化 Qt 交互和截图检查，未声称在其他操作系统或辅助技术中完成验证。

界面统一无行号表格、浅色控件及下拉选项；表格使用横向分隔线、内容最小列宽和完整行高度，长密钥自动换行。碰撞页使用“明文统计”“密钥分组”页签。鼠标点击不显示额外焦点框，Tab 导航保留轻量焦点提示。结果区空状态使用常规小字号。

整页透明度效果已移除，页面切换直接重绘；加载反馈最短 600 ms，展开与进度动画 180 ms，计算耗时不包含展示时长。系统关闭动画或设置 `SDES_REDUCED_MOTION=1` 时简化动效并跳过最短展示等待。测试覆盖快速切换、事件循环响应、取消、重复启动和键盘操作；独立 Qt 进程验证 150% / 200% 缩放的完整行、列宽、长文本、末行滚动和表头重绘。

150% 离屏渲染：[破解页](evidence/screenshots/11-attack-150.png)、[密钥分组](evidence/screenshots/11-groups-150.png)、[交叉表](evidence/screenshots/11-cross-150.png)。[应用图标](../sdes_app/ui/assets/app.png) 为无文字的盾形与分组方块，已设置到应用及主窗口；[ICO](../sdes_app/ui/assets/app.ico) 包含多个尺寸。

## 第1关：基本测试

采用作业截图参数和确认后的累计左移 1、2 位规则。独立手算用例：

| 项目 | 位串 |
|---|---|
| 明文 / 主密钥 | `10011010` / `1010000010` |
| P10 | `1000001100` |
| 累计移位 1 / K1 | `0000111000` / `10100100` |
| 累计移位 2 / K2 | `0001010001` / `10010010` |
| IP | `00011011` |
| 第一轮 EP / XOR | `11010111` / `01110011` |
| 第一轮 S-Box / P4 / fK | `0011` / `0110` / `01111011` |
| SW | `10110111` |
| 第二轮 EP / XOR | `10111110` / `00101100` |
| 第二轮 S-Box / P4 / fK | `0001` / `0100` / `11110111` |
| 最终密文 | `11101111` |
| 解密恢复 | `10011010` |

自动测试逐项断言以上中间状态，并检查全零、全一、前导零及无效输入。通过。

![基本测试窗口](evidence/screenshots/01-binary.png)

## 第2关：交叉测试

**正式组间交叉测试待完成。** 未取得另一小组的程序或真实数据，不将本地文件回读视为组间测试。

已经实现固定列 CSV 的导入、导出、加密对照、解密对照和逐行错误说明；本地 8 条样例往返验证通过。可用 [本地样例 CSV](evidence/results/local-vectors.csv) 与其他小组交换，实际结果填写 [交叉记录模板](cross-test-record.md)。

![自检与交叉数据页面](evidence/screenshots/05-testing.png)

## 第3关：ASCII 扩展

| 项目 | 实测内容 |
|---|---|
| 明文 | `{summary['ascii']['plaintext']}` |
| 密钥 | `1010000010` |
| 十六进制密文 | `{summary['ascii']['ciphertext_hex']}` |
| Base64 密文 | `{summary['ascii']['ciphertext_base64']}` |
| 恢复结果 | `This is a test` |

测试包括空文本、空格、制表符、换行、NUL、DEL、全部 128 种 ASCII 字符及全部 256 字节在三种密文格式中的无损转换。非 ASCII 输入和不合法格式得到明确错误，不采用忽略错误字节的解码方式。通过。

![ASCII 窗口](evidence/screenshots/02-ascii.png)

## 第4关：暴力破解

使用密钥 `1010000010` 生成已知对：依次追加明文 `10011010`、`01010101`、`00000000`、`11111111`；对应密文为 `11101111`、`00000101`、`01101010`、`10001110`。每次均完整枚举 1024 个密钥。

| 明密文对数量 | 候选数 | 全部候选密钥 | 实际计算秒数 |
|---|---|---|---|
{search_rows}

{summary['timing_note']} QThread 的工作是保持窗口响应，本项目没有声称线程提高 CPU 并行速度。多对筛选测试验证候选为单对集合的交集；矛盾数据 `(0,0)`、`(0,1)` 无候选。取消后明确标为未完成，异常后可以重试。功能和本地自动测试通过。

该规则存在等效密钥：原始第 2 位经 P10 到位置 3，累计移位 1、2 位后分别到位置 2、1，均被 P8 排除。因此 `K` 和 `K xor 0100000000` 生成完全相同的两个轮密钥。本次穷举确认只有 {summary['key_equivalence']['unique_subkey_pairs']} 对不同子密钥；样例中的两个候选在全部 256 种明文上完全等效，更多已知对也无法区分。

![暴力破解窗口](evidence/screenshots/03-attack.png)

**真实桌面录像待录制。** 已提供 [录像操作步骤](demo-recording.md)，没有用截图或人为延时冒充演示录像。

[加载动效预览](evidence/screenshots/06-loading.gif) 由真实 Qt 控件帧生成，展示计算和结果过渡；它用于核对界面动效，不作为桌面录屏记录。

## 第5关：封闭测试 / 密钥碰撞

按题面研究固定明文下不同密钥能否产生相同密文。实际执行 {statistics['checked']} 次加密，完整统计 {statistics['plaintext_count']} 种明文，本次耗时 {statistics['elapsed_seconds']:.9f} 秒。

| 指定明文 `10011010` 的指标 | 实测值 |
|---|---|
| 已检查密钥 | 1024 |
| 不同密文数 | {selected['distinct_ciphertexts']} |
| 含多个密钥的碰撞组数 | {selected['collision_groups']} |
| 最大候选密钥数 | {selected['max_candidates']} |
| 密文 `11101111` 的候选 | `1010000010`、`1110000010` |

全部明文的不同密文数范围为 {statistics['min_distinct_ciphertexts']}～{statistics['max_distinct_ciphertexts']}，最大候选数范围为 {statistics['min_max_candidates']}～{statistics['max_max_candidates']}。每个指定明文的分组总计覆盖全部 1024 个密钥，密钥不重复；样例密文分组与暴力破解候选完全一致。

固定明文时，1024 个密钥映射到最多 256 种密文，由鸽巢原理必有碰撞。本次结果并不意味着每个明密文对都具有相同候选数量。通过。

原始数据：[256 明文统计](evidence/results/collision-statistics.csv)、[指定明文的 1024 条映射](evidence/results/collision-mapping-10011010.csv)。

![碰撞分析窗口](evidence/screenshots/04-collisions.png)

[密钥分组页签](evidence/screenshots/09-key-groups.png) 单独展示指定明文的候选列表，表格滚动不影响表头。

## 提交前待补材料

填写真实小组成员与分工；完成另一小组参与的第2关记录；按步骤录制第4关视频或动图；检查仓库文件和启动说明，然后按课程要求提交链接。当前没有上传、push 或提交课程材料。
"""
    (root / "docs" / "test-report.md").write_text(body, encoding="utf-8")
