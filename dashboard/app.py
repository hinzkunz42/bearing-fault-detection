import streamlit as st
import pymysql
import pandas as pd
import plotly.express as px
import requests
import numpy as np

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Unsw123456dd@@@",
    "database": "bearing_db"
}

st.set_page_config(page_title="轴承故障预测系统", layout="wide")
st.title("轴承故障预测监控平台")

# 侧边栏：模拟预测
with st.sidebar:
    st.header("发送传感器数据")
    device_id = st.text_input("设备ID", value="motor_01")
    fault_sim = st.selectbox("模拟故障类型", ["正常信号", "故障信号"])
    
    if st.button("发送并预测", type="primary"):
        # 生成模拟信号
        if fault_sim == "正常信号":
            signal = (np.random.normal(0, 0.1, 512)).tolist()
        else:
            signal = (np.random.normal(0, 0.5, 512) + 
                     np.sin(np.linspace(0, 20*np.pi, 512))).tolist()
        
        try:
            res = requests.post(
                "http://127.0.0.1:8000/predict",
                json={"device_id": device_id, "signal": signal}
            )
            result = res.json()
            fault = result["fault_type"]
            conf  = result["confidence"]
            
            if fault == "正常":
                st.success(f"{fault}（置信度 {conf:.0%}）")
            else:
                st.error(f" {fault}（置信度 {conf:.0%}）")
        except:
            st.error("后端连接失败，请确认 uvicorn 正在运行")

# 主页面：历史记录
st.subheader("预测历史记录")

try:
    db = pymysql.connect(**DB_CONFIG)
    df = pd.read_sql("""
        SELECT p.id, s.device_id, p.fault_type, p.confidence, p.created_at
        FROM predictions p
        JOIN sensor_data s ON p.sensor_id = s.id
        ORDER BY p.created_at DESC
        LIMIT 50
    """, db)
    db.close()

    if len(df) == 0:
        st.info("暂无记录，先在左侧发送数据")
    else:
        # 指标卡
        col1, col2, col3 = st.columns(3)
        col1.metric("总检测次数", len(df))
        normal_rate = (df["fault_type"] == "正常").mean()
        col2.metric("正常率", f"{normal_rate:.0%}")
        col3.metric("平均置信度", f"{df['confidence'].mean():.0%}")

        # 故障分布饼图
        col_left, col_right = st.columns(2)
        with col_left:
            fig = px.pie(df, names="fault_type", title="故障类型分布")
            st.plotly_chart(fig, use_container_width=True)

        with col_right:
            fig2 = px.bar(df["fault_type"].value_counts().reset_index(),
                         x="fault_type", y="count", title="各类故障数量")
            st.plotly_chart(fig2, use_container_width=True)

        # 详细表格
        st.dataframe(df, use_container_width=True)

except Exception as e:
    st.error(f"数据库连接失败: {e}")