"""TTS 원고(script.tsv) → Qwen3-TTS 음성 (Apache-2.0).

화자별 목소리는 VOICES에 둔다. 지금은 내레이터만 확정: 기본 화자 Sohee(따뜻한 한국어 여성) + 말투 지시.
줄마다 wav를 만들고, 다 만들어지면 tts_melo.assemble로 장별·전체 파일과 timings.json을 만든다.

사용:
    python tools/tts_qwen.py docs/episodes/ep01-short [--only 0001-0003] [--device cpu|cuda:0]
설치: pip install qwen-tts soundfile librosa  (CPU에서는 느리다: 실제 길이의 약 6배)
"""
import argparse
import csv
import os
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from tts_melo import SR, assemble, parse_only, write_wav  # noqa: E402

MODEL = "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice"
# 화자 → (Qwen 기본 화자, 말투 지시)
VOICES = {
    "내레이터": ("Sohee", "차분하고 따뜻하게, 조금 천천히 또박또박 말해 주세요."),
}
BATCH = 4


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ep", type=Path)
    ap.add_argument("--only")
    ap.add_argument("--device", default="cpu")
    args = ap.parse_args()

    rows = list(csv.DictReader(open(args.ep / "tts" / "script.tsv", encoding="utf-8"), delimiter="\t"))
    unknown = {r["speaker"] for r in rows} - set(VOICES)
    if unknown:
        raise SystemExit(f"VOICES에 없는 화자: {unknown}")
    only = parse_only(args.only)
    audio = args.ep / "audio"
    lines = audio / "lines"
    lines.mkdir(parents=True, exist_ok=True)
    todo = [r for r in rows if (only is None and not (lines / f"{r['id']}.wav").exists()) or (only and int(r["id"]) in only)]

    if todo:
        import librosa
        import torch
        from qwen_tts import Qwen3TTSModel
        os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
        dtype = torch.float32 if args.device == "cpu" else torch.bfloat16
        model = Qwen3TTSModel.from_pretrained(MODEL, device_map=args.device, dtype=dtype)
        for i in range(0, len(todo), BATCH):
            chunk = todo[i:i + BATCH]
            wavs, sr = model.generate_custom_voice(
                text=[r["text"] for r in chunk],
                language=["Korean"] * len(chunk),
                speaker=[VOICES[r["speaker"]][0] for r in chunk],
                instruct=[VOICES[r["speaker"]][1] for r in chunk],
            )
            for r, w in zip(chunk, wavs):
                x = librosa.resample(np.asarray(w, dtype=np.float32), orig_sr=sr, target_sr=SR)
                write_wav(lines / f"{r['id']}.wav", x)
                print(f"[{r['id']}] {r['speaker']}: {r['text'][:40]}", flush=True)

    assemble(rows, audio, lines, {"engine": "qwen3-tts", "model": MODEL, "voices": VOICES})


if __name__ == "__main__":
    main()
