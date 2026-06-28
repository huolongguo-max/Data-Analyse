from __future__ import annotations

AREA_TO_PROVINCES: dict[str, tuple[str, ...]] = {
    "黑吉辽片区": ("黑龙江省", "吉林省", "辽宁省"),
    "冀豫片区": ("北京市", "河北省", "河南省"),
    "津鲁片区": ("山东省", "天津市"),
    "晋蒙片区": ("内蒙古自治区", "山西省"),
    "陕甘宁青新片区": ("甘肃省", "宁夏回族自治区", "青海省", "陕西省", "新疆维吾尔族自治区"),
    "苏皖片区": ("安徽省", "江苏省"),
    "湘鄂片区": ("湖北省", "湖南省"),
    "粤海片区": ("广东省", "海南省"),
    "云桂黔片区": ("广西壮族自治区", "贵州省", "云南省"),
    "浙闽片区": ("福建省", "浙江省"),
    "中心片区": ("江西省", "上海市", "四川省", "西藏自治区"),
    "重庆片区": ("重庆市",),
}

AREA_NAMES: tuple[str, ...] = tuple(AREA_TO_PROVINCES)
PROVINCE_NAMES: tuple[str, ...] = tuple(
    province
    for provinces in AREA_TO_PROVINCES.values()
    for province in provinces
)
PROVINCE_TO_AREA: dict[str, str] = {
    province: area
    for area, provinces in AREA_TO_PROVINCES.items()
    for province in provinces
}

PROVINCE_SUFFIXES: tuple[str, ...] = (
    "维吾尔族自治区",
    "维吾尔自治区",
    "回族自治区",
    "壮族自治区",
    "特别行政区",
    "自治区",
    "省",
    "市",
)

FIXED_DIMENSION_ORDER: dict[str, tuple[str, ...]] = {
    "area": AREA_NAMES,
    "province": PROVINCE_NAMES,
}


def normalize_province_name(province_name: str | None) -> str:
    raw = "".join((province_name or "").split())
    if not raw:
        return ""
    for suffix in PROVINCE_SUFFIXES:
        if raw.endswith(suffix) and len(raw) > len(suffix):
            return raw[: -len(suffix)]
    return raw


NORMALIZED_PROVINCE_TO_AREA: dict[str, str] = {
    normalize_province_name(province): area
    for province, area in PROVINCE_TO_AREA.items()
    if normalize_province_name(province)
}


def resolve_area_for_province(province_name: str | None) -> str:
    raw = (province_name or "").strip()
    if not raw:
        return ""
    return PROVINCE_TO_AREA.get(raw, "") or NORMALIZED_PROVINCE_TO_AREA.get(normalize_province_name(raw), "")
