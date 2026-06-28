# -*- coding: utf-8 -*-
import pandas as pd, sys, os
sys.stdout.reconfigure(encoding='utf-8')

path = r'F:\大学\中山大学本科\实习\点猫科技--AI产品开发--2026-0119\data-analyse\local-data-analysis\data\uploads\2026-03\upload_001\original\【0306-V1】2026年3月全国储备摸底.xlsx'

xl = pd.ExcelFile(path)
print('Sheets:', xl.sheet_names)
for s in xl.sheet_names:
    df = pd.read_excel(xl, sheet_name=s, header=None)
    print(f'\n=== {s} === shape:{df.shape}')
    print(df.to_string())
