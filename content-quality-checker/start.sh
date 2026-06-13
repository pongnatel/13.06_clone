#!/bin/bash

# 1. Bật Streamlit ở cổng 8501 (Cổng giao diện) chạy ngầm
streamlit run app.py --server.port 8501 --server.address 0.0.0.0 &

# 2. Bật Uvicorn Backend ở cổng 8000 mặc định của dự án
python -m uvicorn main:app --host 0.0.0.0 --port 8000
