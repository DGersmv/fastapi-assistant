from fastapi import FastAPI, Request, UploadFile, File
import openai
import os

app = FastAPI()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Здесь будем хранить загруженные файлы
loaded_files = {}

@app.post("/ask")
async def ask(request: Request):
    data = await request.json()
    question = data.get("question", "")

    if not question:
        return {"answer": "❗ Вопрос не указан."}

    try:
        completion = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Ты ассистент по Archicad API."},
                {"role": "user", "content": question}
            ]
        )
        return {"answer": completion["choices"][0]["message"]["content"]}
    except Exception as e:
        return {"error": str(e)}

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    content = await file.read()
    text = content.decode('utf-8', errors='ignore')
    loaded_files[file.filename] = text
    return {"info": f"Файл '{file.filename}' успешно загружен.", "size": len(text)}

# ⬇️ ОБЯЗАТЕЛЬНО запуск сервера
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))  # Railway автоматически задаёт порт
    uvicorn.run(app, host="0.0.0.0", port=port)
