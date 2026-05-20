# Project Guide

这份导览用于快速读懂 DataFlowBI 的代码结构。代码里的注释主要解释“为什么这样做”和“数据怎么流动”，不是逐行翻译语法。

## Overall Flow

1. 前端 `frontend/src/App.vue` 选择文件并调用上传接口。
2. 后端 `backend/app/api/upload.py` 接收文件，交给 `file_preview.py` 保存、解析、生成预览报告。
3. 后端把 DataFrame 放进 `DATA_CACHE`，同时把快照文件保存到 `backend/uploads`。
4. PostgreSQL 可用时，`upload_records` 表记录历史版本；不可用时，上传和预览仍可继续使用。
5. 清洗、特征工程、机器学习、导出都通过 `saved_name` 找到当前缓存数据。
6. 清洗和特征工程会生成新的快照文件，不会覆盖用户上传的原始 CSV/XLSX。

## Backend Map

- `backend/app/main.py`: FastAPI 应用入口，注册路由、CORS、错误处理、数据库初始化。
- `backend/app/api/`: HTTP 接口层，只做参数校验和调用 service。
- `backend/app/services/file_preview.py`: 上传解析、预览、过滤、清洗、缓存和快照保存。
- `backend/app/services/report_builder.py`: 生成统计报告和图表所需数据。
- `backend/app/services/feature_engineering.py`: 标准化、归一化、独热编码、日期拆分。
- `backend/app/services/ml_service.py`: 数据划分、sklearn 预处理、模型训练、指标输出。
- `backend/app/services/export_service.py`: Word/PDF/Excel/PPT 导出。
- `backend/app/database/db.py`: PostgreSQL 连接配置和 SQLAlchemy session。
- `backend/app/database/init_db.py`: 创建/升级历史记录表。
- `backend/app/models/upload_record.py`: 历史记录表模型。

## Frontend Map

- `frontend/src/App.vue`: 页面总装配，连接上传、图表、清洗、特征工程、历史、导出和机器学习。
- `frontend/src/composables/useFileUpload.js`: 当前数据集、预览、过滤、历史加载状态。
- `frontend/src/composables/useChart.js`: 图表选择状态、ECharts 懒加载和渲染。
- `frontend/src/composables/chartBuilders.js`: 把后端 report 转成 ECharts option。
- `frontend/src/components/CleanPanel.vue`: 清洗弹窗，只收集清洗规则。
- `frontend/src/components/FeatureEngineeringDialog.vue`: 特征工程弹窗，只收集生成规则。
- `frontend/src/components/MachineLearningDialog.vue`: 建模弹窗，只收集模型配置。
- `frontend/src/api/`: axios API 包装，避免组件里散落 URL。

## Key Concepts

- `saved_name`: 后端缓存和快照文件名，是前后端后续操作的关键 ID。
- `DATA_CACHE`: 后端进程内存缓存，速度快但重启会丢；历史 reload 可以从磁盘快照恢复。
- `dataset_id` / `version`: 同一个数据集的不同版本，用于原始、清洗后、特征工程后的历史链路。
- `report`: 后端生成的分析包，前端表格、图表和导出都复用它。
- `filter_info`: 每个字段的类型、范围、候选值和类型建议，清洗/筛选/ML 弹窗都会用到。

## Vite Chunk Warning

`npm run build` 里的 chunk size warning 是构建体积提示，不是运行错误。

当前前端使用 ECharts，它本身比较大。Vite/Rollup 打包后发现某个输出 JS chunk 超过默认的 `500 kB` 提醒阈值，于是提示可以考虑代码分割。项目已经在 `useChart.js` 中用 `import("echarts")` 做了懒加载，所以用户不打开图表时不会立刻加载 ECharts。构建仍然可能提示该异步 chunk 很大，因为 ECharts 代码本身大。

这个 warning 的影响：

- 不会导致构建失败。
- 不会导致页面不能运行。
- 主要影响首次打开图表时需要下载较大的 ECharts chunk。

如果后续要优化，可以按需引入 ECharts 图表模块，或进一步拆分图表功能；目前对功能正确性没有影响。
