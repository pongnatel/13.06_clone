import base64
import os

import requests
import streamlit as st


AGENT_API_URL = os.getenv("AGENT_API_URL", "http://localhost:8000").rstrip("/")


def call_agent_api(caption: str, uploaded_file) -> dict:
    images = []
    if uploaded_file is not None:
        images.append(base64.b64encode(uploaded_file.getvalue()).decode("ascii"))

    payload = {
        "text": caption,
        "images": images,
        "project": {
            "brand_name": "GreenNode",
            "brand_exclusions": ["GreenNode", "AgentBase", "VNG", "VNGCampus"],
            "tone": "casual",
            "is_social_media": True,
        },
        "enable_llm": True,
    }

    response = requests.post(f"{AGENT_API_URL}/check", json=payload, timeout=180)
    response.raise_for_status()
    return response.json()


def render_result(result: dict) -> None:
    score = result.get("score")
    grade = result.get("grade")
    total_issues = result.get("total_issues", 0)
    severity = result.get("issues_by_severity", {})

    st.metric("Quality score", f"{score}/100" if score is not None else "N/A", grade or "")
    st.caption(
        f"Issues: {total_issues} | "
        f"Critical: {severity.get('critical', 0)} | "
        f"Major: {severity.get('major', 0)} | "
        f"Minor: {severity.get('minor', 0)} | "
        f"Suggestion: {severity.get('suggestion', 0)}"
    )

    image_analysis = result.get("image_analysis") or []
    if image_analysis:
        st.subheader("Image OCR")
        for image in image_analysis:
            idx = image.get("image_index", 0)
            extracted_text = image.get("extracted_text") or "(No text extracted)"
            st.markdown(f"**Image {idx}**")
            st.code(extracted_text)

    issues = result.get("issues") or []
    if issues:
        st.subheader("Issues")
        st.dataframe(
            [
                {
                    "rule_id": issue.get("rule_id"),
                    "severity": issue.get("severity"),
                    "category": issue.get("category"),
                    "source": issue.get("source", "caption"),
                    "found": issue.get("found"),
                    "suggestion": issue.get("suggestion"),
                    "message": issue.get("message"),
                }
                for issue in issues
            ],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.success("No issues found.")

    st.subheader("Corrected caption")
    st.write(result.get("corrected_text") or result.get("original_text") or "")


st.set_page_config(
    page_title="VNG Content Quality Checker",
    page_icon="📝",
    layout="wide",
)

st.title("VNG Content Quality Checker")
st.subheader("AI agent kiểm tra caption và độ đồng nhất giữa ảnh với nội dung")

with st.sidebar:
    st.caption("Agent API")
    st.code(AGENT_API_URL)

caption = st.text_area(
    "Caption",
    placeholder="Dán nội dung bài đăng vào đây...",
    height=220,
)

uploaded_file = st.file_uploader(
    "Ảnh đi kèm",
    type=["png", "jpg", "jpeg"],
)

if uploaded_file is not None:
    st.image(uploaded_file, caption=uploaded_file.name, use_container_width=True)

if st.button("Kiểm tra quality", type="primary", use_container_width=True):
    if not caption.strip():
        st.warning("Vui lòng nhập caption trước khi kiểm tra.")
    else:
        with st.spinner("Đang gọi Agent API..."):
            try:
                result = call_agent_api(caption, uploaded_file)
            except requests.HTTPError as exc:
                body = exc.response.text if exc.response is not None else str(exc)
                st.error(f"Agent API returned an error: {body}")
            except requests.RequestException as exc:
                st.error(f"Không thể kết nối tới Agent API: {exc}")
            else:
                st.success("Kiểm tra hoàn tất")
                render_result(result)
