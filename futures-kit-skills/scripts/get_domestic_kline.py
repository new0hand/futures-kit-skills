# -*- coding: utf-8 -*-
"""
国内期货历史K线数据

数据源: AKShare -> 新浪财经
支持: 日K线、分钟K线(1/5/15/30/60分钟)

用法:
    python get_domestic_kline.py AU0                        # 沪金主力日K（默认60天）
    python get_domestic_kline.py AU0 --days 365             # 一年日K
    python get_domestic_kline.py CU0 --start 2024-01-01    # 指定起止日期
    python get_domestic_kline.py AU0 -i 60 --days 30       # 60分钟K线
    python get_domestic_kline.py SC0 -i 5 --days 5         # 5分钟K线
"""
import argparse
import os
import sys
import time
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

try:
    import akshare as ak
    import pandas as pd
    import numpy as np
except ImportError:
    print("请先安装依赖: pip install akshare pandas numpy")
    sys.exit(1)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from cache_manager import cache_get, cache_set

# 品种信息
SYMBOL_INFO = {
    'AU0': {'name': '黄金', 'exchange': 'SHFE'},
    'CU0': {'name': '铜', 'exchange': 'SHFE'},
    'LC0': {'name': '碳酸锂', 'exchange': 'GFEX'},
    'SC0': {'name': '原油', 'exchange': 'INE'},
    'AG0': {'name': '白银', 'exchange': 'SHFE'},
    'AL0': {'name': '铝', 'exchange': 'SHFE'},
    'ZN0': {'name': '锌', 'exchange': 'SHFE'},
    'RB0': {'name': '螺纹钢', 'exchange': 'SHFE'},
    'FU0': {'name': '燃料油', 'exchange': 'SHFE'},
}


def get_kline(symbol: str, interval: str = 'daily', days: int = 60,
              start_date: str = None, end_date: str = None) -> pd.DataFrame:
    """
    获取国内期货K线数据

    Args:
        symbol: 期货代码，如 AU0（主力）、AU2412（指定月份）
        interval: K线周期 - 'daily' 或 分钟数 '1','5','15','30','60'
        days: 获取天数
        start_date: 起始日期 YYYY-MM-DD
        end_date: 结束日期 YYYY-MM-DD

    Returns:
        DataFrame: columns = [datetime, open, high, low, close, volume, hold]
    """
    # 检查缓存
    cache_key_type = 'kline_1d' if interval == 'daily' else 'kline_min'
    cached = cache_get(cache_key_type, symbol, interval, days)
    if cached:
        return pd.DataFrame(cached)

    try:
        if interval == 'daily':
            # 日K线
            df = ak.futures_zh_daily_sina(symbol=symbol)
            if df is None or len(df) == 0:
                print(f"获取 {symbol} 日K线失败", file=sys.stderr)
                return None

            # 标准化列名
            col_map = {
                'date': 'datetime', '日期': 'datetime',
                'open': 'open', '开盘价': 'open',
                'high': 'high', '最高价': 'high',
                'low': 'low', '最低价': 'low',
                'close': 'close', '收盘价': 'close',
                'volume': 'volume', '成交量': 'volume',
                'hold': 'hold', '持仓量': 'hold',
            }
            df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})

            # 确保有 datetime 列
            if 'datetime' not in df.columns:
                # 尝试用索引
                df['datetime'] = df.index

            df['datetime'] = pd.to_datetime(df['datetime'])

            # 按日期过滤
            if start_date:
                df = df[df['datetime'] >= pd.to_datetime(start_date)]
            elif days:
                cutoff = datetime.now() - timedelta(days=days)
                df = df[df['datetime'] >= cutoff]

            if end_date:
                df = df[df['datetime'] <= pd.to_datetime(end_date)]

        else:
            # 分钟K线
            period = str(interval)
            df = ak.futures_zh_minute_sina(symbol=symbol, period=period)
            if df is None or len(df) == 0:
                print(f"获取 {symbol} {period}分钟K线失败", file=sys.stderr)
                return None

            col_map = {
                'datetime': 'datetime', '日期时间': 'datetime',
                'open': 'open', '开盘': 'open',
                'high': 'high', '最高': 'high',
                'low': 'low', '最低': 'low',
                'close': 'close', '收盘': 'close',
                'volume': 'volume', '成交量': 'volume',
                'hold': 'hold', '持仓量': 'hold',
            }
            df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})

            if 'datetime' not in df.columns:
                df['datetime'] = df.index

            df['datetime'] = pd.to_datetime(df['datetime'])

            # 分钟线按天数过滤
            if days:
                cutoff = datetime.now() - timedelta(days=days)
                df = df[df['datetime'] >= cutoff]

        # 确保数值列
        for col in ['open', 'high', 'low', 'close', 'volume']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        if 'hold' in df.columns:
            df['hold'] = pd.to_numeric(df['hold'], errors='coerce').fillna(0).astype(int)

        df = df.sort_values('datetime').reset_index(drop=True)

        # 缓存
        cache_data = df.to_dict(orient='records')
        cache_set(cache_key_type, cache_data, symbol, interval, days)

        return df

    except Exception as e:
        print(f"获取 {symbol} K线失败: {e}", file=sys.stderr)
        return None


def format_kline_output(df: pd.DataFrame, symbol: str, interval: str) -> str:
    """格式化K线输出"""
    if df is None or len(df) == 0:
        return f"获取 {symbol} K线数据失败"

    name = SYMBOL_INFO.get(symbol, {}).get('name', symbol)
    period_str = '日K线' if interval == 'daily' else f'{interval}分钟K线'

    lines = [
        f"# {name}({symbol}) {period_str}\n",
        f"**数据范围**: {df['datetime'].iloc[0].strftime('%Y-%m-%d')} ~ {df['datetime'].iloc[-1].strftime('%Y-%m-%d')}",
        f"**数据条数**: {len(df)} 条\n",
    ]

    # 最近行情摘要
    latest = df.iloc[-1]
    lines.append("## 最新行情\n")
    lines.append("| 项目 | 数值 |")
    lines.append("|------|------|")
    lines.append(f"| 日期 | {latest['datetime'].strftime('%Y-%m-%d')} |")
    lines.append(f"| 开盘 | {latest['open']:.2f} |")
    lines.append(f"| 最高 | {latest['high']:.2f} |")
    lines.append(f"| 最低 | {latest['low']:.2f} |")
    lines.append(f"| 收盘 | {latest['close']:.2f} |")
    if 'volume' in df.columns:
        lines.append(f"| 成交量 | {int(latest['volume']):,} |")
    if 'hold' in df.columns and latest.get('hold', 0) > 0:
        lines.append(f"| 持仓量 | {int(latest['hold']):,} |")
    lines.append("")

    # 最近10条数据
    lines.append("## 最近10条数据\n")
    lines.append("| 日期 | 开盘 | 最高 | 最低 | 收盘 | 成交量 |")
    lines.append("|------|------|------|------|------|--------|")
    for _, row in df.tail(10).iterrows():
        dt = row['datetime'].strftime('%Y-%m-%d') if interval == 'daily' else row['datetime'].strftime('%m-%d %H:%M')
        vol = f"{int(row.get('volume', 0)):,}" if 'volume' in df.columns else '-'
        lines.append(f"| {dt} | {row['open']:.2f} | {row['high']:.2f} | {row['low']:.2f} | {row['close']:.2f} | {vol} |")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description='国内期货历史K线')
    parser.add_argument('symbol', help='期货代码 (如 AU0, CU0, LC0, SC0)')
    parser.add_argument('--days', type=int, default=60, help='获取天数 (默认60)')
    parser.add_argument('--start', help='起始日期 YYYY-MM-DD')
    parser.add_argument('--end', help='结束日期 YYYY-MM-DD')
    parser.add_argument('-i', '--interval', default='daily',
                        help='K线周期: daily(默认), 1, 5, 15, 30, 60')
    parser.add_argument('-o', '--output', help='输出文件路径')

    args = parser.parse_args()

    symbol = args.symbol.upper()
    df = get_kline(symbol, args.interval, args.days, args.start, args.end)

    output = format_kline_output(df, symbol, args.interval)
    print(output)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"\n已保存至: {args.output}")


if __name__ == '__main__':
    main()
