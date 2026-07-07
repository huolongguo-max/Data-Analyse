# -*- coding: utf-8 -*-
"""
基于 V1 生成 V2 测试数据，加高斯噪声，覆盖：
- 新增BD / 退出BD（仅上期出现）
- 招生进度变化（未启动→招生中，招生中→已结束）
- 储备量大涨/大跌 / 归零 edge case
- 日期整体后移7天（第二期）
- 已进线量和目标值小幅浮动
"""
import pandas as pd
import numpy as np
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from copy import copy
import datetime, random, sys

sys.stdout.reconfigure(encoding='utf-8')
rng = np.random.default_rng(42)

# ⚠️ 以下路径为原 Windows 机器硬编码路径，已注释。请按需修改为本地路径。
# 示例（macOS / Linux 相对路径）：
SRC = 'data/uploads/2026-03/【0306-V1】2026年3月全国储备摸底.xlsx'
DST = 'data/exports/【0313-V2】2026年3月全国储备摸底.xlsx'
# 原 Windows 路径: r'F:\大学\中山大学本科\实习\点猫科技--AI产品开发--2026-0119\...'

# ── 读取原始数据 ──────────────────────────────────────────────
xl = pd.ExcelFile(SRC)
df_detail = pd.read_excel(xl, sheet_name='储备明细表', header=0)
df_class  = pd.read_excel(xl, sheet_name='每月班期表',  header=0)
df_inbound= pd.read_excel(xl, sheet_name='已进线表',    header=0)

# ── 工具函数 ──────────────────────────────────────────────────
def gauss_int(val, sigma_ratio=0.15, floor=0):
    """对整数值加高斯噪声，返回非负整数"""
    if pd.isna(val) or val == 0:
        return val
    noise = rng.normal(0, abs(val) * sigma_ratio)
    return max(floor, round(val + noise))

def gauss_float(val, sigma_ratio=0.12):
    if pd.isna(val):
        return val
    noise = rng.normal(0, abs(val) * sigma_ratio)
    return round(val + noise, 4)

def shift_date(val, days=7):
    if pd.isna(val):
        return val
    if isinstance(val, (datetime.datetime, datetime.date)):
        return val + datetime.timedelta(days=days)
    return val

# ── 储备明细表 ────────────────────────────────────────────────
d2 = df_detail.copy()

# 日期整体后移7天
for col in ['启动日期','停止日期','下周启动日期','下周停止日期']:
    if col in d2.columns:
        d2[col] = d2[col].apply(shift_date)

# 数值列加噪声
for col in ['冲高储备量','下周储备量','保底储备量','下周保底储备量','冲高预测业绩','保底预测业绩']:
    if col in d2.columns:
        d2[col] = d2[col].apply(gauss_int)

# BD准确率浮动（0-1区间截断）
if 'BD准确率' in d2.columns:
    d2['BD准确率'] = d2['BD准确率'].apply(
        lambda v: round(min(1.0, max(0.0, gauss_float(v, 0.08))), 2) if not pd.isna(v) else v
    )

# 覆盖更多情况：
# 1) 2行储备量归零（模拟项目取消）
zero_idx = rng.choice(d2.index[d2['冲高储备量'].notna() & (d2['冲高储备量'] > 0)], size=2, replace=False)
d2.loc[zero_idx, ['冲高储备量','保底储备量','冲高预测业绩','保底预测业绩']] = 0

# 2) 2行储备量大涨（+50%~+100%）
up_idx = rng.choice(d2.index[d2['冲高储备量'].notna() & (d2['冲高储备量'] > 0)], size=2, replace=False)
for i in up_idx:
    factor = rng.uniform(1.5, 2.0)
    for c in ['冲高储备量','保底储备量','冲高预测业绩','保底预测业绩']:
        if not pd.isna(d2.loc[i, c]):
            d2.loc[i, c] = round(d2.loc[i, c] * factor)

# 3) 新增1个BD（仅V2出现，制造"仅本期出现"场景）
new_row = d2.iloc[5].copy()
new_row['BD'] = '赵新BD'
new_row['省份'] = '湖北省'
new_row['城市'] = '宜昌市'
new_row['区县'] = float('nan')
new_row['冲高储备量'] = 2500
new_row['保底储备量'] = 1500
new_row['下周储备量'] = 1000
new_row['冲高预测业绩'] = 145000
new_row['保底预测业绩'] = 116000
new_row['启动日期'] = datetime.datetime(2026, 3, 16)
new_row['停止日期'] = datetime.datetime(2026, 3, 23)
new_row['下周启动日期'] = datetime.datetime(2026, 3, 16)
new_row['下周停止日期'] = datetime.datetime(2026, 3, 22)
d2 = pd.concat([d2, pd.DataFrame([new_row])], ignore_index=True)

# 4) 删除1个已有BD（制造"仅上期出现"场景）——删掉原数据里庄小龙的第一条(储备为0的)
drop_mask = (d2['BD'] == '庄小龙') & (d2['冲高储备量'] == 0)
if drop_mask.any():
    d2 = d2[~drop_mask].reset_index(drop=True)

# ── 每月班期表 ────────────────────────────────────────────────
c2 = df_class.copy()

# 日期后移7天
for col in ['班期','进线开始时间','进线截止时间','上课开始时间','上课截止时间']:
    if col in c2.columns:
        c2[col] = c2[col].apply(shift_date)

# 招生进度推进：未启动→招生中（取第一个未启动的班期）
mask_unstarted = c2['招生进度'] == '未启动'
first_unstarted = c2[mask_unstarted].index[:2]
c2.loc[first_unstarted, '招生进度'] = '招生中'
c2.loc[first_unstarted, '已进线量'] = [180, 120]
c2.loc[first_unstarted, '已达成预测业绩'] = [2200, 1600]

# 招生中→已结束（原来第二个班期）
mask_ing = c2['招生进度'] == '招生中'
first_ing = c2[mask_ing].index[:1]
c2.loc[first_ing, '招生进度'] = '已结束'
# 已结束时冲高相关置空
for col in ['冲高储备量','冲高预测业绩','冲高总储备量','冲高总预测业绩']:
    if col in c2.columns:
        c2.loc[first_ing, col] = float('nan')

# 已进线量 + 已达成预测业绩浮动
for col in ['已进线量','已达成预测业绩']:
    if col in c2.columns:
        c2[col] = c2[col].apply(gauss_int, sigma_ratio=0.1)

# ── 已进线表 ──────────────────────────────────────────────────
ib2 = df_inbound.copy()

# 目标值同月保持不变（只有已进线和已达成预测业绩变动）
ib2['已进线'] = ib2['已进线'].apply(gauss_int, sigma_ratio=0.12)
ib2['已达成预测业绩'] = ib2['已达成预测业绩'].apply(gauss_int, sigma_ratio=0.12)

# ── 写出xlsx（复制原格式）────────────────────────────────────
wb = load_workbook(SRC)

def safe_set(cell, value):
    from openpyxl.cell.cell import MergedCell
    if isinstance(cell, MergedCell):
        return
    cell.value = value

def write_df_to_sheet(wb, sheet_name, df):
    ws = wb[sheet_name]
    # 清空数据区（保留表头行=第1行）
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row):
        for cell in row:
            safe_set(cell, None)

    # 写入数据
    for r_idx, row_data in enumerate(df.itertuples(index=False), start=2):
        for c_idx, value in enumerate(row_data, start=1):
            cell = ws.cell(row=r_idx, column=c_idx)
            if isinstance(value, float) and np.isnan(value):
                safe_set(cell, None)
            elif isinstance(value, (datetime.datetime, datetime.date)):
                safe_set(cell, value)
            elif isinstance(value, (np.integer,)):
                safe_set(cell, int(value))
            elif isinstance(value, (np.floating,)):
                safe_set(cell, float(value))
            else:
                safe_set(cell, value)

write_df_to_sheet(wb, '储备明细表', d2)
write_df_to_sheet(wb, '每月班期表', c2)
write_df_to_sheet(wb, '已进线表', ib2)

wb.save(DST)
print(f'已生成：{DST}')
print(f'储备明细表行数（含表头）：{len(d2)+1}')
print(f'每月班期表行数（含表头）：{len(c2)+1}')
print(f'已进线表行数（含表头）：{len(ib2)+1}')
print('\n覆盖的边界情况：')
print('  ✓ 储备量归零（2行）')
print('  ✓ 储备量大涨 +50%~+100%（2行）')
print('  ✓ 新增BD（赵新BD，仅V2出现）')
print('  ✓ 删除BD（庄小龙零储备行，制造仅上期出现）')
print('  ✓ 招生进度：未启动→招生中（2行）')
print('  ✓ 招生进度：招生中→已结束（1行），冲高数据置空')
print('  ✓ 日期整体后移7天')
print('  ✓ 所有数值列加高斯噪声 σ=12%~15%')
