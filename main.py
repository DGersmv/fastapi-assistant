from fastapi import FastAPI, Request, UploadFile, File
import openai
import os
import uuid

app = FastAPI()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Глобальный словарь сессий
sessions = {}  # session_id -> { "messages": [...], "files": {filename: content} }

@app.post("/ask")
async def ask(request: Request):
    data = await request.json()
    question = data.get("question", "")
    session_id = data.get("session_id")

    if not question:
        return {"answer": "❗ Вопрос не указан."}

    # Если нет session_id — создать новую сессию
    if not session_id:
        session_id = str(uuid.uuid4())
        sessions[session_id] = {"messages": [], "files": {}}

    # Если передан session_id, но он новый — инициализировать
    if session_id not in sessions:
        sessions[session_id] = {"messages": [], "files": {}}

    session = sessions[session_id]
    messages = session["messages"]

    # Добавляем system prompt один раз при начале
    if not messages:
        messages.append({
            "role": "system",
            "content": (
                "Ты являешься техническим помощником по разработке плагинов для Archicad. "
                "В данный момент загружены исходники проекта, содержащие .cpp, .h и .grc файлы. "
                "Исходники включают: функции работы с элементами (GetSurfaceHeight, AdjustToTerrain, PlaceElement и др.), "
                "создание окон и диалогов (CreateWindow, CreateDoor, DialogHandler), описание ресурсов в .grc-файлах. "
                "Твои правила: опираться только на примеры, использовать стиль C++ Archicad SDK 27.6003. "
                "Следуй строгой типизации, компактным функциям, используй ACAPinc.h, APIdefs.h, APICommon.h. "
            )
        })

    # Добавляем текущий вопрос
    messages.append({"role": "user", "content": question})

    try:
        completion = openai.ChatCompletion.create(
            model="gpt-4.1",
            temperature=0.2,
            messages=messages
        )
        answer = completion["choices"][0]["message"]["content"]
        messages.append({"role": "assistant", "content": answer})

        return {"answer": answer, "session_id": session_id}
    except Exception as e:
        return {"error": str(e), "session_id": session_id}


@app.post("/upload")
async def upload(request: Request, file: UploadFile = File(...)):
    session_id = request.query_params.get("session_id")
    content = await file.read()
    text = content.decode('utf-8', errors='ignore')

    # Если указана сессия — добавим файл в неё
    if session_id and session_id in sessions:
        session = sessions[session_id]
        session["files"][file.filename] = text
        session["messages"].append({
            "role": "user",
            "content": f"[Файл загружен: {file.filename}]\n\n{text[:1500]}..."
        })

    return {"info": f"Файл '{file.filename}' успешно загружен.", "size": len(text), "session_id": session_id}


# Запуск
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
