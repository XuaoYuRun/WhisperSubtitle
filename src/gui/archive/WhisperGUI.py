#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Whisper 语音识别 GUI 封装器
点击运行 → 选择文件/文件夹 → 一键转录
"""

import subprocess
import threading
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
from pathlib import Path

# ============================================================
# 路径配置（相对当前文件目录）
# ============================================================
SCRIPT_DIR = Path(__file__).parent.resolve()
VENV_PYTHON = SCRIPT_DIR / "whisper_env" / "Scripts" / "python.exe"
SCRIPT_V1 = SCRIPT_DIR / "WhisperProject.py"   # 标准版
SCRIPT_V2 = SCRIPT_DIR / "WhisperProject2.py"  # 防幻觉版


def check_env():
    """检查运行环境是否完整"""
    errors = []
    if not VENV_PYTHON.exists():
        errors.append(f"虚拟环境 Python 未找到:\n{VENV_PYTHON}")
    if not SCRIPT_V1.exists():
        errors.append(f"标准版脚本未找到:\n{SCRIPT_V1}")
    if not SCRIPT_V2.exists():
        errors.append(f"防幻觉版脚本未找到:\n{SCRIPT_V2}")
    return errors


class WhisperGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Whisper 语音识别工具")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)

        # 主题色
        self.bg_color = "#f5f5f5"
        self.accent_color = "#4a90d9"
        self.root.configure(bg=self.bg_color)

        # 状态变量
        self.input_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.version_var = tk.StringVar(value="v2")  # 默认防幻觉版
        self.is_running = False
        self.process = None

        self._build_ui()
        self._check_startup()

    # ==================== UI 构建 ====================
    def _build_ui(self):
        style = ttk.Style()
        style.configure("TFrame", background=self.bg_color)
        style.configure("TLabel", background=self.bg_color, font=("Microsoft YaHei", 11))
        style.configure("TButton", font=("Microsoft YaHei", 10))
        style.configure("Accent.TButton", font=("Microsoft YaHei", 12, "bold"))

        # --- 标题 ---
        title_frame = tk.Frame(self.root, bg=self.bg_color)
        title_frame.pack(pady=(20, 10))
        tk.Label(
            title_frame, text="🎙️ Whisper 语音识别", font=("Microsoft YaHei", 20, "bold"),
            bg=self.bg_color, fg="#333"
        ).pack()
        tk.Label(
            title_frame, text="基于 Faster-Whisper Large-V3-Turbo | 适配 RTX 5070 Ti",
            font=("Microsoft YaHei", 10), bg=self.bg_color, fg="#666"
        ).pack()

        # --- 主内容区 ---
        main_frame = tk.Frame(self.root, bg=self.bg_color)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=10)

        # 输入路径
        input_frame = tk.LabelFrame(main_frame, text="📁 视频 / 音频文件", bg=self.bg_color, font=("Microsoft YaHei", 11))
        input_frame.pack(fill=tk.X, pady=8)
        tk.Entry(input_frame, textvariable=self.input_path, font=("Microsoft YaHei", 11), width=60).pack(side=tk.LEFT, padx=8, pady=8, fill=tk.X, expand=True)
        ttk.Button(input_frame, text="📄 文件", command=self._browse_input).pack(side=tk.RIGHT, padx=4, pady=8)
        ttk.Button(input_frame, text="📁 文件夹", command=self._browse_input_folder).pack(side=tk.RIGHT, padx=4, pady=8)

        # 输出路径（可选）
        output_frame = tk.LabelFrame(main_frame, text="📂 输出目录（留空 = 自动创建 Text/Second 子文件夹）", bg=self.bg_color, font=("Microsoft YaHei", 11))
        output_frame.pack(fill=tk.X, pady=8)
        tk.Entry(output_frame, textvariable=self.output_path, font=("Microsoft YaHei", 11), width=60).pack(side=tk.LEFT, padx=8, pady=8, fill=tk.X, expand=True)
        ttk.Button(output_frame, text="浏览…", command=self._browse_output).pack(side=tk.RIGHT, padx=8, pady=8)

        # 版本选择
        version_frame = tk.LabelFrame(main_frame, text="⚙️ 处理版本", bg=self.bg_color, font=("Microsoft YaHei", 11))
        version_frame.pack(fill=tk.X, pady=8)

        v1_radio = tk.Radiobutton(
            version_frame, text="标准版（WhisperProject）", variable=self.version_var, value="v1",
            bg=self.bg_color, font=("Microsoft YaHei", 11), cursor="hand2"
        )
        v1_radio.pack(side=tk.LEFT, padx=15, pady=10)
        tk.Label(version_frame, text="输出到 Text 文件夹", bg=self.bg_color, fg="#888", font=("Microsoft YaHei", 9)).pack(side=tk.LEFT, pady=10)

        v2_radio = tk.Radiobutton(
            version_frame, text="防幻觉版（WhisperProject2）", variable=self.version_var, value="v2",
            bg=self.bg_color, font=("Microsoft YaHei", 11), cursor="hand2"
        )
        v2_radio.pack(side=tk.LEFT, padx=15, pady=10)
        tk.Label(version_frame, text="输出到 Second 文件夹，自动清理重复幻觉", bg=self.bg_color, fg="#888", font=("Microsoft YaHei", 9)).pack(side=tk.LEFT, pady=10)

        # 操作按钮
        btn_frame = tk.Frame(main_frame, bg=self.bg_color)
        btn_frame.pack(fill=tk.X, pady=15)
        self.start_btn = tk.Button(
            btn_frame, text="▶ 开始转录", command=self._start,
            font=("Microsoft YaHei", 14, "bold"), bg=self.accent_color, fg="white",
            activebackground="#357abd", cursor="hand2", padx=40, pady=10, relief=tk.FLAT
        )
        self.start_btn.pack(side=tk.LEFT, padx=5)
        self.stop_btn = tk.Button(
            btn_frame, text="⏹ 停止", command=self._stop,
            font=("Microsoft YaHei", 12), bg="#e74c3c", fg="white",
            activebackground="#c0392b", cursor="hand2", padx=25, pady=10, relief=tk.FLAT, state=tk.DISABLED
        )
        self.stop_btn.pack(side=tk.LEFT, padx=15)

        # 日志区
        log_frame = tk.LabelFrame(main_frame, text="📋 实时日志", bg=self.bg_color, font=("Microsoft YaHei", 11))
        log_frame.pack(fill=tk.BOTH, expand=True, pady=8)
        self.log_text = scrolledtext.ScrolledText(
            log_frame, wrap=tk.WORD, font=("Consolas", 10),
            bg="#1e1e1e", fg="#d4d4d4", insertbackground="white",
            state=tk.DISABLED, padx=8, pady=8
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        self.log_text.tag_config("error", foreground="#ff6b6b")
        self.log_text.tag_config("success", foreground="#51cf66")
        self.log_text.tag_config("warn", foreground="#ffd43b")

        # 底部状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = tk.Label(self.root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W, font=("Microsoft YaHei", 9))
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    # ==================== 事件处理 ====================
    def _check_startup(self):
        errors = check_env()
        if errors:
            msg = "\n\n".join(errors)
            messagebox.showerror("环境检查失败", msg)
            self._log("❌ 环境检查失败:\n" + msg, "error")
        else:
            self._log("✅ 环境检查通过，可以开始转录")
            self._log(f"   Python: {VENV_PYTHON}")
            self._log(f"   标准版: {SCRIPT_V1}")
            self._log(f"   防幻觉版: {SCRIPT_V2}")

    def _browse_input(self):
        path = filedialog.askopenfilename(
            title="选择视频/音频文件",
            filetypes=[
                ("视频/音频文件", "*.mp4 *.mkv *.avi *.mov *.wmv *.flv *.webm *.m4v *.mpeg *.mpg *.mp3 *.wav *.m4a *.aac *.ogg"),
                ("所有文件", "*.*")
            ]
        )
        if path:
            self.input_path.set(path)

    def _browse_input_folder(self):
        path = filedialog.askdirectory(title="选择包含视频/音频的文件夹（递归扫描子文件夹）")
        if path:
            self.input_path.set(path)

    def _browse_output(self):
        path = filedialog.askdirectory(title="选择输出目录（可选）")
        if path:
            self.output_path.set(path)

    def _log(self, text, level="info"):
        """向日志区追加文本（线程安全）"""
        def _append():
            self.log_text.config(state=tk.NORMAL)
            tag = level if level in ("error", "success", "warn") else ""
            self.log_text.insert(tk.END, text + "\n", tag)
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)
        self.root.after(0, _append)

    def _start(self):
        input_p = self.input_path.get().strip()
        if not input_p:
            messagebox.showwarning("提示", "请先选择要处理的视频/音频文件")
            return
        if not Path(input_p).exists():
            messagebox.showerror("错误", f"路径不存在:\n{input_p}")
            return

        version = self.version_var.get()
        script = SCRIPT_V1 if version == "v1" else SCRIPT_V2

        output_p = self.output_path.get().strip()

        # 构建命令
        cmd = [str(VENV_PYTHON), str(script), input_p]
        if output_p:
            cmd.extend(["-o", output_p])

        self._log("=" * 60, "info")
        self._log(f"▶ 启动转录 | 版本: {version}")
        self._log(f"   命令: {' '.join(cmd)}")
        self._log("=" * 60, "info")

        self.is_running = True
        self.start_btn.config(state=tk.DISABLED, bg="#999")
        self.stop_btn.config(state=tk.NORMAL, bg="#e74c3c")
        self.status_var.set("正在转录中…")

        # 在后台线程运行子进程
        thread = threading.Thread(target=self._run_process, args=(cmd,), daemon=True)
        thread.start()

    def _run_process(self, cmd):
        """在后台线程中执行子进程"""
        try:
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                cwd=str(SCRIPT_DIR),
            )
            for line in iter(self.process.stdout.readline, ""):
                if not line:
                    break
                self._log(line.rstrip())
            self.process.stdout.close()
            return_code = self.process.wait()

            if return_code == 0:
                self._log("\n🎉 转录全部完成！", "success")
                self.status_var.set("转录完成")
            else:
                self._log(f"\n❌ 进程异常退出，返回码: {return_code}", "error")
                self.status_var.set(f"异常退出 (code {return_code})")

        except Exception as e:
            self._log(f"\n❌ 启动失败: {e}", "error")
            self.status_var.set("启动失败")
        finally:
            self.is_running = False
            self.process = None
            self.root.after(0, self._reset_ui)

    def _reset_ui(self):
        self.start_btn.config(state=tk.NORMAL, bg=self.accent_color)
        self.stop_btn.config(state=tk.DISABLED, bg="#999")
        if not self.is_running:
            self.status_var.set("就绪")

    def _stop(self):
        if self.process and self.process.poll() is None:
            self._log("\n⏹ 用户请求停止…", "warn")
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self._log("⚠️ 强制终止进程", "warn")
            self._log("已停止", "warn")
        self.is_running = False
        self._reset_ui()


def main():
    root = tk.Tk()
    app = WhisperGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
