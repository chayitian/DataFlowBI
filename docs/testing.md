# 测试说明

## Python 支持范围

- 后端最低支持 Python 3.9。
- 当前主开发环境可使用 Python 3.13。
- PostgreSQL 持久化需要安装并启动 PostgreSQL；未启动时历史记录接口会降级，但上传、分析、清洗、特征工程和建模仍可测试。

## 后端单元测试

```bash
cd backend
pytest
```

## 前端单元测试

```bash
cd frontend
npm run test
```

## E2E（Playwright）

先启动后端与前端：

```bash
cd backend
uvicorn app.main:app --reload

cd ../frontend
npm run dev
```

然后运行：

```bash
npm run test:e2e:playwright
```

## 性能测试（可选）

```bash
cd backend
set PERF_TESTS=1
pytest -m performance
```
