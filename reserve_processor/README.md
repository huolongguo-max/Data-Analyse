# reserve_processor 维护说明

这个目录负责把原始储备表 `xlsx` 读入、计算补全、再按原表风格导出为 `-补全.xlsx`。

## 处理链路

主调用链：

`cli.py`
-> `pipeline.process_xlsx_to_xlsx()`
-> `pipeline.process_workbook()`
-> `excel_io.read_xlsx()`
-> `validators.validate_workbook()`
-> `detail_calculator.calculate_detail_sheet()`
-> `schedule_calculator.calculate_schedule_sheet()`
-> `target_calculator.calculate_target_sheet()`
-> `excel_io.write_xlsx()`

可以把它理解成三段：

1. 读文件和校验：`excel_io.py`、`filename_parser.py`、`validators.py`
2. 计算补全：`detail_calculator.py`、`schedule_calculator.py`、`target_calculator.py`
3. 导出结果：`excel_io.py`、`utils.py`

## 各文件关系

### `cli.py`

命令行入口。

关键函数：

- `main()`

说明：

- 解析 `--input` 和 `--output`
- 调用 `pipeline.process_xlsx_to_xlsx()`
- 打印输出路径和文件元信息

### `pipeline.py`

总编排层，串起整个处理流程。

关键函数：

- `process_workbook(input_path)`
- `process_xlsx_to_xlsx(input_path, output_path=None)`

说明：

- `process_workbook()` 只负责内存中的读取、校验、计算，返回 `ProcessResult`
- `process_xlsx_to_xlsx()` 在前者基础上再调用 `write_xlsx()`，真正落盘输出文件

如果以后要插入新的处理步骤，优先改这个文件。

### `excel_io.py`

负责 Excel 读写，也是“导出格式控制”的核心文件。

关键函数：

- `read_xlsx(path)`
- `write_xlsx(output_path, template_path, detail, schedule, target)`
- `_build_detail_export_frame(detail)`
- `_build_schedule_export_frame(schedule)`
- `_build_target_export_frame(target)`
- `_write_sheet_from_frame(...)`
- `_copy_cell_style(...)`

说明：

- `read_xlsx()` 读取 3 个 sheet，并做 sheet 名归一化
- `write_xlsx()` 用原文件当模板，复制表头样式、列宽、冻结窗格、行高
- `_build_detail_export_frame()` 会把明细表内部用于计算的 `4 * n` 日期列收缩成“只导出保底储备那 `n` 列”
- 导出时的四舍五入发生在这里，不是在计算阶段
- 日期格式、百分比格式、整数格式也在这里控制

如果以后要改导出列、保留哪些日期列、表头样式或格式，主要改这个文件。

### `detail_calculator.py`

负责先把“储备明细表”扩成按日期展开的宽表，是后面两个 sheet 的基础。

关键函数：

- `build_detail_date_axis(detail)`
- `calculate_base_reserve_for_row(row, date_axis)`
- `calculate_simple_average_for_row(row, metric, date_axis)`
- `calculate_detail_sheet(detail)`

说明：

- `build_detail_date_axis()` 会根据全表最早启动日期和最晚停止日期生成日期轴
- `calculate_base_reserve_for_row()` 是明细表里最特殊的逻辑，处理“下周储备/下周保底储备”的拆分
- `calculate_simple_average_for_row()` 用于其他按区间平均分摊的指标
- `calculate_detail_sheet()` 最终生成带日期宽列的新明细表

如果以后“保底储备”的拆分规则变化，优先看这个文件。

### `schedule_calculator.py`

负责计算“每月班期表”。

关键函数：

- `sum_detail_metric_by_project_and_period(detail, project, start, end, metric, date_axis)`
- `get_schedule_entered_and_achieved(raw_row)`
- `calculate_schedule_sheet(schedule, detail, date_axis)`

说明：

- 先从明细表的日期宽列中，按“课线项目 + 进线时间区间”汇总 4 个基础指标
- 再根据 `招生进度` 计算 4 个总量指标
- `未启动 / 招生中 / 已结束` 的口径分支都在这里

如果以后班期表的状态逻辑变化，主要改这个文件。

### `target_calculator.py`

负责计算“已进线表”。

关键函数：

- `sum_detail_metric_by_target(detail, target_level, target_object, metric)`
- `calculate_target_sheet(target, detail)`

说明：

- 先按“目标层面 + 目标对象”从明细表汇总 4 个基础指标
- 再结合表内已有的 `已进线`、`已达成预测业绩`、`预测业绩目标` 算总量和达标率
- `全国 / 片区 / 省份 / BD` 的维度映射在这里落地

如果以后目标表的汇总维度或达标率口径变化，主要改这个文件。

### `validators.py`

负责结构校验。

关键函数：

- `validate_required_columns(df, required_columns, sheet_name)`
- `validate_workbook(detail, schedule, target)`

说明：

- 检查必填列是否存在
- 检查表头是否重复
- 空表只给 warning，不直接中断

如果新增必填列，通常要连同 `constants.py` 一起改。

### `filename_parser.py`

负责从文件名中提取年月、版本、日期码。

关键函数：

- `parse_filename(path)`

说明：

- 用正则匹配文件名
- 结果写进 `FileMeta`
- 文件名不匹配不会直接报错，但会返回空元信息并在 pipeline 中记 warning

如果以后文件命名规则变了，主要改这个文件和 `constants.py` 里的正则。

### `constants.py`

集中放常量定义。

关键内容：

- sheet 标准名
- sheet 别名
- 导出文件后缀
- 4 个基础指标
- 4 个总量指标
- 2 个达标率指标
- 3 张表的必填列
- 目标层面到明细字段的映射
- 文件名正则

这是最先要看的“配置层”文件。字段名、sheet 名、指标名一旦变更，通常都要先从这里入手。

### `utils.py`

通用工具函数，很多模块都会依赖它。

关键函数：

- `is_blank(value)`
- `to_number(value)`
- `to_number_zero(value)`
- `add_optional(*values)`
- `to_date(value)`
- `inclusive_days(start, end)`
- `date_range_inclusive(start, end)`
- `format_cn_date(date, include_year=False)`
- `metric_date_col(metric, date, include_year=False)`
- `get_first_existing(row, candidates, default="")`
- `ensure_columns(df, columns)`
- `safe_rate(numerator, denominator)`
- `remove_existing_date_metric_columns(df)`
- `build_completed_output_path(input_path, output_path=None)`

说明：

- 这里放的是“所有模块共用的小规则”
- 例如空值判断、数值转换、日期转换、日期列名拼接、输出文件名生成
- 明细表重复计算前先移除旧日期列，也是这里控制

### `models.py`

数据结构定义文件。

关键类：

- `FileMeta`
- `WorkbookData`
- `ProcessResult`

说明：

- `FileMeta` 保存文件名解析结果
- `WorkbookData` 是读入后的 3 张原始表
- `ProcessResult` 是处理完成后的统一返回结构

### `__init__.py`

对外暴露包级入口。

导出的主要接口：

- `process_workbook`
- `process_xlsx_to_xlsx`
- `build_completed_output_path`

## 常见维护定位

### 1. 改文件名规则

优先看：

- `constants.py`
- `filename_parser.py`

### 2. 改 sheet 名或新增别名

优先看：

- `constants.py`
- `excel_io.py`

### 3. 改明细表日期展开逻辑

优先看：

- `detail_calculator.py`

### 4. 改班期表状态口径

优先看：

- `schedule_calculator.py`

### 5. 改目标表汇总维度或达标率逻辑

优先看：

- `target_calculator.py`
- `constants.py`

### 6. 改导出格式

优先看：

- `excel_io.py`

包括：

- 哪些列导出
- 是否四舍五入
- 百分比格式
- 日期格式
- 表头样式、列宽、行高

### 7. 改补全文件名

优先看：

- `constants.py`
- `utils.py`

## 建议的阅读顺序

如果后续要维护，建议按这个顺序读：

1. `pipeline.py`
2. `constants.py`
3. `detail_calculator.py`
4. `schedule_calculator.py`
5. `target_calculator.py`
6. `excel_io.py`
7. `utils.py`

这样能先看主链路，再看计算，再看导出细节。
