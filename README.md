# DATAFLOWBI

企业级 Web 数据分析平台。上传 Excel/CSV 后自动完成解析、统计分析、图表可视化与数据筛选。

## 技术栈

- **后端**: Python 3.9-3.13, FastAPI, Pandas, NumPy, SQLAlchemy, PostgreSQL, Uvicorn
- **前端**: Vue 3 (Composition API + `<script setup>`), Vite 5, ECharts 5 (懒加载), Axios
- **架构**: 组件化前端（9 个组件 + 5 个 composable），模块化后端服务层

## 项目结构

```text
DATAFLOWBI/
├── backend/                          # Python FastAPI 后端
│   ├── app/
│   │   ├── api/                      # API 路由
│   │   │   ├── health.py             # GET /health
│   │   │   ├── upload.py             # POST /upload
│   │   │   ├── rebin.py              # POST /rebin
│   │   │   └── filter.py             # POST /filter
│   │   ├── services/
│   │   │   ├── file_preview.py       # 文件解析、缓存、过滤、重分箱
│   │   │   └── report_builder.py     # 16 项统计分析报告生成（含日/月/年时序）
│   │   ├── models/                   # SQLAlchemy 模型（预留）
│   │   ├── schemas/                  # Pydantic 模型（预留）
│   │   ├── database/                 # PostgreSQL 连接配置
│   │   ├── utils/                    # 工具函数（预留）
│   │   └── main.py                   # 应用入口
│   ├── uploads/                      # 上传文件存储
│   ├── reports/                      # 报告导出目录（预留）
│   └── requirements.txt
├── frontend/                         # Vue 3 前端
│   ├── src/
│   │   ├── api/                      # Axios API 客户端
│   │   │   ├── client.js             # Axios 实例
│   │   │   └── upload.js             # 3 个 API 函数
│   │   ├── composables/              # 状态逻辑层（5 个）
│   │   │   ├── useI18n.js            # 中英双语 i18n
│   │   │   ├── useFileUpload.js      # 上传·预览·筛选生命周期
│   │   │   ├── useSelection.js       # 页面模块控制 + 图表类型配置
│   │   │   ├── useChart.js           # 图表状态·渲染·交互
│   │   │   └── chartBuilders.js      # 18 个纯函数 ECharts option 构造器
│   │   ├── components/               # UI 组件（8 个）
│   │   │   ├── SettingsMenu.vue      # 设置菜单（语言/弹窗样式）
│   │   │   ├── SelectionDialog.vue   # 分析选项对话框
│   │   │   ├── ChartSetupDialog.vue  # 图表类型配置对话框
│   │   │   ├── FilterPanel.vue       # 数据筛选对话框（字段勾选 + 数值范围）
│   │   │   ├── PreviewCard.vue       # 上传摘要卡片
│   │   │   ├── ReportSection.vue     # 统计报告 + 样本数据
│   │   │   ├── ChartToolbar.vue      # 图表工具栏
│   │   │   └── ChartOptionsPanel.vue # 图表参数面板（35 个 props）
│   │   ├── App.vue                   # 主布局 + 组合所有组件与 composable
│   │   ├── style.css                 # 全局样式（973 行）
│   │   └── main.js                   # 入口
│   ├── index.html
│   └── package.json
├── tests/                            # 测试（预留）
├── docs/                             # 文档（预留）
├── docker/                           # Docker 配置（预留）
└── README.md
```

## 架构分层

```
App.vue（主布局 + watch 联动）
  ├── composables/         ← 共享状态（模块级 singleton ref）
  │   ├── useI18n          ← 语言包
  │   ├── useFileUpload    ← 上传、预览、筛选数据流
  │   ├── useSelection     ← 页面模块开关、图表类型
  │   └── useChart         ← 图表状态 + ECharts 懒加载
  │       └── chartBuilders ← 18 个纯函数构造器
  └── components/          ← UI 展示层
       ├── Header 区域     ← SettingsMenu + PreviewCard
       ├── Report 区域     ← ReportSection
       ├── Chart 区域      ← ChartToolbar + FilterPanel + ChartOptionsPanel
       └── Dialog 区域     ← SelectionDialog + ChartSetupDialog + FilterPanel
```

## 后端 API（主要端点）

| 方法 | 路由 | 用途 |
|------|------|------|
| GET | `/health` | 健康检查 |
| POST | `/upload` | 上传 CSV/XLSX → 解析 → 预览 + 报告 + 过滤信息 |
| POST | `/clean` | 数据清洗（缺失/异常/类型转换）并生成新版本 |
| GET | `/clean/templates` | 清洗模板配置 |
| POST | `/rebin` | 直方图动态重分箱（自定义箱数/标准化） |
| POST | `/filter` | 数据筛选（字段选择 + 数值范围 + 分类值过滤） |
| GET | `/history` | 版本记录列表 |
| GET | `/history/{id}` | 版本详情 |
| POST | `/history/{id}/reload` | 加载指定版本 |
| GET | `/history/{id}/versions` | 同一数据集版本列表 |
| GET | `/history/compare` | 版本对比（from_id/to_id） |
| POST | `/history/{id}/import` | 导入版本到 PostgreSQL |
| GET | `/export/docx` | 导出 Word（无图表） |
| POST | `/export/docx` | 导出 Word（含图表） |
| GET | `/export/excel` | 导出 Excel |
| GET | `/export/pdf` | 导出 PDF（无图表） |
| POST | `/export/pdf` | 导出 PDF（含图表） |
| POST | `/export/pptx` | 导出 PPTX（含图表） |

## 统计分析报告（16 项）

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
- 时间序列（自动检测日期字段，日/月/年聚合）
- 异常值检测（IQR + Z-Score 双方法）
- 字段类型分布

## 前端功能

### 应用生命周期

```
选择文件 → 配置模块 → 上传解析 → 配置图表 → 数据筛选 → 可视化分析
```

### 核心功能

- **文件上传**: 支持 .csv / .xlsx
- **分析选项对话框**: 选择展示模块（预览摘要/分析报告/样例数据/图表分析），支持 dialog / drawer 两种样式
- **预览摘要卡片**: 文件名、行数、列数、字段列表（展开/折叠）
- **统计报告表格**: 字段级统计（类型、缺失数、缺失率、均值、标准差、最值）
- **17 种图表分析类别**:

| 类别 | 图表类型 | 说明 |
|------|----------|------|
| 缺失率 | 柱/线 | 各字段缺失率百分比 |
| 缺失热力图 | 热力图 | 缺失值矩阵 |
| 字段类型分布 | 柱/线 | 各数据类型字段数量 |
| 特征分布 | 直方图+分布曲线 | 数值字段分布，支持动态分箱 |
| 频次分布 | 柱/线 | 分类字段 Top N |
| 帕累托分析 | 帕累托图 | Top 20 + 累计曲线 |
| 箱线图 | 箱线图 | 五数概括 |
| 相关性热力图 | 热力图 | 皮尔逊相关系数矩阵 |
| 分组统计 | 柱/线 | 分类 × 数值交叉聚合（均值/最大/最小） |
| 分箱统计 | 柱/线 | 等宽/等频分箱 |
| 小提琴图 | 密度图 | KDE 密度分布 |
| 散点图 | 散点图 | X/Y 轴字段选择 |
| 时间序列 | 折线 | 日/月/年聚合周期 |
| 异常值检测 | 柱/线 | IQR / Z-Score 双方法 |
| 数值均值/最大/最小 | 柱/线 | 数值字段汇总指标 |

- **数据筛选（弹窗）**: 字段勾选（include_fields）+ 数值范围双滑块，应用后实时更新报告与图表
- **全选/取消**: 字段列表支持一键全选或全取消
- **对比模式**: 多字段直方图叠加对比
- **图表工具栏**: 展开/收起选项、数据筛选、对比模式、下载 PNG/SVG、图表指标配置
- **图表下载**: PNG / SVG 格式
- **清洗增强**: 模板化清洗、类型建议、字段质量评分、清洗前后对比、清洗日志导出
- **版本历史**: 版本列表、加载指定版本、版本对比
- **报告导出**: Word/PDF/PPTX 支持图表嵌入，Excel 增强格式
- **中英文切换**: 145+ 个 i18n key
- **弹窗样式切换**: 对话框（居中模态）/ 抽屉（右侧滑入）
- **响应式布局**: 适配 720px 以下设备

### 性能优化

- ECharts 动态导入（懒加载 1MB+ 按需加载）
- 主应用包 172 KB（gzip 59 KB）
- `App.vue` 从 1640 行精简至 279 行（-95%）
- 图表渲染通过 composable 响应式 watch 联动

## 启动方式

### 前置要求

- Python 3.9 - 3.13（最低支持 3.9，Docker 默认 3.13）
- Node.js 18+
- PostgreSQL 12+（可选，仅数据库持久化、历史记录与自动入库需要；推荐 16+）

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

可选：PostgreSQL 配置（用于历史记录、版本持久化和自动入库）。如果不配置或 PostgreSQL 未启动，上传、分析、清洗、特征工程和建模仍可运行，但历史记录会降级为空。

```bash
# Windows PowerShell
$env:POSTGRES_HOST="localhost"
$env:POSTGRES_PORT="5432"
$env:POSTGRES_USER="postgres"
$env:POSTGRES_PASSWORD="123456"
$env:POSTGRES_DB="dataflowbi"
```

也可以复制 `backend/.env.example` 为 `backend/.env` 后修改配置。

可选：自动入库开启（混合持久化）

```bash
# 自动入库（PostgreSQL 可用时）
$env:AUTO_IMPORT_DB="1"
# 入库表冲突策略：replace 或 append
$env:IMPORT_IF_EXISTS="replace"
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

如需自定义后端地址，设置环境变量 `VITE_API_BASE_URL=http://localhost:8000`。

### Docker（可选）

`docker-compose.yml` 使用 PostgreSQL 16 Alpine、Python 3.13 后端镜像和 Nginx 前端镜像：

```bash
docker compose up --build
```

## 使用流程

1. 先后启动后端和前端服务
2. 浏览器访问 `http://localhost:5173/`
3. 点击「选择文件」选择 CSV/XLSX 文件 → 点击「开始解析」
4. 弹出选择窗口：勾选需要展示的模块（预览摘要/分析报告/样例数据/启用图表）
5. 确认后自动上传并解析；解析完成即进入图表区
6. 如需调整图表类型，点击「统计分析指标设置」按钮勾选启用的分析类别
7. 点击「展开可视化选项」→ 左侧选分析类别，右侧选图形类型与字段
8. 如需筛选数据，点击工具栏「数据筛选」打开筛选弹窗 → 勾选字段/调整滑块 → 应用
9. 切换语言或弹窗样式：右上角「设置」
10. 下载图表：工具栏 PNG/SVG 按钮

## API 示例

```bash
# 健康检查
curl http://localhost:8000/health

# 文件上传
curl -F "file=@./sample.csv" http://localhost:8000/upload
```

## 测试

### 后端单元测试

```bash
cd backend
pytest
```

### 前端单元测试

```bash
cd frontend
npm run test
```

### E2E（Playwright）

确保前后端已启动后执行：

```bash
cd frontend
npm run test:e2e:playwright
```

### 性能测试（可选）

```bash
cd backend
set PERF_TESTS=1
pytest -m performance
```

## 文档

- [docs/overview.md](docs/overview.md)
- [docs/api.md](docs/api.md)
- [docs/export.md](docs/export.md)
- [docs/testing.md](docs/testing.md)

## 后续规划

- 权限与多租户
- 审计与操作日志
- 模块化报表模板与主题
- 任务调度与定时报告
- 更细粒度的数据血缘与版本对比
