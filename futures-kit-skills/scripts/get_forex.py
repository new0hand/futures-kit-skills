# -*- coding: utf-8 -*-
"""
外汇历史数据

数据源: AKShare -> 中国银行/外管局
支持: USD/CNY, EUR/USD, GBP/USD, USD/JPY 等主要货币对

用法:
    python get_forex.py USDCNY --days 365       # 美元人民币一年
    python get_forex.py EURUSD --days 60        # 欧元美元两个月
    python get_forex.py GBPUSD --days 365
    python get_forex.py USDJPY --days 365
    python get_forex.py --all --days 30         # 全部货币对近30天
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

# 外汇品种映射
# 使用 ak.forex_hist_em(symbol=...) 获取东方财富外汇数据
FOREX_SYMBOLS = {
    'USDCNY': {
        'name': '美元/人民币',
        'em_symbol': 'USDCNH',  # 东方财富用离岸人民币代码
    },
    'USDCNH': {
        'name': '美元/离岸人民币',
        'em_symbol': 'USDCNH',
    },
    'EURUSD': {
        'name': '欧元/美元',
        'em_symbol': 'EURUSD',
    },
    'GBPUSD': {
        'name': '英镑/美元',
        'em_symbol': 'GBPUSD',
    },
    'USDJPY': {
        'name': '美元/日元',
        'em_symbol': 'USDJPY',
    },
    'AUDUSD': {
        'name': '澳元/美元',
        'em_symbol': 'AUDUSD',
    },
    'USDCAD': {
        'name': '美元/加元',
        'em_symbol': 'USDCAD',
    },
}


def get_forex_data(symbol: str, days: int = 365) -> pd.DataFrame:
    """
    获取外汇历史数据

    Args:
        symbol: 货币对代码 (USDCNY, EURUSD 等)
        days: 获取天数

    Returns:
        DataFrame: columns = [datetime, close] (中间价)
    """
    symbol = symbol.upper()
    if symbol not in FOREX_SYMBOLS:
        print(f"不支持的货币对: {symbol}")
        print(f"支持品种: {', '.join(FOREX_SYMBOLS.keys())}")
        return None

    # 检查缓存
    cached = cache_get('forex', symbol, days)
    if cached:
        df = pd.DataFrame(cached)
        if 'datetime' in df.columns:
            df['datetime'] = pd.to_datetime(df['datetime'])
        return df

    info = FOREX_SYMBOLS[symbol]
    em_symbol = info['em_symbol']

    try:
        df = None

        # 方案1: 东方财富外汇数据 (OHLC完整)
        try:
            df = ak.forex_hist_em(symbol=em_symbol)
            if df is not None and len(df) > 0:
                col_map = {
                    '日期': 'datetime', 'date': 'datetime',
                    '今开': 'open', '最新价': 'close',
                    '最高': 'high', '最低': 'low',
                }
                df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
        except Exception:
            df = None

        # 方案2: 中国银行新浪外汇牌价 (备用，只有收盘价)
        if df is None or len(df) == 0:
            # 从 em_symbol 映射到中行货币名
            boc_map = {
                'USDCNH': '美元', 'EURUSD': '欧元', 'GBPUSD': '英镑',
                'USDJPY': '日元', 'AUDUSD': '澳大利亚元', 'USDCAD': '加拿大元',
            }
            boc_currency = boc_map.get(em_symbol)
            if boc_currency:
                start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')
                end_date = datetime.now().strftime('%Y%m%d')
                boc_df = ak.currency_boc_sina(
                    symbol=boc_currency,
                    start_date=start_date,
                    end_date=end_date
                )
                if boc_df is not None and len(boc_df) > 0:
                    df = pd.DataFrame()
                    df['datetime'] = pd.to_datetime(boc_df['日期'])
                    # 中行折算价作为收盘价（单位是分，需除100变为标准汇率）
                    price_col = '央行中间价' if '央行中间价' in boc_df.columns else '中行折算价'
                    df['close'] = pd.to_numeric(boc_df[price_col], errors='coerce') / 100
                    df['open'] = df['close']
                    df['high'] = df['close']
                    df['low'] = df['close']

        if df is None or len(df) == 0:
            print(f"获取 {info['name']} 数据失败", file=sys.stderr)
            return None

        if 'datetime' not in df.columns:
            df['datetime'] = df.index

        df['datetime'] = pd.to_datetime(df['datetime'])

        # 数值列
        for col in ['open', 'high', 'low', 'close']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # 按天数过滤
        if days:
            cutoff = datetime.now() - timedelta(days=days)
            df = df[df['datetime'] >= cutoff]

        df = df[['datetime', 'open', 'high', 'low', 'close']].dropna(subset=['close'])
        df = df.sort_values('datetime').reset_index(drop=True)

        # 缓存
        cache_data = df.to_dict(orient='records')
        cache_set('forex', cache_data, symbol, days)

        return df

    except Exception as e:
        print(f"获取 {info['name']}({symbol}) 数据失败: {e}", file=sys.stderr)
        return None


def format_output(df: pd.DataFrame, symbol: str) -> str:
    """格式化输出"""
    if df is None or len(df) == 0:
        return f"获取 {symbol} 数据失败"

    info = FOREX_SYMBOLS.get(symbol, {})
    name = info.get('name', symbol)

    lines = [
        f"# {name}({symbol}) 汇率数据\n",
        f"**数据范围**: {df['datetime'].iloc[0].strftime('%Y-%m-%d')} ~ {df['datetime'].iloc[-1].strftime('%Y-%m-%d')}",
        f"**数据条数**: {len(df)} 条\n",
    ]

    # 最新汇率
    latest = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else latest
    change = latest['close'] - prev['close']
    change_pct = (change / prev['close']) * 100 if prev['close'] != 0 else 0

    lines.append("## 最新汇率\n")
    lines.append("| 项目 | 数值 |")
    lines.append("|------|------|")
    lines.append(f"| 日期 | {latest['datetime'].strftime('%Y-%m-%d')} |")
    lines.append(f"| 汇率 | {latest['close']:.4f} |")
    lines.append(f"| 日变动 | {change:+.4f} ({change_pct:+.3f}%) |")
    lines.append("")

    # 区间统计
    lines.append("## 区间统计\n")
    lines.append("| 项目 | 数值 |")
    lines.append("|------|------|")
    lines.append(f"| 区间最高 | {df['high'].max():.4f} |")
    lines.append(f"| 区间最低 | {df['low'].min():.4f} |")
    lines.append(f"| 区间均值 | {df['close'].mean():.4f} |")
    total_change = ((df['close'].iloc[-1] / df['close'].iloc[0]) - 1) * 100
    lines.append(f"| 区间涨跌 | {total_change:+.3f}% |")
    lines.append("")

    # 最近10条
    lines.append("## 最近10条数据\n")
    lines.append("| 日期 | 汇率 | 日变动 |")
    lines.append("|------|------|--------|")
    recent = df.tail(10)
    for i, (_, row) in enumerate(recent.iterrows()):
        if i == 0:
            chg_str = "-"
        else:
            prev_c = recent.iloc[i-1]['close']
            chg = ((row['close'] - prev_c) / prev_c) * 100
            chg_str = f"{chg:+.3f}%"
        lines.append(f"| {row['datetime'].strftime('%Y-%m-%d')} | {row['close']:.4f} | {chg_str} |")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description='外汇历史数据')
    parser.add_argument('symbol', nargs='?', help='货币对代码 (如 USDCNY, EURUSD)')
    parser.add_argument('--days', type=int, default=365, help='获取天数 (默认365)')
    parser.add_argument('--all', action='store_true', help='全部货币对')
    parser.add_argument('-o', '--output', help='输出文件路径')

    args = parser.parse_args()

    if args.all:
        for sym in FOREX_SYMBOLS.keys():
            df = get_forex_data(sym, args.days)
            print(format_output(df, sym))
            print("\n" + "=" * 60 + "\n")
            time.sleep(1)
    elif args.symbol:
        symbol = args.symbol.upper()
        df = get_forex_data(symbol, args.days)
        output = format_output(df, symbol)
        print(output)
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output)
            print(f"\n已保存至: {args.output}")
    else:
        print("请指定货币对或使用 --all")
        print(f"支持品种: {', '.join(FOREX_SYMBOLS.keys())}")
        sys.exit(1)


if __name__ == '__main__':
    main()
