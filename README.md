# S-DES 实验室

信息安全导论课程作业的 Python 桌面实现：二进制加解密、ASCII 文本、已知明密文暴力搜索、密钥碰撞分析，以及 CSV 交叉测试。

**算法参数采用作业截图；两个轮密钥分别累计循环左移 1 位、2 位。** 这与部分常见 S-DES 实现的累计 1、3 位不同，跨组测试前请核对这一规则。

## 启动

已安装本项目依赖时，在项目根目录运行：

```powershell
python -m sdes_app
```

新环境建议使用 Python 3.13 创建虚拟环境，无需执行激活脚本：

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m sdes_app
```

已验证环境：Windows 11、Python 3.13.5、PySide6 / Qt 6.11.1。其他操作系统未进行实际验证。

## 示例

| 输入 | 值 |
|---|---|
| 明文 | `10011010` |
| 密钥 | `1010000010` |
| K1 / K2 | `10100100` / `10010010` |
| 密文 | `11101111` |

默认示例存在两个匹配密钥 `1010000010`、`1110000010`。本移位规则使原始密钥第 2 位不进入任何轮密钥，因此不能用更多明密文对区分这两个等效密钥。程序返回全部候选，不将其中一个误报为唯一密钥。

![暴力破解窗口](docs/screenshots/03-attack.png)

## 验证与复现

```powershell
python -m unittest discover -v
python tools/verify_project.py
python tools/capture_screenshots.py
```

第一条运行自动测试；第二条更新真实测试日志、实验 JSON / CSV 和五关报告；第三条通过实际 Qt 控件操作生成两个尺寸的界面截图。截图使用离屏 Qt 渲染，不等同于桌面录像；应用正常启动时使用 Windows 窗口平台。

测试覆盖 262144 组加解密往返、8192 组独立字符串参考实现对照、手算中间值、控制字节、格式解析、全部候选、碰撞统计、后台取消与异常、Qt 交互及 CSV 交换。

## 文档与结构

- [用户指南](docs/user-guide.md)
- [开发手册与接口](docs/developer-guide.md)
- [五关测试报告](docs/test-report.md)
- [暴力破解录像步骤](docs/demo-recording.md)
- [正式交叉测试记录模板](docs/cross-test-record.md)
- [原始实验汇总](docs/test-results/summary.json)

`sdes_app/core` 是不依赖 Qt 的算法模块，`services` 是文本与实验服务，`ui/pages` 是五个独立页面，`ui/widgets` 是共享组件。主窗口仅组织导航与生命周期；各页面保持小文件结构。

正式组间交叉测试仍待另一小组的数据与记录；本地 CSV 回读不代表该关已经通过。录像步骤已提供，真实录像需要录制后补入材料。项目未包含 TCP 通信或可执行文件打包。
