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

### 이미지(멀티모달) 모델 — 6.2.4.5

`Input Modalities` 에서 `Image` 를 골라 찾음. 냉장고 사진에서 식재료를 알아보는 데 씀.
`예비` 는 앞 모델이 막히면 넘어가는 모델임.

| 구분 | 차례 | 모델 |
| --- | --- | --- |
| 7월 실습의 캡처 | 1 | `google/gemma-4-31b-it:free` |
|  | 예비 | `nvidia/nemotron-nano-12b-v2-vl:free` |
| 이 노트에서 쓰는 모델 | 1 | `google/gemma-4-26b-a4b-it:free` |
| 시연 영상과 시연 앱 | 1 | `google/gemma-4-26b-a4b-it:free` |
|  | 예비 1 | `nvidia/nemotron-3.5-super-vl:free` |
|  | 예비 2 | `dots-studio/dots-3-note-preview:free` |
|  | 예비 3 | `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free` |
| 노트 앱의 최종 코드 | 1 | `minimax/minimax-m3:free` |
|  | 2 | `google/gemma-4-26b-a4b-it:free` |
|  | 3 | `google/gemma-4-31b-it:free` |
|  | 그 뒤 | 그 밖의 무료 비전 모델(무작위 순서) |

### 텍스트 모델 — 6.2.4.6

`Input Modalities` 에서 `Text` 만 고르고 `Image` 는 해제함. 식재료로 레시피를 추천하는 데 씀.

#### 자료별 비교 (2026-10-21 기준)

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

**윈도** — 탐색기에서 `run_test.bat` 을 더블클릭하면 설치와 시험을 한 번에 처리함.
명령 프롬프트에서 직접 치려면 다음과 같이 함.

```
python -m pip install requests pillow
python test_openrouter.py
```

**맥 / 리눅스**

```bash
python3 -m pip install requests pillow
python3 test_openrouter.py
```

시험 내용 두 가지

1. 텍스트 모델에 문장을 보내고 **JSON 형식**으로 제대로 답하는지 확인
2. 멀티모달 모델에 **도형과 문자**가 그려진 그림을 보내고 제대로 읽어내는지 확인

둘 다 `[성공]` 이 나오면 키와 모델이 정상임.

클로드에게 시켜서 시험할 때는 노트 6.3.4.1목의 프롬프트를 씀.

```
이제 준비된 API가 실제로 작동하는지 테스트해 줘.
이미지 인식은 google/gemma-4-26b-a4b-it:free 모델을 이용하고,
텍스트 인식은 nvidia/nemotron-3-super-120b-a12b:free 모델을 이용할 거야.
API를 통한 텍스트와 이미지 인식을 각각 테스트해서 실행 결과를 알려줘.
```

### 오류가 났을 때

| 코드 | 뜻 | 대처 |
| --- | --- | --- |
| `429` | 일시적 요청 제한. 무료 모델에 요청이 몰림 | 키 문제가 아님. 스크립트가 10초·20초 간격으로 두 번 더 시도하고, 그래도 안 되면 잠시 뒤 다시 실행 |
| `403` | 거절. 사용 한도 초과이거나 크레딧 없이 유료 모델 호출 | 모델 이름 끝에 `:free` 가 붙어 있는지 확인. 설정을 바꿔야 풀림 |
| `401` | 인증 실패 | `.env` 의 키 값이 틀렸거나 만료됨 |
| `404` | 모델 없음 | 그 모델이 목록에서 사라짐. 위 표의 예비 모델로 바꿔서 시도 |

텍스트는 성공했는데 이미지만 `429` 로 실패하는 경우가 흔함. 제공 업체 쪽이 혼잡한 것이고
시간이 지나면 풀리므로, 코드를 고치지 말고 다시 실행함.

## 4. 이 저장소의 파일

| 파일 | 역할 |
| --- | --- |
| `.gitignore` | 키 파일을 깃허브에 올리지 않게 막는 규칙 |
| `.env.example` | 키 값을 뺀 변수 이름 견본 |
| `CLAUDE.md` | 클로드에게 주는 이 폴더의 안내 (응답 언어, 명령, 키 취급 규칙) |
| `test_openrouter.py` | 키와 두 모델의 연결 시험 |
| `run_test.bat` | 윈도에서 더블클릭으로 시험을 실행하는 파일 |

`.env` 는 이 목록에 없음. 각자 본인 컴퓨터에서 만들고 깃허브에는 올리지 않음.

## 5. 실행 확인 기록 (2026-10-22)

클라우드 세션에서 실제로 호출해 확인한 결과임.

```
[1] 텍스트 모델 시험
   [선정 모델] nvidia/nemotron-3-super-120b-a12b:free
      건너뜀 — 404 모델을 찾을 수 없음
   [예비 1] cohere/north-mini-code:free
   응답 원문: {"ingredients": ["eggs", "milk", "spinach"]}
[성공] JSON 처리 확인

[2] 멀티모달 모델 시험
   [선정 모델] google/gemma-4-26b-a4b-it:free
      건너뜀 — 429 일시적 요청 제한
   [예비 1] nvidia/nemotron-3.5-super-vl:free
   응답 원문: 모양: 원형 / 색: 빨간색 (글자는 흰색) / 적힌 글자: AI
[성공] 그림을 읽었습니다
```

### 이 날짜 기준 모델 상태

| 모델 | 결과 |
| --- | --- |
| `nvidia/nemotron-3-super-120b-a12b:free` | 404 — 목록에는 있으나 제공 업체가 거절 |
| `google/gemma-4-26b-a4b-it:free` | 429 — 업체 혼잡, 시간이 지나면 풀릴 수 있음 |
| `cohere/north-mini-code:free` | 정상 |
| `nvidia/nemotron-3.5-super-vl:free` | 정상 |
| `dots-studio/dots-3-note-preview:free` | 정상 |
| `google/gemma-4-31b-it:free` | 429 |
| `minimax/minimax-m3:free` | 무료 중단, 유료로 바뀜 |
| `openai/gpt-oss-20b:free` | 무료 중단, 유료로 바뀜 |

목록에 `FREE` 로 보이는 것과 실제로 호출이 되는 것은 다름. 실습일에 이 스크립트를 한 번
돌려 보는 것이 목록을 눈으로 확인하는 것보다 확실함.
