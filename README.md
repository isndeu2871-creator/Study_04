# Study_04 — 오픈라우터 준비 작업 (6장)

클로드 데스크톱 작업 폴더. OpenRouter API 키를 안전하게 쓰기 위한 준비와
수업에서 선정한 모델 정보를 남겨 둔 폴더임.

## 1. 키 보관 규칙

| 파일 | 역할 | 깃허브 업로드 |
| --- | --- | --- |
| `.env` | 실제 API 키를 담는 파일 | ❌ (`.gitignore`로 차단) |
| `.env.example` | 키 값을 뺀 변수 이름 견본 | ✅ |

`.env`는 이 폴더에 직접 만들고, 다음 한 줄만 넣으면 됨.

```
OPENROUTER_API_KEY=sk-or-v1-...
```

`.gitignore` 규칙 설명

- `.env` : 키를 저장한 파일을 올리지 않음
- `.env.*` : `.env.local` 처럼 `.env.` 로 시작하는 다른 키 파일도 올리지 않음
- `!.env.example` : 앞의 `!` 는 예외. 키 값을 뺀 견본은 올림
- `.DS_Store` : 동기화 앱이 폴더마다 만드는 숨김 파일을 올리지 않음

파일 권한도 본인만 읽도록 좁혀 두는 것이 안전함.

```bash
chmod 600 .env
```

## 2. 모델 선정

- OpenRouter 목록에서 **`Prompt pricing` 이 `FREE`** 인지 꼭 확인함
- `google/gemma-4-26b-a4b-it:free` 는 멀티모달 모델이므로 이미지 쪽 목록에도 같이 보임
- 우리 수업의 텍스트 모델: **`nvidia/nemotron-3-super-120b-a12b:free`**
- 선정한 모델 이름은 그대로 복사해서 보관해야 함. 나중에 오픈라우터에 이 문자열을 그대로 전달함
- 모델 목록은 바뀔 수 있으므로, 실습하는 날 같은 조건(무료·텍스트)으로 목록에 남아 있는지 다시 확인함

### 자료별 텍스트 모델 비교 (2026-10-21 기준)

| 구분 | 차례 | 모델 |
| --- | --- | --- |
| 7월 실습의 캡처 | 1 | `openai/gpt-oss-20b:free` |
| 이 노트에서 쓰는 모델 | 1 | `nvidia/nemotron-3-super-120b-a12b:free` |
| 시연 영상과 시연 앱 | 1 | `nvidia/nemotron-3-super-120b-a12b:free` |
| 노트 앱의 최종 코드 | 1 | `minimax/minimax-m3:free` |
|  | 2 | `nvidia/nemotron-3-super-120b-a12b:free` |
|  | 3 | `cohere/north-mini-code:free` |
|  | 그 뒤 | 그 밖의 무료 텍스트 모델(무작위 순서) |

노트 앱은 프로필 화면에서 고른 모델 안에서만 위 차례로 시도함.

## 3. 연결 시험 (6.3.4 AI 모델 시험)

`.env` 를 만든 뒤 아래를 실행함.

```bash
python3 -m pip install requests pillow   # 처음 한 번만
python3 test_openrouter.py
```

시험 내용 두 가지

1. 텍스트 모델에 문장을 보내고 **JSON 형식**으로 제대로 답하는지 확인
2. 멀티모달 모델에 **도형과 문자**가 그려진 그림을 보내고 제대로 읽어내는지 확인

둘 다 `[성공]` 이 나오면 키와 모델이 정상임.
