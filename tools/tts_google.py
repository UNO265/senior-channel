"""TTS 원고(script.tsv) → Google Cloud Text-to-Speech (Chirp 3 HD).

API 키는 환경 변수 GOOGLE_TTS_API_KEY에서 읽는다(레포·채팅에 넣지 않는다).
무료 한도: Chirp 3 HD 월 100만 자(2026-10 기준, 넘으면 100만 자당 30달러).

사용:
    python tools/tts_google.py docs/episodes/ep01-short --voices        # 한국어 목소리 목록
    python tools/tts_google.py docs/episodes/ep01-short --sample        # 후보 목소리로 첫 두 줄 시험
    python tools/tts_google.py docs/episodes/ep01-short [--only 0001-0003]
그다음 python tools/tts_qa.py <ep> 로 자체 검수한다.
"""
import argparse
import base64
import csv
import json
import os
import sys
import urllib.request
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from tts_melo import SR, assemble, parse_only, write_wav  # noqa: E402

API = "https://texttospeech.googleapis.com/v1"
# 화자 → (목소리 이름, 말하기 속도). 내레이터 목소리는 --sample로 들어 보고 정한다.
VOICES = {
    "내레이터": ("ko-KR-Chirp3-HD-Aoede", 0.95),
}


def call(path, body=None):
    key = os.environ.get("GOOGLE_TTS_API_KEY")
    if not key:
        raise SystemExit("환경 변수 GOOGLE_TTS_API_KEY가 없다(클라우드 환경 설정 → 새 세션).")
    req = urllib.request.Request(f"{API}/{path}{'&' if '?' in path else '?'}key={key}",
                                 data=json.dumps(body).encode() if body else None,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)


def synth(text, voice, rate, out: Path):
    res = call("text:synthesize", {
        "input": {"text": text},
        "voice": {"languageCode": "ko-KR", "name": voice},
        "audioConfig": {"audioEncoding": "LINEAR16", "sampleRateHertz": SR, "speakingRate": rate},
    })
    pcm = base64.b64decode(res["audioContent"])[44:]  # WAV 헤더 제거
    write_wav(out, np.frombuffer(pcm, dtype=np.int16).astype(np.float32) / 32768)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ep", type=Path)
    ap.add_argument("--only")
    ap.add_argument("--voices", action="store_true")
    ap.add_argument("--sample", action="store_true")
    args = ap.parse_args()

    if args.voices:
        for v in call("voices?languageCode=ko-KR")["voices"]:
            if "Chirp3" in v["name"]:
                print(v["name"], v["ssmlGender"])
        return

    rows = list(csv.DictReader(open(args.ep / "tts" / "script.tsv", encoding="utf-8"), delimiter="\t"))
    if args.sample:
        out = args.ep / "preview"
        names = [v["name"] for v in call("voices?languageCode=ko-KR")["voices"]
                 if "Chirp3" in v["name"] and v["ssmlGender"] == "FEMALE"]
        for name in names:
            for r in rows[:2]:
                synth(r["text"], name, VOICES["내레이터"][1], out / f"g-{name.split('-')[-1]}-{r['id']}.wav")
            print("시험:", name)
        return

    unknown = {r["speaker"] for r in rows} - set(VOICES)
    if unknown:
        raise SystemExit(f"VOICES에 없는 화자: {unknown}")
    only = parse_only(args.only)
    lines = args.ep / "audio" / "lines"
    lines.mkdir(parents=True, exist_ok=True)
    for r in rows:
        out = lines / f"{r['id']}.wav"
        if (only is None and not out.exists()) or (only and int(r["id"]) in only):
            synth(r["text"], *VOICES[r["speaker"]], out)
            print(f"[{r['id']}] {r['text'][:40]}", flush=True)
    assemble(rows, args.ep / "audio", lines, {"engine": "google-chirp3-hd", "voices": VOICES})


if __name__ == "__main__":
    main()
