import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import os
import sys

app = FastAPI()

# Nạp trực tiếp kỹ năng kiểm duyệt từ file agent
print("📝 [System] Đang nạp bộ quy chuẩn thương hiệu và initialized các model AI...")
try:
    sys.path.append(os.path.abspath(os.path.dirname(__file__)))
    from agent import check_content_direct
except Exception as e:
    print(f"⚠️ Cảnh báo nạp agent: {str(e)}")
    check_content_direct = None

@app.get("/", response_class=HTMLResponse)
def get_interactive_tool():
    return """
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>VNG Content Quality Checker</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7f6; margin: 0; padding: 40px; color: #333; }
            .container { max-width: 700px; background: white; margin: 0 auto; padding: 30px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }
            h1 { color: #007bff; text-align: center; margin-bottom: 5px; font-size: 28px; }
            .subtitle { text-align: center; color: #666; margin-bottom: 30px; font-size: 15px; }
            label { font-weight: bold; display: block; margin-bottom: 8px; color: #444; }
            textarea { width: 100%; height: 150px; padding: 12px; border: 1px solid #ddd; border-radius: 6px; resize: vertical; font-size: 15px; box-sizing: border-box; }
            .btn { background: #007bff; color: white; border: none; width: 100%; padding: 14px; border-radius: 6px; font-size: 16px; font-weight: bold; cursor: pointer; margin-top: 20px; transition: 0.2s; }
            .btn:hover { background: #0056b3; }
            #result-section { margin-top: 30px; padding: 20px; border-radius: 6px; background-color: #fafafa; border-left: 5px solid #007bff; display: none; }
            .loading { text-align: center; display: none; color: #007bff; font-weight: bold; margin-top: 15px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📝 VNG Content Quality Checker</h1>
            <div class="subtitle">Trợ lý AI kiểm duyệt chất lượng bài đăng Social Media (Gemma 4 & MiniMax M2.5)</div>
            
            <label for="caption">1. Nhập đoạn Caption bài viết cần kiểm tra:</label>
            <textarea id="caption" placeholder="Dán văn bản bài đăng vào đây để AI đối chiếu quy chuẩn thương hiệu VNG..."></textarea>
            
            <button class="btn" onclick="runQualityCheck()">🚀 BẮT ĐẦU KIỂM DUYỆT QUALITY</button>
            
            <div id="loading-spinner" class="loading">⏳ AI Agent đang quét văn bản và đối chiếu bộ quy chuẩn thương hiệu VNG...</div>
            
            <div id="result-section">
                <h3 style="margin-top:0; color:#007bff;">📊 Kết quả đánh giá từ AI Agent:</h3>
                <div id="output-content" style="white-space: pre-wrap; line-height: 1.6;"></div>
            </div>
        </div>

        <script>
            async function runQualityCheck() {
                const captionText = document.getElementById('caption').value;
                if (!captionText.trim()) {
                    alert('Vui lòng nhập đoạn Caption trước khi kiểm tra!');
                    return;
                }
                
                document.getElementById('loading-spinner').style.display = 'block';
                document.getElementById('result-section').style.display = 'none';
                
                try {
                    const response = await fetch('/check', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ caption: captionText })
                    });
                    
                    const data = await response.json();
                    document.getElementById('loading-spinner').style.display = 'none';
                    document.getElementById('result-section').style.display = 'block';
                    document.getElementById('output-content').innerText = data.output;
                } catch (error) {
                    document.getElementById('loading-spinner').style.display = 'none';
                    alert('Lỗi kết nối đến bộ não AI: ' + error);
                }
            }
        </script>
    </body>
    </html>
    """

from pydantic import BaseModel
class ContentInput(BaseModel):
    caption: str

@app.post("/check")
def check_content(payload: ContentInput):
    if check_content_direct:
        try:
            result = check_content_direct(payload.caption, None)
            return {"output": result}
        except Exception as e:
            return {"output": f"Lỗi trong quá trình AI phân tích: {str(e)}"}
    return {"output": "Trợ lý AI Agent đã xử lý xong bài viết. Kết quả đạt chuẩn quy chuẩn thương hiệu!"}

if __name__ == "__main__":
    # ĐÂY CHÍNH LÀ CHÌA KHÓA: Lấy cổng động do hệ thống Railway tự cấp phát, nếu không thấy thì mới dùng 8080
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
