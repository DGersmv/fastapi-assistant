from fastapi import FastAPI, Request
import openai
import os

app = FastAPI()
openai.api_key = os.getenv("OPENAI_API_KEY")

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

# ⬇️ ОБЯЗАТЕЛЬНО добавить запуск сервера
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))  # Railway выставляет PORT в переменные окружения
    uvicorn.run(app, host="0.0.0.0", port=port)
