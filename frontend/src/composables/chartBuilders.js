import { useI18n } from "./useI18n";

const { t } = useI18n();

export const MAX_CHART_FIELDS = 12;
export const BAR_COLOR = "#f26b38";
export const LINE_COLOR = "#1da1a7";

export const toNumber = (value) => {
  const n = Number(value);
  return Number.isNaN(n) ? 0 : n;
};

export const buildBarOption = (categories, values, unit, color) => ({
  tooltip: { trigger: "axis" },
  grid: { left: 20, right: 20, top: 20, bottom: 40, containLabel: true },
  xAxis: { type: "category", data: categories, axisLabel: { rotate: 25 } },
  yAxis: { type: "value", axisLabel: { formatter: unit ? `{value}${unit}` : "{value}" } },
  series: [{ type: "bar", data: values, itemStyle: { color: color || BAR_COLOR }, barMaxWidth: 36 }],
});

export const buildLineOption = (categories, values, unit, color) => ({
  tooltip: { trigger: "axis" },
  grid: { left: 20, right: 20, top: 20, bottom: 40, containLabel: true },
  xAxis: { type: "category", data: categories, axisLabel: { rotate: 25 } },
  yAxis: { type: "value", axisLabel: { formatter: unit ? `{value}${unit}` : "{value}" } },
  series: [{
    type: "line", data: values, smooth: true, symbol: "circle", symbolSize: 8,
    lineStyle: { color: color || LINE_COLOR, width: 3 },
    itemStyle: { color: color || LINE_COLOR },
    areaStyle: { color: "rgba(29, 161, 167, 0.15)" },
  }],
});

export const buildHistogramOption = (report, feature) => {
  const histogram = report?.histograms?.[feature];
  if (!histogram || !histogram.bins?.length || !histogram.counts?.length) return null;
  const labels = histogram.bins.slice(0, -1).map((v, i) => `${Number(v).toFixed(2)} - ${Number(histogram.bins[i + 1]).toFixed(2)}`);
  return {
    tooltip: { trigger: "axis" },
    grid: { left: 20, right: 20, top: 20, bottom: 40, containLabel: true },
    xAxis: { type: "category", data: labels, axisLabel: { rotate: 25 } },
    yAxis: { type: "value" },
    series: [
      { type: "bar", data: histogram.counts, itemStyle: { color: BAR_COLOR }, barMaxWidth: 36 },
      { type: "line", data: histogram.counts, smooth: true, symbol: "circle", symbolSize: 8, lineStyle: { color: LINE_COLOR, width: 3 }, itemStyle: { color: LINE_COLOR } },
    ],
  };
};

export const buildNumericOption = (report, metricKey, type) => {
  const summary = report?.numeric_summary || {};
  const entries = Object.entries(summary).slice(0, MAX_CHART_FIELDS);
  if (!entries.length) return null;
  const categories = entries.map(([f]) => f);
  const values = entries.map(([, s]) => toNumber(s?.[metricKey]));
  return type === "line" ? buildLineOption(categories, values, "", LINE_COLOR) : buildBarOption(categories, values, "", BAR_COLOR);
};

export const buildMissingRateOption = (report, type) => {
  const entries = Object.entries(report?.missing_rate || {}).slice(0, MAX_CHART_FIELDS);
  if (!entries.length) return null;
  const categories = entries.map(([f]) => f);
  const values = entries.map(([, v]) => toNumber(v) * 100);
  return type === "line" ? buildLineOption(categories, values, "%", LINE_COLOR) : buildBarOption(categories, values, "%", BAR_COLOR);
};

export const buildTypeDistributionOption = (report, type) => {
  const dtypes = report?.dtypes || {};
  const counts = {};
  Object.values(dtypes).forEach((d) => { counts[d] = (counts[d] || 0) + 1; });
  const entries = Object.entries(counts);
  if (!entries.length) return null;
  const labels = entries.map(([d]) => d);
  const values = entries.map(([, c]) => c);
  return type === "line" ? buildLineOption(labels, values, "", LINE_COLOR) : buildBarOption(labels, values, "", BAR_COLOR);
};

export const buildFrequencyOption = (report, field, type) => {
  const data = report?.frequencies?.[field];
  if (!data?.length) return null;
  const categories = data.map((d) => String(d.value));
  const values = data.map((d) => d.count);
  return type === "line" ? buildLineOption(categories, values, "", LINE_COLOR) : buildBarOption(categories, values, "", BAR_COLOR);
};

export const buildParetoOption = (report, field) => {
  const data = report?.pareto?.[field];
  if (!data?.length) return null;
  const categories = data.map((_, i) => `#${i + 1}`);
  const values = data.map((d) => d.value);
  const cumPcts = data.map((d) => Number((d.cum_pct * 100).toFixed(1)));
  return {
    tooltip: { trigger: "axis" },
    grid: { left: 20, right: 20, top: 30, bottom: 40, containLabel: true },
    xAxis: { type: "category", data: categories, axisLabel: { rotate: 25 } },
    yAxis: [{ type: "value", name: t("analysisPareto") }, { type: "value", name: "%", max: 100 }],
    series: [
      { type: "bar", data: values, itemStyle: { color: BAR_COLOR }, barMaxWidth: 36 },
      { type: "line", data: cumPcts, smooth: true, yAxisIndex: 1, symbol: "circle", symbolSize: 8, lineStyle: { color: LINE_COLOR, width: 3 }, itemStyle: { color: LINE_COLOR }, areaStyle: { color: "rgba(29, 161, 167, 0.15)" } },
    ],
  };
};

export const buildBoxplotOption = (report) => {
  const data = report?.boxplot || {};
  const entries = Object.entries(data).slice(0, MAX_CHART_FIELDS);
  if (!entries.length) return null;
  const categories = entries.map(([f]) => f);
  const boxData = entries.map(([, s]) => [s.min, s.q1, s.median, s.q3, s.max]);
  const outliers = entries.map(([, s]) => s.outliers || []);
  return {
    tooltip: { trigger: "axis" },
    grid: { left: 20, right: 20, top: 20, bottom: 40, containLabel: true },
    xAxis: { type: "category", data: categories, axisLabel: { rotate: 25 } },
    yAxis: { type: "value" },
    series: [
      { name: "boxplot", type: "boxplot", data: boxData, itemStyle: { color: BAR_COLOR }, tooltip: { formatter: (p) => { const d = data[p.name]; return d ? `${p.name}<br/>Min: ${d.min}<br/>Q1: ${d.q1}<br/>Median: ${d.median}<br/>Q3: ${d.q3}<br/>Max: ${d.max}` : p.name; } } },
      { name: "outliers", type: "scatter", data: outliers.flatMap((list, i) => list.map((v) => [i, v])), symbolSize: 6, itemStyle: { color: "#e74c3c" } },
    ],
  };
};

export const buildCorrelationOption = (report) => {
  const corr = report?.correlation;
  if (!corr || !corr.fields?.length || !corr.matrix?.length) return null;
  const fields = corr.fields;
  const matrix = corr.matrix;
  const data = [];
  for (let i = 0; i < fields.length; i++) {
    for (let j = 0; j < fields.length; j++) {
      const val = matrix[i]?.[j];
      if (val !== null && val !== undefined) data.push([i, j, val]);
    }
  }
  return {
    tooltip: { formatter: (p) => `${fields[p.value[0]]} × ${fields[p.value[1]]}<br/>${p.value[2].toFixed(4)}` },
    grid: { left: 60, right: 20, top: 20, bottom: 60 },
    xAxis: { type: "category", data: fields, axisLabel: { rotate: 45 }, splitArea: { show: true } },
    yAxis: { type: "category", data: fields, splitArea: { show: true } },
    visualMap: { min: -1, max: 1, calculable: true, orient: "vertical", right: 0, top: 20, inRange: { color: ["#1da1a7", "#ffffff", "#f26b38"] } },
    series: [{ type: "heatmap", data, label: { show: fields.length <= 8, formatter: (p) => p.value[2].toFixed(2) }, emphasis: { itemStyle: { shadowBlur: 10, shadowColor: "rgba(0,0,0,0.3)" } } }],
  };
};

export const buildGroupStatsOption = (report, groupField, agg) => {
  const gs = report?.group_stats;
  if (!gs || !gs.data?.[groupField]) return null;
  const groupData = gs.data[groupField];
  const groups = Object.keys(groupData);
  const numericFields = gs.numeric_fields || [];
  const allStats = {};
  for (const gf of groups) {
    for (const nf of numericFields) {
      const s = groupData[gf]?.[nf];
      if (s && s[agg] !== null && s[agg] !== undefined) {
        if (!allStats[nf]) allStats[nf] = {};
        allStats[nf][gf] = s[agg];
      }
    }
  }
  const nfEntries = Object.entries(allStats).slice(0, MAX_CHART_FIELDS);
  if (!nfEntries.length) return null;
  return {
    tooltip: { trigger: "axis" },
    grid: { left: 20, right: 20, top: 20, bottom: 40, containLabel: true },
    xAxis: { type: "category", data: groups, axisLabel: { rotate: 25 } },
    yAxis: { type: "value" },
    series: nfEntries.map(([field, groupVals], i) => ({
      name: field, type: "bar", data: groups.map((g) => groupVals[g] ?? null), barMaxWidth: 24,
      itemStyle: { color: i % 2 === 0 ? BAR_COLOR : LINE_COLOR },
    })),
  };
};

export const buildBinningOption = (report, field, method) => {
  const binData = report?.binning?.[field]?.[method];
  if (!binData || !binData.bins?.length) return null;
  const labels = binData.bins.slice(0, -1).map((start, idx) => `${Number(start).toFixed(2)} - ${Number(binData.bins[idx + 1]).toFixed(2)}`);
  return {
    tooltip: { trigger: "axis" },
    grid: { left: 20, right: 20, top: 20, bottom: 40, containLabel: true },
    xAxis: { type: "category", data: labels, axisLabel: { rotate: 25 } },
    yAxis: { type: "value" },
    series: [{ type: "bar", data: binData.counts, itemStyle: { color: BAR_COLOR }, barMaxWidth: 36 }],
  };
};

export const buildViolinOption = (report, field) => {
  const v = report?.violin?.[field];
  if (!v || !v.density_x?.length) return null;
  const left = v.density_x.map((x, i) => [-v.density_y[i], x]);
  const right = v.density_x.map((x, i) => [v.density_y[i], x]);
  return {
    tooltip: { trigger: "axis", formatter: (p) => `${field}<br/>${p[0].name}` },
    grid: { left: 50, right: 20, top: 20, bottom: 40 },
    xAxis: { type: "value", name: t("chartTypeViolin") },
    yAxis: { type: "value", name: t("fieldLabel") },
    series: [
      { type: "scatter", data: left, symbol: "none", areaStyle: { color: BAR_COLOR, opacity: 0.3 }, step: "end" },
      { type: "scatter", data: right, symbol: "none", areaStyle: { color: BAR_COLOR, opacity: 0.3 }, step: "start" },
      { type: "line", data: left, smooth: true, symbol: "none", lineStyle: { color: BAR_COLOR, width: 2 } },
      { type: "line", data: right, smooth: true, symbol: "none", lineStyle: { color: BAR_COLOR, width: 2 } },
    ],
  };
};

export const buildScatterOption = (report, xField, yField) => {
  const data = report?.scatter_matrix?.data;
  if (!data?.length || !xField || !yField) return null;
  const points = data.filter((d) => d[xField] != null && d[yField] != null).slice(0, 1000).map((d) => [Number(d[xField]), Number(d[yField])]);
  if (!points.length) return null;
  return {
    tooltip: { formatter: (p) => `${xField}: ${p.value[0]}<br/>${yField}: ${p.value[1]}` },
    grid: { left: 50, right: 20, top: 20, bottom: 50 },
    xAxis: { type: "value", name: xField },
    yAxis: { type: "value", name: yField },
    series: [{ type: "scatter", data: points, symbolSize: 6, itemStyle: { color: BAR_COLOR, opacity: 0.6 } }],
  };
};

export const buildMissingHeatmapOption = (report) => {
  const hm = report?.missing_heatmap;
  if (!hm || !hm.data?.length) return null;
  const data = [];
  for (let r = 0; r < hm.data.length; r++)
    for (let c = 0; c < hm.data[r].length; c++)
      if (hm.data[r][c]) data.push([c, r, 1]);
  const fields = hm.fields || [];
  const nRows = hm.rows || hm.data.length;
  return {
    tooltip: { formatter: (p) => `${t("fieldLabel")}: ${fields[p.value[0]] || "?"}<br/>${t("rows")}: ${p.value[1] + 1}` },
    grid: { left: 60, right: 30, top: 20, bottom: 60 },
    xAxis: { type: "category", data: fields, axisLabel: { rotate: 45 }, splitArea: { show: true } },
    yAxis: { type: "category", data: Array.from({ length: nRows }, (_, i) => i + 1), show: false },
    visualMap: { min: 0, max: 1, calculable: false, inRange: { color: ["#e8f5e9", "#e74c3c"] }, show: false },
    series: [{ type: "heatmap", data, label: { show: false }, emphasis: { itemStyle: { shadowBlur: 10 } } }],
  };
};

export const buildTimeseriesOption = (report, field, period) => {
  const ts = report?.timeseries?.[field]?.[period];
  if (!ts || !ts.dates?.length) return null;
  return {
    tooltip: { trigger: "axis" },
    grid: { left: 20, right: 20, top: 20, bottom: 50 },
    xAxis: { type: "category", data: ts.dates, axisLabel: { rotate: 45 } },
    yAxis: { type: "value" },
    series: [{ type: "line", data: ts.values, smooth: true, symbol: "circle", symbolSize: 6, lineStyle: { color: LINE_COLOR, width: 2 }, itemStyle: { color: LINE_COLOR }, areaStyle: { color: "rgba(29, 161, 167, 0.15)" } }],
  };
};

export const buildOutliersOption = (report, field) => {
  const o = report?.outliers?.[field];
  if (!o) return null;
  return {
    tooltip: { trigger: "axis" },
    grid: { left: 20, right: 20, top: 30, bottom: 40 },
    xAxis: { type: "category", data: [t("outlierIQR"), t("outlierZScore")] },
    yAxis: { type: "value" },
    series: [{ type: "bar", data: [o.iqr.count, o.zscore.count], itemStyle: { color: BAR_COLOR }, barMaxWidth: 48, label: { show: true, position: "top", fontWeight: "bold" } }],
  };
};

export const buildComparisonHistogramOption = (report, fields) => {
  if (!fields.length) return null;
  const colors = [BAR_COLOR, LINE_COLOR, "#9b59b6", "#2ecc71", "#f39c12", "#e74c3c", "#3498db", "#1abc9c"];
  const series = [];
  for (let i = 0; i < fields.length; i++) {
    const h = report?.histograms?.[fields[i]];
    if (!h || !h.bins?.length) continue;
    series.push({
      name: fields[i], type: "bar", data: h.counts, barMaxWidth: Math.max(8, 24 - fields.length * 2),
      itemStyle: { color: colors[i % colors.length], opacity: 0.75 },
    });
  }
  if (!series.length) return null;
  return {
    tooltip: { trigger: "axis" },
    grid: { left: 20, right: 20, top: 30, bottom: 40, containLabel: true },
    xAxis: { type: "category", data: series[0] ? Object.keys(series[0].data).map(() => "") : [], axisLabel: { rotate: 25 } },
    yAxis: { type: "value" },
    series,
  };
};
