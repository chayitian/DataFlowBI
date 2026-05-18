# 测试说明

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

## E2E（Playwright / Cypress）

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
npm run test:e2e:cypress
```

## 性能测试（可选）

```bash
cd backend
set PERF_TESTS=1
pytest -m performance
```
# 测试说明

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

## E2E（Playwright / Cypress）

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
npm run test:e2e:cypress
```

## 性能测试（可选）

```bash
cd backend
set PERF_TESTS=1
pytest -m performance
```
