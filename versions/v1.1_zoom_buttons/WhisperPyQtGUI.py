#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Whisper 语音识别 — 现代质感 GUI（ttkbootstrap）
优化版：队列批量刷新日志，解决转录卡顿
"""

import os
import queue
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

try:
    import ttkbootstrap as ttk
    from ttkbootstrap.constants import *
    from ttkbootstrap.scrolled import ScrolledText
except ImportError:
    import tkinter.messagebox as _msg
    _msg.showerror(
        "缺少依赖",
        "本界面需要 ttkbootstrap 库。\n\n"
        "请在命令提示符中执行：\n\n"
        "whisper_env\\Scripts\\pip install ttkbootstrap\n\n"
        "安装完成后重新打开本程序。"
    )
    raise SystemExit(1)

# ============================================================
# 路径配置
# ============================================================
SCRIPT_DIR = Path(__file__).parent.resolve()
VENV_PYTHON = SCRIPT_DIR / "whisper_env" / "Scripts" / "python.exe"
SCRIPT_V1 = SCRIPT_DIR / "WhisperProject.py"
SCRIPT_V2 = SCRIPT_DIR / "WhisperProject2.py"


def check_env():
    errors = []
    if not VENV_PYTHON.exists():
        errors.append(f"虚拟环境 Python 未找到:\n{VENV_PYTHON}")
    if not SCRIPT_V1.exists():
        errors.append(f"标准版脚本未找到:\n{SCRIPT_V1}")
    if not SCRIPT_V2.exists():
        errors.append(f"防幻觉版脚本未找到:\n{SCRIPT_V2}")
    return errors


class WhisperModernGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Whisper 语音识别")
        self.root.geometry("1200x850")
        self.root.minsize(1000, 700)

        # 状态变量
        self.input_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.version_var = tk.StringVar(value="v2")
        self.is_running = False
        self.process = None
        self.log_queue = queue.Queue()
        self._flush_timer = None

        self._build_ui()
        self._check_startup()

    # ==================== UI 构建 ====================
    def _build_ui(self):
        # 主容器
        main = ttk.Frame(self.root, padding=0)
        main.pack(fill=BOTH, expand=YES)

        # ========== 顶部标题栏 ==========
        header = ttk.Frame(main, bootstyle="dark", padding=(20, 14, 20, 14))
        header.pack(fill=X)

        ttk.Label(
            header, text="🎙️  Whisper 语音识别",
            font=("Microsoft YaHei", 20, "bold"),
            bootstyle="inverse-dark"
        ).pack(side=LEFT)

        ttk.Label(
            header, text="Faster-Whisper  Large-V3-Turbo  |  RTX 5070 Ti",
            font=("Microsoft YaHei", 10),
            bootstyle="inverse-dark"
        ).pack(side=LEFT, padx=(16, 0), pady=(6, 0))

        # ========== 左侧输入区 ==========
        left_frame = ttk.Frame(main, padding=18, bootstyle="secondary")
        left_frame.pack(side=LEFT, fill=BOTH, expand=YES)

        # --- 文件选择卡片 ---
        file_card = ttk.Labelframe(left_frame, text=" 选择文件 ", padding=15, bootstyle="info")
        file_card.pack(fill=X, pady=(0, 14))

        self.drag_frame = ttk.Frame(file_card, padding=30, bootstyle="dark")
        self.drag_frame.pack(fill=X)
        self.drag_frame.bind("<Button-1>", lambda e: self._browse_input())

        self.drag_icon = ttk.Label(
            self.drag_frame, text="📂",
            font=("Segoe UI Emoji", 44),
            bootstyle="inverse-dark"
        )
        self.drag_icon.pack()
        self.drag_icon.bind("<Button-1>", lambda e: self._browse_input())

        self.drag_label = ttk.Label(
            self.drag_frame,
            text="点击选择文件或文件夹",
            font=("Microsoft YaHei", 11),
            bootstyle="inverse-dark"
        )
        self.drag_label.pack(pady=(8, 4))
        self.drag_label.bind("<Button-1>", lambda e: self._browse_input())

        self.drag_sub = ttk.Label(
            self.drag_frame,
            text="支持 mp4 / mkv / avi / mov / mp3 / wav 等格式",
            font=("Microsoft YaHei", 9),
            bootstyle="inverse-dark"
        )
        self.drag_sub.pack()
        self.drag_sub.bind("<Button-1>", lambda e: self._browse_input())

        # 已选文件路径
        self.path_display = ttk.Entry(file_card, textvariable=self.input_path, font=("Consolas", 10))
        self.path_display.pack(fill=X, pady=(10, 0))

        # 快捷按钮
        btn_row = ttk.Frame(file_card)
        btn_row.pack(fill=X, pady=(8, 0))
        ttk.Button(btn_row, text="📄 选择文件", command=self._browse_input, bootstyle="primary-outline").pack(side=LEFT, padx=(0, 6))
        ttk.Button(btn_row, text="📁 选择文件夹", command=self._browse_input_folder, bootstyle="primary-outline").pack(side=LEFT)
        ttk.Button(btn_row, text="✕ 清空", command=self._clear_input, bootstyle="danger-outline").pack(side=RIGHT)

        # --- 输出设置卡片 ---
        out_card = ttk.Labelframe(left_frame, text=" 输出设置 ", padding=15, bootstyle="info")
        out_card.pack(fill=X, pady=(0, 14))

        ttk.Label(out_card, text="输出目录（留空 = 自动创建）", font=("Microsoft YaHei", 11)).pack(anchor=W)
        out_entry = ttk.Entry(out_card, textvariable=self.output_path, font=("Consolas", 10))
        out_entry.pack(fill=X, pady=(6, 8))
        ttk.Button(out_card, text="📂 浏览…", command=self._browse_output, bootstyle="secondary-outline").pack(side=RIGHT)

        # --- 版本选择卡片 ---
        ver_card = ttk.Labelframe(left_frame, text=" 处理版本 ", padding=15, bootstyle="info")
        ver_card.pack(fill=X, pady=(0, 14))

        ver_frame = ttk.Frame(ver_card)
        ver_frame.pack(fill=X)

        self.v1_radio = ttk.Radiobutton(
            ver_frame, text="标准版", variable=self.version_var, value="v1",
            bootstyle="info-toolbutton", command=self._on_version_change
        )
        self.v1_radio.pack(side=LEFT, fill=X, expand=YES, padx=(0, 8))

        self.v2_radio = ttk.Radiobutton(
            ver_frame, text="防幻觉版（推荐）", variable=self.version_var, value="v2",
            bootstyle="success-toolbutton", command=self._on_version_change
        )
        self.v2_radio.pack(side=LEFT, fill=X, expand=YES)

        self.ver_desc = ttk.Label(
            left_frame,
            text="防幻觉版：自动清理视频结尾的重复幻觉，输出到 Second 文件夹",
            font=("Microsoft YaHei", 9),
            bootstyle="secondary"
        )
        self.ver_desc.pack(anchor=W, pady=(0, 8))

        # --- 控制按钮区 ---
        ctrl_frame = ttk.Frame(left_frame, padding=8)
        ctrl_frame.pack(fill=X, pady=(8, 0))

        self.start_btn = ttk.Button(
            ctrl_frame, text="▶  开始转录", command=self._start,
            bootstyle="success", width=16
        )
        self.start_btn.pack(side=LEFT, padx=(0, 12))

        self.stop_btn = ttk.Button(
            ctrl_frame, text="⏹  停止", command=self._stop,
            bootstyle="danger", width=10, state=DISABLED
        )
        self.stop_btn.pack(side=LEFT)

        # 状态标签
        self.status_lbl = ttk.Label(
            left_frame, text="就绪", font=("Microsoft YaHei", 10, "bold"),
            bootstyle="secondary"
        )
        self.status_lbl.pack(anchor=W, pady=(12, 0))

        # ========== 右侧日志区 ==========
        right_frame = ttk.Frame(main, padding=18, bootstyle="secondary")
        right_frame.pack(side=RIGHT, fill=BOTH, expand=YES)

        log_header = ttk.Frame(right_frame)
        log_header.pack(fill=X, pady=(0, 8))
        ttk.Label(log_header, text="📋 实时日志", font=("Microsoft YaHei", 14, "bold")).pack(side=LEFT)
        ttk.Button(log_header, text="🗑 清空", command=self._clear_log, bootstyle="secondary-outline", width=8).pack(side=RIGHT)

        # 日志文本框
        self.log_text = ScrolledText(
            right_frame, wrap=tk.WORD, font=("Cascadia Code", 10),
            padding=10, height=35, autohide=True,
            bootstyle="dark"
        )
        self.log_text.pack(fill=BOTH, expand=YES)
        self.log_text.text.config(
            bg="#0d1117", fg="#c9d1d9",
            insertbackground="white",
            selectbackground="#238636",
            state=DISABLED
        )
        # 预定义颜色标签
        self.log_text.text.tag_config("error", foreground="#ff7b72")
        self.log_text.text.tag_config("success", foreground="#7ee787")
        self.log_text.text.tag_config("warn", foreground="#ffa657")
        self.log_text.text.tag_config("cmd", foreground="#79c0ff")

        # 底部信息栏
        footer = ttk.Frame(main, padding=(16, 8), bootstyle="dark")
        footer.pack(side=BOTTOM, fill=X)
        ttk.Label(
            footer,
            text="  Whisper 语音识别工具  |  基于 OpenAI Whisper  |  适配 CUDA 12.8  |  © 2025",
            font=("Microsoft YaHei", 9), bootstyle="inverse-dark"
        ).pack(side=LEFT)

    # ==================== 事件处理 ====================
    def _on_version_change(self):
        if self.version_var.get() == "v1":
            self.ver_desc.config(text="标准版：输出到 Text 文件夹")
        else:
            self.ver_desc.config(text="防幻觉版：自动清理视频结尾的重复幻觉，输出到 Second 文件夹")

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
            self._update_drag_display(path)

    def _browse_input_folder(self):
        path = filedialog.askdirectory(title="选择包含视频/音频的文件夹（递归扫描）")
        if path:
            self.input_path.set(path)
            self._update_drag_display(path)

    def _update_drag_display(self, path):
        self.drag_label.config(text=Path(path).name)
        self.drag_sub.config(text=str(Path(path)))

    def _clear_input(self):
        self.input_path.set("")
        self.drag_label.config(text="点击选择文件或文件夹")
        self.drag_sub.config(text="支持 mp4 / mkv / avi / mov / mp3 / wav 等格式")

    def _browse_output(self):
        path = filedialog.askdirectory(title="选择输出目录")
        if path:
            self.output_path.set(path)

    def _clear_log(self):
        self.log_text.text.config(state=NORMAL)
        self.log_text.text.delete("1.0", END)
        self.log_text.text.config(state=DISABLED)

    def _check_startup(self):
        errors = check_env()
        if errors:
            self._log("❌ 环境检查失败", "error")
            for e in errors:
                self._log(e, "error")
            messagebox.showerror("环境检查失败", "\n\n".join(errors))
        else:
            self._log("✅ 环境检查通过，可以开始转录")
            self._log(f"   Python: {VENV_PYTHON}")
            self._log(f"   标准版: {SCRIPT_V1}")
            self._log(f"   防幻觉版: {SCRIPT_V2}")

    # ==================== 日志系统（队列批量刷新）====================
    def _log(self, text, level="info"):
        """将日志放入队列，由定时器批量刷新到 UI"""
        self.log_queue.put((text, level))
        # 启动/延续定时器
        if self._flush_timer is None:
            self._flush_timer = self.root.after(100, self._flush_log)

    def _flush_log(self):
        """每 100ms 批量刷新队列到 UI"""
        # 一次性取出所有队列内容
        lines = []
        while True:
            try:
                lines.append(self.log_queue.get_nowait())
            except queue.Empty:
                break

        if lines:
            self.log_text.text.config(state=NORMAL)
            for text, level in lines:
                tag = level if level in ("error", "success", "warn", "cmd") else ""
                self.log_text.text.insert(END, text + "\n", tag)
            self.log_text.text.see(END)
            self.log_text.text.config(state=DISABLED)

        # 如果还有任务在运行或队列非空，继续定时器
        if self.is_running or not self.log_queue.empty():
            self._flush_timer = self.root.after(100, self._flush_log)
        else:
            self._flush_timer = None

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

        cmd = [str(VENV_PYTHON), str(script), input_p]
        if output_p:
            cmd.extend(["-o", output_p])

        self._log("=" * 60, "cmd")
        self._log(f"▶ 启动转录 | 版本: {version}", "cmd")
        self._log(f"   {' '.join(cmd)}", "cmd")
        self._log("=" * 60, "cmd")

        self.is_running = True
        self.start_btn.config(state=DISABLED)
        self.stop_btn.config(state=NORMAL)
        self.status_lbl.config(text="正在转录中…", bootstyle="warning")

        # 确保日志刷新定时器已启动
        if self._flush_timer is None:
            self._flush_timer = self.root.after(100, self._flush_log)

        thread = threading.Thread(target=self._run_process, args=(cmd,), daemon=True)
        thread.start()

    def _run_process(self, cmd):
        """在后台线程中执行子进程，将输出放入队列"""
        try:
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            env["PYTHONUNBUFFERED"] = "1"
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                cwd=str(SCRIPT_DIR),
                env=env,
            )
            for line in iter(self.process.stdout.readline, ""):
                if not line:
                    break
                self._log(line.rstrip())
            self.process.stdout.close()
            return_code = self.process.wait()

            if return_code == 0:
                self._log("\n🎉 转录全部完成！", "success")
                self.status_lbl.config(text="转录完成", bootstyle="success")
            else:
                self._log(f"\n❌ 进程异常退出，返回码: {return_code}", "error")
                self.status_lbl.config(text=f"异常退出 (code {return_code})", bootstyle="danger")

        except Exception as e:
            self._log(f"\n❌ 启动失败: {e}", "error")
            self.status_lbl.config(text="启动失败", bootstyle="danger")
        finally:
            self.is_running = False
            self.process = None
            self.root.after(0, self._reset_ui)

    def _reset_ui(self):
        self.start_btn.config(state=NORMAL)
        self.stop_btn.config(state=DISABLED)
        if not self.is_running and self.status_lbl.cget("text") not in ("转录完成", "启动失败"):
            self.status_lbl.config(text="就绪", bootstyle="secondary")

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
        self.status_lbl.config(text="已停止", bootstyle="secondary")
        self._reset_ui()


def main():
    root = ttk.Window(
        title="Whisper 语音识别",
        themename="superhero",
        size=(1200, 850),
        minsize=(1000, 700),
        iconphoto="",
    )
    app = WhisperModernGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
