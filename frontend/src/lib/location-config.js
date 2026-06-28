export const AREA_TO_PROVINCES = new Map([
  ["黑吉辽片区", ["黑龙江省", "吉林省", "辽宁省"]],
  ["冀豫片区", ["北京市", "河北省", "河南省"]],
  ["津鲁片区", ["山东省", "天津市"]],
  ["晋蒙片区", ["内蒙古自治区", "山西省"]],
  ["陕甘宁青新片区", ["甘肃省", "宁夏回族自治区", "青海省", "陕西省", "新疆维吾尔族自治区"]],
  ["苏皖片区", ["安徽省", "江苏省"]],
  ["湘鄂片区", ["湖北省", "湖南省"]],
  ["粤海片区", ["广东省", "海南省"]],
  ["云桂黔片区", ["广西壮族自治区", "贵州省", "云南省"]],
  ["浙闽片区", ["福建省", "浙江省"]],
  ["中心片区", ["江西省", "上海市", "四川省", "西藏自治区"]],
  ["重庆片区", ["重庆市"]],
]);

export const AREA_OPTIONS = [...AREA_TO_PROVINCES.keys()];
export const PROVINCE_OPTIONS = AREA_OPTIONS.flatMap((area) => AREA_TO_PROVINCES.get(area) || []);

export const PROVINCE_TO_AREA = new Map(
  AREA_OPTIONS.flatMap((area) => (AREA_TO_PROVINCES.get(area) || []).map((province) => [province, area]))
);

const PROVINCE_SUFFIXES = [
  "维吾尔族自治区",
  "维吾尔自治区",
  "回族自治区",
  "壮族自治区",
  "特别行政区",
  "自治区",
  "省",
  "市",
];

const NORMALIZED_PROVINCE_TO_AREA = new Map(
  [...PROVINCE_TO_AREA.entries()].map(([province, area]) => [normalizeProvinceName(province), area])
);

export function normalizeProvinceName(provinceName = "") {
  const raw = String(provinceName || "").trim().replace(/\s+/g, "");
  if (!raw) {
    return "";
  }
  for (const suffix of PROVINCE_SUFFIXES) {
    if (raw.endsWith(suffix) && raw.length > suffix.length) {
      return raw.slice(0, -suffix.length);
    }
  }
  return raw;
}

export function resolveAreaForProvince(provinceName = "") {
  const raw = String(provinceName || "").trim();
  if (!raw) {
    return "";
  }
  return PROVINCE_TO_AREA.get(raw) || NORMALIZED_PROVINCE_TO_AREA.get(normalizeProvinceName(raw)) || "";
}

export function provinceOptionsForAreas(areaNames = []) {
  if (!areaNames.length) {
    return [...PROVINCE_OPTIONS];
  }
  const selectedAreas = new Set(areaNames);
  return AREA_OPTIONS.flatMap((area) => (selectedAreas.has(area) ? (AREA_TO_PROVINCES.get(area) || []) : []));
}

export function resolveAreasForProvinces(provinceNames = []) {
  const selectedProvinces = new Set(provinceNames);
  return AREA_OPTIONS.filter((area) =>
    (AREA_TO_PROVINCES.get(area) || []).some((province) => selectedProvinces.has(province))
  );
}

export function scopedAreaOptions(areaNames = [], provinceNames = []) {
  let areaOptions = areaNames.length ? AREA_OPTIONS.filter((area) => areaNames.includes(area)) : [...AREA_OPTIONS];
  if (!provinceNames.length) {
    return areaOptions;
  }
  const provinceAreas = new Set(resolveAreasForProvinces(provinceNames));
  return areaOptions.filter((area) => provinceAreas.has(area));
}
