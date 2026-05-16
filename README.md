# DATAFLOWBI

## 项目简介
DATAFLOWBI 是一个企业级 Web 数据分析平台，支持用户上传 Excel/CSV 后自动完成解析、清洗、入库、统计分析、图表展示与报告导出。当前阶段聚焦于“上传 -> pandas 解析 -> 预览返回”的完整链路。

## 技术栈
- 后端：Python 3.11, FastAPI, SQLAlchemy, Pandas, MySQL, Uvicorn
- 前端：Vue3, Vite, Axios, ECharts
- 工程化：Git, RESTful API, 前后端分离（Docker 预留）

## 项目结构
```text
DATAFLOWBI/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── services/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── database/
│   │   ├── utils/
│   │   └── main.py
│   ├── uploads/
│   ├── reports/
│   ├── requirements.txt
│   └── .env
├── frontend/
├── docs/
├── tests/
├── docker/
└── README.md
```

## 功能模块
- 文件上传与解析（Excel/CSV）
- 数据清洗与标准化（规划）
- MySQL 自动入库（规划）
- 数据统计分析（规划）
- ECharts 图表生成（规划）
- Web 分析报告展示（规划）
- PDF/Excel/PPT 报告导出（规划）

## 启动方式
1. 准备环境：Python 3.11、Node.js 18+、MySQL 8+
2. 按需修改 backend/.env 数据库配置
3. 分别启动后端与前端服务

## 后端运行方式
```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
# source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## 前端运行方式
```bash
cd frontend
npm install
npm run dev
```

如需自定义后端地址，可设置 VITE_API_BASE_URL 环境变量。

## 使用方式
1. 先启动后端服务，再启动前端服务
2. 浏览器访问 `http://localhost:5173/`
3. 点击上传按钮，选择 CSV 或 XLSX 文件
4. 页面右侧即可查看文件名、行数、列数与字段列表

## API 示例
- 健康检查
```bash
curl http://localhost:8000/health
```

- 文件上传
```bash
curl -F "file=@./sample.csv" http://localhost:8000/upload
```

响应示例：
```json
{
	"filename": "test.xlsx",
	"rows": 100,
	"columns": 5,
	"fields": ["name", "age", "salary"]
}
```

## 项目开发规划
- 完善数据清洗规则与字段类型推断
- MySQL 自动建表与批量入库
- 统计分析与指标库
- ECharts 可视化模板库
- 报告生成与导出（PDF/Excel/PPT）
- 权限与多租户（后续阶段）
