"""생성된 음성 자체 검수.

줄마다 다음을 재고, 기준을 벗어나면 표시한다.
- 받아쓰기 오류율(CER): Whisper로 받아쓴 글과 원고 비교 → 잘못 읽음·빠뜨림·잘림
- 중간 끊김: 줄 안에서 1.2초 넘는 침묵(문장 사이 0.8~1초 쉼은 정상)
- 말 속도: 초당 글자 수가 전체 중앙값의 ±20% 밖
- 어조 변화: 목소리 높이(중앙값)가 전체보다 2반음 넘게 다름
- 음량 변화: 전체보다 3dB 넘게 다름

사용: python tools/tts_qa.py docs/episodes/ep01-short [--only 0001-0010]
출력: <ep>/audio/qa.json, 화면에 문제 줄 목록
"""
import argparse
import csv
import json
import re
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from tts_melo import parse_only, read_wav, SR  # noqa: E402
from tts_prep import read_numbers  # noqa: E402

LIMITS = {"cer": 0.08, "gap": 1.2, "rate": 0.20, "pitch": 2.0, "loud": 3.0}


def norm(t: str) -> str:
    t = re.sub(r"(?<=\d),(?=\d{3})", "", t)  # 524,550 → 524550
    return re.sub(r"[^가-힣a-z0-9]", "", read_numbers(t).lower())


def cer(ref: str, hyp: str) -> float:
    a, b = norm(ref), norm(hyp)
    if not a:
        return 0.0
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1] / len(a)


def acoustics(x: np.ndarray):
    import librosa
    hop = int(0.02 * SR)
    rms = librosa.feature.rms(y=x, frame_length=hop * 2, hop_length=hop)[0]
    db = 20 * np.log10(rms + 1e-9)
    voiced = db > db.max() - 35
    idx = np.where(voiced)[0]
    gap = 0.0
    if len(idx) > 1:
        run = 0
        for v in voiced[idx[0]:idx[-1] + 1]:
            run = 0 if v else run + 1
            gap = max(gap, run * 0.02)
    f0 = librosa.yin(x, fmin=70, fmax=400, sr=SR, frame_length=2048, hop_length=hop)
    f0 = f0[: len(voiced)][voiced[: len(f0)]]
    pitch = float(np.median(12 * np.log2(f0 / 100))) if len(f0) else 0.0
    loud = float(np.median(db[voiced])) if voiced.any() else -99.0
    speech_sec = (idx[-1] - idx[0] + 1) * 0.02 if len(idx) else len(x) / SR
    return gap, pitch, loud, speech_sec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ep", type=Path)
    ap.add_argument("--only")
    ap.add_argument("--model", default="large-v3-turbo")
    args = ap.parse_args()
    rows = list(csv.DictReader(open(args.ep / "tts" / "script.tsv", encoding="utf-8"), delimiter="\t"))
    only = parse_only(args.only)
    if only:
        rows = [r for r in rows if int(r["id"]) in only]
    from faster_whisper import WhisperModel
    asr = WhisperModel(args.model, device="cpu", compute_type="int8")
    lines = args.ep / "audio" / "lines"
    res = []
    for r in rows:
        p = lines / f"{r['id']}.wav"
        x = read_wav(p)
        segs, _ = asr.transcribe(str(p), language="ko", beam_size=5, vad_filter=False)
        hyp = " ".join(s.text.strip() for s in segs)
        gap, pitch, loud, sec = acoustics(x)
        res.append({"id": r["id"], "speaker": r["speaker"], "text": r["text"], "asr": hyp,
                    "cer": round(cer(r["text"], hyp), 3), "gap": round(gap, 2),
                    "rate": round(len(norm(r["text"])) / max(sec, 0.1), 2),
                    "pitch": round(pitch, 2), "loud": round(loud, 1)})
        print(r["id"], res[-1]["cer"], hyp[:50], flush=True)
    for key in ("rate", "pitch", "loud"):
        for sp in {x["speaker"] for x in res}:
            vals = [x[key] for x in res if x["speaker"] == sp]
            med = float(np.median(vals))
            for x in res:
                if x["speaker"] == sp:
                    x[key + "_dev"] = round((x[key] / med - 1) if key == "rate" else (x[key] - med), 2)
    for x in res:
        x["issues"] = [k for k, bad in [
            ("잘못 읽음/빠뜨림", x["cer"] > LIMITS["cer"]),
            ("중간 끊김", x["gap"] > LIMITS["gap"]),
            ("속도", abs(x["rate_dev"]) > LIMITS["rate"]),
            ("어조(높이)", abs(x["pitch_dev"]) > LIMITS["pitch"]),
            ("음량", abs(x["loud_dev"]) > LIMITS["loud"]),
        ] if bad]
    json.dump({"limits": LIMITS, "lines": res}, open(args.ep / "audio" / "qa.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    bad = [x for x in res if x["issues"]]
    print(f"\n문제 줄 {len(bad)}/{len(res)}")
    for x in bad:
        print(f"[{x['id']}] {', '.join(x['issues'])} | cer {x['cer']} gap {x['gap']}s rate {x['rate_dev']:+.0%} "
              f"pitch {x['pitch_dev']:+.1f} loud {x['loud_dev']:+.1f}\n   원고: {x['text'][:60]}\n   인식: {x['asr'][:60]}")


if __name__ == "__main__":
    main()
