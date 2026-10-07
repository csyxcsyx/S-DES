# 开发手册

## 架构与数据流

项目分为算法核心、功能服务、Qt 页面与共享组件四层。核心和服务只使用标准库，导入它们无需 PySide6。界面将输入解析为整数或 bytes，调用核心或服务，再显示结果；不在页面内实现置换或轮函数。

主窗口通过 `QStackedWidget` 和独立 `QScrollArea` 组织五页。输入框、结果复制、过程表格、明密文对编辑器及后台任务控件均可复用。数据展示使用 `QAbstractTableModel`，长表格按可见行渲染。

`widgets/tables.py` 集中管理表格模型、绘制代理和尺寸计算：`DataTable(headers, visible_rows=6, weights=None, minimums=None)` 创建一次模型，`set_rows(rows)` 就地更新数据。共享 `TableLayout` 按最小列宽、换行后的实际行高计算尺寸，编辑表格也复用该逻辑。`TableTabs` 根据当前数据表调整高度，各页面共用表格布局与绘制规则。

命名采用 snake_case（函数、变量）和 PascalCase（类）。算法位置表以从左到右、从 1 开始编号；整数的最高位对应第 1 位。

## 核心接口

从 `sdes_app.core` 导入：

| 接口 | 返回值与约束 |
|---|---|
| `generate_subkeys(key: int)` | `(k1, k2)`，每个轮密钥范围 0～255；主密钥范围 0～1023 |
| `encrypt_block(block: int, key: int)` | 0～255 的密文整数；输入分组范围 0～255 |
| `decrypt_block(block: int, key: int)` | 0～255 的明文整数；逆序使用子密钥 |
| `encrypt_bytes(data: bytes, key: int)` | 等长 bytes，逐字节加密，不添加填充 |
| `decrypt_bytes(data: bytes, key: int)` | 等长 bytes，保留所有字节值 |
| `trace_block(block, key, decrypt=False)` | `BlockTrace(output, subkeys, steps)`，每个 `TraceStep` 含 `name`、`bits`、`detail` |

主密钥、分组只接受整数，不接受 bool、浮点数或字符串。越界或错误类型抛出 `ValueError`。界面解析使用 `parse_bits(text, width, name)`；首尾空白去除后严格检查位数和字符。

```python
from sdes_app.core import encrypt_block, decrypt_block

key = int("1010000010", 2)
cipher = encrypt_block(int("10011010", 2), key)
assert f"{cipher:08b}" == "11101111"
assert decrypt_block(cipher, key) == int("10011010", 2)
```

子密钥先执行 P10，再将左右两个 5 位分组分别从原状态循环左移 1、2 位并执行 P8。第二轮不是累计 3 位。S-Box 行由外侧两位决定，列由内侧两位决定。

原始密钥第 2 位经过 P10 到位置 3；移位 1 位、2 位后分别到左半位置 2、1，两者均被 P8 排除。因此 `key ^ 0b0100000000` 是其等效密钥，全部 1024 个主密钥只有 512 对不同子密钥。破解服务返回全部满足已知对约束的候选，包括等效密钥。

## 服务接口与文件交换

`services.text_cipher` 提供 `ascii_bytes`、`ascii_text`、`encrypt_text`、`decrypt_text`、`format_ciphertext` 与 `parse_ciphertext`。格式名为“二进制”“十六进制”“Base64”。非 ASCII 内容、无效位数、十六进制或非规范 Base64 均抛出 `ValueError`。

`services.experiments.search_keys(pairs, progress=None, cancel=None)` 接收 `(plaintext, ciphertext)` 整数对列表；返回 `SearchResult`：

- `candidates`：已检查范围内全部匹配密钥，升序 tuple。
- `checked`：实际检查密钥数量，完整运行是 1024。
- `elapsed`：`perf_counter` 测得的计算秒数。
- `completed`：是否完整遍历；取消后不得将部分候选解释为最终集合。

`analyze_collisions(plaintext, all_plaintexts=False, progress=None, cancel=None)` 返回 `CollisionResult`。`summaries` 只包含完整遍历 1024 个密钥的明文统计，按明文排序；`groups` 只保存指定明文完整完成后的 `密文 → 密钥tuple` 映射。`checked`、`total`、`elapsed`、`completed` 记录整体任务状态。全空间任务优先计算指定明文。

两种实验均接收 `progress(checked, total)` 回调和 `threading.Event` 取消标记，循环中检查该标记。回调在调用线程中执行，禁止直接操作 Qt 控件。

`services.exchange.verify_csv(path)` 返回 `CrossCheck` 列表，每行记录实际加密密文、实际解密明文及错误。`passed` 只有在格式正确且双向一致时为真。结构错误的表头或无数据抛出 `ValueError`；逐行格式错误保留在结果中。

`export_vectors(path, pairs)` 接收 `(明文, 主密钥)` 列表，生成固定表头 `plaintext,key,ciphertext`。CSV 使用 UTF-8 BOM，写入时保留位宽。通用 `write_csv` 用于实验导出；调用方处理 `OSError`。

`services.checks.run_checks(exhaustive=False, progress=None, cancel=None)` 返回手算用例验证报告，可选全空间往返。它是界面自检入口，完整单元及 UI 测试仍使用 unittest。

## Qt 后台生命周期

`Worker(QThread)` 在 `run()` 中执行服务，通过 Qt 信号传递进度、结果和异常文本。`TaskPanel` 在主线程中接收信号更新控件。

启动任务时禁用开始按钮并锁定相关输入；取消只设置 Event，不强制终止线程。收到 `finished` 后释放线程：成功结果不足 600 ms 时，通过主线程单次 QTimer 等待剩余展示时间，再发布结果、恢复按钮并通知页面。`running` 包括计算和结果过渡两个阶段，`worker` 仅表示计算线程。服务的 `elapsed` 原样保存，界面没有向算法线程加入延时。取消、异常、关闭窗口和减少动画模式跳过剩余展示等待；已经算完的结果仍保持真实完成状态。

窗口关闭时请求所有任务取消，短间隔检查退出状态后再关闭，避免销毁运行中的 QThread。展示定时器会停止，结果只发布一次；完成或取消后可重新启动。

程序不修改全局异常处理。UI 测试临时捕获 Qt 槽函数的未处理异常，并将其作为测试失败，避免出现日志 traceback 但测试仍显示通过。

主题、字体和焦点样式集中定义。Windows 正常启动由 Qt 发现系统字体；Windows 离屏测试缺少字体目录时显式加载本机微软雅黑和 Consolas，不将字体文件复制到项目。

表格、下拉选项、加载指示器、数值摘要及可展开区域均由 `ui/widgets` 复用。`ui/focus.py` 区分鼠标与键盘焦点；`ui/motion.py` 定义动效时间和系统偏好。主窗口切换页面时直接重绘，展开和任务反馈使用动效。图标源及导出资源位于 `ui/assets`，由 `ui/assets.py` 加载，并纳入 setuptools 包资源配置。详细约定见[界面设计说明](ui-design.md)。

## 验证与实验工具

执行 `python -m unittest discover -v`。核心测试包括独立字符串参考实现、手算中间状态、全密钥全分组往返、等效密钥和字节完整性。服务测试包括无效格式、多对筛选、矛盾数据、碰撞分组、取消及 CSV。Qt 测试使用真实控件事件、信号和主线程事件循环，离屏运行，包含运行中关闭窗口。

`tools/verify_project.py` 组织单元测试与自动实验；`tools/capture_screenshots.py` 通过实际 Qt 控件生成界面截图。实验日志、统计数据、交换数据、截图和录像统一存放于 `docs/evidence`，文件说明见[实验材料索引](evidence/README.md)。

```powershell
python -m unittest discover -v
python tools/capture_screenshots.py
```

需要额外生成加载动图时，安装可选取证依赖并增加参数：

```powershell
python -m pip install -e ".[evidence]"
python tools/capture_screenshots.py --animation
```

Pillow 12.2.0 用于动图与图标导出，应用运行依赖 PySide6。动图捕获实际 Qt 控件帧，帧间隔来自采样时间。文件索引见[实验材料索引](evidence/README.md)。

`python tools/export_icon.py` 更新图标 PNG / ICO，复用可选 Pillow 依赖。缩放回归由 `tests/gui_probe.py` 在独立进程中执行；生成 150% 截图时可使用：

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
$env:QT_SCALE_FACTOR = "1.5"
python tests/gui_probe.py --output docs/evidence/screenshots
Remove-Item Env:QT_SCALE_FACTOR
Remove-Item Env:QT_QPA_PLATFORM
```

新增界面功能优先复用共享组件。当前五个页面均远小于 300 行；新增业务逻辑放入服务，避免扩大主窗口或单一页面。
