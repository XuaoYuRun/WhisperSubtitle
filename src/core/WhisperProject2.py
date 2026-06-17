#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Faster-Whisper 英文语音识别转纯文本 TXT
适配: RTX 5070 Ti | Windows 11 | CUDA 12.8 | float16
模型: Whisper Large-V3-Turbo
输出: 纯文本，每行一句，无时间戳，无文件头
修复: 尾部幻觉重复 (Repetition Hallucination)
"""

import sys
import re
import argparse
import warnings
from pathlib import Path
from faster_whisper import WhisperModel

warnings.filterwarnings("ignore")


def ensure_proper_case(text: str) -> str:
    """确保句子首字母大写，并修复常见专有名词大小写"""
    if not text:
        return text

    sentences = []
    for sentence in text.split('. '):
        sentence = sentence.strip()
        if sentence:
            if sentence[0].islower():
                sentence = sentence[0].upper() + sentence[1:]
            sentences.append(sentence)
    text = '. '.join(sentences)

    proper_nouns = {
        'i': 'I',
        "i'm": "I'm", "i'll": "I'll", "i've": "I've", "i'd": "I'd",
        'monday': 'Monday', 'tuesday': 'Tuesday', 'wednesday': 'Wednesday',
        'thursday': 'Thursday', 'friday': 'Friday', 'saturday': 'Saturday', 'sunday': 'Sunday',
        'january': 'January', 'february': 'February', 'march': 'March', 'april': 'April',
        'may': 'May', 'june': 'June', 'july': 'July', 'august': 'August',
        'september': 'September', 'october': 'October', 'november': 'November', 'december': 'December',
        'english': 'English', 'chinese': 'Chinese', 'japanese': 'Japanese', 'french': 'French',
        'american': 'American', 'british': 'British', 'european': 'European',
        'youtube': 'YouTube', 'google': 'Google', 'facebook': 'Facebook',
        'iphone': 'iPhone', 'ipad': 'iPad', 'macbook': 'MacBook',
        'adobe': 'Adobe', 'photoshop': 'Photoshop', 'blender': 'Blender',
        'gaea': 'Gaea', 'houdini': 'Houdini', 'unreal': 'Unreal', 'unity': 'Unity',
    }

    for lower, proper in proper_nouns.items():
        pattern = re.compile(r'\b' + re.escape(lower) + r'\b', re.IGNORECASE)
        text = pattern.sub(proper, text)

    return text


def ensure_punctuation(text: str) -> str:
    """确保文本以标点符号结尾"""
    text = text.strip()
    if text and text[-1] not in '.!?':
        text += '.'
    return text


def merge_segments_to_sentences(segments):
    """智能合并 Whisper 片段为完整句子"""
    sentences = []
    current_parts = []
    current_start = 0.0
    current_end = 0.0

    for segment in segments:
        text = segment.text.strip()
        if not text:
            continue

        if not current_parts:
            current_start = segment.start

        current_parts.append(text)
        current_end = segment.end

        if any(text.endswith(p) for p in ['.', '!', '?', '."', '!"', '?"', '.\'', '!\'', '?\'']):
            full_text = ' '.join(current_parts)
            sentences.append({
                'start': current_start,
                'end': current_end,
                'text': full_text
            })
            current_parts = []

    if current_parts:
        full_text = ' '.join(current_parts)
        sentences.append({
            'start': current_start,
            'end': current_end,
            'text': full_text
        })

    return sentences


def clean_repetition(lines):
    """
    清理连续重复句子（Whisper 幻觉修复）
    1. 如果末尾有连续4句+完全相同，截断保留第一句
    2. 全文连续重复句只保留一句
    """
    if not lines:
        return lines

    # 保险1: 截断尾部极端重复（常见于视频结尾静音/音乐段）
    n = len(lines)
    if n >= 4:
        last = lines[-1]
        if all(l == last for l in lines[-4:]):
            idx = n - 1
            while idx > 0 and lines[idx - 1] == last:
                idx -= 1
            lines = lines[:idx + 1]

    # 保险2: 全文去重，连续相同句仅保留一句
    if not lines:
        return lines
    cleaned = [lines[0]]
    for line in lines[1:]:
        if line == cleaned[-1]:
            continue
        cleaned.append(line)

    return cleaned


def process_video(video_path: Path, model: WhisperModel, forced_output_dir: Path = None) -> Path:
    """处理单个视频文件"""
    print(f"\n{'='*60}")
    print(f"🎬 正在处理: {video_path.name}")
    print(f"{'='*60}")

    # 决定输出目录：强制指定 或 自动在视频同目录创建 Text 文件夹
    if forced_output_dir is not None:
        output_dir = forced_output_dir
    else:
        output_dir = video_path.parent / "Text"
    output_dir.mkdir(parents=True, exist_ok=True)

    # 转录参数 —— 重点修复重复问题
    segments, info = model.transcribe(
        str(video_path),
        language="en",
        task="transcribe",
        beam_size=5,
        best_of=5,
        patience=1.5,
        length_penalty=1.0,
        temperature=0.0,
        compression_ratio_threshold=2.0,   # 收紧：更容易检测重复文本
        log_prob_threshold=-1.5,               # 收紧：过滤低置信度幻觉
        no_speech_threshold=0.8,              # 提高：静音/噪声不再被当作语音
        condition_on_previous_text=False,     # 关键：关闭上下文依赖，防止重复传染
        initial_prompt=(
            "Please transcribe the following English audio accurately. "
            "Use proper punctuation, capitalization, and grammar. "
            "Ensure each sentence is complete and ends with a period, exclamation mark, or question mark."
        ),
        word_timestamps=False,
        vad_filter=True,
        vad_parameters=dict(
            min_silence_duration_ms=500,     # 500ms静音即切割，避免吞尾音
            max_speech_duration_s=999999,
        ),
    )

    print(f"🌐 检测到语言: {info.language} (概率: {info.language_probability:.2f})")

    segments_list = list(segments)
    print(f"🧩 原始片段数: {len(segments_list)}")

    sentences = merge_segments_to_sentences(segments_list)
    print(f"📝 合并后句子数: {len(sentences)}")

    # 提取纯文本并后处理
    lines = []
    for sentence in sentences:
        text = sentence['text']
        text = ensure_proper_case(text)
        text = ensure_punctuation(text)
        lines.append(text)

    # 清理幻觉重复
    original_count = len(lines)
    lines = clean_repetition(lines)
    removed_count = original_count - len(lines)
    if removed_count > 0:
        print(f"🧹 清理重复句: 删除 {removed_count} 句幻觉重复")

    # 输出纯文本
    base_name = video_path.stem
    output_path = output_dir / f"{base_name}.txt"

    with open(output_path, 'w', encoding='utf-8') as f:
        for line in lines:
            f.write(line + "\n")

    print(f"✅ 完成输出: {output_path} ({len(lines)} 句)")
    return output_path


def main():
    parser = argparse.ArgumentParser(
        description='Faster-Whisper 英文语音识别转纯文本 TXT (修复重复幻觉)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  单文件 (自动创建 Text 目录):
      python faster_whisper_en_aggressive.py "D:\\视频\\课程1.mp4"
      → 输出到 D:\\视频\\Text\\课程1.txt

  文件夹 (递归扫描子文件夹中的视频，自动创建 Text 目录):
      python faster_whisper_en_aggressive.py "D:\\视频\\课程文件夹"
      → 输出到 D:\\视频\\课程文件夹\\子文件夹A\\Text\\课程x.txt
      → 输出到 D:\\视频\\课程文件夹\\子文件夹B\\Text\\课程y.txt

  强制指定输出目录 (不使用自动 Text 目录):
      python faster_whisper_en_aggressive.py "D:\\视频\\课程1.mp4" -o "D:\\字幕"
      → 输出到 D:\\字幕\\课程1.txt
        """
    )
    parser.add_argument('input', help='输入视频文件或文件夹路径')
    parser.add_argument(
        '-o', '--output', default='.',
        help='强制指定输出文件夹路径 (默认: 在视频所在目录自动创建 Text 文件夹)'
    )
    args = parser.parse_args()

    input_path = Path(args.input)

    # 判断是否用户显式指定了输出目录
    forced_output_dir = Path(args.output) if args.output != '.' else None
    if forced_output_dir is not None:
        forced_output_dir.mkdir(parents=True, exist_ok=True)

    import torch
    if not torch.cuda.is_available():
        print("⚠️ 警告: CUDA 不可用，将回退到 CPU 运行 (速度极慢)")
        device = "cpu"
        compute_type = "int8"
    else:
        gpu_name = torch.cuda.get_device_name(0)
        print(f"🖥️  检测到 GPU: {gpu_name}")
        print(f"🔧 CUDA 版本: {torch.version.cuda}")
        print(f"⚡ 使用 float16 半精度加速")
        device = "cuda"
        compute_type = "float16"

    print("\n📦 正在加载 Whisper Large-V3-Turbo 模型...")
    print("   首次运行会自动下载模型到:")
    print("   C:\\Users\\Administrator\\.cache\\huggingface\\hub")
    print("   请保持网络畅通，耐心等待...\n")

    model = WhisperModel(
        "large-v3-turbo",
        device=device,
        compute_type=compute_type,
        cpu_threads=4 if device == "cpu" else 0,
        num_workers=1,
    )
    print("✅ 模型加载完成\n")

    video_extensions = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.mpeg', '.mpg'}

    if input_path.is_file():
        if input_path.suffix.lower() not in video_extensions:
            print(f"❌ 错误: 不支持的文件格式 {input_path.suffix}")
            sys.exit(1)
        video_files = [input_path]
    elif input_path.is_dir():
        # 🔧 修改：递归扫描所有子文件夹中的视频文件
        video_files = sorted([
            f for f in input_path.rglob('*')
            if f.is_file() and f.suffix.lower() in video_extensions
        ])
    else:
        print(f"❌ 错误: 输入路径不存在 {input_path}")
        sys.exit(1)

    if not video_files:
        print("❌ 未找到视频文件，支持格式: " + ", ".join(video_extensions))
        sys.exit(1)

    print(f"📁 找到 {len(video_files)} 个视频文件:")
    for vf in video_files:
        print(f"   • {vf}")
    print()

    success_count = 0
    for video_file in video_files:
        try:
            process_video(video_file, model, forced_output_dir)
            success_count += 1
        except Exception as e:
            print(f"\n❌ 处理 {video_file.name} 时出错: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n{'='*60}")
    print(f"🎉 全部处理完成! 成功: {success_count} / {len(video_files)}")
    if forced_output_dir:
        print(f"📂 强制输出目录: {forced_output_dir.absolute()}")
    else:
        print(f"📂 输出位置: 各视频所在目录的 Text 子文件夹中")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()