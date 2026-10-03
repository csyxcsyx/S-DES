# S-DES 实验室

信息安全导论课程作业的 Python 窗口程序，包含二进制加解密、ASCII 文本、暴力破解、密钥碰撞分析和 CSV 交叉验证。

## 启动

使用 **Python 3.13+**，在项目根目录执行：

```powershell
python -m pip install -r requirements.txt
python -m sdes_app
```

依赖为 PySide6 6.11.1；已在 Windows 11、Python 3.13.5 验证。[虚拟环境与操作指南](docs/user-guide.md)。

## 预览

![暴力破解页面](docs/evidence/screenshots/03-attack.png)

算法采用作业参数，轮密钥累计左移 **1、2 位**，存在等效密钥；破解返回全部候选。默认示例：`10011010` + 密钥 `1010000010` → `11101111`。

## 验证与文档

- 自动测试：`python -m unittest discover -v`
- [开发结构与接口](docs/developer-guide.md) · [五关测试报告](docs/test-report.md)
- [截图与实验数据](docs/evidence/README.md) · [交叉记录](docs/cross-test-record.md) · [录像步骤](docs/demo-recording.md)

正式组间交叉记录与桌面录像待补充。
