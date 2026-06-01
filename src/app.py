import difflib
import json
import os

import streamlit as st
from google import genai
from google.genai import types

from glossary import LANGUAGE_NAMES, relevant_terms


def resolve_project() -> str:
    """프로젝트 ID를 환경변수에서, 없으면 서비스 계정 JSON 키에서 읽는다."""
    if os.environ.get("GOOGLE_CLOUD_PROJECT"):
        return os.environ["GOOGLE_CLOUD_PROJECT"]
    cred_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if cred_path and os.path.exists(cred_path):
        try:
            with open(cred_path, encoding="utf-8") as f:
                return json.load(f).get("project_id", "")
        except (json.JSONDecodeError, OSError):
            return ""
    return ""


PROJECT = resolve_project()
LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "global")
MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")


@st.cache_resource
def get_client() -> genai.Client:
    return genai.Client(vertexai=True, project=PROJECT, location=LOCATION)


def build_prompt(text: str, lang_code: str, use_glossary: bool) -> str:
    target = LANGUAGE_NAMES[lang_code].split(" ")[0]
    lines = [
        f"당신은 제조업 지사 간 업무 메시지를 번역하는 전문 번역가입니다.",
        f"아래 한국어 업무 메시지를 {target}로 번역하세요.",
        "구어체가 아니라 정중한 비즈니스 톤을 유지하고, 번역문만 출력하세요.",
    ]
    if use_glossary:
        terms = relevant_terms(text, lang_code)
        if terms:
            lines.append("다음 용어는 반드시 지정된 표현으로 번역하세요:")
            for ko, tr in terms.items():
                lines.append(f"- {ko} → {tr}")
    lines.append("")
    lines.append(f"[원문]\n{text}")
    return "\n".join(lines)


def translate(text: str, lang_code: str, use_glossary: bool) -> str:
    client = get_client()
    prompt = build_prompt(text, lang_code, use_glossary)
    resp = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(temperature=0.2),
    )
    return resp.text.strip()


def back_translate(translated: str, lang_code: str) -> str:
    """번역 결과를 다시 한국어로 역번역해 원문과 대조할 수 있게 한다."""
    client = get_client()
    source = LANGUAGE_NAMES[lang_code].split(" ")[0]
    prompt = (
        f"다음 {source} 문장을 한국어로 직역하세요. 의역하지 말고 번역문만 출력하세요.\n\n{translated}"
    )
    resp = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(temperature=0.2),
    )
    return resp.text.strip()


def lexical_ratio(a: str, b: str) -> int:
    """표면(문자) 유사도. 한국어는 조사·어미 변화로 낮게 나올 수 있음(참고용)."""
    a2, b2 = a.replace(" ", ""), b.replace(" ", "")
    return round(difflib.SequenceMatcher(None, a2, b2).ratio() * 100)


def judge_similarity(original: str, back: str) -> dict:
    """원문과 역번역을 LLM으로 비교해 의미 일치도·톤 유지·달라진 점을 평가한다."""
    client = get_client()
    prompt = (
        "다음 두 한국어 문장을 비교해 의미 보존과 톤/격식 유지를 평가하세요.\n"
        "A는 원문, B는 '번역 후 다시 한국어로 역번역한 문장'입니다.\n"
        "반드시 JSON으로만 출력하세요. 형식:\n"
        '{"semantic": <0-100 정수>, "tone": <0-100 정수>, '
        '"changes": ["달라지거나 누락/추가된 점을 짧게", ...], "summary": "<한 줄 평>"}\n\n'
        f"A(원문): {original}\nB(역번역): {back}"
    )
    resp = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.1,
            response_mime_type="application/json",
        ),
    )
    return json.loads(resp.text)


st.set_page_config(page_title="지사 업무 번역기", page_icon="🌐")
st.title("🌐 지사 간 업무 메시지 번역기")
st.caption("부산 본사 ↔ 베트남/멕시코 지사 업무 소통용 · Vertex AI Gemini")

with st.sidebar:
    st.header("설정")
    lang_label = st.selectbox("번역할 언어", list(LANGUAGE_NAMES.values()))
    lang_code = next(k for k, v in LANGUAGE_NAMES.items() if v == lang_label)
    use_glossary = st.checkbox("업무 용어집 적용", value=True)
    use_backtranslation = st.checkbox(
        "역번역으로 확인 (대상 언어 → 한국어)", value=False
    )
    st.divider()
    st.caption(f"모델: `{MODEL}`")

text = st.text_area(
    "번역할 한국어 메시지",
    height=160,
    placeholder="예) 이번 주 발주 건 납기를 다음 주 금요일까지로 맞춰주실 수 있을까요? 불량 재고는 검수 후 별도 회신드리겠습니다.",
)

if st.button("번역하기", type="primary", use_container_width=True):
    if not PROJECT:
        st.error("환경변수 GOOGLE_CLOUD_PROJECT 가 설정되지 않았습니다.")
    elif not text.strip():
        st.warning("번역할 메시지를 입력하세요.")
    else:
        with st.spinner("Gemini로 번역 중..."):
            try:
                result = translate(text, lang_code, use_glossary)
                st.subheader("번역 결과")
                st.success(result)
                terms = relevant_terms(text, lang_code) if use_glossary else {}
                if terms:
                    with st.expander("적용된 업무 용어"):
                        for ko, tr in terms.items():
                            st.write(f"**{ko}** → {tr}")
                if use_backtranslation:
                    with st.spinner("역번역 확인 중..."):
                        rt = back_translate(result, lang_code)
                    st.subheader("역번역 확인 (한국어)")
                    col1, col2 = st.columns(2)
                    col1.markdown(f"**원문**\n\n{text}")
                    col2.markdown(f"**역번역**\n\n{rt}")

                    lex = lexical_ratio(text, rt)
                    try:
                        judge = judge_similarity(text, rt)
                    except Exception:
                        judge = None

                    m1, m2, m3 = st.columns(3)
                    m1.metric("표면 단어 유사도", f"{lex}%")
                    if judge:
                        m2.metric("의미 일치도", f"{judge.get('semantic', '-')}%")
                        m3.metric("톤 유지", f"{judge.get('tone', '-')}%")
                        if judge.get("changes"):
                            st.markdown("**달라진 점**")
                            for ch in judge["changes"]:
                                st.markdown(f"- {ch}")
                        if judge.get("summary"):
                            st.caption("판정: " + judge["summary"])
                    st.caption(
                        "⚠ 단어 유사도는 표면 비교라 한국어에선 조사·어미·존대 변화로 낮게 나올 수 있습니다. "
                        "의미·톤은 LLM 판정이며 이 또한 오차가 있습니다."
                    )
            except Exception as e:
                st.error(f"번역 실패: {e}")
