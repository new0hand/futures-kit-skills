# -*- coding: utf-8 -*-
"""
国际期货历史K线数据

数据源: AKShare -> 新浪财经/东方财富
支持品种: 伦敦金(XAU)、COMEX铜(HG)、WTI原油、布伦特原油

用法:
    python get_foreign_kline.py XAU --days 365      # 伦敦金一年日K
    python get_foreign_kline.py HG --days 365       # COMEX铜
    python get_foreign_kline.py WTI --days 365      # WTI原油
    python get_foreign_kline.py BRENT --days 365    # 布伦特原油
    python get_foreign_kline.py --all --days 30     # 全部品种近30天
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

# 国际期货品种映射
# AKShare futures_foreign_hist 使用英文代码
# 可用代码列表: ak.futures_foreign_commodity_subscribe_exchange_symbol()
FOREIGN_SYMBOLS = {
    'XAU': {
        'name': '伦敦金(现货)',
        'akshare_code': 'XAU',
        'unit': '美元/盎司',
    },
    'GC': {
        'name': 'COMEX黄金(期货)',
        'akshare_code': 'GC',
        'unit': '美元/盎司',
    },
    'HG': {
        'name': 'COMEX铜',
        'akshare_code': 'HG',
        'unit': '美分/磅',
    },
    'WTI': {
        'name': 'WTI原油',
        'akshare_code': 'CL',
        'unit': '美元/桶',
    },
    'CL': {
        'name': 'WTI原油',
        'akshare_code': 'CL',
        'unit': '美元/桶',
    },
    'BRENT': {
        'name': '布伦特原油',
        'akshare_code': 'OIL',
        'unit': '美元/桶',
    },
    'OIL': {
        'name': '布伦特原油',
        'akshare_code': 'OIL',
        'unit': '美元/桶',
    },
    'XAG': {
        'name': '伦敦银',
        'akshare_code': 'XAG',
        'unit': '美元/盎司',
    },
}


def get_foreign_kline(symbol: str, days: int = 365) -> pd.DataFrame:
    """
    获取国际期货日K线

    Args:
        symbol: 品种代码 (XAU, HG, WTI, BRENT)
        days: 获取天数

    Returns:
        DataFrame: columns = [datetime, open, high, low, close, volume]
    """
    symbol = symbol.upper()
    if symbol not in FOREIGN_SYMBOLS:
        print(f"不支持的品种: {symbol}")
        print(f"支持品种: {', '.join(FOREIGN_SYMBOLS.keys())}")
        return None

    # 检查缓存
    cached = cache_get('foreign', symbol, days)
    if cached:
        df = pd.DataFrame(cached)
        if 'datetime' in df.columns:
            df['datetime'] = pd.to_datetime(df['datetime'])
        return df

    info = FOREIGN_SYMBOLS[symbol]
    akshare_code = info['akshare_code']

    try:
        # AKShare 获取国际期货历史数据（使用英文代码）
        df = ak.futures_foreign_hist(symbol=akshare_code)

        if df is None or len(df) == 0:
            print(f"获取 {info['name']} 数据失败", file=sys.stderr)
            return None

        # 标准化列名
        col_map = {
            'date': 'datetime', '日期': 'datetime',
            'open': 'open', '开盘': 'open', '开盘价': 'open',
            'high': 'high', '最高': 'high', '最高价': 'high',
            'low': 'low', '最低': 'low', '最低价': 'low',
            'close': 'close', '收盘': 'close', '收盘价': 'close',
            'volume': 'volume', '成交量': 'volume',
        }
        df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})

        if 'datetime' not in df.columns:
            df['datetime'] = df.index

        df['datetime'] = pd.to_datetime(df['datetime'])

        # 数值列
        for col in ['open', 'high', 'low', 'close', 'volume']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # 按天数过滤
        if days:
            cutoff = datetime.now() - timedelta(days=days)
            df = df[df['datetime'] >= cutoff]

        df = df.sort_values('datetime').reset_index(drop=True)
        df = df.dropna(subset=['close'])

        # 缓存
        cache_data = df.to_dict(orient='records')
        cache_set('foreign', cache_data, symbol, days)

        return df

    except Exception as e:
        print(f"获取 {info['name']}({symbol}) 数据失败: {e}", file=sys.stderr)
        return None


def format_output(df: pd.DataFrame, symbol: str) -> str:
    """格式化输出"""
    if df is None or len(df) == 0:
        return f"获取 {symbol} 数据失败"

    info = FOREIGN_SYMBOLS.get(symbol, {})
    name = info.get('name', symbol)
    unit = info.get('unit', '')

    lines = [
        f"# {name}({symbol}) 日K线\n",
        f"**单位**: {unit}",
        f"**数据范围**: {df['datetime'].iloc[0].strftime('%Y-%m-%d')} ~ {df['datetime'].iloc[-1].strftime('%Y-%m-%d')}",
        f"**数据条数**: {len(df)} 条\n",
    ]

    # 最新行情
    latest = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else latest
    change = latest['close'] - prev['close']
    change_pct = (change / prev['close']) * 100 if prev['close'] != 0 else 0

    lines.append("## 最新行情\n")
    lines.append("| 项目 | 数值 |")
    lines.append("|------|------|")
    lines.append(f"| 日期 | {latest['datetime'].strftime('%Y-%m-%d')} |")
    lines.append(f"| 收盘价 | {latest['close']:.2f} |")
    lines.append(f"| 涨跌 | {change:+.2f} ({change_pct:+.2f}%) |")
    lines.append(f"| 最高 | {latest['high']:.2f} |")
    lines.append(f"| 最低 | {latest['low']:.2f} |")
    lines.append("")

    # 区间统计
    lines.append("## 区间统计\n")
    lines.append("| 项目 | 数值 |")
    lines.append("|------|------|")
    lines.append(f"| 区间最高 | {df['high'].max():.2f} |")
    lines.append(f"| 区间最低 | {df['low'].min():.2f} |")
    lines.append(f"| 区间涨跌 | {((df['close'].iloc[-1]/df['close'].iloc[0])-1)*100:.2f}% |")
    lines.append("")

    # 最近10条
    lines.append("## 最近10条数据\n")
    lines.append("| 日期 | 开盘 | 最高 | 最低 | 收盘 | 涨跌% |")
    lines.append("|------|------|------|------|------|-------|")
    recent = df.tail(10)
    for i, (_, row) in enumerate(recent.iterrows()):
        if i == 0:
            pct_str = "-"
        else:
            prev_close = recent.iloc[i-1]['close']
            pct = ((row['close'] - prev_close) / prev_close) * 100 if prev_close else 0
            pct_str = f"{pct:+.2f}%"
        lines.append(
            f"| {row['datetime'].strftime('%Y-%m-%d')} | "
            f"{row['open']:.2f} | {row['high']:.2f} | {row['low']:.2f} | "
            f"{row['close']:.2f} | {pct_str} |"
        )

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description='国际期货历史K线')
    parser.add_argument('symbol', nargs='?', help='品种代码 (XAU, HG, WTI, BRENT)')
    parser.add_argument('--days', type=int, default=365, help='获取天数 (默认365)')
    parser.add_argument('--all', action='store_true', help='全部品种')
    parser.add_argument('-o', '--output', help='输出文件路径')

    args = parser.parse_args()

    if args.all:
        for sym in FOREIGN_SYMBOLS.keys():
            df = get_foreign_kline(sym, args.days)
            print(format_output(df, sym))
            print("\n" + "=" * 60 + "\n")
            time.sleep(1)
    elif args.symbol:
        symbol = args.symbol.upper()
        df = get_foreign_kline(symbol, args.days)
        output = format_output(df, symbol)
        print(output)
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output)
            print(f"\n已保存至: {args.output}")
    else:
        print("请指定品种代码或使用 --all")
        print(f"支持品种: {', '.join(FOREIGN_SYMBOLS.keys())}")
        sys.exit(1)


if __name__ == '__main__':
    main()
