from fastapi import FastAPI, Request, UploadFile, File
import openai
import os
import uuid
import json
from pathlib import Path

app = FastAPI()
openai.api_key = os.getenv("OPENAI_API_KEY")

SESSIONS_FILE = Path("sessions.json")
sessions = {}

# === Загрузка сессий при запуске ===
if SESSIONS_FILE.exists():
    try:
        with open(SESSIONS_FILE, "r", encoding="utf-8") as f:
            sessions = json.load(f)
    except Exception as e:
        print(f"⚠️ Не удалось загрузить sessions.json: {e}")

def save_sessions():
    try:
        with open(SESSIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(sessions, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️ Не удалось сохранить sessions.json: {e}")

@app.post("/ask")
async def ask(request: Request):
    data = await request.json()
    question = data.get("question", "")
    session_id = data.get("session_id")

    if not question:
        return {"answer": "❗ Вопрос не указан."}

    if not session_id:
        session_id = str(uuid.uuid4())
        sessions[session_id] = {"messages": [], "files": {}}

    if session_id not in sessions:
        sessions[session_id] = {"messages": [], "files": {}}

    session = sessions[session_id]
    messages = session["messages"]

    if not messages:
        messages.append({
            "role": "system",
            "content": (
                "Ты помощник по разработке плагинов для Archicad. "
                "Работаешь с исходниками .cpp, .h, .grc. Отвечай строго в контексте кода Archicad API."
            )
        })

    messages.append({"role": "user", "content": question})

    try:
        completion = openai.ChatCompletion.create(
            model="gpt-4o",
            temperature=0.2,
            messages=messages
        )
        answer = completion["choices"][0]["message"]["content"]
        messages.append({"role": "assistant", "content": answer})

        save_sessions()
        return {"answer": answer, "session_id": session_id}
    except Exception as e:
        return {"error": str(e), "session_id": session_id}

@app.post("/upload")
async def upload(request: Request, file: UploadFile = File(...)):
    session_id = request.query_params.get("session_id")
    content = await file.read()
    text = content.decode("utf-8", errors="ignore")

    if session_id and session_id in sessions:
        sessions[session_id]["files"][file.filename] = text
        sessions[session_id]["messages"].append({
            "role": "user",
            "content": f"[Файл загружен: {file.filename}]\n\n{text[:1500]}..."
        })
        save_sessions()

    return {"info": f"Файл '{file.filename}' успешно загружен.", "size": len(text), "session_id": session_id}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
