# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 응답 언어

모든 답과 보고는 한국어로 한다.

## 저장소 성격

대학 수업(6장) 실습용 작업 폴더. OpenRouter의 무료 모델을 쓰는 앱을
만들기 전, 키를 안전하게 보관하고 모델 연결을 확인하는 준비 단계까지 들어 있다.
빌드 체계나 패키지 매니페스트는 아직 없고, 단일 스크립트 하나로 구성된다.

## 명령

```bash
python3 -m pip install requests pillow   # 처음 한 번만
python3 test_openrouter.py               # 키 + 두 모델 연결 시험
```

학생은 윈도를 쓴다. 윈도에서는 `python3` 이 아니라 `python` 이고,
`run_test.bat` 을 더블클릭하는 방법도 있다. 명령을 안내할 때 윈도 쪽을 먼저 적는다.

`test_openrouter.py`는 테스트 프레임워크가 아니라 수동 실행 스크립트다.
텍스트 시험과 멀티모달 시험을 차례로 돌리고, 둘 다 통과하면 종료 코드 0,
하나라도 실패하면 1을 돌려준다. 개별 시험만 돌리려면 함수를 직접 호출한다.

```bash
python3 -c "import test_openrouter as t; t.test_text(t.get_api_key())"
python3 -c "import test_openrouter as t; t.test_vision(t.get_api_key())"
```

## 키 취급

`OPENROUTER_API_KEY`는 작업 폴더의 `.env`에만 둔다. `.gitignore`가 `.env`와
`.env.*`를 막고 `!.env.example`로 견본만 예외로 올린다. 스크립트는 외부
패키지 없이 `load_env()`로 `.env`를 직접 파싱하므로 python-dotenv를 넣지 않는다.
키가 없으면 안내 문구를 찍고 종료 코드 1로 끝난다.

## 모델 이름

수업에서 고른 모델 이름은 문자열 그대로 OpenRouter에 전달해야 하므로 바꾸지 않는다.
`test_openrouter.py` 위쪽의 `TEXT_MODEL`, `VISION_MODEL` 상수와 `.env.example`,
`README.md`의 표가 같은 값을 가리켜야 한다. 모델을 바꿀 때는 네 곳을 함께 고친다.

- 텍스트: `nvidia/nemotron-3-super-120b-a12b:free`
- 멀티모달: `google/gemma-4-26b-a4b-it:free`

두 모델 모두 2026-10-22 기준으로 호출이 막혀 있다(각각 404, 429). 그래서 코드는
`TEXT_MODELS`, `VISION_MODELS` 목록을 차례로 시도하고 404/429 면 예비로 넘어간다.
선정 모델은 1번 자리에 그대로 두어 살아나면 자동으로 다시 쓰이게 한다.
예비는 서로 다른 제공 업체로 섞는다. 같은 업체는 함께 막히기 때문이다.

`max_tokens` 를 제한할 때는 1500 이상으로 둔다. 예비 모델 중 추론 모델이 있어
작게 주면 생각하는 데 다 쓰고 빈 답을 돌려준다.

무료 모델은 목록에서 사라질 수 있다. 호출이 404나 400으로 실패하면 코드를 고치기 전에
OpenRouter 목록에서 `Prompt pricing`이 `FREE`인 상태로 남아 있는지 먼저 확인한다.

## 주의

클라우드 세션에서는 `openrouter.ai`로 나가는 요청이 프록시에서 403으로 막힌다.
실제 응답 시험은 학생 본인 PC에서 해야 하고, 여기서 확인할 수 있는 것은
`.env` 파싱, 그림 생성, 오류 처리 경로까지다.
