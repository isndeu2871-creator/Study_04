"""냉장고 레시피 추천 — Streamlit 화면.

실행: streamlit run src/app.py

화면 구성
  사이드바 : app / 내 레시피 / 프로필, 로그인과 회원 가입
  본문     : ① 사진 업로드 ▸ ② 식재료 확인 ▸ ③ 레시피 추천 (3단계 마법사)
"""

import auth
import client
import db
import recipe as recipe_mod
import streamlit as st
import vision

st.set_page_config(page_title="냉장고 레시피 추천", page_icon="🥬", layout="wide")

STEPS = ["사진 업로드", "식재료 확인", "레시피 추천"]

# 디자인 점검에서 고친 두 가지 (노트 6.4.10.4)
#  - 주요 버튼 빨강을 #D60000 으로. 흰 글자와의 명도 대비 5.44:1 (권장 4.5:1)
#  - 누르는 단추 높이를 44px 로. 권장 터치 크기
st.markdown("""
<style>
  div[data-testid="stHorizontalBlock"] { flex-wrap: nowrap; gap: .4rem; }
  div[data-testid="stHorizontalBlock"] > div { min-width: 0; }
  button[kind="primary"] { background-color: #D60000 !important; border-color: #D60000 !important; }
  .stButton button { min-height: 44px; }
  div[data-testid="stNumberInput"] button { min-height: 44px !important; }
  .chip { display: inline-block; background: #eee; color: #333; border-radius: 999px;
          padding: .25rem .75rem; margin: 0 .3rem .35rem 0; font-size: .85rem; }
  .steps { display: flex; gap: 2rem; flex-wrap: wrap; margin: .4rem 0 1rem; }
  .steps span { color: #888; }
  .steps span.on { color: #D60000; font-weight: 700; }
</style>
""", unsafe_allow_html=True)


# ---------- 상태 ----------

def init_state():
    db.init()
    defaults = {
        "user": None, "page": "app", "step": 1,
        "photo": None, "ingredients": [], "recipes": [],
        "vision_model": "", "recipe_model": "",
        "log": [], "error": "", "auto_generate": False,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def reset_flow():
    """처음부터 다시. 로그아웃할 때도 쓴다 (노트 6.4.9.1목 b.3)."""
    for key in ("photo", "ingredients", "recipes", "log"):
        st.session_state[key] = [] if key != "photo" else None
    st.session_state.step = 1
    st.session_state.error = ""
    st.session_state.auto_generate = False
    st.session_state.vision_model = ""
    st.session_state.recipe_model = ""


def profile():
    user = st.session_state.user
    return db.get_profile(user["id"]) if user else None


# ---------- 사이드바 ----------

def render_sidebar():
    with st.sidebar:
        for key, label in (("app", "app"), ("recipes", "내 레시피"), ("profile", "프로필")):
            if st.button(label, key=f"nav_{key}", use_container_width=True):
                st.session_state.page = key
                st.rerun()
        st.divider()

        user = st.session_state.user
        if user:
            st.write(f"**{user['email']}**")
            if st.button("로그아웃", use_container_width=True):
                st.session_state.user = None
                reset_flow()
                st.rerun()
            return

        st.subheader("로그인 / 회원가입")
        if auth.google_ready():
            if st.button("Google로 로그인", use_container_width=True):
                st.login()
        else:
            st.button("Google로 로그인", use_container_width=True, disabled=True,
                      help="구글 로그인 설정(.streamlit/secrets.toml 의 [auth])이 없습니다.")
        st.divider()

        login_tab, signup_tab = st.tabs(["로그인", "회원가입"])
        with login_tab:
            email = st.text_input("이메일", key="li_email")
            password = st.text_input("비밀번호", type="password", key="li_pw")
            if st.button("로그인", key="li_go", use_container_width=True):
                try:
                    st.session_state.user = auth.log_in(email, password)
                    st.rerun()
                except auth.AuthError as error:
                    st.error(str(error))
        with signup_tab:
            email = st.text_input("이메일", key="su_email")
            password = st.text_input("비밀번호 (8자 이상)", type="password", key="su_pw")
            if st.button("회원가입", key="su_go", use_container_width=True):
                try:
                    st.session_state.user = auth.sign_up(email, password)
                    st.rerun()
                except auth.AuthError as error:
                    st.error(str(error))


# ---------- 공통 조각 ----------

def render_steps():
    marks = []
    for index, name in enumerate(STEPS, start=1):
        on = "on" if index == st.session_state.step else ""
        marks.append(f'<span class="{on}">{"①②③"[index - 1]} {name}</span>')
    st.markdown(f'<div class="steps">{"".join(marks)}</div>', unsafe_allow_html=True)


def chips(names):
    st.markdown("".join(f'<span class="chip">{n}</span>' for n in names),
                unsafe_allow_html=True)


def show_error():
    if st.session_state.error:
        st.error(st.session_state.error)
        if st.session_state.log:
            with st.expander("진행 기록 보기"):
                st.code("\n".join(st.session_state.log))


# ---------- ① 사진 업로드 ----------

def step_upload():
    st.header("① 사진 업로드")
    uploaded = st.file_uploader(
        "냉장고 사진을 업로드하거나, 이 영역으로 파일을 끌어다 놓으세요",
        type=["jpg", "jpeg", "png"],
    )
    if uploaded is None:
        return

    left, right = st.columns([1, 1])
    left.image(uploaded, caption="올린 사진", use_container_width=True)
    with right:
        if st.button("식재료 인식하기", type="primary", use_container_width=True):
            run_recognition(uploaded.getvalue())
            st.rerun()
    show_error()


def run_recognition(image_bytes):
    st.session_state.error = ""
    st.session_state.recipes = []
    st.session_state.ingredients = []
    lines = []
    box = st.empty()

    def on_event(text):
        lines.append(text)
        box.code("\n".join(lines[-8:]))

    try:
        with st.spinner("인식하는 중입니다. 막히면 예비 모델로 넘어갑니다."):
            key = client.get_api_key()
            picked = (profile() or {}).get("vision_models") or None
            result = vision.recognize(image_bytes, key, models=picked, on_event=on_event)
    except client.ModelError as error:
        detail = error.message if error.status == 200 else client.explain(error.status)
        st.session_state.error = f"식재료 인식 실패 — {detail}"
        st.session_state.log = lines
    except Exception as error:
        st.session_state.error = f"식재료 인식 실패 — {error}"
        st.session_state.log = lines
    else:
        st.session_state.photo = image_bytes
        st.session_state.ingredients = result["ingredients"]
        st.session_state.vision_model = result["model"]
        st.session_state.log = result["log"]
        st.session_state.step = 2


# ---------- ② 식재료 확인 ----------

def step_ingredients():
    st.header("② 식재료 확인")
    show_error()
    items = st.session_state.ingredients
    if not items:
        st.info("1단계에서 사진을 먼저 올리세요.")
        return

    # 사진과 재료를 한 화면에서 맞춰 본다 (노트 6.4.11.3목).
    photo_col, list_col = st.columns([1, 2])
    if st.session_state.photo:
        photo_col.image(st.session_state.photo, caption="올린 사진", use_container_width=True)

    with list_col:
        st.success(f"재료 {len(items)}개 · 쓴 모델 `{st.session_state.vision_model}`")
        st.caption("AI 인식 결과는 부정확할 수 있습니다. 아래에서 고치세요.")

        remove_id = None
        for item in items:
            # 위젯 key 에 순번이 아니라 고유 id 를 쓴다 (노트 6.4.11.4목).
            uid = item["_id"]
            name_col, qty_col, unit_col, del_col = st.columns([5, 3, 3, 2])
            item["name"] = name_col.text_input(
                "이름", item["name"], key=f"n_{uid}", label_visibility="collapsed")
            item["quantity"] = qty_col.number_input(
                "수량", 1, 999, int(item["quantity"]), key=f"q_{uid}",
                label_visibility="collapsed")
            item["unit"] = unit_col.selectbox(
                "단위", vision.UNITS, vision.UNITS.index(item["unit"]),
                key=f"u_{uid}", label_visibility="collapsed")
            if del_col.button("삭제", key=f"d_{uid}", use_container_width=True):
                remove_id = uid

        if remove_id is not None:
            st.session_state.ingredients = [i for i in items if i["_id"] != remove_id]
            st.rerun()

        if st.button("+ 재료 추가", use_container_width=True):
            items.append({"_id": f"new-{len(items)}", "name": "", "quantity": 1,
                          "unit": "개", "category": "기타"})
            st.rerun()

    back, forward = st.columns(2)
    if back.button("← 이전", use_container_width=True):
        st.session_state.step = 1
        st.rerun()
    if forward.button("레시피 추천받기", type="primary", use_container_width=True):
        st.session_state.step = 3
        st.session_state.auto_generate = True   # 3단계에서 버튼을 다시 누르지 않아도 되게
        st.rerun()


# ---------- ③ 레시피 추천 ----------

def step_recipes():
    st.header("③ 레시피 추천")
    items = [i for i in st.session_state.ingredients if i["name"].strip()]
    if not items:
        st.info("2단계에서 재료를 먼저 확인하세요.")
        return

    chips([i["name"] for i in items])

    saved = profile() or {}
    cuisine_col, level_col, time_col, serving_col = st.columns(4)
    cuisine = cuisine_col.selectbox("종류", recipe_mod.CUISINE_OPTIONS, _index(
        recipe_mod.CUISINE_OPTIONS, saved.get("cuisine")))
    difficulty = level_col.selectbox("난이도", recipe_mod.DIFFICULTY_OPTIONS, _index(
        recipe_mod.DIFFICULTY_OPTIONS, saved.get("difficulty")))
    time_limit = time_col.selectbox("조리 시간", recipe_mod.TIME_OPTIONS, _index(
        recipe_mod.TIME_OPTIONS, saved.get("time_limit")))
    servings = serving_col.selectbox("인원", recipe_mod.SERVING_OPTIONS, _index(
        recipe_mod.SERVING_OPTIONS, saved.get("servings")), format_func=lambda n: f"{n}인분")

    go = st.button("레시피 생성하기", type="primary", use_container_width=True)
    if go or st.session_state.auto_generate:
        st.session_state.auto_generate = False
        run_generation(items, cuisine, difficulty, time_limit, servings)
        st.rerun()

    show_error()
    render_recipe_cards()

    if st.button("← 이전", use_container_width=True):
        st.session_state.step = 2
        st.rerun()


def _index(options, value):
    try:
        return options.index(value)
    except (ValueError, TypeError):
        return 0


def run_generation(items, cuisine, difficulty, time_limit, servings):
    st.session_state.error = ""
    st.session_state.recipes = []
    lines = []
    box = st.empty()

    def on_event(text):
        lines.append(text)
        box.code("\n".join(lines[-8:]))

    try:
        with st.spinner("레시피를 만드는 중입니다."):
            key = client.get_api_key()
            picked = (profile() or {}).get("text_models") or None
            result = recipe_mod.generate(items, cuisine, difficulty, time_limit, servings,
                                         key, models=picked, on_event=on_event)
    except client.ModelError as error:
        detail = error.message if error.status == 200 else client.explain(error.status)
        st.session_state.error = f"레시피 추천 실패 — {detail}"
        st.session_state.log = lines
    except Exception as error:
        st.session_state.error = f"레시피 추천 실패 — {error}"
        st.session_state.log = lines
    else:
        st.session_state.recipes = result["recipes"]
        st.session_state.recipe_model = result["model"]
        st.session_state.log = result["log"]


def render_recipe_cards():
    recipes = st.session_state.recipes
    if not recipes:
        return
    st.success(f"레시피 {len(recipes)}개 · 쓴 모델 `{st.session_state.recipe_model}`")

    for column, item in zip(st.columns(len(recipes)), recipes):
        with column.container(border=True):
            # 카드 윗부분의 높이를 고정해야 카드마다 버튼의 세로 위치가 같아진다.
            # 부족한 재료가 두 줄이면 그 카드만 버튼이 밀렸다 (노트 6.4.9.1목 b.2).
            with st.container(height=210, border=False):
                st.markdown(f"**{item['title']}**")
                st.caption(
                    f"{item['cuisine']} · {item['difficulty']} · "
                    f"{item['time_minutes']}분 · {item['servings']}인분"
                )
                if item["missing_ingredients"]:
                    st.warning("부족한 재료: " + ", ".join(item["missing_ingredients"]))
                else:
                    st.info("부족한 재료 없음")
            with st.expander("자세히 보기"):
                for number, step in enumerate(item["steps"], start=1):
                    st.write(f"{number}. {step}")
            if st.session_state.user:
                if st.button("저장", key=f"save_{item['title']}", use_container_width=True):
                    db.save_recipe(st.session_state.user["id"], item)
                    st.toast(f"{item['title']} 저장했습니다")


# ---------- 다른 쪽 화면 ----------

def page_saved():
    st.title("내 레시피")
    user = st.session_state.user
    if not user:
        st.info("로그인하면 저장한 레시피를 볼 수 있습니다.")
        return
    rows = db.list_recipes(user["id"])
    if not rows:
        st.info("아직 저장한 레시피가 없습니다.")
        return
    for row in rows:
        with st.expander(row["title"]):
            item = row["recipe"]
            st.caption(f"{item['cuisine']} · {item['difficulty']} · {item['time_minutes']}분")
            for number, step in enumerate(item["steps"], start=1):
                st.write(f"{number}. {step}")
            if st.button("삭제", key=f"rm_{row['id']}"):
                db.delete_recipe(row["id"], user["id"])
                st.rerun()


def page_profile():
    st.title("프로필")
    user = st.session_state.user
    if not user:
        st.info("로그인하면 선호 조건을 저장할 수 있습니다.")
        return
    saved = db.get_profile(user["id"])

    st.subheader("선호 조건")
    cuisine_col, level_col, time_col, serving_col = st.columns(4)
    cuisine = cuisine_col.selectbox("종류", recipe_mod.CUISINE_OPTIONS,
                                    _index(recipe_mod.CUISINE_OPTIONS, saved["cuisine"]))
    difficulty = level_col.selectbox("난이도", recipe_mod.DIFFICULTY_OPTIONS,
                                     _index(recipe_mod.DIFFICULTY_OPTIONS, saved["difficulty"]))
    time_limit = time_col.selectbox("조리 시간", recipe_mod.TIME_OPTIONS,
                                    _index(recipe_mod.TIME_OPTIONS, saved["time_limit"]))
    servings = serving_col.selectbox("인원", recipe_mod.SERVING_OPTIONS,
                                     _index(recipe_mod.SERVING_OPTIONS, saved["servings"]),
                                     format_func=lambda n: f"{n}인분")

    st.subheader("AI 모델 선택")
    st.caption("고르지 않으면 기본 차례를 그대로 씁니다.")
    vision_col, text_col = st.columns(2)
    vision_models = vision_col.multiselect("식재료 인식 모델", vision.VISION_MODELS,
                                           saved["vision_models"])
    text_models = text_col.multiselect("레시피 생성 모델", recipe_mod.TEXT_MODELS,
                                       saved["text_models"])

    if st.button("저장", type="primary"):
        db.save_profile(user["id"], cuisine, difficulty, time_limit, servings,
                        vision_models, text_models)
        st.success("저장했습니다.")


# ---------- 들어가는 곳 ----------

def main():
    init_state()
    render_sidebar()

    if st.session_state.page == "recipes":
        page_saved()
        return
    if st.session_state.page == "profile":
        page_profile()
        return

    title_col, reset_col = st.columns([5, 1])
    title_col.title("🥬 냉장고 레시피 추천")
    if reset_col.button("🔄 처음부터", use_container_width=True):
        reset_flow()
        st.rerun()

    render_steps()
    st.divider()

    {1: step_upload, 2: step_ingredients, 3: step_recipes}[st.session_state.step]()


if __name__ == "__main__":
    main()
