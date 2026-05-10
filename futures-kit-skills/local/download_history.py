# -*- coding: utf-8 -*-
"""
批量下载期货历史数据到本地 Parquet

下载两年的国内期货、国际期货、外汇数据，存为 Parquet 格式供离线分析和回测。

用法:
    python local/download_history.py                      # 下载全部品种
    python local/download_history.py --symbol AU0         # 只下载沪金
    python local/download_history.py --type domestic      # 只下载国内期货
    python local/download_history.py --type foreign       # 只下载国际期货
    python local/download_history.py --type forex         # 只下载外汇
    python local/download_history.py --update             # 增量更新
    python local/download_history.py --summary            # 数据摘要
    python local/download_history.py --days 730           # 指定天数（默认730天=2年）
"""
import argparse
import os
import sys
import time
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

try:
    import pandas as pd
    import numpy as np
except ImportError:
    print("请先安装依赖: pip install pandas numpy pyarrow")
    sys.exit(1)

# 数据目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(SKILL_DIR, 'data')
SCRIPTS_DIR = os.path.join(SKILL_DIR, 'scripts')

sys.path.insert(0, SCRIPTS_DIR)

# 品种定义
DOMESTIC_SYMBOLS = ['AU0', 'CU0', 'LC0', 'SC0']
FOREIGN_SYMBOLS = ['XAU', 'HG', 'WTI', 'BRENT']
FOREX_SYMBOLS = ['USDCNY', 'EURUSD', 'GBPUSD', 'USDJPY']


def ensure_data_dir():
    """确保数据目录存在"""
    os.makedirs(DATA_DIR, exist_ok=True)


def download_domestic(symbols: list, days: int = 730, update: bool = False):
    """下载国内期货数据"""
    from get_domestic_kline import get_kline

    for symbol in symbols:
        filepath = os.path.join(DATA_DIR, f'{symbol}_daily.parquet')

        if update and os.path.exists(filepath):
            # 增量更新：读取已有数据，只补新数据
            existing = pd.read_parquet(filepath)
            last_date = pd.to_datetime(existing['datetime']).max()
            new_days = (datetime.now() - last_date).days + 5  # 多拉几天保险
            print(f"  增量更新 {symbol}，从 {last_date.strftime('%Y-%m-%d')} 起...")
            df = get_kline(symbol, 'daily', new_days)
            if df is not None and len(df) > 0:
                df['datetime'] = pd.to_datetime(df['datetime'])
                existing['datetime'] = pd.to_datetime(existing['datetime'])
                combined = pd.concat([existing, df]).drop_duplicates(subset=['datetime']).sort_values('datetime')
                combined.to_parquet(filepath, index=False)
                print(f"  {symbol}: 更新后共 {len(combined)} 条")
            else:
                print(f"  {symbol}: 无新数据")
        else:
            print(f"  下载 {symbol} 近 {days} 天日K线...")
            df = get_kline(symbol, 'daily', days)
            if df is not None and len(df) > 0:
                df.to_parquet(filepath, index=False)
                print(f"  {symbol}: 保存 {len(df)} 条 -> {filepath}")
            else:
                print(f"  {symbol}: 下载失败")

        time.sleep(1)  # 请求间隔


def download_foreign(symbols: list, days: int = 730, update: bool = False):
    """下载国际期货数据"""
    from get_foreign_kline import get_foreign_kline

    for symbol in symbols:
        filepath = os.path.join(DATA_DIR, f'{symbol}_daily.parquet')

        if update and os.path.exists(filepath):
            existing = pd.read_parquet(filepath)
            last_date = pd.to_datetime(existing['datetime']).max()
            new_days = (datetime.now() - last_date).days + 5
            print(f"  增量更新 {symbol}，从 {last_date.strftime('%Y-%m-%d')} 起...")
            df = get_foreign_kline(symbol, new_days)
            if df is not None and len(df) > 0:
                df['datetime'] = pd.to_datetime(df['datetime'])
                existing['datetime'] = pd.to_datetime(existing['datetime'])
                combined = pd.concat([existing, df]).drop_duplicates(subset=['datetime']).sort_values('datetime')
                combined.to_parquet(filepath, index=False)
                print(f"  {symbol}: 更新后共 {len(combined)} 条")
            else:
                print(f"  {symbol}: 无新数据")
        else:
            print(f"  下载 {symbol} 近 {days} 天日K线...")
            df = get_foreign_kline(symbol, days)
            if df is not None and len(df) > 0:
                df.to_parquet(filepath, index=False)
                print(f"  {symbol}: 保存 {len(df)} 条 -> {filepath}")
            else:
                print(f"  {symbol}: 下载失败")

        time.sleep(1)


def download_forex(symbols: list, days: int = 730, update: bool = False):
    """下载外汇数据"""
    from get_forex import get_forex_data

    for symbol in symbols:
        filepath = os.path.join(DATA_DIR, f'{symbol}_daily.parquet')

        if update and os.path.exists(filepath):
            existing = pd.read_parquet(filepath)
            last_date = pd.to_datetime(existing['datetime']).max()
            new_days = (datetime.now() - last_date).days + 5
            print(f"  增量更新 {symbol}，从 {last_date.strftime('%Y-%m-%d')} 起...")
            df = get_forex_data(symbol, new_days)
            if df is not None and len(df) > 0:
                df['datetime'] = pd.to_datetime(df['datetime'])
                existing['datetime'] = pd.to_datetime(existing['datetime'])
                combined = pd.concat([existing, df]).drop_duplicates(subset=['datetime']).sort_values('datetime')
                combined.to_parquet(filepath, index=False)
                print(f"  {symbol}: 更新后共 {len(combined)} 条")
            else:
                print(f"  {symbol}: 无新数据")
        else:
            print(f"  下载 {symbol} 近 {days} 天数据...")
            df = get_forex_data(symbol, days)
            if df is not None and len(df) > 0:
                df.to_parquet(filepath, index=False)
                print(f"  {symbol}: 保存 {len(df)} 条 -> {filepath}")
            else:
                print(f"  {symbol}: 下载失败")

        time.sleep(1)


def show_summary():
    """显示数据摘要"""
    print("# 本地数据摘要\n")
    print(f"数据目录: {DATA_DIR}\n")
    print("| 文件 | 品种 | 条数 | 起始日期 | 结束日期 | 大小 |")
    print("|------|------|------|----------|----------|------|")

    total_size = 0
    if not os.path.exists(DATA_DIR):
        print("\n数据目录为空，请先运行下载。")
        return

    for f in sorted(os.listdir(DATA_DIR)):
        if f.endswith('.parquet'):
            filepath = os.path.join(DATA_DIR, f)
            size = os.path.getsize(filepath)
            total_size += size
            try:
                df = pd.read_parquet(filepath)
                df['datetime'] = pd.to_datetime(df['datetime'])
                start = df['datetime'].min().strftime('%Y-%m-%d')
                end = df['datetime'].max().strftime('%Y-%m-%d')
                symbol = f.replace('_daily.parquet', '')
                print(f"| {f} | {symbol} | {len(df)} | {start} | {end} | {size/1024:.0f}KB |")
            except Exception as e:
                print(f"| {f} | ? | ? | ? | ? | {size/1024:.0f}KB |")

    print(f"\n**总大小**: {total_size/1024/1024:.1f}MB")


def main():
    parser = argparse.ArgumentParser(description='批量下载期货历史数据')
    parser.add_argument('--symbol', help='指定品种下载')
    parser.add_argument('--type', choices=['domestic', 'foreign', 'forex', 'all'],
                        default='all', help='数据类型 (默认all)')
    parser.add_argument('--days', type=int, default=730, help='下载天数 (默认730=2年)')
    parser.add_argument('--update', action='store_true', help='增量更新')
    parser.add_argument('--summary', action='store_true', help='显示数据摘要')

    args = parser.parse_args()

    if args.summary:
        show_summary()
        return

    ensure_data_dir()
    start_time = time.time()

    if args.symbol:
        # 指定品种
        symbol = args.symbol.upper()
        if symbol in DOMESTIC_SYMBOLS:
            print(f"下载国内期货: {symbol}")
            download_domestic([symbol], args.days, args.update)
        elif symbol in FOREIGN_SYMBOLS:
            print(f"下载国际期货: {symbol}")
            download_foreign([symbol], args.days, args.update)
        elif symbol in FOREX_SYMBOLS:
            print(f"下载外汇: {symbol}")
            download_forex([symbol], args.days, args.update)
        else:
            print(f"尝试作为国内期货下载: {symbol}")
            download_domestic([symbol], args.days, args.update)
    else:
        # 按类型下载
        if args.type in ('domestic', 'all'):
            print("\n## 下载国内期货\n")
            download_domestic(DOMESTIC_SYMBOLS, args.days, args.update)

        if args.type in ('foreign', 'all'):
            print("\n## 下载国际期货\n")
            download_foreign(FOREIGN_SYMBOLS, args.days, args.update)

        if args.type in ('forex', 'all'):
            print("\n## 下载外汇\n")
            download_forex(FOREX_SYMBOLS, args.days, args.update)

    elapsed = time.time() - start_time
    print(f"\n下载完成，耗时 {elapsed:.0f} 秒")
    print("\n--- 数据摘要 ---")
    show_summary()


if __name__ == '__main__':
    main()
