# 报告导出说明

## 图表嵌入（Word/PDF/PPTX）

导出接口支持传入图表图片的 data_url（Base64）：

```json
{
  "saved_name": "...",
  "filename": "report",
  "charts": [
    {
      "title": "Histogram",
      "data_url": "data:image/png;base64,...."
    }
  ]
}
```

- data_url 支持 image/png 或 image/jpeg
- 未提供图表时，将输出纯文本版本

## Excel 格式增强

- 表头加粗与底色
- 自适应列宽（最大 40）
- 多 sheet 输出
