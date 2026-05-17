# DATAFLOWBI

企业级 Web 数据分析平台。上传 Excel/CSV 后自动完成解析、统计分析、图表可视化与数据筛选。

## 技术栈

- **后端**: Python 3.11, FastAPI, Pandas, NumPy, SQLAlchemy, MySQL, Uvicorn
- **前端**: Vue 3 (Composition API), Vite 5, ECharts 5, Axios
- **工程化**: Git, RESTful API, 前后端分离

## 项目结构

```text
DATAFLOWBI/
├── backend/                     # Python FastAPI 后端
│   ├── app/
│   │   ├── api/                 # API 路由
│   │   │   ├── health.py        # GET /health
│   │   │   ├── upload.py        # POST /upload
│   │   │   ├── rebin.py         # POST /rebin
│   │   │   └── filter.py        # POST /filter
│   │   ├── services/
│   │   │   ├── file_preview.py  # 文件解析、缓存、过滤、重分箱
│   │   │   └── report_builder.py# 16 项统计分析报告生成
│   │   ├── models/              # SQLAlchemy 模型（预留）
│   │   ├── schemas/             # Pydantic 模型（预留）
│   │   ├── database/            # MySQL 连接配置
│   │   ├── utils/               # 工具函数（预留）
│   │   └── main.py              # 应用入口
│   ├── uploads/                 # 上传文件存储
│   ├── reports/                 # 报告导出目录（预留）
│   └── requirements.txt
├── frontend/                    # Vue 3 前端
│   ├── src/
│   │   ├── api/                 # Axios API 客户端
│   │   ├── App.vue              # 主组件（模板/逻辑/i18n/图表）
│   │   ├── style.css            # 全局样式
│   │   └── main.js              # 入口
│   ├── index.html
│   └── package.json
├── tests/                       # 测试（预留）
├── docs/                        # 文档（预留）
├── docker/                      # Docker 配置（预留）
└── README.md
```

## 已实现功能

### 后端 API（4 个端点）

| 方法 | 路由 | 用途 |
|------|------|------|
| GET | `/health` | 健康检查 |
| POST | `/upload` | 上传 CSV/XLSX → 解析 → 预览 + 16 项分析报告 |
| POST | `/rebin` | 直方图动态重分箱（自定义箱数/标准化） |
| POST | `/filter` | 数据筛选（数值范围 + 字段选择） |

### 统计分析报告（16 项）

- 缺失统计（缺失值计数 + 缺失率）
- 数值摘要（count, mean, std, min, max）
- 直方图（自动检测前 8 个数值字段，8 箱）
- 样例数据（前 5 行）
- 频率分布（分类字段 Top 20）
- 帕累托分析（Top 20 + 累计百分比）
- 箱线图（五数概括 + 异常值）
- 皮尔逊相关性矩阵（热力图）
- 分组聚合（分类 × 数值字段交叉统计）
- 分箱（等宽 + 等频，10 箱）
- 小提琴密度图（KDE 平滑，30 箱）
- 散点矩阵（最多 6 字段，采样 500 行）
- 缺失热力图（布尔矩阵，采样 200 行）
- 时间序列（自动检测日期字段，日/月聚合）
- 异常值检测（IQR + Z-Score 双方法）
- 字段类型分布

### 前端功能

- **文件上传**: 支持 .csv / .xlsx，拖拽或点击选择文件
- **两级选择流程**: 先选择基础模块（预览/报告/样例/图表），再配置具体图表指标
- **预览摘要**: 文件名、行数、列数、字段列表（展开/折叠）
- **分析报告**: 字段级统计表格（类型、缺失、均值、标准差、最值）
- **17 种图表类型**: 柱状图、折线图、直方图+分布图、帕累托图、箱线图、相关性热力图、分组柱状图、分箱图、密度图、散点图、缺失热力图、时间序列、异常值对比图、数值指标（均值/最大/最小）、频率分布
- **图表交互**: 左侧选择分析类别，右侧选择图形类型，支持字段切换
- **直方图控制**: 动态调整箱数、标准化切换（触发后端重分箱）
- **对比模式**: 多字段直方图叠加对比
- **数据筛选面板**: 数值范围滑块筛选，应用后实时更新报告
- **图表下载**: PNG / SVG
- **中英文切换**: 143 个 i18n key
- **弹窗样式切换**: 对话框（居中模态）/ 抽屉（右侧滑入）
- **响应式布局**: 适配 720px 以下设备

## 启动方式

### 前置要求

- Python 3.11+
- Node.js 18+
- MySQL 8+（可选，仅数据库持久化需要）

### 后端

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

### 前端

```bash
cd frontend
npm install
npm run dev
```

如需自定义后端地址，设置环境变量 `VITE_API_BASE_URL=http://localhost:8000`。

## 使用流程

1. 先后启动后端和前端服务
2. 浏览器访问 `http://localhost:5173/`
3. 点击上传按钮选择 CSV/XLSX 文件
4. 弹出选择窗口：勾选需要展示的模块（预览/报告/样例/图表）
5. 确认后自动上传并解析；若启用图表，弹出二级指标配置窗口
6. 在"统计分析与可视化"内点击"展开可视化选项"，选择分析类别与图形类型
7. 如需筛选数据，点击工具栏"数据筛选"按钮，调整数值范围后应用
8. 切换语言或弹窗样式：右上角"设置"
9. 下载图表：工具栏 PNG/SVG 按钮

## API 示例

```bash
# 健康检查
curl http://localhost:8000/health

# 文件上传
curl -F "file=@./sample.csv" http://localhost:8000/upload
```

## 后续规划

- 数据清洗规则与字段类型推断
- MySQL 自动建表与批量入库
- 报告导出（PDF/Excel/PPT）
- 单元测试与集成测试
- Docker 容器化部署
- 权限与多租户
