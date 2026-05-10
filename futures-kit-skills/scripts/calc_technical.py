# -*- coding: utf-8 -*-
"""
期货技术指标计算

支持指标:
- MA: 均线 (5/10/20/60日)
- MACD: 指数平滑异同移动平均线 (12/26/9)
- RSI: 相对强弱指标 (6/12/24日)
- KDJ: 随机指标 (9/3/3)
- BOLL: 布林带 (20日 ± 2标准差)

用法:
    python calc_technical.py AU0                         # 国内期货（默认）
    python calc_technical.py XAU --source foreign        # 国际期货
    python calc_technical.py USDCNY --source forex       # 外汇
    python calc_technical.py AU0 --days 120              # 指定计算周期
    python calc_technical.py AU0 --indicators MA MACD    # 指定指标
"""
import argparse
import os
import sys
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

try:
    import pandas as pd
    import numpy as np
except ImportError:
    print("请先安装依赖: pip install pandas numpy")
    sys.exit(1)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)


def get_data(symbol: str, source: str, days: int) -> pd.DataFrame:
    """根据数据源获取K线"""
    if source == 'domestic':
        from get_domestic_kline import get_kline
        return get_kline(symbol, 'daily', days)
    elif source == 'foreign':
        from get_foreign_kline import get_foreign_kline
        return get_foreign_kline(symbol, days)
    elif source == 'forex':
        from get_forex import get_forex_data
        return get_forex_data(symbol, days)
    else:
        # 自动判断
        from get_domestic_kline import get_kline, SYMBOL_INFO
        if symbol.upper() in SYMBOL_INFO or symbol.upper().endswith('0'):
            return get_kline(symbol, 'daily', days)
        from get_foreign_kline import FOREIGN_SYMBOLS
        if symbol.upper() in FOREIGN_SYMBOLS:
            from get_foreign_kline import get_foreign_kline
            return get_foreign_kline(symbol, days)
        from get_forex import FOREX_SYMBOLS
        if symbol.upper() in FOREX_SYMBOLS:
            from get_forex import get_forex_data
            return get_forex_data(symbol, days)
        # 默认当国内期货
        return get_kline(symbol, 'daily', days)


def calc_ma(df: pd.DataFrame, periods: list = [5, 10, 20, 60]) -> pd.DataFrame:
    """计算均线"""
    for period in periods:
        if len(df) >= period:
            df[f'MA{period}'] = df['close'].rolling(window=period).mean()
    return df


def calc_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    """计算 MACD"""
    exp1 = df['close'].ewm(span=fast, adjust=False).mean()
    exp2 = df['close'].ewm(span=slow, adjust=False).mean()
    df['DIF'] = exp1 - exp2
    df['DEA'] = df['DIF'].ewm(span=signal, adjust=False).mean()
    df['MACD'] = 2 * (df['DIF'] - df['DEA'])
    return df


def calc_rsi(df: pd.DataFrame, periods: list = [6, 12, 24]) -> pd.DataFrame:
    """计算 RSI"""
    delta = df['close'].diff()
    for period in periods:
        gain = delta.where(delta > 0, 0).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        df[f'RSI{period}'] = 100 - (100 / (1 + rs))
    return df


def calc_kdj(df: pd.DataFrame, n: int = 9, m1: int = 3, m2: int = 3) -> pd.DataFrame:
    """计算 KDJ"""
    low_min = df['low'].rolling(window=n).min()
    high_max = df['high'].rolling(window=n).max()
    rsv = (df['close'] - low_min) / (high_max - low_min) * 100
    df['K'] = rsv.ewm(alpha=1/m1, adjust=False).mean()
    df['D'] = df['K'].ewm(alpha=1/m2, adjust=False).mean()
    df['J'] = 3 * df['K'] - 2 * df['D']
    return df


def calc_boll(df: pd.DataFrame, period: int = 20, std_dev: int = 2) -> pd.DataFrame:
    """计算布林带"""
    df['BOLL_MID'] = df['close'].rolling(window=period).mean()
    std = df['close'].rolling(window=period).std()
    df['BOLL_UP'] = df['BOLL_MID'] + std_dev * std
    df['BOLL_DOWN'] = df['BOLL_MID'] - std_dev * std
    return df


def calc_atr(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """计算 ATR (平均真实波幅)"""
    high_low = df['high'] - df['low']
    high_close = (df['high'] - df['close'].shift(1)).abs()
    low_close = (df['low'] - df['close'].shift(1)).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(window=period).mean()
    return df


def calc_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """计算所有技术指标"""
    df = calc_ma(df)
    df = calc_macd(df)
    df = calc_rsi(df)
    df = calc_kdj(df)
    df = calc_boll(df)
    df = calc_atr(df)
    return df


def analyze_signals(df: pd.DataFrame) -> dict:
    """分析技术信号"""
    latest = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else latest
    signals = {}

    # 均线分析
    if 'MA5' in df.columns and 'MA20' in df.columns:
        if latest['MA5'] > latest['MA20'] and prev['MA5'] <= prev['MA20']:
            signals['均线'] = '🟢 金叉（MA5上穿MA20）'
        elif latest['MA5'] < latest['MA20'] and prev['MA5'] >= prev['MA20']:
            signals['均线'] = '🔴 死叉（MA5下穿MA20）'
        elif latest['close'] > latest['MA5'] > latest['MA20']:
            signals['均线'] = '🟢 多头排列'
        elif latest['close'] < latest['MA5'] < latest['MA20']:
            signals['均线'] = '🔴 空头排列'
        else:
            signals['均线'] = '⚪ 震荡'

    # MACD分析
    if 'DIF' in df.columns and 'DEA' in df.columns:
        if latest['DIF'] > latest['DEA'] and prev['DIF'] <= prev['DEA']:
            signals['MACD'] = '🟢 金叉'
        elif latest['DIF'] < latest['DEA'] and prev['DIF'] >= prev['DEA']:
            signals['MACD'] = '🔴 死叉'
        elif latest['MACD'] > 0:
            signals['MACD'] = '🟢 多头'
        else:
            signals['MACD'] = '🔴 空头'

    # RSI分析
    if 'RSI6' in df.columns:
        rsi = latest['RSI6']
        if pd.notna(rsi):
            if rsi > 80:
                signals['RSI'] = f'🔴 超买 ({rsi:.1f})'
            elif rsi < 20:
                signals['RSI'] = f'🟢 超卖 ({rsi:.1f})'
            elif rsi > 50:
                signals['RSI'] = f'🟢 偏强 ({rsi:.1f})'
            else:
                signals['RSI'] = f'🔴 偏弱 ({rsi:.1f})'

    # KDJ分析
    if 'K' in df.columns and 'D' in df.columns:
        if pd.notna(latest['K']) and pd.notna(latest['D']):
            if latest['K'] > latest['D'] and prev['K'] <= prev['D'] and latest['K'] < 20:
                signals['KDJ'] = '🟢 低位金叉'
            elif latest['K'] < latest['D'] and prev['K'] >= prev['D'] and latest['K'] > 80:
                signals['KDJ'] = '🔴 高位死叉'
            elif latest['J'] > 100:
                signals['KDJ'] = f'🔴 超买 (J={latest["J"]:.1f})'
            elif latest['J'] < 0:
                signals['KDJ'] = f'🟢 超卖 (J={latest["J"]:.1f})'
            else:
                signals['KDJ'] = '⚪ 中性'

    # 布林带分析
    if 'BOLL_UP' in df.columns and pd.notna(latest.get('BOLL_UP')):
        if latest['close'] > latest['BOLL_UP']:
            signals['BOLL'] = '🔴 突破上轨（注意回调）'
        elif latest['close'] < latest['BOLL_DOWN']:
            signals['BOLL'] = '🟢 突破下轨（注意反弹）'
        else:
            width = (latest['BOLL_UP'] - latest['BOLL_DOWN']) / latest['BOLL_MID'] * 100
            signals['BOLL'] = f'⚪ 通道内 (带宽{width:.1f}%)'

    return signals


def format_output(df: pd.DataFrame, symbol: str, signals: dict, source: str) -> str:
    """格式化输出为 Markdown"""
    latest = df.iloc[-1]
    price_fmt = '.4f' if source == 'forex' else '.2f'

    lines = [
        f"# {symbol} 技术分析\n",
        f"**分析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**最新价格**: {latest['close']:{price_fmt}}\n",
    ]

    # 信号汇总
    lines.append("## 技术信号\n")
    lines.append("| 指标 | 信号 |")
    lines.append("|------|------|")
    for name, signal in signals.items():
        lines.append(f"| {name} | {signal} |")
    lines.append("")

    # 指标数值
    lines.append("## 指标数值\n")

    lines.append("### 均线")
    lines.append("| MA5 | MA10 | MA20 | MA60 |")
    lines.append("|-----|------|------|------|")
    ma_vals = []
    for p in [5, 10, 20, 60]:
        v = latest.get(f'MA{p}')
        ma_vals.append(f"{v:{price_fmt}}" if pd.notna(v) else 'N/A')
    lines.append(f"| {' | '.join(ma_vals)} |")
    lines.append("")

    lines.append("### MACD")
    lines.append("| DIF | DEA | MACD |")
    lines.append("|-----|-----|------|")
    dif = f"{latest.get('DIF', 0):{price_fmt}}" if pd.notna(latest.get('DIF')) else 'N/A'
    dea = f"{latest.get('DEA', 0):{price_fmt}}" if pd.notna(latest.get('DEA')) else 'N/A'
    macd = f"{latest.get('MACD', 0):{price_fmt}}" if pd.notna(latest.get('MACD')) else 'N/A'
    lines.append(f"| {dif} | {dea} | {macd} |")
    lines.append("")

    lines.append("### RSI")
    lines.append("| RSI6 | RSI12 | RSI24 |")
    lines.append("|------|-------|-------|")
    rsi_vals = [f"{latest.get(f'RSI{p}', 0):.2f}" if pd.notna(latest.get(f'RSI{p}')) else 'N/A' for p in [6, 12, 24]]
    lines.append(f"| {' | '.join(rsi_vals)} |")
    lines.append("")

    lines.append("### KDJ")
    lines.append("| K | D | J |")
    lines.append("|---|---|---|")
    kdj_vals = [f"{latest.get(k, 0):.2f}" if pd.notna(latest.get(k)) else 'N/A' for k in ['K', 'D', 'J']]
    lines.append(f"| {' | '.join(kdj_vals)} |")
    lines.append("")

    lines.append("### 布林带")
    lines.append("| 上轨 | 中轨 | 下轨 |")
    lines.append("|------|------|------|")
    boll_vals = [f"{latest.get(k, 0):{price_fmt}}" if pd.notna(latest.get(k)) else 'N/A' for k in ['BOLL_UP', 'BOLL_MID', 'BOLL_DOWN']]
    lines.append(f"| {' | '.join(boll_vals)} |")
    lines.append("")

    if pd.notna(latest.get('ATR')):
        lines.append(f"### ATR(14): {latest['ATR']:{price_fmt}}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description='期货技术指标计算')
    parser.add_argument('symbol', help='品种代码 (AU0, XAU, USDCNY 等)')
    parser.add_argument('--source', choices=['domestic', 'foreign', 'forex', 'auto'],
                        default='auto', help='数据源 (默认自动判断)')
    parser.add_argument('--days', type=int, default=120, help='计算周期天数')
    parser.add_argument('-o', '--output', help='输出文件路径')

    args = parser.parse_args()

    symbol = args.symbol.upper()

    # 获取数据
    df = get_data(symbol, args.source, args.days)

    if df is None or len(df) == 0:
        print(f"获取 {symbol} 数据失败")
        sys.exit(1)

    # 计算指标
    df = calc_all_indicators(df)

    # 分析信号
    signals = analyze_signals(df)

    # 确定 source 用于格式化
    effective_source = args.source
    if effective_source == 'auto':
        from get_forex import FOREX_SYMBOLS
        if symbol in FOREX_SYMBOLS:
            effective_source = 'forex'
        else:
            effective_source = 'domestic'

    # 输出
    output = format_output(df, symbol, signals, effective_source)
    print(output)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"\n已保存至: {args.output}")


if __name__ == '__main__':
    main()
