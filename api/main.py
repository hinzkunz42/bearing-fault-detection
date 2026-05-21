from fastapi import FastAPI
from pydantic import BaseModel
import pymysql
import numpy as np
import joblib
from scipy.fft import fft

app = FastAPI()

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Unsw123456dd@@@",
    "database": "bearing_db"
}

# 启动时加载模型
model  = joblib.load("model/model.pkl")
scaler = joblib.load("model/scaler.pkl")

FAULT_LABELS = {
    0: "正常",
    1: "内圈故障",
    2: "外圈故障",
    3: "滚动体故障"
}

def extract_features(segment):
    segment = np.array(segment)
    rms      = np.sqrt(np.mean(segment**2))
    peak     = np.max(np.abs(segment))
    crest    = peak / (rms + 1e-8)
    kurtosis = np.mean((segment - np.mean(segment))**4) / (np.std(segment)**4 + 1e-8)
    skew     = np.mean((segment - np.mean(segment))**3) / (np.std(segment)**3 + 1e-8)
    fft_vals  = np.abs(fft(segment))[:len(segment)//2]
    freq_mean = np.mean(fft_vals)
    freq_std  = np.std(fft_vals)
    freq_peak = np.max(fft_vals)
    return [rms, peak, crest, kurtosis, skew, freq_mean, freq_std, freq_peak]

def get_db():
    return pymysql.connect(**DB_CONFIG)

class SignalInput(BaseModel):
    device_id: str
    signal: list[float]  # 512个点

@app.get("/")
def root():
    return {"status": "running"}

@app.post("/predict")
def predict(data: SignalInput):
    # 提取特征 + 预测
    features = extract_features(data.signal)
    features_scaled = scaler.transform([features])
    pred = model.predict(features_scaled)[0]
    prob = model.predict_proba(features_scaled)[0]
    confidence = round(float(np.max(prob)), 4)
    fault_type = FAULT_LABELS[int(pred)]

    # 存入数据库
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO sensor_data (device_id, signal_data) VALUES (%s, %s)",
        (data.device_id, str(data.signal[:10]))
    )
    db.commit()
    sensor_id = cursor.lastrowid

    cursor.execute(
        "INSERT INTO predictions (sensor_id, fault_type, confidence) VALUES (%s, %s, %s)",
        (sensor_id, fault_type, confidence)
    )
    db.commit()
    cursor.close()
    db.close()

    return {
        "sensor_id": sensor_id,
        "device_id": data.device_id,
        "fault_type": fault_type,
        "confidence": confidence
    }

@app.get("/history")
def get_history():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT p.id, s.device_id, p.fault_type, p.confidence, p.created_at
        FROM predictions p
        JOIN sensor_data s ON p.sensor_id = s.id
        ORDER BY p.created_at DESC
        LIMIT 20
    """)
    rows = cursor.fetchall()
    cursor.close()
    db.close()
    return {"data": [
        {"id": r[0], "device_id": r[1], "fault_type": r[2],
         "confidence": r[3], "time": str(r[4])}
        for r in rows
    ]}