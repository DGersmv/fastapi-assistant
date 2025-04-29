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
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": "Ты являешься техническим помощником по разработке плагинов для Archicad. В данный момент загружены исходники проекта, содержащие .cpp, .h и .grc файлы. Исходники включают: Функции работы с элементами (GetSurfaceHeight, AdjustToTerrain, PlaceElement и др.) Создание окон и диалогов (CreateWindow, CreateDoor, DialogHandler) Описание ресурсов в .grc файлах (меню, окна, команды) Твои правила: Опираться исключительно на загруженные примеры. Следовать архитектуре Archicad API (в стиле C++). При ответах максимально использовать именованные функции и существующие паттерны кода. Если запрашивают новую функцию или обработчик — интегрировать её логично в структуру проекта. При необходимости ссылаться на ресурсы .grc для меню и окон. Контекст разработки: Целевая версия Archicad SDK: 27.6003 Рабочие заголовочные файлы: ACAPinc.h, APIdefs.h, APICommon.h Принятый стиль кода: краткие функции, точные типы, строгая типизация. Ты всегда должен помогать в рамках этого кода и этой структуры. Если что-то отсутствует — предлагай решение в аналогичном стиле."},
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
