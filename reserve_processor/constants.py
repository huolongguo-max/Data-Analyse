# reserve_processor/constants.py

SHEET_DETAIL = "储备明细表"
SHEET_SCHEDULE = "每月班期表"
SHEET_TARGET = "已进线表"
COMPLETED_FILE_SUFFIX = "-补全"

REQUIRED_SHEETS = [
    SHEET_DETAIL,
    SHEET_SCHEDULE,
    SHEET_TARGET,
]

SHEET_ALIASES = {
    "储备明细": SHEET_DETAIL,
    "明细储备表": SHEET_DETAIL,
    "每月班期": SHEET_SCHEDULE,
    "月度班期表": SHEET_SCHEDULE,
    "每月目标表": SHEET_TARGET,
    "已进线表": SHEET_TARGET,
}

BASE_METRICS = [
    "保底储备量",
    "冲高储备量",
    "保底预测业绩",
    "冲高预测业绩",
]

TOTAL_METRICS = [
    "保底总储备量",
    "保底总预测业绩",
    "冲高总储备量",
    "冲高总预测业绩",
]

RATE_METRICS = [
    "保底总预测业绩达标率",
    "冲高总预测业绩达标率",
]

DETAIL_REQUIRED_COLUMNS = [
    "片区",
    "BD",
    "省份",
    "获客类型",
    "启动日期",
    "停止日期",
    "课线项目",
    "冲高储备量",
    "下周储备量",
    "下周启动日期",
    "下周停止日期",
    "保底储备量",
    "下周保底储备量",
    "冲高预测业绩",
    "保底预测业绩",
]

SCHEDULE_REQUIRED_COLUMNS = [
    "课线项目",
    "班期",
    "进线开始时间",
    "进线截止时间",
    "招生进度",
    "保底总储备量",
    "保底总预测业绩",
    "冲高总储备量",
    "冲高总预测业绩",
]

TARGET_REQUIRED_COLUMNS = [
    "目标层面",
    "目标对象",
    "预测业绩目标",
    "已进线",
    "已达成预测业绩",
]

TARGET_LEVEL_TO_DETAIL_COLUMN = {
    "全国": None,
    "片区": "片区",
    "省份": "省份",
    "BD": "BD",
}

# New format: 【MMDD】YYYY年M月全国储备摸底.xlsx
FILENAME_PATTERN = r"【(?P<date_code>\d{4})】(?P<year>\d{4})年(?P<month>\d{1,2})月"
