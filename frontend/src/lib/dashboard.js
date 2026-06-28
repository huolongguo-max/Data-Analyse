import { AREA_OPTIONS, resolveAreaForProvince } from "./location-config";

export const SINGLE_FIELDS = {
  base: {
    reserve: "base_reserve_qty",
    forecast: "base_forecast_revenue",
    totalReserve: "base_total_reserve_qty",
    totalRevenue: "base_total_revenue",
    rate: "base_achievement_rate",
  },
  stretch: {
    reserve: "stretch_reserve_qty",
    forecast: "stretch_forecast_revenue",
    totalReserve: "stretch_total_reserve_qty",
    totalRevenue: "stretch_total_revenue",
    rate: "stretch_achievement_rate",
  },
};

export const SHEET_FIELDS = {
  base: {
    reserve: "保底储备量",
    forecast: "保底预测业绩",
    totalReserve: "保底总储备量",
    totalRevenue: "保底总预测业绩",
  },
  stretch: {
    reserve: "冲高储备量",
    forecast: "冲高预测业绩",
    totalReserve: "冲高总储备量",
    totalRevenue: "冲高总预测业绩",
  },
};

export const KEY_ALIASES = {
  courseLine: ["课线项目", "项目名称"],
  className: ["班期"],
  status: ["招生进度"],
  inboundQty: ["已进线量", "已进线"],
  achievedRevenue: ["已达成预测业绩"],
  targetRevenue: ["预测业绩目标"],
  area: ["片区"],
  province: ["省份"],
  city: ["城市"],
  district: ["区县"],
  bd: ["BD", "BD姓名"],
  acquisitionType: ["获客类型"],
  projectReliability: ["项目可靠程度"],
};

function sortText(left, right) {
  return String(left ?? "").localeCompare(String(right ?? ""), "zh-CN");
}

function groupBy(items, keyGetter) {
  const groups = new Map();
  items.forEach((item) => {
    const key = keyGetter(item);
    if (!groups.has(key)) {
      groups.set(key, []);
    }
    groups.get(key).push(item);
  });
  return groups;
}

function aggregateBy(items, keyGetter, builders) {
  const groups = groupBy(items, keyGetter);
  return [...groups.values()].map((group) => {
    const first = group[0];
    const row = {};
    Object.entries(builders).forEach(([key, builder]) => {
      row[key] = builder(group, first);
    });
    return row;
  });
}

function sumOf(key) {
  return (rows) => rows.reduce((sum, row) => sum + num(row[key]), 0);
}

function prependTotalRow(rows, totalRow) {
  return [totalRow, ...rows];
}

function appendTotalRow(rows, totalRow) {
  return [...rows, totalRow];
}

export function scenarioLabel(scenario) {
  return scenario === "stretch" ? "冲高" : "保底";
}

export function compareFieldNames(scenario) {
  const fields = SINGLE_FIELDS[scenario];
  return {
    reserve: fields.reserve,
    forecast: fields.forecast,
    totalReserve: fields.totalReserve,
    totalRevenue: fields.totalRevenue,
    rate: fields.rate,
  };
}

export function pick(row, aliases) {
  for (const alias of aliases) {
    const value = row?.[alias];
    if (value !== null && value !== undefined && String(value).trim() !== "") {
      return value;
    }
  }
  return "";
}

export function num(value) {
  if (value === null || value === undefined || value === "") {
    return 0;
  }
  if (typeof value === "number") {
    return Number.isFinite(value) ? value : 0;
  }
  const normalized = String(value).replaceAll(",", "").trim();
  if (normalized === "") {
    return 0;
  }
  const parsed = Number(normalized);
  return Number.isFinite(parsed) ? parsed : 0;
}

export function optionalNumber(value) {
  if (value === null || value === undefined || value === "") {
    return null;
  }
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

export function formatNumber(value) {
  if (value === null || value === undefined || value === "") {
    return "-";
  }
  return num(value).toLocaleString("zh-CN", {
    maximumFractionDigits: 0,
  });
}

export function formatSignedNumber(value) {
  const numeric = num(value);
  if (numeric > 0) {
    return `+${formatNumber(numeric)}`;
  }
  if (numeric < 0) {
    return `-${formatNumber(Math.abs(numeric))}`;
  }
  return "0";
}

export function formatRate(value) {
  if (value === null || value === undefined || value === "") {
    return "-";
  }
  return `${(num(value) * 100).toFixed(1)}%`;
}

export function formatSignedRate(value) {
  const numeric = num(value) * 100;
  if (numeric > 0) {
    return `+${numeric.toFixed(1)}%`;
  }
  if (numeric < 0) {
    return `-${Math.abs(numeric).toFixed(1)}%`;
  }
  return "0.0%";
}

function padDatePart(value) {
  return String(value).padStart(2, "0");
}

function parsePeriodCode(periodCode) {
  const matched = String(periodCode || "").trim().match(/^(\d{4})[-/](\d{1,2})$/);
  if (!matched) {
    return { year: "", month: "" };
  }
  return {
    year: matched[1],
    month: String(Number(matched[2])),
  };
}

export function formatDateOnly(value) {
  if (value === null || value === undefined || value === "") {
    return "-";
  }

  const raw = String(value).trim();
  const matched = raw.match(/^(\d{4})[-/](\d{1,2})[-/](\d{1,2})/);
  if (matched) {
    return `${matched[1]}-${padDatePart(matched[2])}-${padDatePart(matched[3])}`;
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return raw;
  }

  return `${date.getFullYear()}-${padDatePart(date.getMonth() + 1)}-${padDatePart(date.getDate())}`;
}

export function formatDateTime(value) {
  if (!value) {
    return "-";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return String(value);
  }
  return date.toLocaleString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function buildWorkbookBaseName(upload, fallbackPeriodCode = "") {
  const { year: fallbackYear, month: fallbackMonth } = parsePeriodCode(fallbackPeriodCode);
  const year = upload?.source_period_year || fallbackYear;
  const month = upload?.source_period_month || fallbackMonth;
  const record = String(upload?.source_record_mmdd || "").trim() || "未标注";

  if (!year || !month) {
    return `【${record}】全国储备摸底`;
  }

  return `【${record}】${year}年${month}月全国储备摸底`;
}

export function buildExportFilterLabel({ periodCode = "", upload = null, areas = [], area = areas.length ? areas.join("、") : "", provinces = [] } = {}) {
  const batchLabel = buildWorkbookBaseName(upload, periodCode) || periodCode || "未选择批次";
  const areaLabel = area || "全部区域";
  const provinceLabel = provinces.length ? provinces.join("、") : "全部省份";
  return [batchLabel, areaLabel, provinceLabel].join("_");
}

export function formatUploadLabel(upload, fallbackPeriodCode = "") {
  if (!upload && !fallbackPeriodCode) {
    return "-";
  }
  return buildWorkbookBaseName(upload, fallbackPeriodCode);
}

export function uploadRecordLabel(upload) {
  const record = String(upload?.source_record_mmdd || "").trim();
  return record || "未标注";
}

export function formatComparePairLabel(currentUpload, previousUpload = null) {
  if (!currentUpload) {
    return "暂无可对比班期";
  }
  if (!previousUpload) {
    return "当月首期，无上期对比";
  }
  return `${uploadRecordLabel(previousUpload)}-${uploadRecordLabel(currentUpload)}`;
}

export function formatUploadOptionLabel(upload, previousUpload = null, fallbackPeriodCode = "") {
  const label = formatUploadLabel(upload, fallbackPeriodCode);
  if (!previousUpload) {
    return `${label}（当月首期）`;
  }
  return `${label}（对比 ${formatComparePairLabel(upload, previousUpload)}）`;
}

export function deltaClass(value) {
  const numeric = num(value);
  if (numeric > 0) {
    return "delta-up";
  }
  if (numeric < 0) {
    return "delta-down";
  }
  return "delta-neutral";
}

export function maxAbs(values) {
  return values.reduce((maxValue, value) => Math.max(maxValue, Math.abs(num(value))), 0) || 1;
}

export function compareByOperator(value, operator, threshold) {
  if (threshold === null || threshold === undefined || Number.isNaN(threshold)) {
    return true;
  }
  switch (operator) {
    case ">":
      return value > threshold;
    case ">=":
      return value >= threshold;
    case "<":
      return value < threshold;
    case "<=":
      return value <= threshold;
    case "=":
      return value === threshold;
    default:
      return true;
  }
}

export function deltaCell(value, maxValue, rateOrOptions = false) {
  const numeric = num(value);
  const safeMax = maxValue || 1;
  const options = typeof rateOrOptions === "object" && rateOrOptions !== null
    ? rateOrOptions
    : { rate: Boolean(rateOrOptions) };
  const {
    rate = false,
    minAlpha = 0,
    maxAlpha = 0.34,
    gamma = 1,
  } = options;
  const normalized = Math.min(1, Math.abs(numeric) / safeMax);
  const intensity = normalized > 0 ? Math.pow(normalized, gamma) : 0;
  const alpha = intensity > 0 ? minAlpha + intensity * (maxAlpha - minAlpha) : 0;
  const background =
    numeric > 0
      ? `rgba(215, 66, 66, ${alpha})`
      : numeric < 0
        ? `rgba(31, 157, 99, ${alpha})`
        : "transparent";
  const display = rate ? formatSignedRate(numeric) : formatSignedNumber(numeric);
  return {
    html: `<span class="delta-cell ${deltaClass(numeric)}" style="background:${background}">${display}</span>`,
    sortValue: numeric,
  };
}

export function progressCell(value) {
  const numeric = num(value);
  const rate = Math.max(0, Math.min(1, numeric));
  return {
    html:
      `<div class="table-progress">` +
      `<span class="table-progress-text">${formatRate(numeric)}</span>` +
      `<span class="table-progress-track"><span class="table-progress-fill" style="width:${rate * 100}%"></span></span>` +
      `</div>`,
    sortValue: numeric,
  };
}

const DEFAULT_STATUS_STYLE_MAP = {
  "未启动": "not-started",
  "招生中": "in-progress",
  "已结束": "ended",
};

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

export function statusBadgeCell(status, statusStyles = {}) {
  const text = String(status || "").trim();
  if (!text || text === "-") {
    return "-";
  }
  const tone = statusStyles[text] || DEFAULT_STATUS_STYLE_MAP[text] || "default";
  return {
    html: `<span class="status-badge status-badge--${tone}">${escapeHtml(text)}</span>`,
  };
}

export function currentValue(row, fieldName) {
  if (!row) {
    return 0;
  }
  if (fieldName === "target_revenue") {
    return row.current_target_revenue ?? row.target_revenue ?? 0;
  }
  return row[`current_${fieldName}`] ?? row[fieldName] ?? 0;
}

export function previousValue(row, fieldName) {
  if (!row) {
    return 0;
  }
  return row[`previous_${fieldName}`] ?? 0;
}

export function diffValue(row, fieldName) {
  if (!row) {
    return 0;
  }
  return row[`diff_${fieldName}`] ?? 0;
}

export function normalizedCityLabel(row) {
  return pick(row, KEY_ALIASES.city)
    || pick(row, KEY_ALIASES.district)
    || pick(row, KEY_ALIASES.province)
    || "未填写城市";
}

export function getNationalRow(nationalRows, areaRows) {
  if (nationalRows?.[0]) {
    return nationalRows[0];
  }
  if (!areaRows?.length) {
    return null;
  }
  return areaRows.reduce(
    (acc, row) => ({
      target_revenue: num(acc.target_revenue) + num(row.target_revenue),
      achieved_revenue: num(acc.achieved_revenue) + num(row.achieved_revenue),
      inbound_qty: num(acc.inbound_qty) + num(row.inbound_qty),
      base_reserve_qty: num(acc.base_reserve_qty) + num(row.base_reserve_qty),
      base_forecast_revenue: num(acc.base_forecast_revenue) + num(row.base_forecast_revenue),
      base_total_reserve_qty: num(acc.base_total_reserve_qty) + num(row.base_total_reserve_qty),
      base_total_revenue: num(acc.base_total_revenue) + num(row.base_total_revenue),
      base_achievement_rate: 0,
      stretch_reserve_qty: num(acc.stretch_reserve_qty) + num(row.stretch_reserve_qty),
      stretch_forecast_revenue: num(acc.stretch_forecast_revenue) + num(row.stretch_forecast_revenue),
      stretch_total_reserve_qty: num(acc.stretch_total_reserve_qty) + num(row.stretch_total_reserve_qty),
      stretch_total_revenue: num(acc.stretch_total_revenue) + num(row.stretch_total_revenue),
      stretch_achievement_rate: 0,
    }),
    {
      target_revenue: 0,
      achieved_revenue: 0,
      inbound_qty: 0,
      base_reserve_qty: 0,
      base_forecast_revenue: 0,
      base_total_reserve_qty: 0,
      base_total_revenue: 0,
      base_achievement_rate: 0,
      stretch_reserve_qty: 0,
      stretch_forecast_revenue: 0,
      stretch_total_reserve_qty: 0,
      stretch_total_revenue: 0,
      stretch_achievement_rate: 0,
    }
  );
}

function mapSingleDimensionRow(row, fields) {
  return {
    name: row.dimension_name,
    areaName: row.area_name || "",
    targetRevenue: num(row.target_revenue),
    totalRevenue: num(row[fields.totalRevenue]),
    totalReserve: num(row[fields.totalReserve]),
    rate: num(row[fields.rate]),
    forecast: num(row[fields.forecast]),
    achieved: num(row.achieved_revenue),
    reserve: num(row[fields.reserve]),
    inbound: num(row.inbound_qty),
  };
}

export function buildAreaRows(rows, nationalRows, scenario) {
  const fields = SINGLE_FIELDS[scenario];
  const mapped = rows.map((row) => mapSingleDimensionRow(row, fields));
  const national = getNationalRow(nationalRows, rows);
  if (!national) {
    return mapped;
  }
  return [
    {
      name: "全国",
      areaName: "",
      targetRevenue: num(national.target_revenue),
      totalRevenue: num(national[fields.totalRevenue]),
      totalReserve: num(national[fields.totalReserve]),
      rate: num(national[fields.rate]),
      forecast: num(national[fields.forecast]),
      achieved: num(national.achieved_revenue),
      reserve: num(national[fields.reserve]),
      inbound: num(national.inbound_qty),
    },
    ...mapped,
  ];
}

export function buildAreaRowsFromProvinceRows(rows, areaNames = AREA_OPTIONS) {
  const provinceRows = rows.filter((row) => row.name !== "全国");
  const grouped = new Map();
  for (const row of provinceRows) {
    const areaName = row.areaName || resolveAreaForProvince(row.name);
    if (!areaName) {
      continue;
    }
    if (!grouped.has(areaName)) {
      grouped.set(areaName, {
        name: areaName,
        areaName: "",
        targetRevenue: 0,
        totalRevenue: 0,
        totalReserve: 0,
        forecast: 0,
        achieved: 0,
        reserve: 0,
        inbound: 0,
      });
    }
    const target = grouped.get(areaName);
    target.targetRevenue += num(row.targetRevenue);
    target.totalRevenue += num(row.totalRevenue);
    target.totalReserve += num(row.totalReserve);
    target.forecast += num(row.forecast);
    target.achieved += num(row.achieved);
    target.reserve += num(row.reserve);
    target.inbound += num(row.inbound);
  }

  return areaNames.map((areaName) => {
    const row = grouped.get(areaName);
    if (row) {
      return {
        ...row,
        rate: row.targetRevenue ? row.totalRevenue / row.targetRevenue : 0,
      };
    }
    return {
      name: areaName,
      areaName: "",
      targetRevenue: 0,
      totalRevenue: 0,
      totalReserve: 0,
      rate: 0,
      forecast: 0,
      achieved: 0,
      reserve: 0,
      inbound: 0,
    };
  });
}

export function buildProvinceRows(rows, scenario, nationalRows = [], areaRows = []) {
  const fields = SINGLE_FIELDS[scenario];
  const mapped = rows.map((row) => {
    const mappedRow = mapSingleDimensionRow(row, fields);
    return {
      ...mappedRow,
      areaName: mappedRow.areaName || resolveAreaForProvince(mappedRow.name),
    };
  });
  const national = getNationalRow(nationalRows, areaRows);
  if (!national) {
    return mapped;
  }
  return [
    {
      name: "全国",
      areaName: "-",
      targetRevenue: num(national.target_revenue),
      totalRevenue: num(national[fields.totalRevenue]),
      totalReserve: num(national[fields.totalReserve]),
      rate: num(national[fields.rate]),
      forecast: num(national[fields.forecast]),
      achieved: num(national.achieved_revenue),
      reserve: num(national[fields.reserve]),
      inbound: num(national.inbound_qty),
    },
    ...mapped,
  ];
}

export function buildBdRows(rows, scenario) {
  const fields = SINGLE_FIELDS[scenario];
  return rows.map((row) => ({
    name: String(row.dimension_name || "").trim(),
    areaName: row.area_name || resolveAreaForProvince(row.province_name) || "",
    targetRevenue: num(row.target_revenue),
    totalRevenue: num(row[fields.totalRevenue]),
    totalReserve: num(row[fields.totalReserve]),
    rate: num(row[fields.rate]),
    forecast: num(row[fields.forecast]),
    achieved: num(row.achieved_revenue),
    reserve: num(row[fields.reserve]),
    inbound: num(row.inbound_qty),
  }));
}

export function buildCompareDimensionRows(rows, nationalRows, scenario, options = {}) {
  const { includeNational = false } = options;
  const names = compareFieldNames(scenario);
  const mapped = rows.map((row) => ({
    name: row.dimension_name,
    areaName: row.area_name || resolveAreaForProvince(row.province_name) || null,
    targetRevenue: num(currentValue(row, "target_revenue")),
    currentInbound: num(currentValue(row, "inbound_qty")),
    previousInbound: num(previousValue(row, "inbound_qty")),
    inboundDiff: num(diffValue(row, "inbound_qty")),
    currentAchieved: num(currentValue(row, "achieved_revenue")),
    previousAchieved: num(previousValue(row, "achieved_revenue")),
    achievedDiff: num(diffValue(row, "achieved_revenue")),
    currentReserve: num(currentValue(row, names.reserve)),
    previousReserve: num(previousValue(row, names.reserve)),
    reserveQtyDiff: num(diffValue(row, names.reserve)),
    currentForecast: num(currentValue(row, names.forecast)),
    previousForecast: num(previousValue(row, names.forecast)),
    forecastDiff: num(diffValue(row, names.forecast)),
    currentTotalReserve: num(currentValue(row, names.totalReserve)),
    currentTotalRevenue: num(currentValue(row, names.totalRevenue)),
    currentRate: num(currentValue(row, names.rate)),
    previousTotalReserve: num(previousValue(row, names.totalReserve)),
    previousTotalRevenue: num(previousValue(row, names.totalRevenue)),
    previousRate: num(previousValue(row, names.rate)),
    reserveDiff: num(diffValue(row, names.totalReserve)),
    revenueDiff: num(diffValue(row, names.totalRevenue)),
    rateDiff: num(diffValue(row, names.rate)),
  }));

  if (!includeNational || !nationalRows?.[0]) {
    return mapped;
  }

  const national = nationalRows[0];
  return [
    {
      name: "全国",
      areaName: null,
      targetRevenue: num(currentValue(national, "target_revenue")),
      currentInbound: num(currentValue(national, "inbound_qty")),
      previousInbound: num(previousValue(national, "inbound_qty")),
      inboundDiff: num(diffValue(national, "inbound_qty")),
      currentAchieved: num(currentValue(national, "achieved_revenue")),
      previousAchieved: num(previousValue(national, "achieved_revenue")),
      achievedDiff: num(diffValue(national, "achieved_revenue")),
      currentReserve: num(currentValue(national, names.reserve)),
      previousReserve: num(previousValue(national, names.reserve)),
      reserveQtyDiff: num(diffValue(national, names.reserve)),
      currentForecast: num(currentValue(national, names.forecast)),
      previousForecast: num(previousValue(national, names.forecast)),
      forecastDiff: num(diffValue(national, names.forecast)),
      currentTotalReserve: num(currentValue(national, names.totalReserve)),
      currentTotalRevenue: num(currentValue(national, names.totalRevenue)),
      currentRate: num(currentValue(national, names.rate)),
      previousTotalReserve: num(previousValue(national, names.totalReserve)),
      previousTotalRevenue: num(previousValue(national, names.totalRevenue)),
      previousRate: num(previousValue(national, names.rate)),
      reserveDiff: num(diffValue(national, names.totalReserve)),
      revenueDiff: num(diffValue(national, names.totalRevenue)),
      rateDiff: num(diffValue(national, names.rate)),
    },
    ...mapped,
  ];
}

export function buildCompareAreaRowsFromProvinceRows(rows, areaNames = AREA_OPTIONS) {
  const provinceRows = rows.filter((row) => row.name !== "全国");
  const grouped = new Map();
  for (const row of provinceRows) {
    const areaName = row.areaName || resolveAreaForProvince(row.name);
    if (!areaName) {
      continue;
    }
    if (!grouped.has(areaName)) {
      grouped.set(areaName, {
        name: areaName,
        areaName: null,
        targetRevenue: 0,
        currentInbound: 0,
        previousInbound: 0,
        inboundDiff: 0,
        currentAchieved: 0,
        previousAchieved: 0,
        achievedDiff: 0,
        currentReserve: 0,
        previousReserve: 0,
        reserveQtyDiff: 0,
        currentForecast: 0,
        previousForecast: 0,
        forecastDiff: 0,
        currentTotalReserve: 0,
        currentTotalRevenue: 0,
        previousTotalReserve: 0,
        previousTotalRevenue: 0,
        reserveDiff: 0,
        revenueDiff: 0,
      });
    }
    const target = grouped.get(areaName);
    target.targetRevenue += num(row.targetRevenue);
    target.currentInbound += num(row.currentInbound);
    target.previousInbound += num(row.previousInbound);
    target.inboundDiff += num(row.inboundDiff);
    target.currentAchieved += num(row.currentAchieved);
    target.previousAchieved += num(row.previousAchieved);
    target.achievedDiff += num(row.achievedDiff);
    target.currentReserve += num(row.currentReserve);
    target.previousReserve += num(row.previousReserve);
    target.reserveQtyDiff += num(row.reserveQtyDiff);
    target.currentForecast += num(row.currentForecast);
    target.previousForecast += num(row.previousForecast);
    target.forecastDiff += num(row.forecastDiff);
    target.currentTotalReserve += num(row.currentTotalReserve);
    target.currentTotalRevenue += num(row.currentTotalRevenue);
    target.previousTotalReserve += num(row.previousTotalReserve);
    target.previousTotalRevenue += num(row.previousTotalRevenue);
    target.reserveDiff += num(row.reserveDiff);
    target.revenueDiff += num(row.revenueDiff);
  }

  return areaNames.map((areaName) => {
    const row = grouped.get(areaName);
    if (row) {
      return {
        ...row,
        currentRate: row.targetRevenue ? row.currentTotalRevenue / row.targetRevenue : 0,
        previousRate: row.targetRevenue ? row.previousTotalRevenue / row.targetRevenue : 0,
        rateDiff:
          (row.targetRevenue ? row.currentTotalRevenue / row.targetRevenue : 0)
          - (row.targetRevenue ? row.previousTotalRevenue / row.targetRevenue : 0),
      };
    }
    return {
      name: areaName,
      areaName: null,
      targetRevenue: 0,
      currentInbound: 0,
      previousInbound: 0,
      inboundDiff: 0,
      currentAchieved: 0,
      previousAchieved: 0,
      achievedDiff: 0,
      currentReserve: 0,
      previousReserve: 0,
      reserveQtyDiff: 0,
      currentForecast: 0,
      previousForecast: 0,
      forecastDiff: 0,
      currentTotalReserve: 0,
      currentTotalRevenue: 0,
      currentRate: 0,
      previousTotalReserve: 0,
      previousTotalRevenue: 0,
      previousRate: 0,
      reserveDiff: 0,
      revenueDiff: 0,
      rateDiff: 0,
    };
  });
}

function buildClassShareRow(courseLine, totals, overallTotals) {
  const ratio = (value, denominator) => (num(denominator) ? num(value) / num(denominator) : 0);
  return {
    rowType: "share",
    courseLine,
    className: "占比(全月)",
    status: "",
    reserve: ratio(totals.reserve, overallTotals.reserve),
    totalReserve: ratio(totals.totalReserve, overallTotals.totalReserve),
    inbound: ratio(totals.inbound, overallTotals.inbound),
    forecast: ratio(totals.forecast, overallTotals.forecast),
    totalRevenue: ratio(totals.totalRevenue, overallTotals.totalRevenue),
    achieved: ratio(totals.achieved, overallTotals.achieved),
  };
}

export function aggregateSingleClassTables(rows, scenario, options = {}) {
  const { overallTotals = null } = options;
  const fields = SHEET_FIELDS[scenario];
  const mappedRows = rows.map((row) => ({
    courseLine: pick(row, KEY_ALIASES.courseLine) || "未命名课线",
    className: formatDateOnly(pick(row, KEY_ALIASES.className) || "-"),
    status: pick(row, KEY_ALIASES.status) || "",
    inbound: num(pick(row, KEY_ALIASES.inboundQty)),
    achieved: num(pick(row, KEY_ALIASES.achievedRevenue)),
    reserve: num(row[fields.reserve]),
    totalReserve: num(row[fields.totalReserve]),
    forecast: num(row[fields.forecast]),
    totalRevenue: num(row[fields.totalRevenue]),
  }));

  const totalRows = appendTotalRow(
    aggregateBy(mappedRows, (row) => row.className, {
      className: (_rows, first) => first.className,
      reserve: sumOf("reserve"),
      totalReserve: sumOf("totalReserve"),
      inbound: sumOf("inbound"),
      forecast: sumOf("forecast"),
      totalRevenue: sumOf("totalRevenue"),
      achieved: sumOf("achieved"),
    }).sort((left, right) => sortText(left.className, right.className)),
    {
      className: "总计",
      reserve: sumOf("reserve")(mappedRows),
      totalReserve: sumOf("totalReserve")(mappedRows),
      inbound: sumOf("inbound")(mappedRows),
      forecast: sumOf("forecast")(mappedRows),
      totalRevenue: sumOf("totalRevenue")(mappedRows),
      achieved: sumOf("achieved")(mappedRows),
    }
  );

  const resolvedOverallTotals = overallTotals || {
    reserve: sumOf("reserve")(mappedRows),
    totalReserve: sumOf("totalReserve")(mappedRows),
    inbound: sumOf("inbound")(mappedRows),
    forecast: sumOf("forecast")(mappedRows),
    totalRevenue: sumOf("totalRevenue")(mappedRows),
    achieved: sumOf("achieved")(mappedRows),
  };

  const courseLineSections = [...groupBy(mappedRows, (row) => row.courseLine).entries()]
    .sort((left, right) => sortText(left[0], right[0]))
    .map(([name, values]) => ({
      name,
      rows: appendTotalRow(
        values.slice().sort((left, right) => sortText(left.className, right.className)),
        {
          courseLine: "总计",
          className: "-",
          status: "-",
          reserve: sumOf("reserve")(values),
          totalReserve: sumOf("totalReserve")(values),
          inbound: sumOf("inbound")(values),
          forecast: sumOf("forecast")(values),
          totalRevenue: sumOf("totalRevenue")(values),
          achieved: sumOf("achieved")(values),
        }
      ),
    }))
    .map((section) => {
      const totalRow = section.rows[section.rows.length - 1];
      return {
        ...section,
        rows: [...section.rows, buildClassShareRow(section.name, totalRow, resolvedOverallTotals)],
      };
    });

  return { totalRows, courseLineSections };
}

function mapCompareClassRows(rows, fields) {
  return rows.map((row) => ({
    courseLine: pick(row, KEY_ALIASES.courseLine) || "未命名课线",
    className: formatDateOnly(pick(row, KEY_ALIASES.className) || "-"),
    status: pick(row, KEY_ALIASES.status) || "",
    reserve: num(row[fields.reserve]),
    totalReserve: num(row[fields.totalReserve]),
    inbound: num(pick(row, KEY_ALIASES.inboundQty)),
    forecast: num(row[fields.forecast]),
    totalRevenue: num(row[fields.totalRevenue]),
    achieved: num(pick(row, KEY_ALIASES.achievedRevenue)),
  }));
}

function buildCompareRowsByKey(currentRows, previousRows, keyGetter, seedFromAnchor) {
  const currentMap = new Map(currentRows.map((row) => [keyGetter(row), row]));
  const previousMap = new Map(previousRows.map((row) => [keyGetter(row), row]));
  const keys = [...new Set([...currentMap.keys(), ...previousMap.keys()])].sort(sortText);

  return keys.map((key) => {
    const current = currentMap.get(key);
    const previous = previousMap.get(key);
    const anchor = current || previous;
    return {
      ...seedFromAnchor(anchor),
      currentTotalReserve: num(current?.totalReserve),
      currentTotalRevenue: num(current?.totalRevenue),
      previousTotalReserve: num(previous?.totalReserve),
      previousTotalRevenue: num(previous?.totalRevenue),
      reserveDiff: num(current?.totalReserve) - num(previous?.totalReserve),
      revenueDiff: num(current?.totalRevenue) - num(previous?.totalRevenue),
    };
  });
}

function buildCourseLineShare(currentRows, previousRows) {
  const courseLines = [...new Set([...currentRows.map((row) => row.courseLine), ...previousRows.map((row) => row.courseLine)])].sort(sortText);

  const buildMetricSegments = (rows, key) => {
    const grouped = aggregateBy(rows, (row) => row.courseLine, {
      label: (_rows, first) => first.courseLine,
      value: sumOf(key),
    });
    const valueMap = new Map(grouped.map((row) => [row.label, num(row.value)]));
    const total = grouped.reduce((sum, row) => sum + num(row.value), 0);
    return courseLines.map((label) => {
      const value = num(valueMap.get(label));
      return {
        label,
        value,
        pct: total ? value / total : 0,
      };
    });
  };

  const metricGroups = [
    {
      key: "reserve",
      title: "储备板块",
      metrics: [
        { key: "totalReserve", label: "总储备量" },
        { key: "reserve", label: "储备量" },
        { key: "inbound", label: "已进线量" },
      ],
    },
    {
      key: "performance",
      title: "业绩板块",
      metrics: [
        { key: "totalRevenue", label: "总预测业绩" },
        { key: "forecast", label: "预测业绩" },
        { key: "achieved", label: "已达成预测业绩" },
      ],
    },
  ];

  return metricGroups.map((group) => ({
    ...group,
    metrics: group.metrics.map((metric) => ({
      ...metric,
      current: buildMetricSegments(currentRows, metric.key),
      previous: buildMetricSegments(previousRows, metric.key),
    })),
  }));
}

export function aggregateCompareClassTables(currentRows, previousRows, scenario) {
  const fields = SHEET_FIELDS[scenario];
  const current = mapCompareClassRows(currentRows, fields);
  const previous = mapCompareClassRows(previousRows, fields);

  const totalRowsCore = buildCompareRowsByKey(
    aggregateBy(current, (row) => row.className, {
      className: (_rows, first) => first.className,
      totalReserve: sumOf("totalReserve"),
      totalRevenue: sumOf("totalRevenue"),
    }),
    aggregateBy(previous, (row) => row.className, {
      className: (_rows, first) => first.className,
      totalReserve: sumOf("totalReserve"),
      totalRevenue: sumOf("totalRevenue"),
    }),
    (row) => row.className,
    (row) => ({
      className: row.className,
      status: "-",
    })
  );

  const totalRows = appendTotalRow(totalRowsCore, {
    className: "总计",
    status: "-",
    currentTotalReserve: sumOf("currentTotalReserve")(totalRowsCore),
    currentTotalRevenue: sumOf("currentTotalRevenue")(totalRowsCore),
    previousTotalReserve: sumOf("previousTotalReserve")(totalRowsCore),
    previousTotalRevenue: sumOf("previousTotalRevenue")(totalRowsCore),
    reserveDiff: sumOf("reserveDiff")(totalRowsCore),
    revenueDiff: sumOf("revenueDiff")(totalRowsCore),
  });

  const courseLines = [...new Set([...current.map((row) => row.courseLine), ...previous.map((row) => row.courseLine)])].sort(sortText);
  const sections = courseLines.map((courseLine) => {
    const currentScoped = current.filter((row) => row.courseLine === courseLine);
    const previousScoped = previous.filter((row) => row.courseLine === courseLine);
    const sectionRowsCore = buildCompareRowsByKey(
      currentScoped,
      previousScoped,
      (row) => row.className,
      (row) => ({
        className: row.className,
        status: row.status,
      })
    );
    return {
      courseLine,
      rows: appendTotalRow(sectionRowsCore, {
        className: "总计",
        status: "-",
        currentTotalReserve: sumOf("currentTotalReserve")(sectionRowsCore),
        currentTotalRevenue: sumOf("currentTotalRevenue")(sectionRowsCore),
        previousTotalReserve: sumOf("previousTotalReserve")(sectionRowsCore),
        previousTotalRevenue: sumOf("previousTotalRevenue")(sectionRowsCore),
        reserveDiff: sumOf("reserveDiff")(sectionRowsCore),
        revenueDiff: sumOf("revenueDiff")(sectionRowsCore),
      }),
    };
  });

  const allRows = [
    ...totalRows,
    ...sections.flatMap((section) => section.rows),
  ];

  return {
    totalRows,
    sections,
    share: buildCourseLineShare(current, previous),
    maxReserveDiff: maxAbs(allRows.map((row) => row.reserveDiff)),
    maxRevenueDiff: maxAbs(allRows.map((row) => row.revenueDiff)),
  };
}

export function aggregateAreaCourseLine(rows, scenario, areaNames = AREA_OPTIONS) {
  const fields = SHEET_FIELDS[scenario];
  const scopedRows = rows.map((row) => ({
    areaName: pick(row, KEY_ALIASES.area) || "未填写片区",
    courseLine: pick(row, KEY_ALIASES.courseLine) || "未命名课线",
    reserve: num(row[fields.reserve]),
    forecast: num(row[fields.forecast]),
  }));

  const grouped = aggregateBy(scopedRows, (row) => `${row.areaName}__${row.courseLine}`, {
    areaName: (_rows, first) => first.areaName,
    courseLine: (_rows, first) => first.courseLine,
    reserve: sumOf("reserve"),
    forecast: sumOf("forecast"),
  });

  const courseLines = [...new Set(grouped.map((row) => row.courseLine))].sort(sortText);
  const areaOrder = areaNames.length ? [...areaNames] : [...AREA_OPTIONS];
  const valueMap = new Map(grouped.map((row) => [`${row.areaName}__${row.courseLine}`, row]));

  const byReserve = areaOrder.map((areaName) => ({
    label: areaName,
    segments: courseLines.map((courseLine) => ({
      label: courseLine,
      value: num(valueMap.get(`${areaName}__${courseLine}`)?.reserve),
    })),
  }));

  const byForecast = areaOrder.map((areaName) => ({
    label: areaName,
    segments: courseLines.map((courseLine) => ({
      label: courseLine,
      value: num(valueMap.get(`${areaName}__${courseLine}`)?.forecast),
    })),
  }));

  const tables = courseLines.map((courseLine) => {
    const scoped = areaOrder
      .map((areaName) => ({
        areaName,
        reserve: num(valueMap.get(`${areaName}__${courseLine}`)?.reserve),
        forecast: num(valueMap.get(`${areaName}__${courseLine}`)?.forecast),
      }))
      .sort((left, right) => right.reserve - left.reserve);
    return {
      courseLine,
      rows: prependTotalRow(scoped, {
        areaName: "总计",
        reserve: sumOf("reserve")(scoped),
        forecast: sumOf("forecast")(scoped),
      }),
    };
  });

  return { byReserve, byForecast, tables };
}

export function aggregateCityRows(rows, scenario) {
  const fields = SHEET_FIELDS[scenario];
  const grouped = aggregateBy(
    rows.map((row) => ({
      areaName: pick(row, KEY_ALIASES.area) || "",
      provinceName: pick(row, KEY_ALIASES.province) || "",
      cityLabel: normalizedCityLabel(row),
      reserve: num(row[fields.reserve]),
      forecast: num(row[fields.forecast]),
    })),
    (row) => `${row.areaName}__${row.provinceName}__${row.cityLabel}`,
    {
      areaName: (_rows, first) => first.areaName,
      provinceName: (_rows, first) => first.provinceName,
      cityLabel: (_rows, first) => first.cityLabel,
      reserve: sumOf("reserve"),
      forecast: sumOf("forecast"),
    }
  ).sort((left, right) => right.reserve - left.reserve);

  return prependTotalRow(grouped, {
    areaName: "总计",
    provinceName: "-",
    cityLabel: "-",
    reserve: sumOf("reserve")(grouped),
    forecast: sumOf("forecast")(grouped),
  });
}

export function aggregateCityCourseLineTables(rows, scenario) {
  const fields = SHEET_FIELDS[scenario];
  const mapped = rows.map((row) => ({
    areaName: pick(row, KEY_ALIASES.area) || "",
    provinceName: pick(row, KEY_ALIASES.province) || "",
    cityLabel: normalizedCityLabel(row),
    courseLine: pick(row, KEY_ALIASES.courseLine) || "未命名课线",
    reserve: num(row[fields.reserve]),
    forecast: num(row[fields.forecast]),
  }));
  const courseLines = [...new Set(mapped.map((row) => row.courseLine))].sort(sortText);

  return courseLines.map((courseLine) => {
    const scoped = aggregateBy(
      mapped.filter((row) => row.courseLine === courseLine),
      (row) => `${row.areaName}__${row.provinceName}__${row.cityLabel}`,
      {
        areaName: (_rows, first) => first.areaName,
        provinceName: (_rows, first) => first.provinceName,
        cityLabel: (_rows, first) => first.cityLabel,
        reserve: sumOf("reserve"),
        forecast: sumOf("forecast"),
      }
    ).sort((left, right) => right.reserve - left.reserve);

    return {
      courseLine,
      rows: prependTotalRow(scoped, {
        areaName: "总计",
        provinceName: "-",
        cityLabel: "-",
        reserve: sumOf("reserve")(scoped),
        forecast: sumOf("forecast")(scoped),
      }),
    };
  });
}

export function aggregateCompareCity(currentRows, previousRows, scenario) {
  const fields = SHEET_FIELDS[scenario];
  const current = currentRows.map((row) => ({
    areaName: pick(row, KEY_ALIASES.area) || "",
    provinceName: pick(row, KEY_ALIASES.province) || "",
    cityLabel: normalizedCityLabel(row),
    courseLine: pick(row, KEY_ALIASES.courseLine) || "未命名课线",
    reserve: num(row[fields.reserve]),
    forecast: num(row[fields.forecast]),
  }));
  const previous = previousRows.map((row) => ({
    areaName: pick(row, KEY_ALIASES.area) || "",
    provinceName: pick(row, KEY_ALIASES.province) || "",
    cityLabel: normalizedCityLabel(row),
    courseLine: pick(row, KEY_ALIASES.courseLine) || "未命名课线",
    reserve: num(row[fields.reserve]),
    forecast: num(row[fields.forecast]),
  }));

  const currentGrouped = aggregateBy(current, (row) => `${row.areaName}__${row.provinceName}__${row.cityLabel}`, {
    areaName: (_rows, first) => first.areaName,
    provinceName: (_rows, first) => first.provinceName,
    cityLabel: (_rows, first) => first.cityLabel,
    totalReserve: sumOf("reserve"),
    totalRevenue: sumOf("forecast"),
  });
  const previousGrouped = aggregateBy(previous, (row) => `${row.areaName}__${row.provinceName}__${row.cityLabel}`, {
    areaName: (_rows, first) => first.areaName,
    provinceName: (_rows, first) => first.provinceName,
    cityLabel: (_rows, first) => first.cityLabel,
    totalReserve: sumOf("reserve"),
    totalRevenue: sumOf("forecast"),
  });

  const rowsCore = buildCompareRowsByKey(
    currentGrouped,
    previousGrouped,
    (row) => `${row.areaName}__${row.provinceName}__${row.cityLabel}`,
    (row) => ({
      areaName: row.areaName,
      provinceName: row.provinceName,
      cityLabel: row.cityLabel,
    })
  ).map((row) => ({
    ...row,
    currentReserve: row.currentTotalReserve,
    currentForecast: row.currentTotalRevenue,
    previousReserve: row.previousTotalReserve,
    previousForecast: row.previousTotalRevenue,
    reserveDiff: row.reserveDiff,
    forecastDiff: row.revenueDiff,
  })).sort((left, right) => right.currentReserve - left.currentReserve);

  const rows = prependTotalRow(rowsCore, {
    areaName: "总计",
    provinceName: "-",
    cityLabel: "-",
    currentReserve: sumOf("currentReserve")(rowsCore),
    currentForecast: sumOf("currentForecast")(rowsCore),
    previousReserve: sumOf("previousReserve")(rowsCore),
    previousForecast: sumOf("previousForecast")(rowsCore),
    reserveDiff: sumOf("reserveDiff")(rowsCore),
    forecastDiff: sumOf("forecastDiff")(rowsCore),
  });

  const courseLines = [...new Set([...current.map((row) => row.courseLine), ...previous.map((row) => row.courseLine)])].sort(sortText);
  const sections = courseLines.map((courseLine) => {
    const currentScoped = aggregateBy(
      current.filter((row) => row.courseLine === courseLine),
      (row) => `${row.areaName}__${row.provinceName}__${row.cityLabel}`,
      {
        areaName: (_rows, first) => first.areaName,
        provinceName: (_rows, first) => first.provinceName,
        cityLabel: (_rows, first) => first.cityLabel,
        totalReserve: sumOf("reserve"),
        totalRevenue: sumOf("forecast"),
      }
    );
    const previousScoped = aggregateBy(
      previous.filter((row) => row.courseLine === courseLine),
      (row) => `${row.areaName}__${row.provinceName}__${row.cityLabel}`,
      {
        areaName: (_rows, first) => first.areaName,
        provinceName: (_rows, first) => first.provinceName,
        cityLabel: (_rows, first) => first.cityLabel,
        totalReserve: sumOf("reserve"),
        totalRevenue: sumOf("forecast"),
      }
    );
    const rowsForLineCore = buildCompareRowsByKey(
      currentScoped,
      previousScoped,
      (row) => `${row.areaName}__${row.provinceName}__${row.cityLabel}`,
      (row) => ({
        areaName: row.areaName,
        provinceName: row.provinceName,
        cityLabel: row.cityLabel,
      })
    ).map((row) => ({
      ...row,
      currentReserve: row.currentTotalReserve,
      currentForecast: row.currentTotalRevenue,
      previousReserve: row.previousTotalReserve,
      previousForecast: row.previousTotalRevenue,
      reserveDiff: row.reserveDiff,
      forecastDiff: row.revenueDiff,
    })).sort((left, right) => right.currentReserve - left.currentReserve);

    return {
      courseLine,
      rows: prependTotalRow(rowsForLineCore, {
        areaName: "总计",
        provinceName: "-",
        cityLabel: "-",
        currentReserve: sumOf("currentReserve")(rowsForLineCore),
        currentForecast: sumOf("currentForecast")(rowsForLineCore),
        previousReserve: sumOf("previousReserve")(rowsForLineCore),
        previousForecast: sumOf("previousForecast")(rowsForLineCore),
        reserveDiff: sumOf("reserveDiff")(rowsForLineCore),
        forecastDiff: sumOf("forecastDiff")(rowsForLineCore),
      }),
    };
  });

  return {
    rows,
    sections,
    maxReserveDiff: maxAbs(rows.map((row) => row.reserveDiff)),
    maxForecastDiff: maxAbs(rows.map((row) => row.forecastDiff)),
  };
}
