# Whisper GUI 版本历史

> 版本管理文件夹，根据对话迭代记录每个关键里程碑。

---

## v1.0 initial — 初始完整 GUI
**时间**：2025-06-14  
**核心变更**：
- 创建 PyQt5 高性能 GUI
- 原生 Windows 11 窗口（DWM 圆角、边框颜色）
- 三列布局：设置（左）| 队列（中）| 日志（右）
- `QSplitter` 可调整面板宽度
- 文件队列管理（添加/清空/删除）
- 实时性能监视图表（CPU、Memory、GPU、VRAM）
- 使用 `LXGW WenKai` 字体

**文件**：`versions/v1.0_initial/WhisperPyQtGUI.py`

---

## v1.1 zoom buttons — 缩放按钮
**时间**：2025-06-14  
**核心变更**：
- 在右下角添加 25% / 50% / 75% 缩放按钮
- 点击后按屏幕百分比调整窗口并居中
- 保持宽高比例锁定

**文件**：`versions/v1.1_zoom_buttons/WhisperPyQtGUI.py`

---

## v1.2 centered — 默认居中
**时间**：2025-06-14  
**核心变更**：
- 窗口启动默认 55%×65% 屏幕大小
- 居中显示
- 移除固定尺寸，使用比例计算

**文件**：`versions/v1.2_centered/WhisperPyQtGUI.py`

---

## v1.3 aligned — 对齐优化
**时间**：2025-06-14  
**核心变更**：
- 队列和日志核心框上边对齐
- "日志" 标题增加圆角深色框包裹，与 "队列" 样式一致
- 调整 `QSplitter` 布局使三列顶部水平对齐

**文件**：`versions/v1.3_aligned/WhisperPyQtGUI.py`

---

## v1.4 monitor — 监视页面
**时间**：2025-06-14  
**核心变更**：
- 中间面板改为 `QStackedWidget`（队列 / 监视双页）
- "队列" 下拉按钮切换页面
- 性能图表实时刷新（CPU、Memory、GPU、VRAM）
- 添加窗口标题 Logo + 文字

**文件**：`versions/v1.4_monitor/WhisperPyQtGUI.py`

---

## v1.5 cuda — CUDA 监控
**时间**：2025-06-14  
**核心变更**：
- 监视页面添加 CUDA 利用率检测（`nvidia-ml-py`）
- GPU 和 CUDA 分开显示（GPU = 利用率，CUDA = 核心使用率）
- 只在本地跑 AI 时 CUDA 才会有运行值

**文件**：`versions/v1.5_cuda/WhisperPyQtGUI.py`

---

## v1.6 resize fix — 窗口 Resize 修复尝试
**时间**：2025-06-15  
**核心变更**：
- 尝试多种 Windows API 锁定窗口宽高比例：
  - `nativeEvent`（WM_SIZING）— 失败
  - `SetWindowSubclass`（comctl32）— 失败
  - `SetWindowLong`（WNDPROC 替换）— 失败
  - `SetWindowsHookEx`（WH_CALLWNDPROC）— 失败
- 原因：PyQt5 5.15+ 的 `message` 是 `PyCapsule`，指针解析复杂；Qt 事件循环与 Windows 消息机制冲突
- 过程中 `resizeEvent` 修正导致队列 UI 闪影/跳动

**文件**：`versions/v1.6_resize_fix/WhisperPyQtGUI.py`

---

## v1.7 final — 最终稳定版
**时间**：2025-06-15  
**核心变更**：
- 使用 `QAbstractNativeEventFilter`（全局 Native 事件过滤器）拦截 `WM_SIZING`
- `PyCapsule_GetPointer` 正确解析底层 `MSG*` 指针
- 实时修正 `RECT` 并返回 `TRUE(1)`
- `resizeEvent` 作为备用后处理（防闪影）
- 窗口拖动 Resize 时队列 UI 不再跳动
- 比例锁定稳定

**文件**：`versions/v1.7_final/WhisperPyQtGUI.py`

---

## 使用说明

```bash
# 查看最新版本
ls versions/v1.7_final/WhisperPyQtGUI.py

# 回溯到任意版本
cp versions/v1.4_monitor/WhisperPyQtGUI.py src/gui/WhisperPyQtGUI.py
```

## 目录结构

```
versions/
├── v1.0_initial/
│   └── WhisperPyQtGUI.py
├── v1.1_zoom_buttons/
│   └── WhisperPyQtGUI.py
├── v1.2_centered/
│   └── WhisperPyQtGUI.py
├── v1.3_aligned/
│   └── WhisperPyQtGUI.py
├── v1.4_monitor/
│   └── WhisperPyQtGUI.py
├── v1.5_cuda/
│   └── WhisperPyQtGUI.py
├── v1.6_resize_fix/
│   └── WhisperPyQtGUI.py
└── v1.7_final/
    └── WhisperPyQtGUI.py
```
