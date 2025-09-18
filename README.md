RAG Chat API — FastAPI + OpenAI SDK (Streaming)

1) Yêu cầu
- Python 3.11+ (đã test 3.13)
- pip, virtualenv (khuyến nghị)

2) Cài đặt
```bash
pip install -r requirements.txt
```

3) Cấu hình .env (đặt tại thư mục dự án)
```env
OPENAI_API_KEY=sk-...

# Dùng Assistants (managed history)
USE_ASSISTANTS=true
ASSISTANT_ID=asst_...   # tạo bằng API (xem mục 6)

# Nếu chỉ test SQLite/DB khác cho các phần còn lại:
DATABASE_URL=sqlite+aiosqlite:///./app.db
```

4) Chạy server
```bash
uvicorn --env-file .env app.main:app --reload
```
Server chạy tại: http://127.0.0.1:8000

5) Endpoints chính
- POST `/chat/stream` — SSE streaming chat
  - Headers: `Content-Type: application/json`, `Accept: text/event-stream`
  - Body ví dụ:
  ```json
  { "message": "Xin chào!", "model": "gpt-4o-mini" }
  ```
  - Server sẽ stream các event `delta` và kết thúc bằng `{"type":"done","thread_id":"..."}`.

- GET `/threads/{thread_id}/messages` — Lấy lịch sử hội thoại
  - Khi `USE_ASSISTANTS=true`: đọc lịch sử từ OpenAI Threads/Messages.

6) Tạo ASSISTANT_ID nhanh (nếu không dùng Dashboard)
```powershell
pip install -U openai
$env:OPENAI_API_KEY="YOUR_OPENAI_KEY"
python -c "from openai import OpenAI; c=OpenAI(); a=c.beta.assistants.create(name='RAG Assistant', instructions='You are helpful and answer in Vietnamese.', model='gpt-4o-mini'); print(a.id)"
```
Copy `asst_...` vào `.env` rồi restart server.

7) Gợi ý test với curl (SSE)
```bash
curl -N \
  -H "Accept: text/event-stream" \
  -H "Content-Type: application/json" \
  -d '{"message":"Xin chào!","model":"gpt-4o-mini"}' \
  http://127.0.0.1:8000/chat/stream
```

Ghi chú
- `thread_id` được trả ở event `done`. Client nên lưu `thread_id` để tiếp tục cuộc hội thoại hoặc gọi `GET /threads/{id}/messages`.
- Nếu SDK không phát text-delta, server sẽ tự lấy câu trả lời cuối từ thread và emit 1 `delta` trước `done`.
