# Whisper 语音识别工具 — 封装使用说明

## 项目结构

```
F:\WhisperSubtitle\
├── whisper_env\              # 虚拟环境（必须保留）
│   └── Scripts\python.exe
├── WhisperProject.py          # 标准版转录脚本（必须保留）
├── WhisperProject2.py         # 防幻觉版转录脚本（必须保留）
├── WhisperGUI.py              # 旧版：基础 tkinter GUI（无需额外依赖）
├── 启动WhisperGUI.bat        # 旧版：带黑窗启动器
├── 启动WhisperGUI.vbs        # 旧版：无黑窗启动器
│
├── WhisperModernGUI.py        # 新版：现代质感 GUI（推荐⭐）
├── 启动精美版.bat            # 新版：调试启动器（自动安装依赖）
├── 启动精美版.vbs            # 新版：无黑窗启动器（自动安装依赖）⭐推荐
│
└── 打包说明.md                # 使用文档
```

---

## 快速使用（推荐方案）

### 第一步：双击启动精美版

在文件资源管理器中 **双击 `启动精美版.vbs`**。

- 首次启动会自动安装 `ttkbootstrap`（约 1-2 秒）
- 之后无需重复安装
- 无需打开命令提示符，无需手动激活虚拟环境

### 界面风格

- **深色卡片主题**：暗蓝灰背景 + 蓝色强调色，简约大气
- **左侧操作面板**：大卡片式文件选择区、版本选择、控制按钮
- **右侧日志面板**：类终端深色风格，语法高亮（错误红色、成功绿色、命令蓝色）
- **状态实时反馈**：顶部标题栏、底部状态栏、动态颜色变化

### 使用步骤

1. **选择文件** → 点击大卡片区域，或点击 📄 文件 / 📁 文件夹 按钮
2. **版本选择** → 标准版或防幻觉版（默认防幻觉版，推荐）
3. **输出目录** → 可选，留空则自动创建 `Text` / `Second` 子文件夹
4. **点击"开始转录"** → 实时日志在右侧滚动显示
5. **等待完成** → 处理结束后直接打开输出文件夹

### 新旧界面对比

| 特性 | 旧版 WhisperGUI | 新版 WhisperModernGUI |
|------|-----------------|----------------------|
| 界面风格 | 原生 Windows 灰白 | 深色卡片、现代扁平 |
| 日志颜色 | 单色 | 语法高亮（红/绿/蓝/橙） |
| 状态反馈 | 底部单行文字 | 动态变色 + 多位置提示 |
| 依赖 | 零额外依赖 | 需 ttkbootstrap（自动安装） |
| 启动速度 | 快 | 快（首次多 1-2 秒安装） |
| 推荐度 | ⭐⭐ | ⭐⭐⭐⭐⭐ |

---

## 进阶方案：打包为独立 .exe（可选）

> ⚠️ 由于项目依赖 PyTorch + CUDA，打包后的 `.exe` 体积会很大（约 2~5 GB），且 CUDA 动态库可能无法正确捆绑。因此 **VBS 启动器是日常使用的首选**。

### 打包步骤（在已激活虚拟环境中执行）

```bash
cd F:\WhisperSubtitle
whisper_env\Scripts\activate
pip install pyinstaller
pyinstaller --onefile --noconsole --name "Whisper语音识别工具" ^
  --add-data "WhisperProject.py;." ^
  --add-data "WhisperProject2.py;." ^
  --add-data "whisper_env;whisper_env" ^
  WhisperModernGUI.py
```

---

## 技术细节

- `WhisperModernGUI.py` 使用 `ttkbootstrap` 构建，Bootstrap 风格的现代主题
- `WhisperGUI.py` 使用纯 `tkinter`，无需任何额外依赖，作为保底方案
- 两个转录脚本（`WhisperProject.py` / `WhisperProject2.py`）**完全保留**，未做任何修改
- `启动精美版.vbs` 自动检测 `ttkbootstrap`，未安装则静默自动安装

---

## 故障排查

| 问题 | 解决方案 |
|------|----------|
| 精美版启动报错 "ttkbootstrap" | 手动执行：`whisper_env\Scripts\pip install ttkbootstrap` |
| 双击 .vbs 无反应 | 尝试双击 `.bat` 版本，查看错误信息 |
| 提示"虚拟环境未找到" | 确认 `whisper_env` 文件夹存在 |
| 转录时提示找不到脚本 | 确认 `WhisperProject.py` 和 `WhisperProject2.py` 存在 |
| 日志显示 CUDA 不可用 | 检查显卡驱动，或等待 CPU 模式（极慢） |
| 首次转录卡住 | 自动下载模型中，需保持网络畅通，耐心等待 |
| 想回到旧版界面 | 双击 `启动WhisperGUI.vbs` 即可 |

---

## 文件路径对照

| 文件 | 路径 | 作用 |
|------|------|------|
| 虚拟环境 Python | `whisper_env\Scripts\python.exe` | 运行引擎 |
| 标准版脚本 | `WhisperProject.py` | 转录逻辑（输出到 Text） |
| 防幻觉版脚本 | `WhisperProject2.py` | 转录逻辑（输出到 Second） |
| 精美版 GUI | `WhisperModernGUI.py` | 现代界面（推荐） |
| 精美版启动器 | `启动精美版.vbs` | 无黑窗启动 + 自动安装依赖 |
| 基础版 GUI | `WhisperGUI.py` | 保底界面（无额外依赖） |
| 基础版启动器 | `启动WhisperGUI.vbs` | 无黑窗启动（旧版） |
