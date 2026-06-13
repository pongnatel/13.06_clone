import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
import subprocess
import os
import sys
import time
import httpx

app = FastAPI()

# 1. Tự động kích hoạt Streamlit chạy ngầm ở cổng nội bộ 8501 khi Uvicorn vừa bật
@app.on_event("startup")
def start_streamlit_inside():
    print("🚀 [System] Khởi động âm thầm Streamlit ở cổng nội bộ 8501...")
    subprocess.Popen([
        sys.executable, "-m", "streamlit", "run", "app.py", 
        "--server.port", "8501", 
        "--server.address", "127.0.0.1",
        "--server.headless", "true",
        "--server.enableCORS", "false",
        "--server.enableXsrfProtection", "false"
    ], cwd="content-quality-checker")

# 2. Tuyệt chiêu Reverse Proxy: Hứng bất kỳ luồng truy cập nào vào cổng 8000 
# rồi bốc dữ liệu từ Streamlit (8501) trả về cho trình duyệt
@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_to_streamlit(request: Request, path: str):
    streamlit_url = f"http://127.0.0.1:8501/{path}"
    
    # Lấy query parameters nếu có
    query_params = request.url.query
    if query_params:
        streamlit_url += f"?{query_params}"
        
    async with httpx.AsyncClient() as client:
        # Bốc dữ liệu từ Streamlit
        req_headers = dict(request.headers)
        # Xóa host cũ để tránh lặp vòng gửi nhận
        req_headers.pop("host", None) 
        
        # Đọc body nếu có (dành cho POST request)
        req_content = await request.body()
        
        # Gửi ngược về Streamlit nội bộ
        res = await client.request(
            method=request.method,
            url=streamlit_url,
            headers=req_headers,
            content=req_content,
            timeout=60.0
        )
        
        # Trả kết quả về cho người dùng qua cổng 8000 công cộng
        return StreamingResponse(
            res.iter_bytes(),
            status_code=res.status_code,
            headers=dict(res.headers)
        )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
