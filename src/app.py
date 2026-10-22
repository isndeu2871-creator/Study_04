"""냉장고 레시피 추천 앱 — Streamlit 화면.

실행: streamlit run src/app.py
"""

import streamlit as st

import client
import vision

st.set_page_config(page_title="냉장고 레시피", page_icon="🥗", layout="centered")

# 좁은 화면에서도 한 줄 배열이 깨지지 않게 한다 (PRD 1단계 F5).
st.markdown("""
<style>
  div[data-testid="stHorizontalBlock"] { flex-wrap: nowrap; gap: .4rem; }
  div[data-testid="stHorizontalBlock"] > div { min-width: 0; }
  @media (max-width: 420px) { .block-container { padding: 1rem .6rem; } }
</style>
""", unsafe_allow_html=True)


def init_state():
    st.session_state.setdefault("ingredients", [])
    st.session_state.setdefault("last_model", "")
    st.session_state.setdefault("log", [])
    st.session_state.setdefault("error", "")


def reset_result():
    """새로 인식하기 전에 이전 결과를 지운다.

    실패했는데 옛 결과가 남아 이번 사진의 결과처럼 보이면 안 된다 (PRD 1단계 F6).
    """
    st.session_state.ingredients = []
    st.session_state.last_model = ""
    st.session_state.log = []
    st.session_state.error = ""


def render_upload():
    st.subheader("1단계 · 냉장고 사진에서 식재료 인식")
    uploaded = st.file_uploader(
        "냉장고 사진을 올리세요 (끌어다 놓아도 됩니다)",
        type=["jpg", "jpeg", "png"],
    )
    if uploaded is None:
        return

    st.image(uploaded, caption="올린 사진", use_container_width=True)
    if not st.button("식재료 인식하기", type="primary", use_container_width=True):
        return

    reset_result()
    progress = st.empty()
    lines = []

    def on_event(text):
        lines.append(text)
        progress.code("\n".join(lines[-8:]))

    try:
        with st.spinner("인식하는 중입니다. 모델이 막히면 예비 모델로 넘어갑니다."):
            key = client.get_api_key()
            result = vision.recognize(uploaded.getvalue(), key, on_event=on_event)
    except client.ModelError as error:
        detail = error.message if error.status == 200 else client.explain(error.status)
        st.session_state.error = f"식재료 인식 실패 — {detail}"
        st.session_state.log = lines
    except Exception as error:
        st.session_state.error = f"식재료 인식 실패 — {error}"
        st.session_state.log = lines
    else:
        st.session_state.ingredients = result["ingredients"]
        st.session_state.last_model = result["model"]
        st.session_state.log = result["log"]
        st.caption(
            f"사진 {result['original_bytes'] // 1024}KB → {result['resized_bytes'] // 1024}KB"
        )
    st.rerun()


def render_error():
    if not st.session_state.error:
        return
    st.error(st.session_state.error)
    if st.session_state.log:
        with st.expander("진행 기록 보기"):
            st.code("\n".join(st.session_state.log))


def render_ingredients():
    items = st.session_state.ingredients
    if not items:
        return

    st.success(f"재료 {len(items)}개를 찾았습니다 · 쓴 모델 `{st.session_state.last_model}`")
    st.caption("AI 인식 결과는 부정확할 수 있습니다. 아래에서 고치세요.")

    remove_at = None
    for index, item in enumerate(items):
        name_col, qty_col, unit_col, del_col = st.columns([5, 2, 3, 2])
        item["name"] = name_col.text_input(
            "이름", item["name"], key=f"name{index}", label_visibility="collapsed")
        item["quantity"] = qty_col.number_input(
            "수량", min_value=1, max_value=999, value=int(item["quantity"]),
            key=f"qty{index}", label_visibility="collapsed")
        item["unit"] = unit_col.selectbox(
            "단위", vision.UNITS, index=vision.UNITS.index(item["unit"]),
            key=f"unit{index}", label_visibility="collapsed")
        if del_col.button("삭제", key=f"del{index}", use_container_width=True):
            remove_at = index

    if remove_at is not None:
        items.pop(remove_at)
        st.rerun()

    if st.button("+ 재료 추가", use_container_width=True):
        items.append({"name": "", "quantity": 1, "unit": "개", "category": "기타"})
        st.rerun()

    with st.expander("진행 기록 보기"):
        st.code("\n".join(st.session_state.log))

    st.button("레시피 추천받기 (2단계)", type="primary", use_container_width=True, disabled=True,
              help="2단계는 아직 만들지 않았습니다.")


def main():
    init_state()
    st.title("🥗 냉장고 레시피")
    render_upload()
    render_error()
    render_ingredients()


if __name__ == "__main__":
    main()
