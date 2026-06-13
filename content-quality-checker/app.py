import streamlit as st
import requests

st.set_page_config(page_title="VNG Content Quality Checker", page_icon="📝", layout="centered")

st.title("📝 VNG Content Quality Checker")
st.subheader("Trợ lý AI kiểm duyệt chất lượng bài đăng Social Media")
st.write("---")

caption = st.text_area("1. Nhập đoạn Caption bài viết cần kiểm tra:", placeholder="Dán văn bản bài đăng vào đây...", height=150)
uploaded_file = st.file_uploader("2. Tải lên hình ảnh Banner đi kèm (nếu có):", type=["png", "jpg", "jpeg"])

st.write("---")

if st.button("🚀 BẤT ĐẦU KIỂM DUYỆT QUALITY"):
    if not caption:
        st.warning("Vui lòng nhập đoạn Caption trước khi kiểm tra!")
    else:
        with st.spinner("AI đang quét ảnh và đối chiếu bộ quy chuẩn thương hiệu VNG..."):
            try:
                files = None
                if uploaded_file is not None:
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                
                # THAY ĐỔI QUAN TRỌNG: Gọi thẳng ra domain public của bạn thay vì localhost
                backend_url = "https://1306clawathon-production.up.railway.app/check" 
                data = {"caption": caption}
                
                response = requests.post(backend_url, data=data, files=files)
                
                if response.status_code == 200:
                    result = response.json()
                    st.success("🎉 Kiểm duyệt hoàn tất!")
                    st.markdown("### 📊 Kết quả đánh giá từ AI Agent:")
                    st.markdown(result.get("output", "Không có phản hồi từ AI."))
                else:
                    st.error(f"Lỗi kết nối Backend: {response.status_code}")
            except Exception as e:
                st.error(f"Không thể kết nối đến bộ não AI: {str(e)}")
