# -*- coding: utf-8 -*-
"""
国内期货实时行情

数据源: AKShare -> 新浪财经
支持品种: 黄金(AU)、铜(CU)、碳酸锂(LC)、原油(SC) 等全部国内期货品种

用法:
    python get_domestic_realtime.py AU0          # 沪金主力
    python get_domestic_realtime.py CU0          # 沪铜主力
    python get_domestic_realtime.py LC0          # 碳酸锂主力
    python get_domestic_realtime.py SC0          # 原油主力
    python get_domestic_realtime.py --all        # 全部监控品种
"""
import argparse
import os
import sys
import time
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

try:
    import akshare as ak
    import pandas as pd
except ImportError:
    print("请先安装依赖: pip install akshare pandas")
    sys.exit(1)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from cache_manager import cache_get, cache_set

# 监控品种列表
WATCHLIST = {
    'AU0': {'name': '黄金', 'exchange': 'SHFE', 'unit': '元/克', 'multiplier': 1000},
    'CU0': {'name': '铜', 'exchange': 'SHFE', 'unit': '元/吨', 'multiplier': 5},
    'LC0': {'name': '碳酸锂', 'exchange': 'GFEX', 'unit': '元/吨', 'multiplier': 1},
    'SC0': {'name': '原油', 'exchange': 'INE', 'unit': '元/桶', 'multiplier': 1000},
}


def get_realtime_quote(symbol: str) -> dict:
    """获取单个品种实时行情"""
    # 检查缓存
    cached = cache_get('realtime', symbol)
    if cached:
        return cached

    # 方法1: futures_zh_spot
    try:
        df = ak.futures_zh_spot(symbol=symbol, market="CF", adjust="0")
        if df is not None and len(df) > 0:
            row = df.iloc[0]
            # 计算涨跌幅
            current = float(row.get('current_price', 0))
            pre_settle = float(row.get('last_settle_price', 0))
            change_pct = ((current - pre_settle) / pre_settle * 100) if pre_settle > 0 else 0
            change = current - pre_settle if pre_settle > 0 else 0

            result = {
                'symbol': symbol,
                'name': WATCHLIST.get(symbol, {}).get('name', symbol),
                'current_price': current,
                'change_pct': change_pct,
                'change': change,
                'open': float(row.get('open', 0)),
                'high': float(row.get('high', 0)),
                'low': float(row.get('low', 0)),
                'volume': int(row.get('volume', 0)),
                'amount': 0.0,
                'hold': int(row.get('hold', 0)),
                'settle': 0.0,
                'pre_settle': pre_settle,
                'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            }
            cache_set('realtime', result, symbol)
            return result
    except Exception as e:
        print(f"[futures_zh_spot] {symbol} 失败: {e}", file=sys.stderr)

    # 方法2: futures_zh_realtime
    try:
        df = ak.futures_zh_realtime(symbol=symbol)
        if df is not None and len(df) > 0:
            row = df.iloc[0]
            result = {
                'symbol': symbol,
                'name': WATCHLIST.get(symbol, {}).get('name', symbol),
                'current_price': float(row.get('current_price', row.get('最新价', 0))),
                'change_pct': float(row.get('涨跌幅', 0)),
                'change': 0.0,
                'open': float(row.get('open', row.get('今开', 0))),
                'high': float(row.get('high', row.get('最高', 0))),
                'low': float(row.get('low', row.get('最低', 0))),
                'volume': int(row.get('volume', row.get('成交量', 0))),
                'amount': 0.0,
                'hold': int(row.get('hold', row.get('持仓量', 0))),
                'settle': 0.0,
                'pre_settle': 0.0,
                'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            }
            cache_set('realtime', result, symbol)
            return result
    except Exception as e:
        print(f"[futures_zh_realtime] {symbol} 失败: {e}", file=sys.stderr)

    # 方法3: futures_main_sina（用最近一天的日线当作最新行情，休市也能用）
    try:
        from datetime import timedelta
        end = datetime.now().strftime('%Y%m%d')
        start = (datetime.now() - timedelta(days=10)).strftime('%Y%m%d')
        df = ak.futures_main_sina(symbol=symbol, start_date=start, end_date=end)
        if df is not None and len(df) > 0:
            row = df.iloc[-1]  # 最后一条 = 最近交易日
            close = float(row.get('收盘价', 0))
            settle = float(row.get('动态结算价', 0))
            prev_close = float(df.iloc[-2]['收盘价']) if len(df) > 1 else close
            change_pct = ((close - prev_close) / prev_close * 100) if prev_close > 0 else 0

            result = {
                'symbol': symbol,
                'name': WATCHLIST.get(symbol, {}).get('name', symbol),
                'current_price': close,
                'change_pct': change_pct,
                'change': close - prev_close,
                'open': float(row.get('开盘价', 0)),
                'high': float(row.get('最高价', 0)),
                'low': float(row.get('最低价', 0)),
                'volume': int(row.get('成交量', 0)),
                'amount': 0.0,
                'hold': int(row.get('持仓量', 0)),
                'settle': settle,
                'pre_settle': prev_close,
                'update_time': f"{row.get('日期', '')} (收盘)",
            }
            cache_set('realtime', result, symbol)
            return result
    except Exception as e:
        print(f"[futures_main_sina] {symbol} 失败: {e}", file=sys.stderr)

    print(f"获取 {symbol} 实时行情失败（所有数据源均不可用）", file=sys.stderr)
    return None


def format_single(data: dict) -> str:
    """格式化单个品种行情"""
    if not data:
        return "获取失败"

    lines = [
        f"# {data['name']}({data['symbol']}) 实时行情\n",
        f"**更新时间**: {data['update_time']}\n",
        "| 项目 | 数值 |",
        "|------|------|",
        f"| 最新价 | {data['current_price']:.2f} |",
        f"| 涨跌幅 | {data['change_pct']:.2f}% |",
    ]

    if data.get('change'):
        lines.append(f"| 涨跌额 | {data['change']:.2f} |")
    if data.get('open'):
        lines.append(f"| 今开 | {data['open']:.2f} |")
    if data.get('high'):
        lines.append(f"| 最高 | {data['high']:.2f} |")
    if data.get('low'):
        lines.append(f"| 最低 | {data['low']:.2f} |")
    if data.get('volume'):
        lines.append(f"| 成交量 | {data['volume']:,} 手 |")
    if data.get('hold'):
        lines.append(f"| 持仓量 | {data['hold']:,} 手 |")
    if data.get('settle'):
        lines.append(f"| 结算价 | {data['settle']:.2f} |")

    return "\n".join(lines)


def format_all(data_list: list) -> str:
    """格式化全部品种行情概览"""
    lines = [
        "# 期货监控品种行情概览\n",
        f"**更新时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
        "| 品种 | 代码 | 最新价 | 涨跌幅 | 成交量 | 持仓量 |",
        "|------|------|--------|--------|--------|--------|",
    ]

    for data in data_list:
        if data:
            pct = data.get('change_pct', 0)
            pct_str = f"+{pct:.2f}%" if pct > 0 else f"{pct:.2f}%"
            lines.append(
                f"| {data['name']} | {data['symbol']} | "
                f"{data['current_price']:.2f} | {pct_str} | "
                f"{data.get('volume', 0):,} | {data.get('hold', 0):,} |"
            )

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description='国内期货实时行情')
    parser.add_argument('symbol', nargs='?', help='期货代码 (如 AU0, CU0)')
    parser.add_argument('--all', action='store_true', help='全部监控品种')

    args = parser.parse_args()

    if args.all or not args.symbol:
        # 获取全部品种
        data_list = []
        for sym in WATCHLIST.keys():
            data = get_realtime_quote(sym)
            data_list.append(data)
            time.sleep(0.5)  # 请求间隔
        print(format_all(data_list))
    else:
        symbol = args.symbol.upper()
        data = get_realtime_quote(symbol)
        if data:
            print(format_single(data))
        else:
            print(f"获取 {symbol} 实时行情失败")
            sys.exit(1)


if __name__ == '__main__':
    main()
