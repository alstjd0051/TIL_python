from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from datetime import datetime
app = FastAPI()
# ----------------------
# GET 요청 예제
# ----------------------
@app.get("/v1/status")
def status():
    return {
        "status": "ok",
        "message": "서버가 정상 작동 중입니다",
        "server_time": datetime.now().isoformat()
    }
# ----------------------
# POST 요청 예제
# ----------------------
class PredictRequest(BaseModel):
    user_id: int
    features: List[float]
@app.post("/v1/predict")
def predict(req: PredictRequest):
    avg = sum(req.features) / len(req.features)
    result = 1 if avg >= 0.5 else 0
    return {
        "user_id": req.user_id,
        "avg_feature": round(avg, 3),
        "prediction": result
    }