"""TTS 원고(script.tsv) → MeloTTS 한국어 음성.

화자는 MeloTTS 한국어 목소리 하나뿐이라, 인물은 속도와 음높이로만 구분한다(VOICES).
줄마다 wav를 만들고, 쉼을 넣어 장별·전체 파일로 이은 뒤, 줄별 시작·끝 시각을 timings.json에 남긴다.

사용(윈도우, 설치는 tools/README.md):
    python tools/tts_melo.py docs/episodes/ep01
    python tools/tts_melo.py docs/episodes/ep01 --only 0001-0010   # 일부만 다시 생성
    python tools/tts_melo.py docs/episodes/ep01 --dry-run          # 합성 없이 흐름만 시험(무음)
출력: <ep>/audio/lines/*.wav, <ep>/audio/chNN.wav, <ep>/audio/full.wav, <ep>/audio/timings.json
"""
import argparse
import csv
import json
import wave
from pathlib import Path

import numpy as np

SR = 44100
# 화자별 속도(1.0 = 기본)와 음높이(반음). 시니어 시청자에 맞춰 내레이터도 조금 느리게.
VOICES = {
    "내레이터": (0.92, 0),
    "김씨": (0.90, -4),
    "김씨아내": (0.95, -1),
    "이씨": (0.88, -5),
    "이씨아들": (0.97, -3),
    "박씨": (0.90, -5),
    "박씨아내": (0.93, -2),
    "정씨": (0.92, -6),
    "한씨": (0.90, -4),
}
GAP_LINE = 0.45      # 줄 사이 쉼(초)
GAP_SPEAKER = 0.7    # 화자가 바뀔 때 쉼
GAP_CHAPTER = 1.8    # 장 사이 쉼


def read_wav(p: Path) -> np.ndarray:
    with wave.open(str(p)) as w:
        assert w.getnchannels() == 1 and w.getsampwidth() == 2, p
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
        sr = w.getframerate()
    if sr != SR:
        import librosa
        x = librosa.resample(x, orig_sr=sr, target_sr=SR)
    return x


def write_wav(p: Path, x: np.ndarray):
    p.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(p), "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())


def synth_line(model, text: str, speaker: str, out: Path, dry: bool):
    speed, semitones = VOICES[speaker]
    if dry:  # 한글 1자 ≈ 0.16초로 길이만 흉내 낸다
        write_wav(out, np.zeros(int(len(text) * 0.16 / speed * SR), dtype=np.float32))
        return
    tmp = out.with_suffix(".raw.wav")
    model.tts_to_file(text, model.hps.data.spk2id["KR"], str(tmp), speed=speed, quiet=True)
    x = read_wav(tmp)
    tmp.unlink()
    if semitones:
        import librosa
        x = librosa.effects.pitch_shift(x, sr=SR, n_steps=semitones)
    write_wav(out, x)


def parse_only(spec):
    if not spec:
        return None
    ids = set()
    for part in spec.split(","):
        a, _, b = part.partition("-")
        ids.update(range(int(a), int(b or a) + 1))
    return ids


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ep", type=Path)
    ap.add_argument("--only", help="다시 만들 줄 id, 예: 0001-0010,0042")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--device", default="auto")
    args = ap.parse_args()

    rows = list(csv.DictReader(open(args.ep / "tts" / "script.tsv", encoding="utf-8"), delimiter="\t"))
    unknown = {r["speaker"] for r in rows} - set(VOICES)
    if unknown:
        raise SystemExit(f"VOICES에 없는 화자: {unknown}")
    only = parse_only(args.only)
    audio = args.ep / "audio"
    lines = audio / "lines"
    lines.mkdir(parents=True, exist_ok=True)

    model = None
    if not args.dry_run:
        from melo.api import TTS
        model = TTS(language="KR", device=args.device)

    for r in rows:
        out = lines / f"{r['id']}.wav"
        if (only is None and not out.exists()) or (only and int(r["id"]) in only):
            print(f"[{r['id']}] {r['speaker']}: {r['text'][:40]}")
            synth_line(model, r["text"], r["speaker"], out, args.dry_run)

    missing = [r["id"] for r in rows if not (lines / f"{r['id']}.wav").exists()]
    if missing:
        print(f"아직 없는 줄 {len(missing)}개 — 이어 붙이기는 전체가 만들어진 뒤에 한다")
        return
    # 이어 붙이기
    timings, chapters, full, t = [], {}, [], 0.0
    prev = None
    for r in rows:
        if prev is not None:
            gap = GAP_CHAPTER if r["chapter"] != prev["chapter"] else GAP_SPEAKER if r["speaker"] != prev["speaker"] else GAP_LINE
            sil = np.zeros(int(gap * SR), dtype=np.float32)
            full.append(sil)
            if r["chapter"] == prev["chapter"]:
                chapters[r["chapter"]].append(sil)
            t += gap
        x = read_wav(lines / f"{r['id']}.wav")
        chapters.setdefault(r["chapter"], []).append(x)
        full.append(x)
        dur = len(x) / SR
        timings.append({"id": r["id"], "chapter": r["chapter"], "speaker": r["speaker"],
                        "start": round(t, 3), "end": round(t + dur, 3), "chars": len(r["text"])})
        t += dur
        prev = r
    for ch, parts in chapters.items():
        write_wav(audio / f"ch{ch}.wav", np.concatenate(parts))
    write_wav(audio / "full.wav", np.concatenate(full))
    json.dump({"total_sec": round(t, 3), "dry_run": args.dry_run, "voices": VOICES, "lines": timings},
              open(audio / "timings.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"전체 {t/60:.1f}분 → {audio}")


if __name__ == "__main__":
    main()
