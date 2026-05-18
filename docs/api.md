# API 说明

以下为主要端点与用途，完整参数参考前端调用或后端代码。

## 基础

- GET /health

## 上传与分析

- POST /upload
- POST /filter
- POST /rebin

## 清洗

- POST /clean
- GET /clean/templates

## 历史与版本

- GET /history
- GET /history/{id}
- POST /history/{id}/reload
- GET /history/{id}/versions
- GET /history/compare?from_id=1&to_id=2
- POST /history/{id}/import

## 导出

- GET /export/docx
- POST /export/docx
- GET /export/excel
- GET /export/pdf
- POST /export/pdf
- POST /export/pptx

## 导出示例（含图表）

```bash
curl -X POST http://localhost:8000/export/docx \
  -H "Content-Type: application/json" \
  -d '{"saved_name":"abc.csv","filename":"report","charts":[{"title":"Missing Rate","data_url":"data:image/png;base64,..."}]}'
```
