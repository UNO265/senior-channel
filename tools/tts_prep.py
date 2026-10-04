"""대본(md) → TTS 원고(tsv) 변환.

- `[화면]`·제목·인용 블록·구분선은 버린다.
- 줄 전체가 큰따옴표인 대사는 SPEAKERS에 적은 화자로, 나머지는 내레이터로 둔다.
- 숫자·기호를 한글 읽기로 바꾼다(엔진마다 숫자 읽기가 달라서 원고에서 통일한다).

사용: python tools/tts_prep.py docs/episodes/ep01
출력: <ep>/tts/script.tsv (id, chapter, speaker, text), <ep>/tts/by_speaker/*.txt
"""
import re
import sys
from pathlib import Path

DIGITS = "영일이삼사오육칠팔구"
UNITS = ["", "십", "백", "천"]
BIG = ["", "만", "억", "조"]


def sino(n: int) -> str:
    if n == 0:
        return "영"
    out, g = [], 0
    while n:
        n, part = divmod(n, 10000)
        if part:
            s = ""
            for i, d in enumerate(reversed(f"{part}")):
                d = int(d)
                if d:
                    s = ("" if d == 1 and i > 0 else DIGITS[d]) + UNITS[i] + s
            if g == 1 and part == 1:  # 10000 → 만
                s = ""
            out.append(s + BIG[g])
        g += 1
    return "".join(reversed(out))


def num(tok: str) -> str:
    if "." in tok:
        a, b = tok.split(".")
        return sino(int(a)) + " 점 " + "".join(DIGITS[int(c)] for c in b)
    return sino(int(tok))


MONTH = {6: "유월", 10: "시월"}


def read_numbers(t: str) -> str:
    t = t.replace("%포인트", " 퍼센트포인트").replace("%", " 퍼센트")
    t = re.sub(r"\bA급여", "에이급여", t)
    t = re.sub(r"(\d+)월", lambda m: MONTH.get(int(m[1]), sino(int(m[1])) + "월"), t)
    # 만/천/백 앞의 1은 읽지 않는다(1만 → 만)
    t = re.sub(r"(?<![\d.])1(?=[만천백십])", "", t)
    t = re.sub(r"\d+(?:\.\d+)?", lambda m: num(m[0]), t)
    t = t.replace("⅔", "삼분의 이")
    return re.sub(r"\s+", " ", t).strip()


def chapters(md: str):
    ch = None
    for line in md.splitlines():
        s = line.strip()
        m = re.match(r"## (\d+)장", s)
        if m:
            ch = int(m[1])
            continue
        if not s or ch is None or s.startswith(("#", ">", "[화면]", "---")):
            continue
        yield ch, s


def main(ep: Path):
    speakers = {}
    sp_file = ep / "tts" / "speakers.tsv"
    for row in sp_file.read_text().splitlines()[1:]:
        if row.strip():
            key, who = row.split("\t")[:2]
            speakers[key.strip()] = who.strip()
    rows, used = [], set()
    for act in sorted((ep / "script").glob("act*.md")):
        for ch, s in chapters(act.read_text()):
            quote = re.fullmatch(r"\"(.+)\"", s)
            if quote:
                key = quote[1][:20].strip()
                who = speakers.get(key)
                if who is None:
                    sys.exit(f"화자 미지정 대사: {key}  → tts/speakers.tsv에 추가")
                used.add(key)
                text = quote[1]
            else:
                who, text = "내레이터", s.replace('"', "")
            rows.append((ch, who, read_numbers(text)))
    unused = set(speakers) - used
    if unused:
        sys.exit(f"대본에 없는 speakers.tsv 항목: {sorted(unused)}")
    out = ep / "tts"
    with open(out / "script.tsv", "w") as f:
        f.write("id\tchapter\tspeaker\ttext\n")
        for i, (ch, who, text) in enumerate(rows, 1):
            f.write(f"{i:04d}\t{ch:02d}\t{who}\t{text}\n")
    bysp = out / "by_speaker"
    bysp.mkdir(exist_ok=True)
    for old in bysp.glob("*.txt"):
        old.unlink()
    for who in sorted({r[1] for r in rows}):
        with open(bysp / f"{who}.txt", "w") as f:
            for i, (ch, w, text) in enumerate(rows, 1):
                if w == who:
                    f.write(f"[{i:04d}] {text}\n")
    print(f"{len(rows)}줄, 화자 {len({r[1] for r in rows})}명 → {out}/script.tsv")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
