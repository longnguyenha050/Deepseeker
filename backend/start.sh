#!/bin/bash
# Chạy LiteLLM proxy ở port 4000 dưới nền (background)
litellm --port 4000 & 

# Chạy FastAPI ở port chính mà Render cấp
uvicorn main:app --host 0.0.0.0 --port $PORT