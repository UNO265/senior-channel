# 도구

| 파일 | 하는 일 |
|---|---|
| `tts_prep.py` | 확정 대본(`script/act*.md`) → TTS 원고(`tts/script.tsv`). 화자 지정(`tts/speakers.tsv`)·숫자 한글 읽기 |
| `tts_melo.py` | TTS 원고 → MeloTTS 한국어 음성, 장별·전체 wav, 줄별 타이밍(`audio/timings.json`) |

## MeloTTS 설치 (윈도우 + NVIDIA GPU)

> MeloTTS는 MIT 라이선스다(설치 전에 https://github.com/myshell-ai/MeloTTS 에서 다시 확인). 한국어 목소리는 하나뿐이라, 인물은 `tts_melo.py`의 `VOICES`(속도·음높이)로만 구분한다.
> 이 레포의 작업 환경에서는 모델을 내려받을 수 없어 실제 합성은 시험하지 못했다. 처음 돌릴 때 오류가 나면 메시지를 그대로 알려 주세요.

1. **Python 3.10** 설치(python.org, 설치 화면에서 "Add python.exe to PATH" 체크)
2. 레포 폴더에서 PowerShell을 열고 가상환경을 만든다
   ```powershell
   python -m venv .venv
   .venv\Scripts\activate
   ```
3. GPU용 PyTorch 설치(그래픽카드 드라이버의 CUDA 버전에 맞는 명령은 https://pytorch.org 에서 고른다. 예: CUDA 12.1)
   ```powershell
   pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
   ```
4. MeloTTS와 나머지 설치
   ```powershell
   pip install git+https://github.com/myshell-ai/MeloTTS.git
   python -m unidic download
   pip install librosa numpy
   ```
5. 시험: 먼저 두 줄만 만들어 듣는다
   ```powershell
   python tools/tts_melo.py docs/episodes/ep01 --only 0001-0002
   ```
   `docs/episodes/ep01/audio/lines/0001.wav`(김 씨)와 `0002.wav`(내레이터)를 들어 보고, 목소리·속도가 괜찮으면 전체를 만든다.
6. 전체 생성
   ```powershell
   python tools/tts_melo.py docs/episodes/ep01
   ```
   이미 만든 줄은 건너뛴다. 특정 줄만 다시 만들 때는 `--only 0042` 또는 `--only 0040-0045`.

## 무엇을 올리나

- **올린다**: `docs/episodes/ep01/audio/timings.json` (장면 설계에 쓴다), 이상한 줄 번호 메모
- **올리지 않는다**: wav 파일(수백 MB라 git에 넣지 않는다, `.gitignore` 처리). 보관은 개인 드라이브에.

읽기가 이상한 줄(숫자·고유명사 등)은 `tts/script.tsv`에서 그 줄의 글자를 고치는 게 아니라, 원인(대본 표기나 `tts_prep.py`의 읽기 규칙)을 고친 뒤 `tts_prep.py`를 다시 돌린다.
