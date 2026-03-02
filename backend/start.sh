#!/bin/bash

# 1. Trỏ đường dẫn tương đối tới vị trí mới của file config
litellm --config llm-proxy/config.yaml --port 4000 &

# 2. Đợi 3 giây để đảm bảo LiteLLM đã khởi động xong hoàn toàn
sleep 3

# 3. Khởi chạy FastAPI
uvicorn main:app --host 0.0.0.0 --port $PORT