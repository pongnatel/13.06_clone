import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import subprocess
import os
import sys
import time

app = FastAPI()

@app.on_event("startup")
def start_streamlit_backend():
    # Ép Streamlit chạy ở cổng phụ 8501 ngay khi Uvicorn vừa bật
    print("🚀 [System] Khởi động giao diện Streamlit ở cổng phụ 8501...")
    subprocess.Popen([
        sys.executable, "-m", "streamlit", "run", "app.py", 
        "--server.port", "8501", 
        "--server.address", "0.0.0.0",
        "--server.headless", "true"
    ], cwd="content-quality-checker")

@app.get("/", response_class=HTMLResponse)
def read_root():
    # Khi người dùng truy cập vào trang chủ cổng 8000, thay vì báo 404, 
    # Ta trả về một giao diện HTML siêu đẹp cấu hình sẵn nút bấm hướng về cổng 8501 
    # Hoặc hiển thị trực tiếp một thông báo điều hướng sạch sẽ.
    return """
    <html>
        <head>
            <title>VNG Content Quality Checker</title>
            <meta http-equiv="refresh" content="0; url=http://localhost:8501" />
            <style>
                body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; text-align: center; padding-top: 100px; background-color: #f4f7f6; color: #333; }
                .card { background: white; padding: 40px; border-radius: 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); display: inline-block; max-width: 500px; }
                h1 { color: #007bff; margin-bottom: 10px; }
                p { color: #666; margin-bottom: 25px; }
                .btn { background: #007bff; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block; transition: 0.2s; }
                .btn:hover { background: #0056b3; }
            </style>
        </head>
        <body>
            <div class="card">
                <h1>📝 VNG Content Quality Checker</h1>
                <p>Hệ thống đang chuyển hướng bạn sang giao diện kiểm duyệt tương tác...</p>
                <a class="btn" href="/streamlit">BẤM VÀO ĐÂY ĐỂ VÀO TOOL</a>
            </div>
        </body>
    </html>
    """

# Giữ nguyên hàm API cũ để giao diện gọi xuống không bị lỗi
@app.post("/check")
def check_content():
    return {"output": "AI Agent đã sẵn sàng đối chiếu quy chuẩn thương hiệu!"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
