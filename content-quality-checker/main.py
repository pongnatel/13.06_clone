import uvicorn
from fastapi import FastAPI
import subprocess
import os
import sys

app = FastAPI()

@app.on_event("startup")
def start_streamlit_parallel():
    # Tuyệt chiêu: Khi Uvicorn vừa bật lên, dùng Python kích hoạt luôn Streamlit chạy ở cổng 8501
    print("🚀 [System] Giao diện Streamlit đang được kích hoạt song song ở cổng phụ...")
    subprocess.Popen([
        sys.executable, "-m", "streamlit", "run", "app.py", 
        "--server.port", "8501", 
        "--server.address", "0.0.0.0",
        "--server.headless", "true"
    ], cwd="content-quality-checker")

@app.get("/")
def read_root():
    # Khi người dùng vào cổng 8000 (cổng gốc), thay vì báo 404, ta tự động chuyển hướng họ sang giao diện Streamlit hoặc nhúng HTML hiển thị giao diện luôn!
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content="""
        <html>
            <head>
                <title>VNG Content Quality Checker</title>
                <style>
                    body, html { margin:0; padding:0; height:100%; overflow:hidden; font-family: Arial, sans-serif; }
                    iframe { width:100%; height:100%; border:none; }
                </style>
            </head>
            <body>
                <iframe src="/streamlit/"></iframe>
            </body>
        </html>
    """)

# Giữ nguyên cấu trúc API cũ của dự án phía dưới này để không làm ảnh hưởng bộ não AI
@app.post("/check")
def check_content():
    return {"output": "Bộ não AI Agent đã sẵn sàng đối chiếu quy chuẩn thương hiệu!"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
