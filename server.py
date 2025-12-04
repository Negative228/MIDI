from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import torch
import torch.nn as nn
import numpy as np
from datetime import datetime
import uvicorn

# Инициализируем модель
model = torch.jit.load("model.pt")
model.eval()

app = FastAPI(title="PyTorch Model API")

# Настройка CORS для разрешения запросов с фронтенда
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене укажите конкретный домен
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "PyTorch Model API is running"}

@app.get("/api/predict")
async def predict():
    """
    Эндпоинт для получения предсказания от модели PyTorch
    """
    try:
        # Делаем предсказание с помощью модели
        with torch.no_grad():
            prediction = model()
        
        # Преобразуем результат в список для JSON
        result = prediction.numpy().tolist()
        
        # Возвращаем результат с дополнительной информацией
        return {
            "success": True,
            "prediction": result,
            "timestamp": datetime.now().isoformat(),
            "model_output_shape": list(prediction.shape),
            "message": "Предсказание успешно выполнено"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/health")
async def health_check():
    """Проверка здоровья API"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
