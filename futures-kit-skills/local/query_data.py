# -*- coding: utf-8 -*-
"""
本地数据查询（DuckDB）

查询本地 Parquet 文件中的期货历史数据。

用法:
    python local/query_data.py AU0                                 # 查看沪金全部数据
    python local/query_data.py AU0 --start 2024-06-01              # 从指定日期
    python local/query_data.py AU0 --start 2024-01-01 --end 2024-12-31  # 指定区间
    python local/query_data.py AU0 --max                           # 查历史最高价
    python local/query_data.py AU0 --min                           # 查历史最低价
    python local/query_data.py AU0 --tail 20                       # 最近20条
    python local/query_data.py --list                              # 列出所有本地数据
"""
import argparse
import os
import sys
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

try:
    import pandas as pd
except ImportError:
    print("请先安装依赖: pip install pandas pyarrow")
    sys.exit(1)

# 尝试导入 DuckDB，不强制要求
try:
    import duckdb
    HAS_DUCKDB = True
except ImportError:
    HAS_DUCKDB = False

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(SKILL_DIR, 'data')


def list_data_files():
    """列出所有本地数据文件"""
    print("# 本地数据文件\n")
    if not os.path.exists(DATA_DIR):
        print("数据目录为空，请先运行 download_history.py")
        return

    files = [f for f in os.listdir(DATA_DIR) if f.endswith('.parquet')]
    if not files:
        print("无数据文件，请先运行 download_history.py")
        return

    print("| 品种 | 条数 | 起始日期 | 结束日期 |")
    print("|------|------|----------|----------|")
    for f in sorted(files):
        filepath = os.path.join(DATA_DIR, f)
        try:
            df = pd.read_parquet(filepath)
            df['datetime'] = pd.to_datetime(df['datetime'])
            symbol = f.replace('_daily.parquet', '')
            start = df['datetime'].min().strftime('%Y-%m-%d')
            end = df['datetime'].max().strftime('%Y-%m-%d')
            print(f"| {symbol} | {len(df)} | {start} | {end} |")
        except Exception:
            print(f"| {f} | 读取失败 | - | - |")


def query_data(symbol: str, start_date: str = None, end_date: str = None,
               tail: int = None, show_max: bool = False, show_min: bool = False) -> pd.DataFrame:
    """查询本地数据"""
    filepath = os.path.join(DATA_DIR, f'{symbol}_daily.parquet')
    if not os.path.exists(filepath):
        print(f"未找到 {symbol} 的本地数据文件: {filepath}")
        print("请先运行: python local/download_history.py --symbol " + symbol)
        return None

    df = pd.read_parquet(filepath)
    df['datetime'] = pd.to_datetime(df['datetime'])

    if start_date:
        df = df[df['datetime'] >= pd.to_datetime(start_date)]
    if end_date:
        df = df[df['datetime'] <= pd.to_datetime(end_date)]

    df = df.sort_values('datetime').reset_index(drop=True)
    return df


def format_query_output(df: pd.DataFrame, symbol: str,
                        show_max: bool = False, show_min: bool = False,
                        tail: int = None) -> str:
    """格式化查询结果"""
    if df is None or len(df) == 0:
        return "无数据"

    lines = [
        f"# {symbol} 本地数据查询\n",
        f"**数据范围**: {df['datetime'].iloc[0].strftime('%Y-%m-%d')} ~ {df['datetime'].iloc[-1].strftime('%Y-%m-%d')}",
        f"**数据条数**: {len(df)} 条\n",
    ]

    if show_max:
        max_row = df.loc[df['high'].idxmax()]
        lines.append("## 历史最高价\n")
        lines.append("| 项目 | 数值 |")
        lines.append("|------|------|")
        lines.append(f"| 日期 | {max_row['datetime'].strftime('%Y-%m-%d')} |")
        lines.append(f"| 最高价 | {max_row['high']:.2f} |")
        lines.append(f"| 收盘价 | {max_row['close']:.2f} |")
        lines.append("")

    if show_min:
        min_row = df.loc[df['low'].idxmin()]
        lines.append("## 历史最低价\n")
        lines.append("| 项目 | 数值 |")
        lines.append("|------|------|")
        lines.append(f"| 日期 | {min_row['datetime'].strftime('%Y-%m-%d')} |")
        lines.append(f"| 最低价 | {min_row['low']:.2f} |")
        lines.append(f"| 收盘价 | {min_row['close']:.2f} |")
        lines.append("")

    # 显示数据
    display_df = df.tail(tail) if tail else df.tail(20)
    lines.append(f"## 最近 {len(display_df)} 条数据\n")
    lines.append("| 日期 | 开盘 | 最高 | 最低 | 收盘 | 成交量 |")
    lines.append("|------|------|------|------|------|--------|")
    for _, row in display_df.iterrows():
        vol = f"{int(row.get('volume', 0)):,}" if 'volume' in df.columns else '-'
        lines.append(
            f"| {row['datetime'].strftime('%Y-%m-%d')} | "
            f"{row['open']:.2f} | {row['high']:.2f} | {row['low']:.2f} | "
            f"{row['close']:.2f} | {vol} |"
        )

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description='本地期货数据查询')
    parser.add_argument('symbol', nargs='?', help='品种代码')
    parser.add_argument('--start', help='起始日期 YYYY-MM-DD')
    parser.add_argument('--end', help='结束日期 YYYY-MM-DD')
    parser.add_argument('--tail', type=int, help='显示最后N条')
    parser.add_argument('--max', action='store_true', help='查询历史最高价')
    parser.add_argument('--min', action='store_true', help='查询历史最低价')
    parser.add_argument('--list', action='store_true', help='列出所有本地数据')

    args = parser.parse_args()

    if args.list or not args.symbol:
        list_data_files()
        return

    symbol = args.symbol.upper()
    df = query_data(symbol, args.start, args.end)

    if df is not None:
        output = format_query_output(df, symbol, args.max, args.min, args.tail)
        print(output)


if __name__ == '__main__':
    main()
