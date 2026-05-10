# -*- coding: utf-8 -*-
"""
期货综合分析评分

三维度加权评分:
- 趋势分析 (40%): 均线排列、MACD方向、价格趋势
- 动量分析 (30%): RSI、KDJ、涨跌幅
- 波动率分析 (30%): 布林带宽、ATR、成交量

用法:
    python analyze_futures.py AU0                      # 国内黄金
    python analyze_futures.py XAU --source foreign     # 国际黄金
    python analyze_futures.py USDCNY --source forex    # 外汇
    python analyze_futures.py AU0 --days 120
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
from calc_technical import get_data, calc_all_indicators, analyze_signals


def score_trend(df: pd.DataFrame) -> tuple:
    """趋势评分 (0-100)"""
    latest = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else latest
    score = 50  # 中性基准
    details = []

    # 均线排列 (+/-20)
    if 'MA5' in df.columns and 'MA20' in df.columns:
        if pd.notna(latest['MA5']) and pd.notna(latest['MA20']):
            if latest['close'] > latest['MA5'] > latest['MA20']:
                score += 20
                details.append("多头排列 +20")
            elif latest['close'] < latest['MA5'] < latest['MA20']:
                score -= 20
                details.append("空头排列 -20")
            elif latest['MA5'] > latest['MA20']:
                score += 10
                details.append("短期均线在上 +10")
            else:
                score -= 10
                details.append("短期均线在下 -10")

    # MA5 金叉/死叉 (+/-10)
    if 'MA5' in df.columns and 'MA20' in df.columns:
        if pd.notna(prev.get('MA5')) and pd.notna(prev.get('MA20')):
            if latest['MA5'] > latest['MA20'] and prev['MA5'] <= prev['MA20']:
                score += 10
                details.append("MA金叉 +10")
            elif latest['MA5'] < latest['MA20'] and prev['MA5'] >= prev['MA20']:
                score -= 10
                details.append("MA死叉 -10")

    # MACD 方向 (+/-15)
    if 'MACD' in df.columns and pd.notna(latest.get('MACD')):
        if latest['MACD'] > 0 and latest['DIF'] > latest['DEA']:
            score += 15
            details.append("MACD多头 +15")
        elif latest['MACD'] < 0 and latest['DIF'] < latest['DEA']:
            score -= 15
            details.append("MACD空头 -15")

    # 价格相对位置 (+/-5)
    if 'MA60' in df.columns and pd.notna(latest.get('MA60')):
        if latest['close'] > latest['MA60']:
            score += 5
            details.append("价格在MA60上方 +5")
        else:
            score -= 5
            details.append("价格在MA60下方 -5")

    return max(0, min(100, score)), details


def score_momentum(df: pd.DataFrame) -> tuple:
    """动量评分 (0-100)"""
    latest = df.iloc[-1]
    score = 50
    details = []

    # RSI (+/-20)
    if 'RSI6' in df.columns and pd.notna(latest.get('RSI6')):
        rsi = latest['RSI6']
        if rsi > 70:
            score += 15
            details.append(f"RSI偏强({rsi:.0f}) +15")
        elif rsi > 50:
            score += 8
            details.append(f"RSI中性偏强({rsi:.0f}) +8")
        elif rsi < 30:
            score -= 15
            details.append(f"RSI偏弱({rsi:.0f}) -15")
        elif rsi < 50:
            score -= 8
            details.append(f"RSI中性偏弱({rsi:.0f}) -8")

    # KDJ (+/-15)
    if 'K' in df.columns and 'J' in df.columns:
        if pd.notna(latest.get('J')):
            j = latest['J']
            if j > 80:
                score += 10
                details.append(f"KDJ偏强(J={j:.0f}) +10")
            elif j < 20:
                score -= 10
                details.append(f"KDJ偏弱(J={j:.0f}) -10")

    # 近5日涨跌幅 (+/-15)
    if len(df) >= 6:
        pct_5d = (df['close'].iloc[-1] / df['close'].iloc[-6] - 1) * 100
        if pct_5d > 3:
            score += 15
            details.append(f"5日涨{pct_5d:.1f}% +15")
        elif pct_5d > 1:
            score += 8
            details.append(f"5日涨{pct_5d:.1f}% +8")
        elif pct_5d < -3:
            score -= 15
            details.append(f"5日跌{pct_5d:.1f}% -15")
        elif pct_5d < -1:
            score -= 8
            details.append(f"5日跌{pct_5d:.1f}% -8")

    return max(0, min(100, score)), details


def score_volatility(df: pd.DataFrame) -> tuple:
    """波动率评分 (0-100, 高波动高分)"""
    latest = df.iloc[-1]
    score = 50
    details = []

    # 布林带宽度
    if 'BOLL_UP' in df.columns and pd.notna(latest.get('BOLL_UP')):
        boll_width = (latest['BOLL_UP'] - latest['BOLL_DOWN']) / latest['BOLL_MID'] * 100
        if boll_width > 8:
            score += 15
            details.append(f"布林带宽{boll_width:.1f}%（高波动） +15")
        elif boll_width > 4:
            score += 5
            details.append(f"布林带宽{boll_width:.1f}%（中等波动） +5")
        else:
            score -= 10
            details.append(f"布林带宽{boll_width:.1f}%（低波动，可能蓄势） -10")

        # 价格在布林带中的位置
        boll_pct = (latest['close'] - latest['BOLL_DOWN']) / (latest['BOLL_UP'] - latest['BOLL_DOWN']) * 100
        if boll_pct > 80:
            details.append(f"价格在布林带上方({boll_pct:.0f}%)，注意回调风险")
        elif boll_pct < 20:
            details.append(f"价格在布林带下方({boll_pct:.0f}%)，注意反弹机会")

    # ATR
    if 'ATR' in df.columns and pd.notna(latest.get('ATR')):
        atr_pct = latest['ATR'] / latest['close'] * 100
        if atr_pct > 3:
            score += 10
            details.append(f"ATR波动率{atr_pct:.2f}%（高） +10")
        elif atr_pct > 1.5:
            score += 5
            details.append(f"ATR波动率{atr_pct:.2f}%（中等） +5")

    # 成交量变化
    if 'volume' in df.columns and len(df) >= 6:
        vol_5 = df['volume'].iloc[-5:].mean()
        vol_20 = df['volume'].iloc[-20:].mean() if len(df) >= 20 else vol_5
        if vol_20 > 0:
            vol_ratio = vol_5 / vol_20
            if vol_ratio > 1.5:
                score += 10
                details.append(f"成交量放大({vol_ratio:.1f}倍) +10")
            elif vol_ratio < 0.5:
                score -= 10
                details.append(f"成交量萎缩({vol_ratio:.1f}倍) -10")

    return max(0, min(100, score)), details


def get_rating(total_score: float) -> str:
    """根据总分给出评级"""
    if total_score >= 75:
        return "强势看多"
    elif total_score >= 60:
        return "偏多"
    elif total_score >= 40:
        return "中性震荡"
    elif total_score >= 25:
        return "偏空"
    else:
        return "强势看空"


def format_analysis(symbol: str, source: str,
                    trend_score: float, trend_details: list,
                    momentum_score: float, momentum_details: list,
                    vol_score: float, vol_details: list,
                    signals: dict, df: pd.DataFrame) -> str:
    """格式化分析报告"""
    latest = df.iloc[-1]
    price_fmt = '.4f' if source == 'forex' else '.2f'

    # 加权总分
    total = trend_score * 0.4 + momentum_score * 0.3 + vol_score * 0.3
    rating = get_rating(total)

    lines = [
        f"# {symbol} 综合分析报告\n",
        f"**分析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**最新价格**: {latest['close']:{price_fmt}}",
        f"**综合评分**: {total:.0f}/100 — **{rating}**\n",
    ]

    # 评分明细
    lines.append("## 评分明细\n")
    lines.append("| 维度 | 权重 | 得分 | 加权 |")
    lines.append("|------|------|------|------|")
    lines.append(f"| 趋势 | 40% | {trend_score:.0f} | {trend_score*0.4:.0f} |")
    lines.append(f"| 动量 | 30% | {momentum_score:.0f} | {momentum_score*0.3:.0f} |")
    lines.append(f"| 波动率 | 30% | {vol_score:.0f} | {vol_score*0.3:.0f} |")
    lines.append(f"| **合计** | **100%** | | **{total:.0f}** |")
    lines.append("")

    # 技术信号
    lines.append("## 技术信号\n")
    lines.append("| 指标 | 信号 |")
    lines.append("|------|------|")
    for name, signal in signals.items():
        lines.append(f"| {name} | {signal} |")
    lines.append("")

    # 趋势分析详情
    lines.append("## 趋势分析详情\n")
    for d in trend_details:
        lines.append(f"- {d}")
    lines.append("")

    # 动量分析详情
    lines.append("## 动量分析详情\n")
    for d in momentum_details:
        lines.append(f"- {d}")
    lines.append("")

    # 波动率分析详情
    lines.append("## 波动率分析详情\n")
    for d in vol_details:
        lines.append(f"- {d}")
    lines.append("")

    # 评分参考
    lines.append("---")
    lines.append("**评分参考**: 75+ 强势看多 / 60-75 偏多 / 40-60 中性震荡 / 25-40 偏空 / <25 强势看空")
    lines.append("\n**免责声明**: 分析结果仅供参考，不构成投资建议。期货交易风险极高，请谨慎操作。")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description='期货综合分析')
    parser.add_argument('symbol', help='品种代码 (AU0, XAU, USDCNY 等)')
    parser.add_argument('--source', choices=['domestic', 'foreign', 'forex', 'auto'],
                        default='auto', help='数据源')
    parser.add_argument('--days', type=int, default=120, help='分析周期天数')
    parser.add_argument('-o', '--output', help='输出文件路径')

    args = parser.parse_args()
    symbol = args.symbol.upper()

    # 获取数据
    df = get_data(symbol, args.source, args.days)
    if df is None or len(df) < 10:
        print(f"获取 {symbol} 数据失败或数据不足")
        sys.exit(1)

    # 计算指标
    df = calc_all_indicators(df)

    # 三维评分
    trend_score, trend_details = score_trend(df)
    momentum_score, momentum_details = score_momentum(df)
    vol_score, vol_details = score_volatility(df)

    # 技术信号
    signals = analyze_signals(df)

    # 确定 source
    effective_source = args.source
    if effective_source == 'auto':
        from get_forex import FOREX_SYMBOLS
        effective_source = 'forex' if symbol in FOREX_SYMBOLS else 'domestic'

    # 输出
    output = format_analysis(symbol, effective_source,
                             trend_score, trend_details,
                             momentum_score, momentum_details,
                             vol_score, vol_details,
                             signals, df)
    print(output)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"\n已保存至: {args.output}")


if __name__ == '__main__':
    main()
