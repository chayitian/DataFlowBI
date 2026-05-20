import { exportReportDocx, exportReportExcel, exportReportPdf, exportReportPptx } from "../api/upload";

export function useExport({ savedName, preview, chartInstance, hasChartData, currentChartTitle, errorMessage }) {
  const downloadBlob = (blob, filename) => {
    // 所有报告导出格式共用的浏览器下载辅助函数。
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const buildChartPayload = () => {
    // 导出接口接收由 ECharts 生成的图表 data URL。
    if (!chartInstance.value || !hasChartData.value) return [];
    const dataUrl = chartInstance.value.getDataURL({
      type: "png",
      pixelRatio: 2,
      backgroundColor: "#fff",
    });
    return [{ title: currentChartTitle.value || "Chart", data_url: dataUrl }];
  };

  const handleExportDocx = async () => {
    if (!savedName.value) return;
    try {
      const blob = await exportReportDocx(
        savedName.value,
        preview.value?.filename || "report",
        buildChartPayload()
      );
      downloadBlob(blob, `${preview.value?.filename || "report"}.docx`);
    } catch (e) {
      console.error("Word export failed:", e);
      errorMessage.value = e?.response?.data?.detail || "Word export failed";
    }
  };

  const handleExportExcel = async () => {
    if (!savedName.value) return;
    try {
      const blob = await exportReportExcel(savedName.value, preview.value?.filename || "report");
      downloadBlob(blob, `${preview.value?.filename || "report"}.xlsx`);
    } catch (e) {
      console.error("Excel export failed:", e);
      errorMessage.value = e?.response?.data?.detail || "Excel export failed";
    }
  };

  const handleExportPdf = async () => {
    if (!savedName.value) return;
    try {
      const blob = await exportReportPdf(
        savedName.value,
        preview.value?.filename || "report",
        buildChartPayload()
      );
      downloadBlob(blob, `${preview.value?.filename || "report"}.pdf`);
    } catch (e) {
      console.error("PDF export failed:", e);
      errorMessage.value = e?.response?.data?.detail || "PDF export failed";
    }
  };

  const handleExportPptx = async () => {
    if (!savedName.value) return;
    try {
      const blob = await exportReportPptx(
        savedName.value,
        preview.value?.filename || "report",
        buildChartPayload()
      );
      downloadBlob(blob, `${preview.value?.filename || "report"}.pptx`);
    } catch (e) {
      console.error("PPT export failed:", e);
      errorMessage.value = e?.response?.data?.detail || "PPT export failed";
    }
  };

  return {
    handleExportDocx,
    handleExportExcel,
    handleExportPdf,
    handleExportPptx,
  };
}
