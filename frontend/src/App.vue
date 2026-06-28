<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref } from "vue";

import DataTable from "./components/DataTable.vue";
import ChangePasswordDialog from "./components/ChangePasswordDialog.vue";
import CompareCourseLineShare from "./components/CompareCourseLineShare.vue";
import LoginPage from "./components/LoginPage.vue";
import MetricCard from "./components/MetricCard.vue";
import PermPanel from "./components/PermPanel.vue";
import RankChart from "./components/RankChart.vue";
import StackChart from "./components/StackChart.vue";
import {
  SINGLE_FIELDS,
  aggregateAreaCourseLine,
  aggregateCityCourseLineTables,
  aggregateCityRows,
  aggregateCompareCity,
  aggregateCompareClassTables,
  aggregateSingleClassTables,
  buildAreaRows,
  buildAreaRowsFromProvinceRows,
  buildBdRows,
  buildCompareAreaRowsFromProvinceRows,
  buildCompareDimensionRows,
  buildProvinceRows,
  compareByOperator,
  compareFieldNames,
  currentValue,
  buildExportFilterLabel,
  buildWorkbookBaseName,
  deltaCell,
  deltaClass,
  diffValue,
  formatDateTime,
  formatComparePairLabel,
  formatNumber,
  formatRate,
  formatSignedNumber,
  formatSignedRate,
  formatUploadOptionLabel,
  formatUploadLabel,
  getNationalRow,
  maxAbs,
  num,
  optionalNumber,
  previousValue,
  progressCell,
  scenarioLabel,
  statusBadgeCell,
} from "./lib/dashboard";
import {
  AREA_OPTIONS,
  provinceOptionsForAreas,
  resolveAreaForProvince,
  scopedAreaOptions,
} from "./lib/location-config";

const brandIconUrl = new URL("./assets/brandicon.jpg", import.meta.url).href;

function headerCell(label, options = {}) {
  return { label, ...options };
}

const HEADERS = {
  uploadHistory: ["批次", "记录日", "上传人", "上传时间", "状态", "备注"],
  classTotal: ["班期", "总储备量", "储备量", "已进线量", "总预测业绩", "预测业绩", "已达成预测业绩"],
  classCourseLine: ["课线名称", "班期", "招生进度", "总储备量", "储备量", "已进线量", "总预测业绩", "预测业绩", "已达成预测业绩"],
  areaPerformance: ["片区", "预测业绩目标", "总预测业绩", "总储备量", "总预测业绩达标率", "预测业绩", "已达成预测业绩"],
  areaReserve: ["片区", "总储备量", "储备量", "已进线量"],
  areaCourseLine: ["课线名称", "片区", "储备量", "预测业绩"],
  provincePerformance: ["片区", "省份", "预测业绩目标", "总预测业绩", "总预测业绩达标率", "预测业绩", "已达成预测业绩"],
  provinceReserve: ["片区", "省份", "总储备量", "储备量", "已进线量"],
  city: ["片区", "省份", "城市", "储备量", "预测业绩"],
  cityCourseLine: ["课线名称", "片区", "省份", "城市", "储备量", "预测业绩"],
  bdPerformance: ["片区", "BD", "预测业绩目标", "总预测业绩", "总预测业绩达标率", "预测业绩", "已达成预测业绩"],
  bdReserve: ["片区", "BD", "总储备量", "储备量", "已进线量"],
  compareClassTotal: ["班期", "本期总储备量", "本期总预测业绩", "上期总储备量", "上期总预测业绩", "总储备量变化", "总预测业绩变化"],
  compareClassCourseLine: ["课线名称", "班期", "招生进度", "本期总储备量", "本期总预测业绩", "上期总储备量", "上期总预测业绩", "总储备量变化", "总预测业绩变化"],
  compareArea: ["片区", "预测业绩目标", "本期总储备量", "本期总预测业绩", "本期达标率", "上期总储备量", "上期总预测业绩", "上期达标率", "总储备量变化", "总预测业绩变化", "达标率变化"],
  compareAreaReserve: ["片区", "本期总储备量", "本期已进线量", "本期储备量", "上期总储备量", "上期已进线量", "上期储备量", "总储备量变化", "已进线量变化", "储备量变化"],
  compareProvince: ["片区", "省份", "预测业绩目标", "本期总储备量", "本期总预测业绩", "本期达标率", "上期总储备量", "上期总预测业绩", "上期达标率", "总储备量变化", "总预测业绩变化", "达标率变化"],
  compareProvinceReserve: ["片区", "省份", "本期总储备量", "本期已进线量", "本期储备量", "上期总储备量", "上期已进线量", "上期储备量", "总储备量变化", "已进线量变化", "储备量变化"],
  compareCity: ["片区", "省份", "城市", "本期储备量", "本期预测业绩", "上期储备量", "上期预测业绩", "储备量变化", "预测业绩变化"],
  compareCityCourseLine: ["课线名称", "片区", "省份", "城市", "本期储备量", "本期预测业绩", "上期储备量", "上期预测业绩", "储备量变化", "预测业绩变化"],
  compareBd: ["片区", "BD", "预测业绩目标", "本期总储备量", "本期总预测业绩", "本期达标率", "上期总储备量", "上期总预测业绩", "上期达标率", "总储备量变化", "总预测业绩变化", "达标率变化"],
  compareBdReserve: ["片区", "BD", "本期总储备量", "本期已进线量", "本期储备量", "上期总储备量", "上期已进线量", "上期储备量", "总储备量变化", "已进线量变化", "储备量变化"],
};

const GROUPED_HEADERS = {
  compareClassTotal: [
    [
      headerCell("班期", { rowspan: 2 }),
      headerCell("本期", { colspan: 2, className: "header-current" }),
      headerCell("上期", { colspan: 2, className: "header-previous" }),
      headerCell("两期变化", { colspan: 2, className: "header-delta" }),
    ],
    [
      headerCell("总储备量"),
      headerCell("总预测业绩"),
      headerCell("总储备量"),
      headerCell("总预测业绩"),
      headerCell("总储备量变化"),
      headerCell("总预测业绩变化"),
    ],
  ],
  compareClassCourseLine: [
    [
      headerCell("课线名称", { rowspan: 2 }),
      headerCell("班期", { rowspan: 2 }),
      headerCell("招生进度", { rowspan: 2 }),
      headerCell("本期", { colspan: 2, className: "header-current" }),
      headerCell("上期", { colspan: 2, className: "header-previous" }),
      headerCell("两期变化", { colspan: 2, className: "header-delta" }),
    ],
    [
      headerCell("总储备量"),
      headerCell("总预测业绩"),
      headerCell("总储备量"),
      headerCell("总预测业绩"),
      headerCell("总储备量变化"),
      headerCell("总预测业绩变化"),
    ],
  ],
  compareArea: [
    [
      headerCell("片区", { rowspan: 2 }),
      headerCell("预测业绩目标", { rowspan: 2 }),
      headerCell("本期", { colspan: 3, className: "header-current" }),
      headerCell("上期", { colspan: 3, className: "header-previous" }),
      headerCell("两期变化", { colspan: 3, className: "header-delta" }),
    ],
    [
      headerCell("总储备量"),
      headerCell("总预测业绩"),
      headerCell("达标率"),
      headerCell("总储备量"),
      headerCell("总预测业绩"),
      headerCell("达标率"),
      headerCell("总储备量变化"),
      headerCell("总预测业绩变化"),
      headerCell("达标率变化"),
    ],
  ],
  compareProvince: [
    [
      headerCell("片区", { rowspan: 2 }),
      headerCell("省份", { rowspan: 2 }),
      headerCell("预测业绩目标", { rowspan: 2 }),
      headerCell("本期", { colspan: 3, className: "header-current" }),
      headerCell("上期", { colspan: 3, className: "header-previous" }),
      headerCell("两期变化", { colspan: 3, className: "header-delta" }),
    ],
    [
      headerCell("总储备量"),
      headerCell("总预测业绩"),
      headerCell("达标率"),
      headerCell("总储备量"),
      headerCell("总预测业绩"),
      headerCell("达标率"),
      headerCell("总储备量变化"),
      headerCell("总预测业绩变化"),
      headerCell("达标率变化"),
    ],
  ],
  compareCity: [
    [
      headerCell("片区", { rowspan: 2 }),
      headerCell("省份", { rowspan: 2 }),
      headerCell("城市", { rowspan: 2 }),
      headerCell("本期", { colspan: 2, className: "header-current" }),
      headerCell("上期", { colspan: 2, className: "header-previous" }),
      headerCell("两期变化", { colspan: 2, className: "header-delta" }),
    ],
    [
      headerCell("储备量"),
      headerCell("预测业绩"),
      headerCell("储备量"),
      headerCell("预测业绩"),
      headerCell("储备量变化"),
      headerCell("预测业绩变化"),
    ],
  ],
  compareCityCourseLine: [
    [
      headerCell("课线名称", { rowspan: 2 }),
      headerCell("片区", { rowspan: 2 }),
      headerCell("省份", { rowspan: 2 }),
      headerCell("城市", { rowspan: 2 }),
      headerCell("本期", { colspan: 2, className: "header-current" }),
      headerCell("上期", { colspan: 2, className: "header-previous" }),
      headerCell("两期变化", { colspan: 2, className: "header-delta" }),
    ],
    [
      headerCell("储备量"),
      headerCell("预测业绩"),
      headerCell("储备量"),
      headerCell("预测业绩"),
      headerCell("储备量变化"),
      headerCell("预测业绩变化"),
    ],
  ],
  compareBd: [
    [
      headerCell("片区", { rowspan: 2 }),
      headerCell("BD", { rowspan: 2 }),
      headerCell("预测业绩目标", { rowspan: 2 }),
      headerCell("本期", { colspan: 3, className: "header-current" }),
      headerCell("上期", { colspan: 3, className: "header-previous" }),
      headerCell("两期变化", { colspan: 3, className: "header-delta" }),
    ],
    [
      headerCell("总储备量"),
      headerCell("总预测业绩"),
      headerCell("达标率"),
      headerCell("总储备量"),
      headerCell("总预测业绩"),
      headerCell("达标率"),
      headerCell("总储备量变化"),
      headerCell("总预测业绩变化"),
      headerCell("达标率变化"),
    ],
  ],
  compareBdReserve: [
    [
      headerCell("片区", { rowspan: 2 }),
      headerCell("BD", { rowspan: 2 }),
      headerCell("本期", { colspan: 3, className: "header-current" }),
      headerCell("上期", { colspan: 3, className: "header-previous" }),
      headerCell("两期变化", { colspan: 3, className: "header-delta" }),
    ],
    [
      headerCell("总储备量"),
      headerCell("已进线量"),
      headerCell("储备量"),
      headerCell("总储备量"),
      headerCell("已进线量"),
      headerCell("储备量"),
      headerCell("总储备量变化"),
      headerCell("已进线量变化"),
      headerCell("储备量变化"),
    ],
  ],
  compareAreaReserve: [
    [
      headerCell("片区", { rowspan: 2 }),
      headerCell("本期", { colspan: 3, className: "header-current" }),
      headerCell("上期", { colspan: 3, className: "header-previous" }),
      headerCell("两期变化", { colspan: 3, className: "header-delta" }),
    ],
    [
      headerCell("总储备量"),
      headerCell("已进线量"),
      headerCell("储备量"),
      headerCell("总储备量"),
      headerCell("已进线量"),
      headerCell("储备量"),
      headerCell("总储备量变化"),
      headerCell("已进线量变化"),
      headerCell("储备量变化"),
    ],
  ],
  compareProvinceReserve: [
    [
      headerCell("片区", { rowspan: 2 }),
      headerCell("省份", { rowspan: 2 }),
      headerCell("本期", { colspan: 3, className: "header-current" }),
      headerCell("上期", { colspan: 3, className: "header-previous" }),
      headerCell("两期变化", { colspan: 3, className: "header-delta" }),
    ],
    [
      headerCell("总储备量"),
      headerCell("已进线量"),
      headerCell("储备量"),
      headerCell("总储备量"),
      headerCell("已进线量"),
      headerCell("储备量"),
      headerCell("总储备量变化"),
      headerCell("已进线量变化"),
      headerCell("储备量变化"),
    ],
  ],
};

// ===== 鉴权 =====
const authUser = ref(null); // { username, role, permissions }
const showPermPanel = ref(false);
const showChangePasswordDialog = ref(false);
const showDeleteDialog = ref(false);
const deleteConfirming = ref(false);

function loadStoredAuth() {
  const token = localStorage.getItem("auth_token");
  const userJson = localStorage.getItem("auth_user");
  if (token && userJson) {
    try {
      authUser.value = JSON.parse(userJson);
    } catch {
      authUser.value = null;
    }
  }
}

function onLoginSuccess(user) {
  authUser.value = user;
}

function logout() {
  localStorage.removeItem("auth_token");
  localStorage.removeItem("auth_user");
  authUser.value = null;
}

function confirmLogout() {
  if (!window.confirm("确认退出当前账号吗？")) {
    return;
  }
  logout();
}

function handlePasswordChanged(message) {
  showChangePasswordDialog.value = false;
  window.alert(message || "密码已修改，请重新登录");
  logout();
}

// 获取请求头，带 token
function authHeaders() {
  const token = localStorage.getItem("auth_token") || "";
  return token ? { Authorization: `Bearer ${token}` } : {};
}

const isSuperAdmin = computed(() => authUser.value?.role === "super_admin");
const perms = computed(() => authUser.value?.permissions || {});

// 判断某个 tab 是否有权限访问
function canViewTab(module, tab) {
  if (isSuperAdmin.value) return true;
  const m = perms.value[module];
  if (!m?.enabled) return false;
  return !tab || m.tabs?.includes(tab);
}

function canExport(module) {
  if (isSuperAdmin.value) return true;
  return !!(perms.value[module]?.allow_export);
}

const singleExportLabel = computed(() => canExport("single") ? currentFilterLabel.value : "");
const compareExportLabel = computed(() => canExport("compare") ? currentFilterLabel.value : "");
const canDownloadCompletedTable = computed(() => canExport("single") || canExport("compare"));

// ===== end 鉴权 =====

function createMetricRangeFilterState(defaultMetric) {
  return {
    metric: defaultMetric,
    firstOperator: "",
    firstValue: "",
    logic: "and",
    secondOperator: "",
    secondValue: "",
  };
}

const state = reactive({
  activeView: "single",
  singleTab: "overview",
  compareTab: "overview",
  singleScenario: "base",
  compareScenario: "base",
  showUploadPanel: false,
  periods: [],
  uploads: [],
  selectedPeriod: "",
  selectedUploadSeq: null,
  uploadedBy: "",
  selectedFile: null,
  uploadMessage: "",
  uploadMessageType: "",
  loadingData: false,
  areaFilter: [],
  areaDropdownOpen: false,
  provinceFilter: [],
  provinceDropdownOpen: false,
  singleAreaCourseLine: "",
  singleCityCourseLine: "",
  compareCityCourseLine: "",
  datasets: {
    currentMonthlyClass: [],
    currentMonthlyClassMeta: {},
    previousMonthlyClass: [],
    previousMonthlyClassMeta: {},
    currentMonthlyTarget: [],
    previousMonthlyTarget: [],
    currentInbound: [],
    previousInbound: [],
    currentReserveDetail: [],
    previousReserveDetail: [],
    singleNational: [],
    singleArea: [],
    singleProvince: [],
    singleBd: [],
    compareNational: null,
    compareArea: [],
    compareProvince: [],
    compareBd: [],
  },
  cityFilters: createMetricRangeFilterState("reserveDiff"),
  cityCourseLineFilters: {},
  bdTargetFilters: createMetricRangeFilterState("reserveDiff"),
  bdReserveFilters: createMetricRangeFilterState("reserveDiff"),
});

const currentUpload = computed(() =>
  state.uploads.find((item) => item.upload_seq === state.selectedUploadSeq) || null
);

const uploadMap = computed(() => new Map(state.uploads.map((upload) => [upload.upload_seq, upload])));

const uploadInputRef = ref(null);

const CITY_FILTER_OPTIONS = [
  { value: "reserveDiff", label: "储备量变化" },
];

const BD_TARGET_FILTER_OPTIONS = [
  { value: "reserveDiff", label: "总储备量变化" },
];

const BD_RESERVE_FILTER_OPTIONS = [
  { value: "reserveDiff", label: "总储备量变化" },
  { value: "reserveQtyDiff", label: "储备量变化" },
];

// --- 区域/省份筛选 ---
const areaProvinceMap = computed(() => {
  const map = new Map();
  for (const row of state.datasets.currentReserveDetail) {
    const area = row["片区"] || row.area_name || "";
    const province = row["省份"] || row.province_name || "";
    if (!area) continue;
    if (!map.has(area)) map.set(area, new Set());
    if (province) map.get(area).add(province);
  }
  return map;
});

const provinceAreaMap = computed(() => {
  const map = new Map();
  for (const [area, provinces] of areaProvinceMap.value.entries()) {
    for (const province of provinces) {
      if (!map.has(province)) {
        map.set(province, area);
      }
    }
  }
  return map;
});

const areaOptions = computed(() => [...AREA_OPTIONS]);

const provinceOptions = computed(() => provinceOptionsForAreas(state.areaFilter));

function normalizeDraftProvinceFilter() {
  const allowedProvinces = new Set(provinceOptions.value);
  state.provinceFilter = state.provinceFilter.filter((province) => allowedProvinces.has(province));
}

function syncDraftFiltersFromApplied() {
  state.areaFilter = [...appliedAreas.value];
  state.provinceFilter = [...appliedProvinces.value];
  normalizeDraftProvinceFilter();
}

function summarizeSelection(selectedItems, availableItems, allLabel, unitLabel) {
  if (!selectedItems.length) {
    return allLabel;
  }
  if (availableItems.length && selectedItems.length === availableItems.length) {
    return allLabel;
  }
  if (selectedItems.length === 1) {
    return selectedItems[0];
  }
  return `已选 ${selectedItems.length} 个${unitLabel}`;
}

function toggleArea(area) {
  const idx = state.areaFilter.indexOf(area);
  if (idx === -1) state.areaFilter.push(area);
  else state.areaFilter.splice(idx, 1);

  normalizeDraftProvinceFilter();
}

function selectAllAreas() {
  state.areaFilter = [...areaOptions.value];
}

function clearAreas() {
  state.areaFilter = [];
}

function toggleProvince(p) {
  const idx = state.provinceFilter.indexOf(p);
  if (idx === -1) state.provinceFilter.push(p);
  else state.provinceFilter.splice(idx, 1);
}

function selectAllProvinces() {
  state.provinceFilter = [...provinceOptions.value];
}

function clearProvinces() {
  state.provinceFilter = [];
}

function clearAreaFilter() {
  state.areaFilter = [];
  state.provinceFilter = [];
}

function toggleAreaDropdown() {
  const opening = !state.areaDropdownOpen;
  if (opening && !state.areaDropdownOpen && !state.provinceDropdownOpen) {
    syncDraftFiltersFromApplied();
  }
  state.areaDropdownOpen = opening;
  state.provinceDropdownOpen = false;
}

function toggleProvinceDropdown() {
  const opening = !state.provinceDropdownOpen;
  if (opening && !state.areaDropdownOpen && !state.provinceDropdownOpen) {
    syncDraftFiltersFromApplied();
  }
  state.provinceDropdownOpen = opening;
  state.areaDropdownOpen = false;
}

function cancelLocationFilterEditing() {
  syncDraftFiltersFromApplied();
  state.areaDropdownOpen = false;
  state.provinceDropdownOpen = false;
}

function resolveActiveCourseLine(selectedCourseLine, courseLines) {
  return courseLines.includes(selectedCourseLine) ? selectedCourseLine : courseLines[0] || "";
}

// Applied filters (committed on 确定 click or immediate for area)
const appliedAreas = ref([]);
const appliedProvinces = ref([]);
const editingLocationFilters = computed(() => state.areaDropdownOpen || state.provinceDropdownOpen);
const areaTriggerText = computed(() =>
  summarizeSelection(
    editingLocationFilters.value ? state.areaFilter : appliedAreas.value,
    areaOptions.value,
    "全部片区",
    "片区"
  )
);
const provinceTriggerText = computed(() => {
  const selectedItems = editingLocationFilters.value ? state.provinceFilter : appliedProvinces.value;
  const availableItems = provinceOptionsForAreas(
    editingLocationFilters.value ? state.areaFilter : appliedAreas.value
  );
  return summarizeSelection(selectedItems, availableItems, "全部省份", "省份");
});
const locationFilterActive = computed(() => Boolean(appliedAreas.value.length || appliedProvinces.value.length));
const showLocationFilteredClassSections = computed(() => !locationFilterActive.value);
const locationFilterNotice = computed(() => {
  if (!locationFilterActive.value) {
    return "";
  }
  const areaText = appliedAreas.value.length ? appliedAreas.value.join("、") : "全部片区";
  const appliedArea = { value: areaText };
  const provinceText = appliedProvinces.value.length ? ` / ${appliedProvinces.value.join("、")}` : "";
  return `已按 ${appliedArea.value}${provinceText} 筛选。课线班期相关看板当前数据未包含片区、省份维度，继续展示会变成全量数据，因此在筛选状态下暂不显示。`;
});

function applyFilters() {
  normalizeDraftProvinceFilter();
  appliedAreas.value = [...state.areaFilter];
  appliedProvinces.value = [...state.provinceFilter];
  state.areaDropdownOpen = false;
  state.provinceDropdownOpen = false;
}

function resetLocationFilters() {
  clearAreaFilter();
  applyFilters();
}

function filterLabel() {
  return buildExportFilterLabel({
    periodCode: state.selectedPeriod,
    upload: currentUpload.value,
    areas: appliedAreas.value,
    provinces: appliedProvinces.value,
  });
}

const currentFilterLabel = computed(() => filterLabel());

function filterDetailRows(rows) {
  if (!locationFilterActive.value) return rows;
  return rows.filter((row) => {
    const area = row["片区"] || row.area_name || "";
    if (appliedAreas.value.length && !appliedAreas.value.includes(area)) return false;
    if (appliedProvinces.value.length) {
      const prov = row["省份"] || row.province_name || "";
      return appliedProvinces.value.includes(prov);
    }
    return true;
  });
}

function currentAreaScope(areaNames, provinceNames) {
  return scopedAreaOptions(areaNames, provinceNames);
}

function filterAreaRows(rows) {
  if (!locationFilterActive.value) return rows;
  const allowedAreas = new Set(currentAreaScope(appliedAreas.value, appliedProvinces.value));
  return rows.filter((row) => row.name === "全国" || allowedAreas.has(row.name));
}

function filterProvinceRows(rows) {
  if (!locationFilterActive.value) return rows;
  const allowedProvinces = new Set(
    appliedProvinces.value.length ? appliedProvinces.value : provinceOptionsForAreas(appliedAreas.value)
  );
  return rows.filter((row) => {
    return row.name === "全国" || allowedProvinces.has(row.name);
  });
}

function cellLabelText(cell) {
  if (typeof cell === "object" && cell !== null) {
    if (Object.hasOwn(cell, "text")) {
      return cellLabelText(cell.text);
    }
    if (Object.hasOwn(cell, "html")) {
      return String(cell.html).replace(/<[^>]+>/g, "").trim();
    }
  }
  return String(cell ?? "").trim();
}

function shouldPinNationalFirstRow(rows) {
  const firstRow = rows?.[0];
  if (!Array.isArray(firstRow)) {
    return false;
  }
  return firstRow.slice(0, 3).some((cell) => cellLabelText(cell) === "全国");
}

function buildBdScopeMap(rows) {
  const map = new Map();
  for (const row of rows) {
    const bdName = String(row["BD"] || row.bd_name || "").trim();
    if (!bdName) continue;
    const provinceName = row["省份"] || row.province_name || "";
    const areaName = row["片区"] || row.area_name || resolveAreaForProvince(provinceName) || "";
    if (!map.has(bdName)) {
      map.set(bdName, {
        primaryArea: areaName || "",
        areas: new Set(),
        provinces: new Set(),
      });
    }
    const scope = map.get(bdName);
    if (areaName) {
      scope.areas.add(areaName);
      if (!scope.primaryArea) {
        scope.primaryArea = areaName;
      }
    }
    if (provinceName) {
      scope.provinces.add(provinceName);
    }
  }
  return map;
}

function buildBdScopeRows(...collections) {
  return collections.flatMap((rows) => rows || []);
}

const singleBdScopeMap = computed(() =>
  buildBdScopeMap(
    buildBdScopeRows(
      state.datasets.currentReserveDetail,
      state.datasets.currentMonthlyTarget,
      state.datasets.currentInbound
    )
  )
);
const compareBdScopeMap = computed(() =>
  buildBdScopeMap(
    buildBdScopeRows(
      state.datasets.currentReserveDetail,
      state.datasets.previousReserveDetail,
      state.datasets.currentMonthlyTarget,
      state.datasets.previousMonthlyTarget,
      state.datasets.currentInbound,
      state.datasets.previousInbound
    )
  )
);

function filterBdRows(rows, scopeMap) {
  if (!locationFilterActive.value) {
    return rows;
  }
  return rows.filter((row) => {
    const scope = scopeMap.get(String(row.name || "").trim());
    if (!scope) {
      return false;
    }
    if (appliedProvinces.value.length) {
      return appliedProvinces.value.some((province) => scope.provinces.has(province));
    }
    if (appliedAreas.value.length) {
      return appliedAreas.value.some((area) => scope.areas.has(area));
    }
    return true;
  });
}

function resolveProvinceAreaName(row) {
  return row.areaName || resolveAreaForProvince(row.name) || appliedAreas.value[0] || "-";
}

function resolveBdAreaName(row, scopeMap) {
  return row.areaName || scopeMap.get(String(row.name || "").trim())?.primaryArea || "-";
}


function getPreviousUpload(upload) {
  const previousSeq = upload?.compare_previous_upload_seq;
  if (!previousSeq) {
    return null;
  }
  return uploadMap.value.get(previousSeq) || null;
}

function formatUploadSelectLabel(upload) {
  return formatUploadOptionLabel(upload, getPreviousUpload(upload), state.selectedPeriod);
}

const previousUpload = computed(() => getPreviousUpload(currentUpload.value));
const currentCompareText = computed(() => formatComparePairLabel(currentUpload.value, previousUpload.value));

const compareEnabled = computed(() => Boolean(state.datasets.compareNational?.show_compare));
const uploadPanelVisible = computed(() => state.showUploadPanel || !state.uploads.length);
const uploadButtonLabel = computed(() => (uploadPanelVisible.value && state.uploads.length ? "收起上传" : "上传数据"));
const selectedFilename = computed(() => state.selectedFile?.name || "未选择文件");

const currentSelectionText = computed(() => {
  if (!state.selectedPeriod || !currentUpload.value) {
    return "未选择批次";
  }
  return `${state.selectedPeriod} / ${formatUploadLabel(currentUpload.value, state.selectedPeriod)}`;
});

const downloadAvailable = computed(() => Boolean(state.selectedPeriod && state.selectedUploadSeq));

const batchSummaryList = computed(() => {
  if (!currentUpload.value) {
    return [];
  }
  return [
    { label: "班期时间", value: state.selectedPeriod },
    { label: "当前批次", value: formatUploadLabel(currentUpload.value, state.selectedPeriod) },
    { label: "两期对比", value: currentCompareText.value },
    { label: "记录日", value: currentUpload.value.source_record_mmdd || "-" },
    { label: "上传时间", value: formatDateTime(currentUpload.value.uploaded_at) },
    { label: "上传人", value: currentUpload.value.uploaded_by || "-" },
    { label: "状态", value: currentUpload.value.status || "-" },
  ];
});

const uploadHistoryRows = computed(() =>
  state.uploads.map((upload) => [
    formatUploadSelectLabel(upload),
    upload.source_record_mmdd || "-",
    upload.uploaded_by || "-",
    formatDateTime(upload.uploaded_at),
    upload.status || "-",
    upload.message || "-",
  ])
);

function summarizeSingleDimensionRows(rows) {
  const summary = rows.reduce(
    (acc, row) => ({
      targetRevenue: acc.targetRevenue + num(row.targetRevenue),
      totalRevenue: acc.totalRevenue + num(row.totalRevenue),
      totalReserve: acc.totalReserve + num(row.totalReserve),
      forecast: acc.forecast + num(row.forecast),
      achieved: acc.achieved + num(row.achieved),
      reserve: acc.reserve + num(row.reserve),
      inbound: acc.inbound + num(row.inbound),
    }),
    {
      targetRevenue: 0,
      totalRevenue: 0,
      totalReserve: 0,
      forecast: 0,
      achieved: 0,
      reserve: 0,
      inbound: 0,
    }
  );
  return {
    ...summary,
    rate: summary.targetRevenue ? summary.totalRevenue / summary.targetRevenue : 0,
  };
}

function buildSingleOverviewCards(summaryRow, scenario) {
  const mode = scenarioLabel(scenario);
  const reserveProgress = num(summaryRow?.totalReserve) ? num(summaryRow?.inbound) / num(summaryRow?.totalReserve) : 0;
  return [
    {
      label: `${mode}总预测业绩`,
      value: formatNumber(num(summaryRow?.totalRevenue)),
      meta: [
        { label: "已达成业绩", value: formatNumber(num(summaryRow?.achieved)) },
        { label: "预估业绩", value: formatNumber(num(summaryRow?.forecast)) },
      ],
      progress: num(summaryRow?.rate),
      rateText: `达成率 ${formatRate(num(summaryRow?.rate))}`,
      targetText: `目标值 ${formatNumber(num(summaryRow?.targetRevenue))}`,
      accent: false,
    }, 
    {
      label: `${mode}总储备量`,
      value: formatNumber(num(summaryRow?.totalReserve)),
      meta: [
        { label: "已进线量", value: formatNumber(num(summaryRow?.inbound)) },
        { label: `${mode}储备量`, value: formatNumber(num(summaryRow?.reserve)) },
      ],
      progress: reserveProgress,
      rateText: `已进线进度${formatRate(reserveProgress)}`,
      targetText: `总储备量 ${formatNumber(num(summaryRow?.totalReserve))}`,
      accent: true,
    },
  ];
}

const singleClassData = computed(() =>
  aggregateSingleClassTables(state.datasets.currentMonthlyClass, state.singleScenario, {
    overallTotals: state.datasets.currentMonthlyClassMeta?.overall_totals?.[state.singleScenario] || null,
  })
);

const currentMonthlyClassStatusStyles = computed(() => state.datasets.currentMonthlyClassMeta?.status_styles || {});

const singleClassTotalRows = computed(() =>
  singleClassData.value.totalRows.map((row) => [
    row.className,
    formatNumber(row.totalReserve),
    formatNumber(row.reserve),
    formatNumber(row.inbound),
    formatNumber(row.totalRevenue),
    formatNumber(row.forecast),
    formatNumber(row.achieved),
  ])
);

const singleCourseLineSections = computed(() =>
  singleClassData.value.courseLineSections.map((section) => ({
    ...section,
    tableRows: section.rows.map((row) => [
      row.courseLine || section.name,
      row.className,
      row.rowType === "share" ? "-" : statusBadgeCell(row.status, currentMonthlyClassStatusStyles.value),
      row.rowType === "share" ? formatRate(row.totalReserve) : formatNumber(row.totalReserve),
      row.rowType === "share" ? formatRate(row.reserve) : formatNumber(row.reserve),
      row.rowType === "share" ? formatRate(row.inbound) : formatNumber(row.inbound),
      row.rowType === "share" ? formatRate(row.totalRevenue) : formatNumber(row.totalRevenue),
      row.rowType === "share" ? formatRate(row.forecast) : formatNumber(row.forecast),
      row.rowType === "share" ? formatRate(row.achieved) : formatNumber(row.achieved),
    ]),
  }))
);

function sortWithNationalFirst(rows, sortField) {
  const pinned = rows.filter((row) => row.name === "全国");
  const others = rows.filter((row) => row.name !== "全国");
  return [...pinned, ...others.sort((left, right) => right[sortField] - left[sortField])];
}

const singleAreaData = computed(() =>
  buildAreaRows(state.datasets.singleArea, state.datasets.singleNational, state.singleScenario)
);

const visibleSingleAreaData = computed(() => {
  if (!locationFilterActive.value) {
    return singleAreaData.value;
  }
  return buildAreaRowsFromProvinceRows(
    filteredSingleProvinceData.value,
    currentAreaScope(appliedAreas.value, appliedProvinces.value)
  );
});

const filteredSingleAreaScopeData = computed(() => visibleSingleAreaData.value.filter((row) => row.name !== "全国"));

const filteredSingleAreaData = computed(() => filterAreaRows(singleAreaData.value).filter((row) => row.name !== "全国"));

const singleAreaPerformanceRows = computed(() =>
  sortWithNationalFirst(visibleSingleAreaData.value, "totalRevenue").map((row) => [
    row.name,
    formatNumber(row.targetRevenue),
    formatNumber(row.totalRevenue),
    formatNumber(row.totalReserve),
    progressCell(row.rate),
    formatNumber(row.forecast),
    formatNumber(row.achieved),
  ])
);

const singleAreaReserveRows = computed(() =>
  sortWithNationalFirst(visibleSingleAreaData.value, "totalReserve").map((row) => [
    row.name,
    formatNumber(row.totalReserve),
    formatNumber(row.reserve),
    formatNumber(row.inbound),
  ])
);

const singleAreaCourseLine = computed(() =>
  aggregateAreaCourseLine(
    filterDetailRows(state.datasets.currentReserveDetail),
    state.singleScenario,
    currentAreaScope(appliedAreas.value, appliedProvinces.value)
  )
);

const singleAreaReserveChart = computed(() =>
  singleAreaCourseLine.value.byReserve.map((row) => ({
    ...row,
    segments: row.segments.map((segment) => ({
      ...segment,
      display: formatNumber(segment.value),
    })),
  }))
);

const singleAreaForecastChart = computed(() =>
  singleAreaCourseLine.value.byForecast.map((row) => ({
    ...row,
    segments: row.segments.map((segment) => ({
      ...segment,
      display: formatNumber(segment.value),
    })),
  }))
);

const singleAreaCourseLineTables = computed(() =>
  singleAreaCourseLine.value.tables.map((section) => ({
    ...section,
    tableRows: section.rows.map((row) => [
      section.courseLine,
      row.areaName || "-",
      formatNumber(row.reserve),
      formatNumber(row.forecast),
    ]),
  }))
);

const singleAreaCourseLineOptions = computed(() =>
  singleAreaCourseLineTables.value.map((section) => section.courseLine)
);

const activeSingleAreaCourseLine = computed(() =>
  resolveActiveCourseLine(state.singleAreaCourseLine, singleAreaCourseLineOptions.value)
);

const selectedSingleAreaCourseLineSection = computed(() =>
  singleAreaCourseLineTables.value.find((section) => section.courseLine === activeSingleAreaCourseLine.value) || null
);

const singleProvinceData = computed(() =>
  buildProvinceRows(
    state.datasets.singleProvince,
    state.singleScenario,
    state.datasets.singleNational,
    state.datasets.singleArea
  )
);

const filteredSingleProvinceData = computed(() =>
  filterProvinceRows(singleProvinceData.value).filter((row) => row.name !== "全国")
);

const singleOverviewSourceRow = computed(() => {
  if (appliedProvinces.value.length) {
    return summarizeSingleDimensionRows(filteredSingleProvinceData.value);
  }
  if (appliedAreas.value.length) {
    return summarizeSingleDimensionRows(filteredSingleAreaScopeData.value);
  }
  return singleAreaData.value.find((row) => row.name === "全国") || summarizeSingleDimensionRows(singleAreaData.value);
});

const singleOverviewCards = computed(() =>
  buildSingleOverviewCards(singleOverviewSourceRow.value, state.singleScenario)
);

const singleProvincePerformanceRows = computed(() =>
  sortWithNationalFirst(filterProvinceRows(singleProvinceData.value), "totalRevenue").map((row) => [
    resolveProvinceAreaName(row),
    row.name,
    formatNumber(row.targetRevenue),
    formatNumber(row.totalRevenue),
    progressCell(row.rate),
    formatNumber(row.forecast),
    formatNumber(row.achieved),
  ])
);

const singleProvinceReserveRows = computed(() =>
  sortWithNationalFirst(filterProvinceRows(singleProvinceData.value), "totalReserve").map((row) => [
    resolveProvinceAreaName(row),
    row.name,
    formatNumber(row.totalReserve),
    formatNumber(row.reserve),
    formatNumber(row.inbound),
  ])
);

const singleCityData = computed(() =>
  aggregateCityRows(filterDetailRows(state.datasets.currentReserveDetail), state.singleScenario)
);

const singleCityRows = computed(() =>
  singleCityData.value.map((row) => [
    row.areaName || "-",
    row.provinceName || "-",
    row.cityLabel,
    formatNumber(row.reserve),
    formatNumber(row.forecast),
  ])
);

const singleCityCourseLineSections = computed(() =>
  aggregateCityCourseLineTables(filterDetailRows(state.datasets.currentReserveDetail), state.singleScenario).map((section) => ({
    ...section,
    tableRows: section.rows.map((row) => [
      section.courseLine,
      row.areaName || "-",
      row.provinceName || "-",
      row.cityLabel,
      formatNumber(row.reserve),
      formatNumber(row.forecast),
    ]),
  }))
);

const singleCityCourseLineOptions = computed(() =>
  singleCityCourseLineSections.value.map((section) => section.courseLine)
);

const activeSingleCityCourseLine = computed(() =>
  resolveActiveCourseLine(state.singleCityCourseLine, singleCityCourseLineOptions.value)
);

const selectedSingleCityCourseLineSection = computed(() =>
  singleCityCourseLineSections.value.find((section) => section.courseLine === activeSingleCityCourseLine.value) || null
);

const singleBdData = computed(() =>
  buildBdRows(state.datasets.singleBd, state.singleScenario)
    .filter((row) => singleBdScopeMap.value.has(row.name))
);

const filteredSingleBdData = computed(() => filterBdRows(singleBdData.value, singleBdScopeMap.value));

const singleBdPerformanceChart = computed(() =>
  [...filteredSingleBdData.value]
    .sort((left, right) => right.totalRevenue - left.totalRevenue)
    .map((row) => ({
      name: row.name,
      primaryLabel: "已达成",
      secondaryLabel: "预测业绩",
      primaryValue: row.achieved,
      secondaryValue: row.forecast,
      totalValue: num(row.achieved) + num(row.forecast),
      primaryText: formatNumber(row.achieved),
      secondaryText: formatNumber(row.forecast),
      totalText: formatNumber(num(row.achieved) + num(row.forecast)),
    }))
);

const singleBdReserveChart = computed(() =>
  [...filteredSingleBdData.value]
    .sort((left, right) => right.totalReserve - left.totalReserve)
    .map((row) => ({
      name: row.name,
      primaryLabel: "已进线",
      secondaryLabel: "储备",
      primaryValue: row.inbound,
      secondaryValue: row.reserve,
      totalValue: num(row.inbound) + num(row.reserve),
      primaryText: formatNumber(row.inbound),
      secondaryText: formatNumber(row.reserve),
      totalText: formatNumber(num(row.inbound) + num(row.reserve)),
    }))
);

const singleBdPerformanceRows = computed(() =>
  [...filteredSingleBdData.value]
    .sort((left, right) => right.totalRevenue - left.totalRevenue)
    .map((row) => [
      resolveBdAreaName(row, singleBdScopeMap.value),
      row.name,
      formatNumber(row.targetRevenue),
      formatNumber(row.totalRevenue),
      progressCell(row.rate),
      formatNumber(row.forecast),
      formatNumber(row.achieved),
    ])
);

const singleBdReserveRows = computed(() =>
  [...filteredSingleBdData.value]
    .sort((left, right) => right.totalReserve - left.totalReserve)
    .map((row) => [
      resolveBdAreaName(row, singleBdScopeMap.value),
      row.name,
      formatNumber(row.totalReserve),
      formatNumber(row.reserve),
      formatNumber(row.inbound),
    ])
);

function buildCompareCard(label, row, fieldName, isRate = false) {
  const diff = diffValue(row, fieldName);
  return {
    label,
    value: isRate ? formatRate(currentValue(row, fieldName)) : formatNumber(currentValue(row, fieldName)),
    diff: isRate ? formatSignedRate(diff) : formatSignedNumber(diff),
    diffClass: deltaClass(diff),
    previous: isRate ? formatRate(previousValue(row, fieldName)) : formatNumber(previousValue(row, fieldName)),
    diffValue: diff,
  };
}

function summarizeCompareDimensionRows(rows) {
  const summary = rows.reduce(
    (acc, row) => ({
      targetRevenue: acc.targetRevenue + num(row.targetRevenue),
      currentInbound: acc.currentInbound + num(row.currentInbound),
      previousInbound: acc.previousInbound + num(row.previousInbound),
      currentAchieved: acc.currentAchieved + num(row.currentAchieved),
      previousAchieved: acc.previousAchieved + num(row.previousAchieved),
      currentReserve: acc.currentReserve + num(row.currentReserve),
      previousReserve: acc.previousReserve + num(row.previousReserve),
      currentForecast: acc.currentForecast + num(row.currentForecast),
      previousForecast: acc.previousForecast + num(row.previousForecast),
      currentTotalReserve: acc.currentTotalReserve + num(row.currentTotalReserve),
      currentTotalRevenue: acc.currentTotalRevenue + num(row.currentTotalRevenue),
      previousTotalReserve: acc.previousTotalReserve + num(row.previousTotalReserve),
      previousTotalRevenue: acc.previousTotalRevenue + num(row.previousTotalRevenue),
    }),
    {
      targetRevenue: 0,
      currentInbound: 0,
      previousInbound: 0,
      currentAchieved: 0,
      previousAchieved: 0,
      currentReserve: 0,
      previousReserve: 0,
      currentForecast: 0,
      previousForecast: 0,
      currentTotalReserve: 0,
      currentTotalRevenue: 0,
      previousTotalReserve: 0,
      previousTotalRevenue: 0,
    }
  );
  return {
    ...summary,
    currentRate: summary.targetRevenue ? summary.currentTotalRevenue / summary.targetRevenue : 0,
    previousRate: summary.targetRevenue ? summary.previousTotalRevenue / summary.targetRevenue : 0,
    inboundDiff: summary.currentInbound - summary.previousInbound,
    achievedDiff: summary.currentAchieved - summary.previousAchieved,
    reserveQtyDiff: summary.currentReserve - summary.previousReserve,
    forecastDiff: summary.currentForecast - summary.previousForecast,
    reserveDiff: summary.currentTotalReserve - summary.previousTotalReserve,
    revenueDiff: summary.currentTotalRevenue - summary.previousTotalRevenue,
    rateDiff: (summary.targetRevenue ? summary.currentTotalRevenue / summary.targetRevenue : 0)
      - (summary.targetRevenue ? summary.previousTotalRevenue / summary.targetRevenue : 0),
  };
}

function deltaBadgeStyle(value, maxValue) {
  const numeric = num(value);
  const safeMax = maxValue || 1;
  const alpha = Math.min(0.34, Math.abs(numeric) / safeMax * 0.34);
  if (numeric > 0) {
    return { background: `rgba(215, 66, 66, ${alpha})`, color: "#b4233a" };
  }
  if (numeric < 0) {
    return { background: `rgba(31, 157, 99, ${alpha})`, color: "#167447" };
  }
  return { background: "#eef2f7", color: "#5f6e82" };
}

const compareClassData = computed(() =>
  aggregateCompareClassTables(
    state.datasets.currentMonthlyClass,
    state.datasets.previousMonthlyClass,
    state.compareScenario
  )
);

const compareClassTotalRows = computed(() =>
  compareClassData.value.totalRows.map((row) => [
    row.className,
    formatNumber(row.currentTotalReserve),
    formatNumber(row.currentTotalRevenue),
    formatNumber(row.previousTotalReserve),
    formatNumber(row.previousTotalRevenue),
    deltaCell(row.reserveDiff, compareClassData.value.maxReserveDiff),
    deltaCell(row.revenueDiff, compareClassData.value.maxRevenueDiff),
  ])
);

const compareCourseLineSections = computed(() =>
  compareClassData.value.sections.map((section) => ({
    ...section,
    tableRows: section.rows.map((row) => [
      section.courseLine,
      row.className,
      statusBadgeCell(row.status, currentMonthlyClassStatusStyles.value),
      formatNumber(row.currentTotalReserve),
      formatNumber(row.currentTotalRevenue),
      formatNumber(row.previousTotalReserve),
      formatNumber(row.previousTotalRevenue),
      deltaCell(row.reserveDiff, compareClassData.value.maxReserveDiff),
      deltaCell(row.revenueDiff, compareClassData.value.maxRevenueDiff),
    ]),
  }))
);

const compareShareData = computed(() =>
  compareClassData.value.share.map((group) => ({
    ...group,
    metrics: group.metrics.map((metric) => ({
      ...metric,
      current: metric.current.map((segment) => ({
        ...segment,
        rawValue: segment.value,
        display: formatNumber(segment.value),
      })),
      previous: metric.previous.map((segment) => ({
        ...segment,
        rawValue: segment.value,
        display: formatNumber(segment.value),
      })),
    })),
  }))
);

const compareAreaData = computed(() =>
  buildCompareDimensionRows(
    state.datasets.compareArea,
    state.datasets.compareNational?.rows || [],
    state.compareScenario,
    { includeNational: true }
  )
);

const filteredCompareAreaData = computed(() => filterAreaRows(compareAreaData.value).filter((row) => row.name !== "全国"));

const compareAreaMaxReserve = computed(() => maxAbs(filterAreaRows(compareAreaData.value).map((row) => row.reserveDiff)));
const compareAreaMaxRevenue = computed(() => maxAbs(filterAreaRows(compareAreaData.value).map((row) => row.revenueDiff)));
const compareAreaMaxRate = computed(() => maxAbs(filterAreaRows(compareAreaData.value).map((row) => row.rateDiff)));

const compareAreaRows = computed(() =>
  sortWithNationalFirst(filterAreaRows(compareAreaData.value), "currentTotalRevenue").map((row) => [
    row.name,
    formatNumber(row.targetRevenue),
    formatNumber(row.currentTotalReserve),
    formatNumber(row.currentTotalRevenue),
    formatRate(row.currentRate),
    formatNumber(row.previousTotalReserve),
    formatNumber(row.previousTotalRevenue),
    formatRate(row.previousRate),
    deltaCell(row.reserveDiff, compareAreaMaxReserve.value),
    deltaCell(row.revenueDiff, compareAreaMaxRevenue.value),
    deltaCell(row.rateDiff, compareAreaMaxRate.value, true),
  ])
);

const compareAreaReserveMaxReserve = computed(() => maxAbs(filterAreaRows(compareAreaData.value).map((row) => row.reserveDiff)));
const compareAreaReserveMaxInbound = computed(() => maxAbs(filterAreaRows(compareAreaData.value).map((row) => row.inboundDiff)));
const compareAreaReserveMaxReserveQty = computed(() => maxAbs(filterAreaRows(compareAreaData.value).map((row) => row.reserveQtyDiff)));

const compareAreaReserveRows = computed(() =>
  sortWithNationalFirst(filterAreaRows(compareAreaData.value), "currentTotalReserve").map((row) => [
    row.name,
    formatNumber(row.currentTotalReserve),
    formatNumber(row.currentInbound),
    formatNumber(row.currentReserve),
    formatNumber(row.previousTotalReserve),
    formatNumber(row.previousInbound),
    formatNumber(row.previousReserve),
    deltaCell(row.reserveDiff, compareAreaReserveMaxReserve.value),
    deltaCell(row.inboundDiff, compareAreaReserveMaxInbound.value),
    deltaCell(row.reserveQtyDiff, compareAreaReserveMaxReserveQty.value),
  ])
);

const compareProvinceData = computed(() =>
  buildCompareDimensionRows(
    state.datasets.compareProvince,
    state.datasets.compareNational?.rows || [],
    state.compareScenario,
    { includeNational: true }
  )
);

const filteredCompareProvinceData = computed(() =>
  filterProvinceRows(compareProvinceData.value).filter((row) => row.name !== "全国")
);

const compareProvinceMaxReserve = computed(() =>
  maxAbs(filterProvinceRows(compareProvinceData.value).map((row) => row.reserveDiff))
);
const compareProvinceMaxRevenue = computed(() =>
  maxAbs(filterProvinceRows(compareProvinceData.value).map((row) => row.revenueDiff))
);
const compareProvinceMaxRate = computed(() =>
  maxAbs(filterProvinceRows(compareProvinceData.value).map((row) => row.rateDiff))
);

const compareProvinceRows = computed(() =>
  sortWithNationalFirst(filterProvinceRows(compareProvinceData.value), "currentTotalRevenue").map((row) => [
    resolveProvinceAreaName(row),
    row.name,
    formatNumber(row.targetRevenue),
    formatNumber(row.currentTotalReserve),
    formatNumber(row.currentTotalRevenue),
    formatRate(row.currentRate),
    formatNumber(row.previousTotalReserve),
    formatNumber(row.previousTotalRevenue),
    formatRate(row.previousRate),
    deltaCell(row.reserveDiff, compareProvinceMaxReserve.value),
    deltaCell(row.revenueDiff, compareProvinceMaxRevenue.value),
    deltaCell(row.rateDiff, compareProvinceMaxRate.value, true),
  ])
);

const compareProvinceReserveMaxReserve = computed(() => maxAbs(filterProvinceRows(compareProvinceData.value).map((row) => row.reserveDiff)));
const compareProvinceReserveMaxInbound = computed(() => maxAbs(filterProvinceRows(compareProvinceData.value).map((row) => row.inboundDiff)));
const compareProvinceReserveMaxReserveQty = computed(() => maxAbs(filterProvinceRows(compareProvinceData.value).map((row) => row.reserveQtyDiff)));

const compareProvinceReserveRows = computed(() =>
  sortWithNationalFirst(filterProvinceRows(compareProvinceData.value), "currentTotalReserve").map((row) => [
    resolveProvinceAreaName(row),
    row.name,
    formatNumber(row.currentTotalReserve),
    formatNumber(row.currentInbound),
    formatNumber(row.currentReserve),
    formatNumber(row.previousTotalReserve),
    formatNumber(row.previousInbound),
    formatNumber(row.previousReserve),
    deltaCell(row.reserveDiff, compareProvinceReserveMaxReserve.value),
    deltaCell(row.inboundDiff, compareProvinceReserveMaxInbound.value),
    deltaCell(row.reserveQtyDiff, compareProvinceReserveMaxReserveQty.value),
  ])
);

const compareOverviewSourceRow = computed(() => {
  if (!compareEnabled.value) {
    return null;
  }
  if (appliedProvinces.value.length) {
    return summarizeCompareDimensionRows(filteredCompareProvinceData.value);
  }
  if (appliedAreas.value.length) {
    return summarizeCompareDimensionRows(filteredCompareAreaData.value);
  }
  return compareAreaData.value.find((row) => row.name === "全国") || null;
});

const compareOverviewGroups = computed(() => {
  if (!compareEnabled.value || !compareOverviewSourceRow.value) {
    return { performance: [], reserve: [] };
  }
  const row = compareOverviewSourceRow.value;
  const performance = [
    {
      label: `${scenarioLabel(state.compareScenario)}总预测业绩`,
      value: formatNumber(row.currentTotalRevenue),
      diff: formatSignedNumber(row.revenueDiff),
      diffClass: deltaClass(row.revenueDiff),
      previous: formatNumber(row.previousTotalRevenue),
      diffValue: row.revenueDiff,
    },
    {
      label: "预测业绩",
      value: formatNumber(row.currentForecast),
      diff: formatSignedNumber(row.forecastDiff),
      diffClass: deltaClass(row.forecastDiff),
      previous: formatNumber(row.previousForecast),
      diffValue: row.forecastDiff,
    },
    {
      label: "已达成预测业绩",
      value: formatNumber(row.currentAchieved),
      diff: formatSignedNumber(row.achievedDiff),
      diffClass: deltaClass(row.achievedDiff),
      previous: formatNumber(row.previousAchieved),
      diffValue: row.achievedDiff,
    },
  ];
  const reserve = [
    {
      label: `${scenarioLabel(state.compareScenario)}总储备量`,
      value: formatNumber(row.currentTotalReserve),
      diff: formatSignedNumber(row.reserveDiff),
      diffClass: deltaClass(row.reserveDiff),
      previous: formatNumber(row.previousTotalReserve),
      diffValue: row.reserveDiff,
    },
    {
      label: "储备量",
      value: formatNumber(row.currentReserve),
      diff: formatSignedNumber(row.reserveQtyDiff),
      diffClass: deltaClass(row.reserveQtyDiff),
      previous: formatNumber(row.previousReserve),
      diffValue: row.reserveQtyDiff,
    },
    {
      label: "已进线量",
      value: formatNumber(row.currentInbound),
      diff: formatSignedNumber(row.inboundDiff),
      diffClass: deltaClass(row.inboundDiff),
      previous: formatNumber(row.previousInbound),
      diffValue: row.inboundDiff,
    },
  ];
  const maxDiff = Math.max(1, ...[...performance, ...reserve].map((card) => Math.abs(num(card.diffValue))));
  return {
    performance: performance.map((card) => ({
      ...card,
      diffStyle: deltaBadgeStyle(card.diffValue, maxDiff),
    })),
    reserve: reserve.map((card) => ({
      ...card,
      diffStyle: deltaBadgeStyle(card.diffValue, maxDiff),
    })),
  };
});

const compareCityData = computed(() =>
  aggregateCompareCity(
    filterDetailRows(state.datasets.currentReserveDetail),
    filterDetailRows(state.datasets.previousReserveDetail),
    state.compareScenario
  )
);

function applyMetricFilter(rows, filterState) {
  const metric = filterState?.metric || "reserveDiff";
  const firstOperator = filterState?.firstOperator || "";
  const secondOperator = filterState?.secondOperator || "";
  const logic = filterState?.logic === "or" ? "or" : "and";
  const firstThreshold = optionalNumber(filterState?.firstValue);
  const secondThreshold = optionalNumber(filterState?.secondValue);

  if (!firstOperator && !secondOperator) {
    return rows;
  }

  return rows.filter((row) => {
    const value = num(row[metric]);
    const firstMatch = firstOperator ? compareByOperator(value, firstOperator, firstThreshold) : true;
    const secondMatch = secondOperator ? compareByOperator(value, secondOperator, secondThreshold) : true;
    if (firstOperator && secondOperator) {
      return logic === "or" ? firstMatch || secondMatch : firstMatch && secondMatch;
    }
    if (firstOperator) {
      return firstMatch;
    }
    if (secondOperator) {
      return secondMatch;
    }
    return true;
  });
}

function buildCompareCityTotalRow(rows) {
  return {
    areaName: "总计",
    provinceName: "-",
    cityLabel: "-",
    currentReserve: rows.reduce((sum, row) => sum + num(row.currentReserve), 0),
    currentForecast: rows.reduce((sum, row) => sum + num(row.currentForecast), 0),
    previousReserve: rows.reduce((sum, row) => sum + num(row.previousReserve), 0),
    previousForecast: rows.reduce((sum, row) => sum + num(row.previousForecast), 0),
    reserveDiff: rows.reduce((sum, row) => sum + num(row.reserveDiff), 0),
    forecastDiff: rows.reduce((sum, row) => sum + num(row.forecastDiff), 0),
  };
}

function buildCompareCityTableRows(rows, maxReserveDiff, maxForecastDiff) {
  return rows.map((row) => [
    row.areaName || "-",
    row.provinceName || "-",
    row.cityLabel,
    formatNumber(row.currentReserve),
    formatNumber(row.currentForecast),
    formatNumber(row.previousReserve),
    formatNumber(row.previousForecast),
    deltaCell(row.reserveDiff, maxReserveDiff),
    deltaCell(row.forecastDiff, maxForecastDiff),
  ]);
}

function buildCompareCityCourseLineTableRows(courseLine, rows, maxReserveDiff, maxForecastDiff) {
  return rows.map((row) => [
    courseLine,
    row.areaName || "-",
    row.provinceName || "-",
    row.cityLabel,
    formatNumber(row.currentReserve),
    formatNumber(row.currentForecast),
    formatNumber(row.previousReserve),
    formatNumber(row.previousForecast),
    deltaCell(row.reserveDiff, maxReserveDiff),
    deltaCell(row.forecastDiff, maxForecastDiff),
  ]);
}

function getCityCourseLineFilterState(courseLine) {
  return state.cityCourseLineFilters[courseLine] || createMetricRangeFilterState("reserveDiff");
}

function updateCityCourseLineFilter(courseLine, field, value) {
  if (!state.cityCourseLineFilters[courseLine]) {
    state.cityCourseLineFilters[courseLine] = createMetricRangeFilterState("reserveDiff");
  }
  state.cityCourseLineFilters[courseLine][field] = value;
}

function buildCompareBdTargetTotalRow(rows) {
  const targetRevenue = rows.reduce((sum, row) => sum + num(row.targetRevenue), 0);
  const currentTotalRevenue = rows.reduce((sum, row) => sum + num(row.currentTotalRevenue), 0);
  const previousTotalRevenue = rows.reduce((sum, row) => sum + num(row.previousTotalRevenue), 0);
  return {
    areaName: "总计",
    name: "-",
    targetRevenue,
    currentTotalReserve: rows.reduce((sum, row) => sum + num(row.currentTotalReserve), 0),
    currentTotalRevenue,
    currentRate: targetRevenue ? currentTotalRevenue / targetRevenue : 0,
    previousTotalReserve: rows.reduce((sum, row) => sum + num(row.previousTotalReserve), 0),
    previousTotalRevenue,
    previousRate: targetRevenue ? previousTotalRevenue / targetRevenue : 0,
    reserveDiff: rows.reduce((sum, row) => sum + num(row.reserveDiff), 0),
    revenueDiff: rows.reduce((sum, row) => sum + num(row.revenueDiff), 0),
    rateDiff: (targetRevenue ? currentTotalRevenue / targetRevenue : 0) - (targetRevenue ? previousTotalRevenue / targetRevenue : 0),
  };
}

function buildCompareBdReserveTotalRow(rows) {
  return {
    areaName: "总计",
    name: "-",
    currentTotalReserve: rows.reduce((sum, row) => sum + num(row.currentTotalReserve), 0),
    currentInbound: rows.reduce((sum, row) => sum + num(row.currentInbound), 0),
    currentReserve: rows.reduce((sum, row) => sum + num(row.currentReserve), 0),
    previousTotalReserve: rows.reduce((sum, row) => sum + num(row.previousTotalReserve), 0),
    previousInbound: rows.reduce((sum, row) => sum + num(row.previousInbound), 0),
    previousReserve: rows.reduce((sum, row) => sum + num(row.previousReserve), 0),
    reserveDiff: rows.reduce((sum, row) => sum + num(row.reserveDiff), 0),
    inboundDiff: rows.reduce((sum, row) => sum + num(row.inboundDiff), 0),
    reserveQtyDiff: rows.reduce((sum, row) => sum + num(row.reserveQtyDiff), 0),
  };
}

const BD_DELTA_CELL_OPTIONS = {
  minAlpha: 0.1,
  maxAlpha: 0.52,
  gamma: 0.78,
};

function buildCompareBdTargetTableRows(rows) {
  const displayRows = [buildCompareBdTargetTotalRow(rows), ...rows];
  const maxReserveDiff = maxAbs(rows.map((row) => row.reserveDiff));
  const maxRevenueDiff = maxAbs(rows.map((row) => row.revenueDiff));
  const maxRateDiff = maxAbs(rows.map((row) => row.rateDiff));
  return displayRows.map((row) => [
    resolveBdAreaName(row, compareBdScopeMap.value),
    row.name,
    formatNumber(row.targetRevenue),
    formatNumber(row.currentTotalReserve),
    formatNumber(row.currentTotalRevenue),
    formatRate(row.currentRate),
    formatNumber(row.previousTotalReserve),
    formatNumber(row.previousTotalRevenue),
    formatRate(row.previousRate),
    deltaCell(row.reserveDiff, maxReserveDiff, BD_DELTA_CELL_OPTIONS),
    deltaCell(row.revenueDiff, maxRevenueDiff, BD_DELTA_CELL_OPTIONS),
    deltaCell(row.rateDiff, maxRateDiff, { ...BD_DELTA_CELL_OPTIONS, rate: true }),
  ]);
}

function buildCompareBdReserveTableRows(rows) {
  const displayRows = [buildCompareBdReserveTotalRow(rows), ...rows];
  const maxReserveDiff = maxAbs(rows.map((row) => row.reserveDiff));
  const maxInboundDiff = maxAbs(rows.map((row) => row.inboundDiff));
  const maxReserveQtyDiff = maxAbs(rows.map((row) => row.reserveQtyDiff));
  return displayRows.map((row) => [
    resolveBdAreaName(row, compareBdScopeMap.value),
    row.name,
    formatNumber(row.currentTotalReserve),
    formatNumber(row.currentInbound),
    formatNumber(row.currentReserve),
    formatNumber(row.previousTotalReserve),
    formatNumber(row.previousInbound),
    formatNumber(row.previousReserve),
    deltaCell(row.reserveDiff, maxReserveDiff, BD_DELTA_CELL_OPTIONS),
    deltaCell(row.inboundDiff, maxInboundDiff, BD_DELTA_CELL_OPTIONS),
    deltaCell(row.reserveQtyDiff, maxReserveQtyDiff, BD_DELTA_CELL_OPTIONS),
  ]);
}

const compareCityRows = computed(() => {
  const rows = applyMetricFilter(compareCityData.value.rows.slice(1), state.cityFilters);
  return buildCompareCityTableRows(
    [buildCompareCityTotalRow(rows), ...rows],
    compareCityData.value.maxReserveDiff,
    compareCityData.value.maxForecastDiff
  );
});

const compareCityCourseLineSections = computed(() =>
  compareCityData.value.sections.map((section) => ({
    ...section,
    filterState: getCityCourseLineFilterState(section.courseLine),
    tableRows: buildCompareCityCourseLineTableRows(
      section.courseLine,
      [
        buildCompareCityTotalRow(applyMetricFilter(section.rows.slice(1), getCityCourseLineFilterState(section.courseLine))),
        ...applyMetricFilter(section.rows.slice(1), getCityCourseLineFilterState(section.courseLine)),
      ],
      compareCityData.value.maxReserveDiff,
      compareCityData.value.maxForecastDiff
    ),
  }))
);

const compareCityCourseLineOptions = computed(() =>
  compareCityCourseLineSections.value.map((section) => section.courseLine)
);

const activeCompareCityCourseLine = computed(() =>
  resolveActiveCourseLine(state.compareCityCourseLine, compareCityCourseLineOptions.value)
);

const selectedCompareCityCourseLineSection = computed(() =>
  compareCityCourseLineSections.value.find((section) => section.courseLine === activeCompareCityCourseLine.value) || null
);

const compareBdData = computed(() =>
  buildCompareDimensionRows(state.datasets.compareBd, [], state.compareScenario)
);

const filteredCompareBdData = computed(() =>
  [...filterBdRows(compareBdData.value, compareBdScopeMap.value)].sort(
    (left, right) => right.currentTotalReserve - left.currentTotalReserve
  )
);

const compareBdTargetRows = computed(() => {
  const rows = applyMetricFilter(filteredCompareBdData.value, state.bdTargetFilters);
  return buildCompareBdTargetTableRows(rows);
});

const compareBdReserveRows = computed(() => {
  const rows = applyMetricFilter(filteredCompareBdData.value, state.bdReserveFilters);
  return buildCompareBdReserveTableRows(rows);
});

let messageTimerId = 0;

function clearMessage() {
  state.uploadMessage = "";
  state.uploadMessageType = "";
}

function setMessage(message, type = "success") {
  if (messageTimerId) {
    window.clearTimeout(messageTimerId);
    messageTimerId = 0;
  }

  state.uploadMessage = message;
  state.uploadMessageType = type;

  const timeoutMs = type === "error" ? 5000 : 3000;
  if (!message) {
    return;
  }

  messageTimerId = window.setTimeout(() => {
    clearMessage();
    messageTimerId = 0;
  }, timeoutMs);
}

function clearDatasets() {
  state.datasets.currentMonthlyClass = [];
  state.datasets.currentMonthlyClassMeta = {};
  state.datasets.previousMonthlyClass = [];
  state.datasets.previousMonthlyClassMeta = {};
  state.datasets.currentMonthlyTarget = [];
  state.datasets.previousMonthlyTarget = [];
  state.datasets.currentInbound = [];
  state.datasets.previousInbound = [];
  state.datasets.currentReserveDetail = [];
  state.datasets.previousReserveDetail = [];
  state.datasets.singleNational = [];
  state.datasets.singleArea = [];
  state.datasets.singleProvince = [];
  state.datasets.singleBd = [];
  state.datasets.compareNational = null;
  state.datasets.compareArea = [];
  state.datasets.compareProvince = [];
  state.datasets.compareBd = [];
}

function extractMessage(body, fallback) {
  const raw = body?.message || body?.detail;
  if (!raw) return fallback;
  if (typeof raw === "string") return raw;
  if (Array.isArray(raw)) return raw.map((e) => e?.msg || JSON.stringify(e)).join("; ");
  return JSON.stringify(raw);
}

async function apiGet(path) {
  const response = await fetch(path, {
    credentials: "same-origin",
    headers: authHeaders(),
  });
  const contentType = response.headers.get("content-type") || "";
  const body = contentType.includes("application/json")
    ? await response.json()
    : { message: await response.text() };
  if (response.status === 401) {
    logout();
    throw new Error("登录已过期，请重新登录");
  }
  if (!response.ok || (body.code != null && body.code >= 400)) {
    throw new Error(extractMessage(body, "请求失败"));
  }
  return body.data;
}

async function apiUpload(formData) {
  const response = await fetch("/api/uploads/monthly-batch", {
    method: "POST",
    body: formData,
    credentials: "same-origin",
    headers: authHeaders(),
  });
  let body;
  try {
    body = await response.json();
  } catch {
    throw new Error(`上传失败（HTTP ${response.status}）：服务器返回了非 JSON 响应`);
  }
  if (!response.ok || (body.code != null && body.code >= 400)) {
    throw new Error(extractMessage(body, "上传失败"));
  }
  return body.data;
}

async function apiDelete(path) {
  const response = await fetch(path, {
    method: "DELETE",
    credentials: "same-origin",
    headers: authHeaders(),
  });
  const body = await response.json();
  if (response.status === 401) { logout(); throw new Error("登录已过期，请重新登录"); }
  if (!response.ok || (body.code != null && body.code >= 400)) throw new Error(extractMessage(body, "删除失败"));
  return body;
}

function getFilenameFromDisposition(disposition) {
  if (!disposition) {
    return "";
  }
  const utf8Match = disposition.match(/filename\*=UTF-8''([^;]+)/i);
  if (utf8Match?.[1]) {
    return decodeURIComponent(utf8Match[1]);
  }
  const plainMatch = disposition.match(/filename="?([^";]+)"?/i);
  return plainMatch?.[1] || "";
}

async function downloadCompletedWorkbook() {
  if (!canDownloadCompletedTable.value) {
    setMessage("当前账号未开启复制 / 下载权限。", "error");
    return;
  }
  if (!state.selectedPeriod || !state.selectedUploadSeq) {
    return;
  }

  try {
    const query = `period_code=${encodeURIComponent(state.selectedPeriod)}&upload_seq=${state.selectedUploadSeq}`;
    const response = await fetch(`/api/exports/completed-workbook?${query}`, {
      credentials: "same-origin",
      headers: authHeaders(),
    });

    if (response.status === 401) {
      logout();
      throw new Error("登录已过期，请重新登录");
    }

    if (!response.ok) {
      const contentType = response.headers.get("content-type") || "";
      const payload = contentType.includes("application/json")
        ? await response.json()
        : { detail: await response.text() };
      throw new Error(payload.message || payload.detail || "下载失败");
    }

    const blob = await response.blob();
    const objectUrl = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = objectUrl;
    link.download = getFilenameFromDisposition(response.headers.get("content-disposition"))
      || `${buildWorkbookBaseName(currentUpload.value, state.selectedPeriod)}.xlsx`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(objectUrl);
  } catch (error) {
    setMessage(error.message || "下载失败", "error");
  }
}

async function loadPeriods(preferredPeriod = "", preferredUploadSeq = null) {
  state.periods = await apiGet("/api/periods");
  if (!state.periods.length) {
    state.selectedPeriod = "";
    state.uploads = [];
    state.selectedUploadSeq = null;
    state.showUploadPanel = true;
    clearDatasets();
    return;
  }

  const targetPeriod = state.periods.some((period) => period.period_code === preferredPeriod)
    ? preferredPeriod
    : state.periods[0].period_code;
  state.selectedPeriod = targetPeriod;
  await loadUploads(preferredUploadSeq);
}

async function loadUploads(preferredUploadSeq = null) {
  if (!state.selectedPeriod) {
    state.uploads = [];
    state.selectedUploadSeq = null;
    state.showUploadPanel = true;
    clearDatasets();
    return;
  }

  state.uploads = await apiGet(`/api/periods/${encodeURIComponent(state.selectedPeriod)}/uploads`);
  if (!state.uploads.length) {
    state.selectedUploadSeq = null;
    state.showUploadPanel = true;
    clearDatasets();
    return;
  }

  const hasPreferred = state.uploads.some((upload) => upload.upload_seq === preferredUploadSeq);
  state.selectedUploadSeq = hasPreferred ? preferredUploadSeq : state.uploads[0].upload_seq;
  await loadDatasets();
}

async function loadDatasets() {
  if (!state.selectedPeriod || !state.selectedUploadSeq) {
    clearDatasets();
    return;
  }

  state.loadingData = true;
  try {
    const previousSeq = currentUpload.value?.compare_previous_upload_seq || null;
    const requests = [
      apiGet(`/api/exports/completed-table?period_code=${encodeURIComponent(state.selectedPeriod)}&upload_seq=${state.selectedUploadSeq}&table_type=monthly_class`),
      apiGet(`/api/exports/completed-table?period_code=${encodeURIComponent(state.selectedPeriod)}&upload_seq=${state.selectedUploadSeq}&table_type=monthly_target`),
      apiGet(`/api/exports/completed-table?period_code=${encodeURIComponent(state.selectedPeriod)}&upload_seq=${state.selectedUploadSeq}&table_type=inbound`),
      apiGet(`/api/exports/completed-table?period_code=${encodeURIComponent(state.selectedPeriod)}&upload_seq=${state.selectedUploadSeq}&table_type=reserve_detail`),
      apiGet(`/api/dashboard/single?period_code=${encodeURIComponent(state.selectedPeriod)}&upload_seq=${state.selectedUploadSeq}&dimension_level=national&scenario=all`),
      apiGet(`/api/dashboard/single?period_code=${encodeURIComponent(state.selectedPeriod)}&upload_seq=${state.selectedUploadSeq}&dimension_level=area&scenario=all`),
      apiGet(`/api/dashboard/single?period_code=${encodeURIComponent(state.selectedPeriod)}&upload_seq=${state.selectedUploadSeq}&dimension_level=province&scenario=all`),
      apiGet(`/api/dashboard/single?period_code=${encodeURIComponent(state.selectedPeriod)}&upload_seq=${state.selectedUploadSeq}&dimension_level=bd&scenario=all`),
      previousSeq
        ? apiGet(`/api/exports/completed-table?period_code=${encodeURIComponent(state.selectedPeriod)}&upload_seq=${previousSeq}&table_type=monthly_class`)
        : Promise.resolve({ rows: [] }),
      previousSeq
        ? apiGet(`/api/exports/completed-table?period_code=${encodeURIComponent(state.selectedPeriod)}&upload_seq=${previousSeq}&table_type=monthly_target`)
        : Promise.resolve({ rows: [] }),
      previousSeq
        ? apiGet(`/api/exports/completed-table?period_code=${encodeURIComponent(state.selectedPeriod)}&upload_seq=${previousSeq}&table_type=inbound`)
        : Promise.resolve({ rows: [] }),
      previousSeq
        ? apiGet(`/api/exports/completed-table?period_code=${encodeURIComponent(state.selectedPeriod)}&upload_seq=${previousSeq}&table_type=reserve_detail`)
        : Promise.resolve({ rows: [] }),
      previousSeq
        ? apiGet(`/api/dashboard/compare?period_code=${encodeURIComponent(state.selectedPeriod)}&upload_seq=${state.selectedUploadSeq}&dimension_level=national&scenario=all`)
        : Promise.resolve({ show_compare: false, rows: [], message: "当前批次为当月首期，暂无上期对比数据。" }),
      previousSeq
        ? apiGet(`/api/dashboard/compare?period_code=${encodeURIComponent(state.selectedPeriod)}&upload_seq=${state.selectedUploadSeq}&dimension_level=area&scenario=all`)
        : Promise.resolve({ rows: [] }),
      previousSeq
        ? apiGet(`/api/dashboard/compare?period_code=${encodeURIComponent(state.selectedPeriod)}&upload_seq=${state.selectedUploadSeq}&dimension_level=province&scenario=all`)
        : Promise.resolve({ rows: [] }),
      previousSeq
        ? apiGet(`/api/dashboard/compare?period_code=${encodeURIComponent(state.selectedPeriod)}&upload_seq=${state.selectedUploadSeq}&dimension_level=bd&scenario=all`)
        : Promise.resolve({ rows: [] }),
    ];

    const [
      currentMonthlyClass,
      currentMonthlyTarget,
      currentInbound,
      currentReserveDetail,
      singleNational,
      singleArea,
      singleProvince,
      singleBd,
      previousMonthlyClass,
      previousMonthlyTarget,
      previousInbound,
      previousReserveDetail,
      compareNational,
      compareArea,
      compareProvince,
      compareBd,
    ] = await Promise.all(requests);

    state.datasets.currentMonthlyClass = currentMonthlyClass.rows || [];
    state.datasets.currentMonthlyClassMeta = currentMonthlyClass.meta || {};
    state.datasets.currentMonthlyTarget = currentMonthlyTarget.rows || [];
    state.datasets.currentInbound = currentInbound.rows || [];
    state.datasets.currentReserveDetail = currentReserveDetail.rows || [];
    state.datasets.singleNational = singleNational.rows || [];
    state.datasets.singleArea = singleArea.rows || [];
    state.datasets.singleProvince = singleProvince.rows || [];
    state.datasets.singleBd = singleBd.rows || [];
    state.datasets.previousMonthlyClass = previousMonthlyClass.rows || [];
    state.datasets.previousMonthlyClassMeta = previousMonthlyClass.meta || {};
    state.datasets.previousMonthlyTarget = previousMonthlyTarget.rows || [];
    state.datasets.previousInbound = previousInbound.rows || [];
    state.datasets.previousReserveDetail = previousReserveDetail.rows || [];
    state.datasets.compareNational = compareNational;
    state.datasets.compareArea = compareArea.rows || [];
    state.datasets.compareProvince = compareProvince.rows || [];
    state.datasets.compareBd = compareBd.rows || [];
  } finally {
    state.loadingData = false;
  }
}

function handleFileChange(event) {
  state.selectedFile = event.target.files?.[0] || null;
}

function resetUploadSelection() {
  state.selectedFile = null;
  if (uploadInputRef.value) {
    uploadInputRef.value.value = "";
  }
}

function openUploadPanel() {
  state.showUploadPanel = true;
}

function toggleUploadPanel() {
  if (uploadPanelVisible.value && state.uploads.length) {
    state.showUploadPanel = false;
    resetUploadSelection();
    return;
  }
  openUploadPanel();
}

async function submitUpload() {
  if (!state.selectedFile) {
    setMessage("请先选择要上传的 xlsx 文件。", "error");
    return;
  }

  const formData = new FormData();
  formData.append("file", state.selectedFile);
  if (state.uploadedBy.trim()) {
    formData.append("uploaded_by", state.uploadedBy.trim());
  }

  state.loadingData = true;
  try {
    const result = await apiUpload(formData);
    setMessage(`上传完成：${result.workbook_filename}`, "success");
    state.activeView = "single";
    resetUploadSelection();
    state.uploadedBy = "";
    state.showUploadPanel = false;
    await loadPeriods(result.period_code, result.upload_seq);
  } catch (error) {
    setMessage(error.message || "上传失败", "error");
  } finally {
    state.loadingData = false;
  }
}

async function refreshCurrentBatch() {
  try {
    await loadDatasets();
    setMessage("当前批次数据已刷新。", "success");
  } catch (error) {
    setMessage(error.message || "刷新失败", "error");
  }
}

async function deleteCurrentBatch() {
  if (!state.selectedPeriod || !state.selectedUploadSeq) return;
  deleteConfirming.value = true;

  // 记录删除前的状态，用于删除后的跳转决策
  const deletedPeriod = state.selectedPeriod;
  const deletedSeq = state.selectedUploadSeq;
  const uploadsBeforeDelete = [...state.uploads];

  try {
    await apiDelete(
      `/api/periods/${encodeURIComponent(deletedPeriod)}/uploads/${deletedSeq}`
    );
    showDeleteDialog.value = false;
    setMessage("批次已删除", "success");

    // 同期还有其他批次：优先跳到同期中 seq 最近的那个（删掉的前一个，若没有则后一个）
    const deletedIndex = uploadsBeforeDelete.findIndex((u) => u.upload_seq === deletedSeq);
    const remainingInPeriod = uploadsBeforeDelete.filter((u) => u.upload_seq !== deletedSeq);

    if (remainingInPeriod.length > 0) {
      // 找同期里小于 deletedSeq 的最大值（即前一个），否则取第一个（后一个）
      const fallback =
        remainingInPeriod[Math.min(Math.max(deletedIndex, 0), remainingInPeriod.length - 1)] ||
        remainingInPeriod[0];
      await loadPeriods(deletedPeriod, fallback.upload_seq);
    } else {
      // 该期已无批次，loadPeriods 会 fallback 到 periods[0]（后端已删除该期记录）
      await loadPeriods();
    }
  } catch (error) {
    setMessage(error.message || "删除失败", "error");
  } finally {
    deleteConfirming.value = false;
  }
}

function handleDocumentClick() {
  cancelLocationFilterEditing();
}

onMounted(async () => {
  loadStoredAuth();
  if (authUser.value) {
    try {
      await loadPeriods();
    } catch (error) {
      setMessage(error.message || "初始化失败", "error");
    }
  }
  document.addEventListener("click", handleDocumentClick);
});

onBeforeUnmount(() => {
  if (messageTimerId) {
    window.clearTimeout(messageTimerId);
    messageTimerId = 0;
  }
  document.removeEventListener("click", handleDocumentClick);
});
</script>

<template>
  <LoginPage v-if="!authUser" @login-success="onLoginSuccess($event); loadPeriods()" />
  <div v-else class="dashboard-shell">
    <header class="global-header">
      <div class="header-brand">
        <img class="header-logo" :src="brandIconUrl" alt="点猫科技 编程猫" />
        <div class="header-copy">
          <h1>储备数据可视化看板</h1>
          <div class="header-chip-row">
            <span class="header-chip">当前选择：{{ currentSelectionText }}</span>
            <span class="header-chip" :class="{ muted: !compareEnabled }">
              对比基线：{{ currentCompareText }}
            </span>
          </div>
        </div>
      </div>

      <div class="header-toolbar">
        <label class="header-filter">
          <span class="header-filter-label">班期时间</span>
          <select v-model="state.selectedPeriod" @change="loadUploads()">
            <option v-for="period in state.periods" :key="period.period_code" :value="period.period_code">
              {{ period.period_code }}
            </option>
          </select>
        </label>
        <label class="header-filter">
          <span class="header-filter-label">批次版本</span>
          <select v-model.number="state.selectedUploadSeq" @change="loadDatasets()">
            <option v-for="upload in state.uploads" :key="upload.batch_id" :value="upload.upload_seq">
              {{ formatUploadSelectLabel(upload) }}
            </option>
          </select>
        </label>
        <div class="header-filter area-filter-wrap">
          <span class="header-filter-label">片区</span>
          <div class="province-dropdown-trigger" @click.stop="toggleAreaDropdown">
            <span class="province-trigger-text">
              {{ areaTriggerText }}
            </span>
            <span class="province-trigger-arrow">▾</span>
          </div>
          <div v-if="state.areaDropdownOpen" class="province-dropdown" @click.stop>
            <div class="province-dropdown-actions">
              <button type="button" @click="selectAllAreas">全选</button>
              <button type="button" @click="clearAreas">清除</button>
              <button type="button" class="dropdown-confirm-btn" @click="applyFilters">确认</button>
            </div>
            <label v-for="area in areaOptions" :key="area" class="province-option">
              <input type="checkbox" :checked="state.areaFilter.includes(area)" @change="toggleArea(area)" />
              {{ area }}
            </label>
          </div>
        </div>
        <div class="header-filter province-filter-wrap">
          <span class="header-filter-label">省份</span>
          <div class="province-dropdown-trigger" @click.stop="toggleProvinceDropdown">
            <span class="province-trigger-text">
              {{ provinceTriggerText }}
            </span>
            <span class="province-trigger-arrow">▾</span>
          </div>
          <div v-if="state.provinceDropdownOpen" class="province-dropdown" @click.stop>
            <div class="province-dropdown-actions">
              <button type="button" @click="selectAllProvinces">全选</button>
              <button type="button" @click="clearProvinces">清除</button>
              <button type="button" class="dropdown-confirm-btn" @click="applyFilters">确认</button>
            </div>
            <label v-for="p in provinceOptions" :key="p" class="province-option">
              <input type="checkbox" :checked="state.provinceFilter.includes(p)" @change="toggleProvince(p)" />
              {{ p }}
            </label>
          </div>
        </div>
        <div class="header-actions">
          <button
            v-if="isSuperAdmin"
            class="action-btn secondary action-btn-icon"
            type="button"
            @click="toggleUploadPanel"
          >
            <svg viewBox="0 0 20 20" aria-hidden="true">
              <path d="M10 2.5a.75.75 0 0 1 .75.75v7.19l2.72-2.72a.75.75 0 1 1 1.06 1.06l-4 4a.75.75 0 0 1-1.06 0l-4-4a.75.75 0 0 1 1.06-1.06l2.72 2.72V3.25A.75.75 0 0 1 10 2.5Zm-5.75 11a.75.75 0 0 1 .75.75v1.25c0 .14.11.25.25.25h9.5a.25.25 0 0 0 .25-.25v-1.25a.75.75 0 0 1 1.5 0v1.25a1.75 1.75 0 0 1-1.75 1.75h-9.5a1.75 1.75 0 0 1-1.75-1.75v-1.25a.75.75 0 0 1 .75-.75Z" />
            </svg>
            <span>{{ uploadButtonLabel }}</span>
          </button>
          <button v-if="appliedAreas.length || appliedProvinces.length" class="action-btn secondary" type="button" @click="resetLocationFilters">重置筛选</button>
          <button v-if="downloadAvailable && canDownloadCompletedTable" class="action-btn secondary" type="button" @click="downloadCompletedWorkbook">下载补全表</button>
          <button class="action-btn" type="button" @click="refreshCurrentBatch">刷新数据</button>
          <button v-if="isSuperAdmin && downloadAvailable" class="action-btn danger" type="button" @click="showDeleteDialog = true">删除此批次</button>
          <button class="action-btn secondary" type="button" @click="showChangePasswordDialog = true">修改密码</button>
          <button v-if="isSuperAdmin" class="action-btn secondary" type="button" @click="showPermPanel = true">权限管理</button>
          <button class="action-btn danger" type="button" @click="confirmLogout">退出登录</button>
        </div>
      </div>
    </header>

    <div v-if="state.uploadMessage" class="message-box" :class="state.uploadMessageType">
      {{ state.uploadMessage }}
    </div>

    <section v-if="uploadPanelVisible" class="upload-panel-shell">
      <article class="card upload-panel-card">
        <div class="upload-panel-header">
          <div class="upload-panel-copy">
            <div class="card-title upload-panel-title">数据上传与处理</div>
            <p class="upload-panel-note">上传月度 xlsx 后会自动完成补全、入库和看板刷新。</p>
          </div>
          <button
            v-if="state.uploads.length"
            class="action-btn ghost upload-panel-close"
            type="button"
            @click="toggleUploadPanel"
          >
            收起
          </button>
        </div>

        <div class="upload-panel-grid">
          <section class="upload-panel-block">
            <h3 class="upload-block-title">上传新批次</h3>
            <div v-if="isSuperAdmin" class="form-stack">
              <label class="field">
                <span>上传文件</span>
                <input ref="uploadInputRef" type="file" accept=".xlsx" @change="handleFileChange" />
              </label>
              <div class="upload-file-chip" :class="{ empty: !state.selectedFile }">
                {{ selectedFilename }}
              </div>
              <label class="field">
                <span>上传人</span>
                <input v-model.trim="state.uploadedBy" type="text" placeholder="可选，记录本次上传人" />
              </label>
              <div class="form-actions">
                <button class="action-btn" type="button" :disabled="!state.selectedFile || state.loadingData" @click="submitUpload">
                  {{ state.loadingData ? "处理中..." : "上传并处理" }}
                </button>
                <button class="action-btn secondary upload-cancel-btn" type="button" :disabled="state.loadingData" @click="resetUploadSelection">
                  清空文件
                </button>
              </div>
            </div>
            <div v-else class="empty-state upload-empty-state">
              当前账号没有上传权限，请联系超级管理员上传新批次数据。
            </div>
          </section>

          <section class="upload-panel-block">
            <h3 class="upload-block-title">当前批次信息</h3>
            <div v-if="batchSummaryList.length" class="summary-list">
              <div v-for="item in batchSummaryList" :key="item.label" class="summary-item">
                <span>{{ item.label }}</span>
                <strong>{{ item.value }}</strong>
              </div>
            </div>
            <div v-else class="empty-state upload-empty-state">
              当前还没有可用批次，请先上传首个数据文件。
            </div>
          </section>
        </div>

        <section class="upload-history-block">
          <div class="upload-history-head">
            <h3 class="upload-block-title">批次历史</h3>
            <span class="upload-history-tip">上传完成后会自动刷新当前看板。</span>
          </div>
          <DataTable
            card-title="批次历史"
            :headers="HEADERS.uploadHistory"
            :rows="uploadHistoryRows"
          />
        </section>
      </article>
    </section>

    <nav class="main-nav">
      <button
        v-if="isSuperAdmin || perms.single?.enabled"
        class="main-nav-btn"
        :class="{ active: state.activeView === 'single' }"
        type="button"
        @click="state.activeView = 'single'"
      >
        本期看板
      </button>
      <button
        v-if="isSuperAdmin || perms.compare?.enabled"
        class="main-nav-btn"
        :class="{ active: state.activeView === 'compare' }"
        type="button"
        @click="state.activeView = 'compare'"
      >
        两期对比看板
      </button>
    </nav>

    <div v-show="state.activeView === 'single'" id="main-single">
      <nav class="sub-nav">
        <button v-if="canViewTab('single','overview')" class="sub-nav-btn" :class="{ active: state.singleTab === 'overview' }" type="button" @click="state.singleTab = 'overview'">
          总览与课线
        </button>
        <button v-if="canViewTab('single','area')" class="sub-nav-btn" :class="{ active: state.singleTab === 'area' }" type="button" @click="state.singleTab = 'area'">
          片区
        </button>
        <button v-if="canViewTab('single','region')" class="sub-nav-btn" :class="{ active: state.singleTab === 'region' }" type="button" @click="state.singleTab = 'region'">
          地区
        </button>
        <button v-if="canViewTab('single','bd')" class="sub-nav-btn" :class="{ active: state.singleTab === 'bd' }" type="button" @click="state.singleTab = 'bd'">
          BD
        </button>
      </nav>

      <div class="scenario-bar">
        <div class="toggle-group">
          <button class="toggle-btn" :class="{ active: state.singleScenario === 'base' }" type="button" @click="state.singleScenario = 'base'">保底</button>
          <button class="toggle-btn" :class="{ active: state.singleScenario === 'stretch' }" type="button" @click="state.singleScenario = 'stretch'">冲高</button>
        </div>
      </div>

      <div class="content">
        <div v-if="state.loadingData" class="empty-state page-loading">正在同步当前批次数据...</div>

        <template v-else>
          <div v-show="state.singleTab === 'overview'" class="section active">
            <div class="section-header">
              <h2>总储备看板</h2>
              <span class="badge">总览</span>
            </div>

            <div class="overview-row">
              <article class="card overview-panel">
                <div class="card-title">业绩板块</div>
                <MetricCard
                  :label="singleOverviewCards[0].label"
                  :value="singleOverviewCards[0].value"
                  :meta="singleOverviewCards[0].meta"
                  :progress="singleOverviewCards[0].progress"
                  :rate-text="singleOverviewCards[0].rateText"
                  :target-text="singleOverviewCards[0].targetText"
                  :accent="singleOverviewCards[0].accent"
                />
              </article>

              <article class="card overview-panel">
                <div class="card-title">储备板块</div>
                <MetricCard
                  :label="singleOverviewCards[1].label"
                  :value="singleOverviewCards[1].value"
                  :meta="singleOverviewCards[1].meta"
                  :progress="singleOverviewCards[1].progress"
                  :rate-text="singleOverviewCards[1].rateText"
                  :target-text="singleOverviewCards[1].targetText"
                  :accent="singleOverviewCards[1].accent"
                />
              </article>
            </div>

            <div class="section-divider"></div>

            <div class="section-header">
              <h2>课线项目看板</h2>
              <span class="badge">课线</span>
            </div>

            <template v-if="showLocationFilteredClassSections">
              <article class="card">
                <DataTable
                  card-title="班期总看板"
                  :filter-label="singleExportLabel"
                  :headers="HEADERS.classTotal"
                  :rows="singleClassTotalRows"
                  :total-row-index="singleClassTotalRows.length ? singleClassTotalRows.length - 1 : null"
                />
              </article>

              <article v-for="section in singleCourseLineSections" :key="section.name" class="card">
                <DataTable
                  :card-title="`${section.name}-课线班期看板`"
                  :filter-label="singleExportLabel"
                  :headers="HEADERS.classCourseLine"
                  :rows="section.tableRows"
                  :total-row-index="section.tableRows.length ? section.tableRows.length - 1 : null"
                />
              </article>
            </template>

            <article v-else class="card">
              <div class="empty-state">{{ locationFilterNotice }}</div>
            </article>
          </div>

          <div v-show="state.singleTab === 'area'" class="section active section--fit-width section--area-fit">
            <div class="section-header">
              <h2>片区看板</h2>
              <span class="badge">片区</span>
            </div>

            <div class="grid-2">
              <article class="card">
                <DataTable
                  card-title="片区-业绩看板"
                  :filter-label="singleExportLabel"
                  :headers="HEADERS.areaPerformance"
                  :rows="singleAreaPerformanceRows"
                  :pin-first-row="shouldPinNationalFirstRow(singleAreaPerformanceRows)"
                  table-class="wire-table table-progress-compact"
                />
              </article>
              <article class="card">
                <DataTable
                  card-title="片区-储备看板"
                  :filter-label="singleExportLabel"
                  :headers="HEADERS.areaReserve"
                  :rows="singleAreaReserveRows"
                  :pin-first-row="shouldPinNationalFirstRow(singleAreaReserveRows)"
                />
              </article>
            </div>

            <div class="grid-2">
              <article class="card">
                <div class="card-title">片区-各课线储备看板</div>
                <StackChart
                  :rows="singleAreaReserveChart"
                  note="横轴指标为储备量，纵轴为片区，分组为课线项目。"
                  single-series-legend
                  sort-visible-ascending
                  hide-track-background
                />
              </article>
              <article class="card">
                <div class="card-title">片区-各课线业绩看板</div>
                <StackChart
                  :rows="singleAreaForecastChart"
                  note="横轴指标为预测业绩，纵轴为片区，分组为课线项目。"
                  single-series-legend
                />
              </article>
            </div>

            <div v-if="singleAreaCourseLineOptions.length" class="course-line-switcher">
              <div class="course-line-switcher-label">课线切换</div>
              <div class="course-line-switcher-tabs">
                <button
                  v-for="courseLine in singleAreaCourseLineOptions"
                  :key="courseLine"
                  class="course-line-tab"
                  :class="{ active: courseLine === activeSingleAreaCourseLine }"
                  type="button"
                  @click="state.singleAreaCourseLine = courseLine"
                >
                  {{ courseLine }}
                </button>
              </div>
            </div>

            <article v-if="selectedSingleAreaCourseLineSection" class="card">
              <DataTable
                :card-title="`${selectedSingleAreaCourseLineSection.courseLine}-片区储备看板`"
                :filter-label="singleExportLabel"
                :headers="HEADERS.areaCourseLine"
                :rows="selectedSingleAreaCourseLineSection.tableRows"
                :total-row-index="0"
                disable-internal-scroll
              />
            </article>
          </div>

          <div v-show="state.singleTab === 'region'" class="section active section--fit-width">
            <div class="section-header">
              <h2>省份看板</h2>
              <span class="badge">省份 / 城市</span>
            </div>

            <div class="grid-2">
              <article class="card">
                <DataTable
                  card-title="省份-业绩看板"
                  :filter-label="singleExportLabel"
                  :headers="HEADERS.provincePerformance"
                  :rows="singleProvincePerformanceRows"
                  :pin-first-row="shouldPinNationalFirstRow(singleProvincePerformanceRows)"
                  table-class="wire-table table-progress-compact"
                />
              </article>
              <article class="card">
                <DataTable card-title="省份-储备看板" :filter-label="singleExportLabel" :headers="HEADERS.provinceReserve" :rows="singleProvinceReserveRows" :pin-first-row="shouldPinNationalFirstRow(singleProvinceReserveRows)" />
              </article>
            </div>

            <div class="section-divider"></div>

            <div class="section-header">
              <h2>城市看板</h2>
              <span class="badge">城市</span>
            </div>

            <article class="card">
              <DataTable card-title="城市-总储备看板" :filter-label="singleExportLabel" :headers="HEADERS.city" :rows="singleCityRows" :total-row-index="0" />
            </article>

            <div v-if="singleCityCourseLineOptions.length" class="course-line-switcher">
              <div class="course-line-switcher-label">课线切换</div>
              <div class="course-line-switcher-tabs">
                <button
                  v-for="courseLine in singleCityCourseLineOptions"
                  :key="courseLine"
                  class="course-line-tab"
                  :class="{ active: courseLine === activeSingleCityCourseLine }"
                  type="button"
                  @click="state.singleCityCourseLine = courseLine"
                >
                  {{ courseLine }}
                </button>
              </div>
            </div>

            <article v-if="selectedSingleCityCourseLineSection" class="card">
              <DataTable
                :card-title="`${selectedSingleCityCourseLineSection.courseLine}-城市储备看板`"
                :filter-label="singleExportLabel"
                :headers="HEADERS.cityCourseLine"
                :rows="selectedSingleCityCourseLineSection.tableRows"
                :total-row-index="0"
              />
            </article>
          </div>

          <div v-show="state.singleTab === 'bd'" class="section active section--fit-width">
            <div class="section-header">
              <h2>BD 看板</h2>
              <span class="badge">BD</span>
            </div>

            <div class="grid-2">
              <article class="card">
                <div class="card-title">BD 业绩排名看板</div>
                <RankChart :rows="singleBdPerformanceChart" :visible-count="15" />
              </article>
              <article class="card">
                <div class="card-title">BD 储备排名看板</div>
                <RankChart :rows="singleBdReserveChart" :visible-count="15" />
              </article>
            </div>

            <div class="grid-2">
              <article class="card">
                <DataTable
                  card-title="BD-业绩看板"
                  :filter-label="singleExportLabel"
                  :headers="HEADERS.bdPerformance"
                  :rows="singleBdPerformanceRows"
                  table-class="wire-table table-progress-compact"
                />
              </article>
              <article class="card">
                <DataTable card-title="BD-储备看板" :filter-label="singleExportLabel" :headers="HEADERS.bdReserve" :rows="singleBdReserveRows" />
              </article>
            </div>
          </div>
        </template>
      </div>
    </div>

    <div v-show="state.activeView === 'compare'" id="main-compare">
      <nav class="sub-nav">
        <button v-if="canViewTab('compare','overview')" class="sub-nav-btn" :class="{ active: state.compareTab === 'overview' }" type="button" @click="state.compareTab = 'overview'">
          总览与课线
        </button>
        <button v-if="canViewTab('compare','area')" class="sub-nav-btn" :class="{ active: state.compareTab === 'area' }" type="button" @click="state.compareTab = 'area'">
          片区
        </button>
        <button v-if="canViewTab('compare','region')" class="sub-nav-btn" :class="{ active: state.compareTab === 'region' }" type="button" @click="state.compareTab = 'region'">
          地区
        </button>
        <button v-if="canViewTab('compare','bd')" class="sub-nav-btn" :class="{ active: state.compareTab === 'bd' }" type="button" @click="state.compareTab = 'bd'">
          BD
        </button>
      </nav>

      <div class="scenario-bar">
        <div class="toggle-group">
          <button class="toggle-btn" :class="{ active: state.compareScenario === 'base' }" type="button" @click="state.compareScenario = 'base'">保底</button>
          <button class="toggle-btn" :class="{ active: state.compareScenario === 'stretch' }" type="button" @click="state.compareScenario = 'stretch'">冲高</button>
        </div>
      </div>

      <div class="content">
        <div v-if="state.loadingData" class="empty-state page-loading">正在同步两期对比数据...</div>
        <div v-else-if="!compareEnabled" class="empty-state page-loading">
          {{ state.datasets.compareNational?.message || "当前批次暂无可对比的上期数据。" }}
        </div>

        <template v-else>
          <div v-show="state.compareTab === 'overview'" class="section active">
            <div class="section-header">
              <h2>总储备看板</h2>
              <span class="badge">两期对比</span>
            </div>

            <article class="card">
              <div class="card-title">业绩板块</div>
              <div class="metric-row col-3">
                <article v-for="card in compareOverviewGroups.performance" :key="card.label" class="metric-card compare-card">
                  <div class="period-label">{{ card.label }}</div>
                  <div class="period-value">{{ card.value }}</div>
                  <div
                    class="delta"
                    :class="card.diffClass === 'delta-down' ? 'down' : card.diffClass === 'delta-up' ? 'up' : ''"
                    :style="card.diffStyle"
                  >
                    较上期 {{ card.diff }}
                  </div>
                  <div class="period-meta">上期：{{ card.previous }}</div>
                </article>
              </div>
            </article>

            <article class="card">
              <div class="card-title">储备板块</div>
              <div class="metric-row col-3">
                <article v-for="card in compareOverviewGroups.reserve" :key="card.label" class="metric-card compare-card">
                  <div class="period-label">{{ card.label }}</div>
                  <div class="period-value">{{ card.value }}</div>
                  <div
                    class="delta"
                    :class="card.diffClass === 'delta-down' ? 'down' : card.diffClass === 'delta-up' ? 'up' : ''"
                    :style="card.diffStyle"
                  >
                    较上期 {{ card.diff }}
                  </div>
                  <div class="period-meta">上期：{{ card.previous }}</div>
                </article>
              </div>
            </article>

            <div class="section-divider"></div>

            <div class="section-header">
              <h2>课线项目看板</h2>
              <span class="badge">课线对比</span>
            </div>

            <template v-if="showLocationFilteredClassSections">
              <article class="card">
                <DataTable
                  card-title="班期总看板（两期变化）"
                  :filter-label="compareExportLabel"
                  :headers="HEADERS.compareClassTotal"
                  :grouped-headers="GROUPED_HEADERS.compareClassTotal"
                  :rows="compareClassTotalRows"
                  :total-row-index="compareClassTotalRows.length ? compareClassTotalRows.length - 1 : null"
                  table-class="compare-table"
                />
              </article>

              <article class="card">
                <div class="card-title">课线项目占比</div>
                <CompareCourseLineShare :groups="compareShareData" />
              </article>

              <article v-for="section in compareCourseLineSections" :key="section.courseLine" class="card">
                <DataTable
                  :card-title="`${section.courseLine}-课线班期看板（两期变化）`"
                  :filter-label="compareExportLabel"
                  :headers="HEADERS.compareClassCourseLine"
                  :grouped-headers="GROUPED_HEADERS.compareClassCourseLine"
                  :rows="section.tableRows"
                  :total-row-index="section.tableRows.length ? section.tableRows.length - 1 : null"
                  table-class="compare-table"
                />
              </article>
            </template>

            <article v-else class="card">
              <div class="empty-state">{{ locationFilterNotice }}</div>
            </article>
          </div>

          <div v-show="state.compareTab === 'area'" class="section active section--fit-width">
            <div class="section-header">
              <h2>片区看板</h2>
              <span class="badge">片区对比</span>
            </div>

            <article class="card">
              <DataTable
                card-title="片区-总目标储备变化看板"
                :filter-label="compareExportLabel"
                :headers="HEADERS.compareArea"
                :grouped-headers="GROUPED_HEADERS.compareArea"
                :rows="compareAreaRows"
                :pin-first-row="shouldPinNationalFirstRow(compareAreaRows)"
                table-class="compare-table"
              />
            </article>

            <div class="section-divider"></div>

            <article class="card">
              <DataTable
                card-title="片区-储备变化看板"
                :filter-label="compareExportLabel"
                :headers="HEADERS.compareAreaReserve"
                :grouped-headers="GROUPED_HEADERS.compareAreaReserve"
                :rows="compareAreaReserveRows"
                :pin-first-row="shouldPinNationalFirstRow(compareAreaReserveRows)"
                table-class="compare-table"
              />
            </article>
          </div>

          <div v-show="state.compareTab === 'region'" class="section active section--fit-width">
            <div class="section-header">
              <h2>省份看板</h2>
              <span class="badge">省份对比</span>
            </div>

            <article class="card">
              <DataTable
                card-title="省份-总目标储备变化看板"
                :filter-label="compareExportLabel"
                :headers="HEADERS.compareProvince"
                :grouped-headers="GROUPED_HEADERS.compareProvince"
                :rows="compareProvinceRows"
                :pin-first-row="shouldPinNationalFirstRow(compareProvinceRows)"
                table-class="compare-table"
              />
            </article>

            <div class="section-divider"></div>

            <article class="card">
              <DataTable
                card-title="省份-储备变化看板"
                :filter-label="compareExportLabel"
                :headers="HEADERS.compareProvinceReserve"
                :grouped-headers="GROUPED_HEADERS.compareProvinceReserve"
                :rows="compareProvinceReserveRows"
                :pin-first-row="shouldPinNationalFirstRow(compareProvinceReserveRows)"
                table-class="compare-table"
              />
            </article>

            <div class="section-divider"></div>

            <div class="section-header">
              <h2>城市看板</h2>
              <span class="badge">城市对比</span>
            </div>

            <article class="card">
              <DataTable
                card-title="城市-总储备看板（两期对比）"
                :filter-label="compareExportLabel"
                :headers="HEADERS.compareCity"
                :grouped-headers="GROUPED_HEADERS.compareCity"
                :rows="compareCityRows"
                :total-row-index="0"
                table-class="compare-table"
              >
                <template #before-table>
                  <div class="adv-filter-panel adv-filter-panel--compact adv-filter-panel--row">
                    <div class="adv-filter-label">指标筛选</div>
                    <div class="adv-filter-controls adv-filter-controls--range">
                      <select v-if="CITY_FILTER_OPTIONS.length > 1" v-model="state.cityFilters.metric">
                        <option v-for="option in CITY_FILTER_OPTIONS" :key="option.value" :value="option.value">
                          {{ option.label }}
                        </option>
                      </select>
                      <span v-else class="adv-filter-pill">{{ CITY_FILTER_OPTIONS[0]?.label || "无可筛选指标" }}</span>
                      <select v-model="state.cityFilters.firstOperator">
                        <option value="">不限</option>
                        <option value=">=">&gt;=</option>
                        <option value="<=">&lt;=</option>
                        <option value="=">=</option>
                        <option value=">">&gt;</option>
                        <option value="<">&lt;</option>
                      </select>
                      <input v-model="state.cityFilters.firstValue" type="number" placeholder="值 1" />
                      <select v-model="state.cityFilters.logic" class="adv-filter-logic-select">
                        <option value="and">且</option>
                        <option value="or">或</option>
                      </select>
                      <select v-model="state.cityFilters.secondOperator">
                        <option value="">不限</option>
                        <option value=">=">&gt;=</option>
                        <option value="<=">&lt;=</option>
                        <option value="=">=</option>
                        <option value=">">&gt;</option>
                        <option value="<">&lt;</option>
                      </select>
                      <input v-model="state.cityFilters.secondValue" type="number" placeholder="值 2" />
                    </div>
                  </div>
                </template>
              </DataTable>
            </article>

            <div v-if="compareCityCourseLineOptions.length" class="course-line-switcher">
              <div class="course-line-switcher-label">课线切换</div>
              <div class="course-line-switcher-tabs">
                <button
                  v-for="courseLine in compareCityCourseLineOptions"
                  :key="courseLine"
                  class="course-line-tab"
                  :class="{ active: courseLine === activeCompareCityCourseLine }"
                  type="button"
                  @click="state.compareCityCourseLine = courseLine"
                >
                  {{ courseLine }}
                </button>
              </div>
            </div>

            <article v-if="selectedCompareCityCourseLineSection" class="card">
              <DataTable
                :card-title="`${selectedCompareCityCourseLineSection.courseLine}-城市储备看板（两期对比）`"
                :filter-label="compareExportLabel"
                :headers="HEADERS.compareCityCourseLine"
                :grouped-headers="GROUPED_HEADERS.compareCityCourseLine"
                :rows="selectedCompareCityCourseLineSection.tableRows"
                :total-row-index="0"
                table-class="compare-table"
              >
                <template #before-table>
                  <div class="adv-filter-panel adv-filter-panel--compact adv-filter-panel--row">
                    <div class="adv-filter-label">指标筛选</div>
                    <div class="adv-filter-controls adv-filter-controls--range">
                      <select
                        v-if="CITY_FILTER_OPTIONS.length > 1"
                        :value="selectedCompareCityCourseLineSection.filterState.metric"
                        @change="updateCityCourseLineFilter(selectedCompareCityCourseLineSection.courseLine, 'metric', $event.target.value)"
                      >
                        <option v-for="option in CITY_FILTER_OPTIONS" :key="option.value" :value="option.value">
                          {{ option.label }}
                        </option>
                      </select>
                      <span v-else class="adv-filter-pill">{{ CITY_FILTER_OPTIONS[0]?.label || "无可筛选指标" }}</span>
                      <select
                        :value="selectedCompareCityCourseLineSection.filterState.firstOperator"
                        @change="updateCityCourseLineFilter(selectedCompareCityCourseLineSection.courseLine, 'firstOperator', $event.target.value)"
                      >
                        <option value="">不限</option>
                        <option value=">=">&gt;=</option>
                        <option value="<=">&lt;=</option>
                        <option value="=">=</option>
                        <option value=">">&gt;</option>
                        <option value="<">&lt;</option>
                      </select>
                      <input
                        :value="selectedCompareCityCourseLineSection.filterState.firstValue"
                        type="number"
                        placeholder="值 1"
                        @input="updateCityCourseLineFilter(selectedCompareCityCourseLineSection.courseLine, 'firstValue', $event.target.value)"
                      />
                      <select
                        class="adv-filter-logic-select"
                        :value="selectedCompareCityCourseLineSection.filterState.logic"
                        @change="updateCityCourseLineFilter(selectedCompareCityCourseLineSection.courseLine, 'logic', $event.target.value)"
                      >
                        <option value="and">且</option>
                        <option value="or">或</option>
                      </select>
                      <select
                        :value="selectedCompareCityCourseLineSection.filterState.secondOperator"
                        @change="updateCityCourseLineFilter(selectedCompareCityCourseLineSection.courseLine, 'secondOperator', $event.target.value)"
                      >
                        <option value="">不限</option>
                        <option value=">=">&gt;=</option>
                        <option value="<=">&lt;=</option>
                        <option value="=">=</option>
                        <option value=">">&gt;</option>
                        <option value="<">&lt;</option>
                      </select>
                      <input
                        :value="selectedCompareCityCourseLineSection.filterState.secondValue"
                        type="number"
                        placeholder="值 2"
                        @input="updateCityCourseLineFilter(selectedCompareCityCourseLineSection.courseLine, 'secondValue', $event.target.value)"
                      />
                    </div>
                  </div>
                </template>
              </DataTable>
            </article>
          </div>

          <div v-show="state.compareTab === 'bd'" class="section active section--fit-width">
            <div class="section-header">
              <h2>BD 看板</h2>
              <span class="badge">BD 对比</span>
            </div>

            <article class="card">
              <DataTable
                card-title="BD-目标储备看板（两期对比）"
                :filter-label="compareExportLabel"
                :headers="HEADERS.compareBd"
                :grouped-headers="GROUPED_HEADERS.compareBd"
                :rows="compareBdTargetRows"
                :total-row-index="0"
                table-class="compare-table"
              >
                <template #before-table>
                  <div class="adv-filter-panel adv-filter-panel--compact adv-filter-panel--row">
                    <div class="adv-filter-label">指标筛选</div>
                    <div class="adv-filter-controls adv-filter-controls--range">
                      <select v-if="BD_TARGET_FILTER_OPTIONS.length > 1" v-model="state.bdTargetFilters.metric">
                        <option v-for="option in BD_TARGET_FILTER_OPTIONS" :key="option.value" :value="option.value">
                          {{ option.label }}
                        </option>
                      </select>
                      <span v-else class="adv-filter-pill">{{ BD_TARGET_FILTER_OPTIONS[0]?.label || "无可筛选指标" }}</span>
                      <select v-model="state.bdTargetFilters.firstOperator">
                        <option value="">不限</option>
                        <option value=">=">&gt;=</option>
                        <option value="<=">&lt;=</option>
                        <option value="=">=</option>
                        <option value=">">&gt;</option>
                        <option value="<">&lt;</option>
                      </select>
                      <input v-model="state.bdTargetFilters.firstValue" type="number" placeholder="值 1" />
                      <select v-model="state.bdTargetFilters.logic" class="adv-filter-logic-select">
                        <option value="and">且</option>
                        <option value="or">或</option>
                      </select>
                      <select v-model="state.bdTargetFilters.secondOperator">
                        <option value="">不限</option>
                        <option value=">=">&gt;=</option>
                        <option value="<=">&lt;=</option>
                        <option value="=">=</option>
                        <option value=">">&gt;</option>
                        <option value="<">&lt;</option>
                      </select>
                      <input v-model="state.bdTargetFilters.secondValue" type="number" placeholder="值 2" />
                    </div>
                  </div>
                </template>
              </DataTable>
            </article>

            <article class="card">
              <DataTable
                card-title="BD-储备结构看板（两期对比）"
                :filter-label="compareExportLabel"
                :headers="HEADERS.compareBdReserve"
                :grouped-headers="GROUPED_HEADERS.compareBdReserve"
                :rows="compareBdReserveRows"
                :total-row-index="0"
                table-class="compare-table"
              >
                <template #before-table>
                  <div class="adv-filter-panel adv-filter-panel--compact adv-filter-panel--row">
                    <div class="adv-filter-label">指标筛选</div>
                    <div class="adv-filter-controls adv-filter-controls--range">
                      <select v-if="BD_RESERVE_FILTER_OPTIONS.length > 1" v-model="state.bdReserveFilters.metric">
                        <option v-for="option in BD_RESERVE_FILTER_OPTIONS" :key="option.value" :value="option.value">
                          {{ option.label }}
                        </option>
                      </select>
                      <span v-else class="adv-filter-pill">{{ BD_RESERVE_FILTER_OPTIONS[0]?.label || "无可筛选指标" }}</span>
                      <select v-model="state.bdReserveFilters.firstOperator">
                        <option value="">不限</option>
                        <option value=">=">&gt;=</option>
                        <option value="<=">&lt;=</option>
                        <option value="=">=</option>
                        <option value=">">&gt;</option>
                        <option value="<">&lt;</option>
                      </select>
                      <input v-model="state.bdReserveFilters.firstValue" type="number" placeholder="值 1" />
                      <select v-model="state.bdReserveFilters.logic" class="adv-filter-logic-select">
                        <option value="and">且</option>
                        <option value="or">或</option>
                      </select>
                      <select v-model="state.bdReserveFilters.secondOperator">
                        <option value="">不限</option>
                        <option value=">=">&gt;=</option>
                        <option value="<=">&lt;=</option>
                        <option value="=">=</option>
                        <option value=">">&gt;</option>
                        <option value="<">&lt;</option>
                      </select>
                      <input v-model="state.bdReserveFilters.secondValue" type="number" placeholder="值 2" />
                    </div>
                  </div>
                </template>
              </DataTable>
            </article>
          </div>
        </template>
      </div>
    </div>

    <PermPanel :visible="showPermPanel" @close="showPermPanel = false" />
    <ChangePasswordDialog
      :visible="showChangePasswordDialog"
      :username="authUser?.username || ''"
      @close="showChangePasswordDialog = false"
      @password-changed="handlePasswordChanged"
    />

    <!-- 删除批次确认对话框 -->
    <teleport to="body">
      <div v-if="showDeleteDialog" class="confirm-overlay" @click.self="showDeleteDialog = false">
        <div class="confirm-dialog">
          <div class="confirm-title">删除批次数据</div>
          <div class="confirm-body">
            确认删除 <strong>{{ state.selectedPeriod }}</strong>
            第 <strong>{{ state.selectedUploadSeq }}</strong> 次版本的所有数据？<br/>
            <span class="confirm-warn">此操作不可恢复。</span>
          </div>
          <div class="confirm-actions">
            <button class="action-btn danger" :disabled="deleteConfirming" @click="deleteCurrentBatch">
              {{ deleteConfirming ? "删除中..." : "确认删除" }}
            </button>
            <button class="action-btn secondary" :disabled="deleteConfirming" @click="showDeleteDialog = false">取消</button>
          </div>
        </div>
      </div>
    </teleport>
  </div>
</template>
