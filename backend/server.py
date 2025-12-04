from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import numpy as np
from model import load_model, predict

app = FastAPI()

# Настройка CORS для доступа с фронтенда
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене укажите конкретный домен
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Загрузка модели при старте приложения
model = load_model(r'models/ckpt_220.weights.h5')

class PredictionResponse(BaseModel):
    result: list
    prediction: float
    message: str

@app.get("/")
def read_root():
    return {"message": "API для работы с моделью Keras"}

@app.get("/predict", response_model=PredictionResponse)
def get_prediction():
    """
    Эндпоинт для получения предсказания от модели
    """
    try:
        # Получаем предсказание от модели
        result = predict(model)
        
        # Пример обработки результата
        prediction_value = float(np.mean(result))
        
        return PredictionResponse(
            result=result.tolist(),
            prediction=prediction_value,
            message="Предсказание успешно получено"
        )
    except Exception as e:
        return PredictionResponse(
            result=[],
            prediction=0.0,
            message=f"Ошибка: {str(e)}"
        )

@app.get("/health")
def health_check():
    return {"status": "healthy", "model_loaded": True}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
