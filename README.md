# 工业轴承故障预测系统

基于 CWRU 公开数据集，构建端到端的预测性维护平台。

## 技术栈
- **模型**：随机森林分类器，准确率 100%
- **特征工程**：FFT 频域分析 + 时域统计特征（8维）
- **后端**：FastAPI + MySQL
- **前端**：Streamlit Dashboard

## 系统架构
振动信号 → 特征提取(FFT) → 随机森林 → FastAPI接口 → MySQL存储 → Streamlit展示
## 故障类别
| 类别 | 说明 |
|------|------|
| 正常 | 轴承正常运行 |
| 内圈故障 | 内圈裂纹/磨损 |
| 外圈故障 | 外圈裂纹/磨损 |
| 滚动体故障 | 滚珠损坏 |

## 快速启动

### 安装依赖
```bash
pip install -r requirements.txt
```

### 启动后端
```bash
uvicorn api.main:app --reload
```

### 启动Dashboard
```bash
streamlit run dashboard/app.py
```

## 项目结构
bearing-fault-detection/
├── data/              # CWRU 数据集
├── model/             # 训练脚本
├── api/               # FastAPI 后端
│   └── main.py
├── dashboard/         # Streamlit 前端
│   └── app.py
├── notebooks/         # 数据分析notebook
│   └── 01_data.ipynb
└── README.md