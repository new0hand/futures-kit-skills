# -*- coding: utf-8 -*-
"""
期货策略回测

支持策略:
- ma: 双均线交叉策略（默认 MA5/MA20）
- rsi: RSI 超买超卖策略

用法:
    python backtest.py ma AU0                           # 沪金MA回测
    python backtest.py ma AU0 --days 500                # 近500天
    python backtest.py ma AU0 --fast 5 --slow 20        # 自定义均线
    python backtest.py rsi CU0 --days 365               # 沪铜RSI回测
    python backtest.py ma XAU --source foreign --days 500  # 国际黄金
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
from calc_technical import get_data, calc_ma, calc_rsi


def backtest_ma(df: pd.DataFrame, fast: int = 5, slow: int = 20,
                initial_capital: float = 100000, fee_rate: float = 0.0001) -> dict:
    """双均线交叉回测"""
    df = calc_ma(df, periods=[fast, slow])
    df = df.dropna(subset=[f'MA{fast}', f'MA{slow}']).copy()

    if len(df) < 2:
        return {'error': '数据不足'}

    capital = initial_capital
    position = 0.0
    trades = []
    holding = False

    for i in range(1, len(df)):
        prev = df.iloc[i - 1]
        curr = df.iloc[i]
        price = curr['close']
        dt_val = curr.get('datetime')
        if dt_val and pd.notna(dt_val):
            dt = pd.to_datetime(dt_val).strftime('%Y-%m-%d') if not isinstance(dt_val, str) else str(dt_val)[:10]
        else:
            dt = str(i)

        # 金叉买入
        if prev[f'MA{fast}'] <= prev[f'MA{slow}'] and curr[f'MA{fast}'] > curr[f'MA{slow}'] and not holding:
            fee = capital * fee_rate
            position = (capital - fee) / price
            trades.append({
                'type': 'BUY', 'date': dt, 'price': price,
                'amount': position, 'capital': capital, 'fee': fee
            })
            holding = True

        # 死叉卖出
        elif prev[f'MA{fast}'] >= prev[f'MA{slow}'] and curr[f'MA{fast}'] < curr[f'MA{slow}'] and holding:
            capital = position * price
            fee = capital * fee_rate
            capital -= fee
            trades.append({
                'type': 'SELL', 'date': dt, 'price': price,
                'amount': position, 'capital': capital, 'fee': fee
            })
            position = 0.0
            holding = False

    # 如果最后还持仓，按最后收盘价计算
    final_price = df.iloc[-1]['close']
    if holding:
        capital = position * final_price

    # 统计
    total_return = (capital / initial_capital - 1) * 100
    buy_hold_return = (df.iloc[-1]['close'] / df.iloc[0]['close'] - 1) * 100
    if 'datetime' in df.columns:
        n_days = (pd.to_datetime(df['datetime'].iloc[-1]) - pd.to_datetime(df['datetime'].iloc[0])).days
    else:
        n_days = len(df)

    # 计算最大回撤
    max_drawdown = 0
    peak = initial_capital
    equity_curve = [initial_capital]
    temp_capital = initial_capital
    temp_holding = False
    temp_position = 0.0

    for i in range(1, len(df)):
        prev = df.iloc[i - 1]
        curr = df.iloc[i]
        price = curr['close']

        if prev[f'MA{fast}'] <= prev[f'MA{slow}'] and curr[f'MA{fast}'] > curr[f'MA{slow}'] and not temp_holding:
            temp_position = temp_capital / price
            temp_holding = True
        elif prev[f'MA{fast}'] >= prev[f'MA{slow}'] and curr[f'MA{fast}'] < curr[f'MA{slow}'] and temp_holding:
            temp_capital = temp_position * price
            temp_position = 0.0
            temp_holding = False

        current_value = temp_position * price if temp_holding else temp_capital
        equity_curve.append(current_value)
        if current_value > peak:
            peak = current_value
        dd = (peak - current_value) / peak * 100
        if dd > max_drawdown:
            max_drawdown = dd

    # 胜率
    wins = 0
    for i in range(0, len(trades) - 1, 2):
        if i + 1 < len(trades):
            if trades[i + 1]['capital'] > trades[i]['capital']:
                wins += 1
    total_rounds = len(trades) // 2
    win_rate = (wins / total_rounds * 100) if total_rounds > 0 else 0

    return {
        'strategy': f'MA{fast}/{slow}交叉',
        'initial_capital': initial_capital,
        'final_capital': round(capital, 2),
        'total_return': round(total_return, 2),
        'buy_hold_return': round(buy_hold_return, 2),
        'excess_return': round(total_return - buy_hold_return, 2),
        'max_drawdown': round(max_drawdown, 2),
        'total_trades': len(trades),
        'trade_rounds': total_rounds,
        'win_rate': round(win_rate, 1),
        'n_days': n_days,
        'annualized_return': round(total_return / max(n_days/365, 0.01), 2),
        'trades': trades[-10:],  # 最近10笔交易
    }


def backtest_rsi(df: pd.DataFrame, oversold: int = 30, overbought: int = 70,
                 initial_capital: float = 100000, fee_rate: float = 0.0001) -> dict:
    """RSI 超买超卖回测"""
    df = calc_rsi(df, periods=[6])
    df = df.dropna(subset=['RSI6']).copy()

    if len(df) < 2:
        return {'error': '数据不足'}

    capital = initial_capital
    position = 0.0
    trades = []
    holding = False

    for i in range(1, len(df)):
        curr = df.iloc[i]
        price = curr['close']
        rsi = curr['RSI6']
        dt_val = curr.get('datetime')
        if dt_val and pd.notna(dt_val):
            dt = pd.to_datetime(dt_val).strftime('%Y-%m-%d') if not isinstance(dt_val, str) else str(dt_val)[:10]
        else:
            dt = str(i)

        # RSI 超卖买入
        if rsi < oversold and not holding:
            fee = capital * fee_rate
            position = (capital - fee) / price
            trades.append({
                'type': 'BUY', 'date': dt, 'price': price,
                'rsi': round(rsi, 1), 'capital': capital
            })
            holding = True

        # RSI 超买卖出
        elif rsi > overbought and holding:
            capital = position * price
            fee = capital * fee_rate
            capital -= fee
            trades.append({
                'type': 'SELL', 'date': dt, 'price': price,
                'rsi': round(rsi, 1), 'capital': capital
            })
            position = 0.0
            holding = False

    final_price = df.iloc[-1]['close']
    if holding:
        capital = position * final_price

    total_return = (capital / initial_capital - 1) * 100
    buy_hold_return = (df.iloc[-1]['close'] / df.iloc[0]['close'] - 1) * 100
    if 'datetime' in df.columns:
        n_days = (pd.to_datetime(df['datetime'].iloc[-1]) - pd.to_datetime(df['datetime'].iloc[0])).days
    else:
        n_days = len(df)

    wins = 0
    for i in range(0, len(trades) - 1, 2):
        if i + 1 < len(trades):
            if trades[i + 1]['capital'] > trades[i]['capital']:
                wins += 1
    total_rounds = len(trades) // 2
    win_rate = (wins / total_rounds * 100) if total_rounds > 0 else 0

    return {
        'strategy': f'RSI({oversold}/{overbought})',
        'initial_capital': initial_capital,
        'final_capital': round(capital, 2),
        'total_return': round(total_return, 2),
        'buy_hold_return': round(buy_hold_return, 2),
        'excess_return': round(total_return - buy_hold_return, 2),
        'total_trades': len(trades),
        'trade_rounds': total_rounds,
        'win_rate': round(win_rate, 1),
        'n_days': n_days,
        'annualized_return': round(total_return / max(n_days/365, 0.01), 2),
        'trades': trades[-10:],
    }


def format_result(result: dict, symbol: str) -> str:
    """格式化回测结果"""
    if 'error' in result:
        return f"回测失败: {result['error']}"

    lines = [
        f"# {symbol} 策略回测报告\n",
        f"**策略**: {result['strategy']}",
        f"**回测区间**: {result['n_days']} 个交易日\n",
        "## 回测结果\n",
        "| 项目 | 数值 |",
        "|------|------|",
        f"| 初始资金 | {result['initial_capital']:,.0f} |",
        f"| 最终资金 | {result['final_capital']:,.0f} |",
        f"| 策略收益率 | {result['total_return']:+.2f}% |",
        f"| 买入持有收益率 | {result['buy_hold_return']:+.2f}% |",
        f"| 超额收益 | {result['excess_return']:+.2f}% |",
        f"| 年化收益率 | {result['annualized_return']:+.2f}% |",
    ]

    if 'max_drawdown' in result:
        lines.append(f"| 最大回撤 | {result['max_drawdown']:.2f}% |")

    lines.extend([
        f"| 交易次数 | {result['total_trades']} 次 |",
        f"| 交易轮次 | {result['trade_rounds']} 轮 |",
        f"| 胜率 | {result['win_rate']}% |",
        "",
    ])

    # 最近交易记录
    if result.get('trades'):
        lines.append("## 最近交易记录\n")
        lines.append("| 类型 | 日期 | 价格 | 资金 |")
        lines.append("|------|------|------|------|")
        for t in result['trades']:
            lines.append(
                f"| {t['type']} | {t['date']} | {t['price']:.2f} | {t.get('capital', 0):,.0f} |"
            )
    lines.append("")

    # 评价
    lines.append("## 策略评价\n")
    if result['excess_return'] > 5:
        lines.append("策略显著跑赢买入持有，信号有效。")
    elif result['excess_return'] > 0:
        lines.append("策略小幅跑赢买入持有。")
    elif result['excess_return'] > -5:
        lines.append("策略与买入持有基本持平。")
    else:
        lines.append("策略跑输买入持有，需要优化参数或换策略。")

    lines.append("\n**免责声明**: 历史回测不代表未来表现。期货交易风险极高，请谨慎操作。")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description='期货策略回测')
    subparsers = parser.add_subparsers(dest='strategy', help='回测策略')

    # MA 策略
    ma_parser = subparsers.add_parser('ma', help='均线交叉策略')
    ma_parser.add_argument('symbol', help='品种代码')
    ma_parser.add_argument('--fast', type=int, default=5, help='快线周期 (默认5)')
    ma_parser.add_argument('--slow', type=int, default=20, help='慢线周期 (默认20)')
    ma_parser.add_argument('--days', type=int, default=500, help='回测天数 (默认500)')
    ma_parser.add_argument('--capital', type=float, default=100000, help='初始资金')
    ma_parser.add_argument('--source', default='auto', help='数据源')
    ma_parser.add_argument('-o', '--output', help='输出文件')

    # RSI 策略
    rsi_parser = subparsers.add_parser('rsi', help='RSI策略')
    rsi_parser.add_argument('symbol', help='品种代码')
    rsi_parser.add_argument('--oversold', type=int, default=30, help='超卖线 (默认30)')
    rsi_parser.add_argument('--overbought', type=int, default=70, help='超买线 (默认70)')
    rsi_parser.add_argument('--days', type=int, default=500, help='回测天数')
    rsi_parser.add_argument('--capital', type=float, default=100000, help='初始资金')
    rsi_parser.add_argument('--source', default='auto', help='数据源')
    rsi_parser.add_argument('-o', '--output', help='输出文件')

    args = parser.parse_args()

    if not args.strategy:
        parser.print_help()
        sys.exit(1)

    symbol = args.symbol.upper()

    # 获取数据
    df = get_data(symbol, args.source, args.days)
    if df is None or len(df) < 30:
        print(f"获取 {symbol} 数据失败或数据不足（需要至少30条）")
        sys.exit(1)

    # 运行回测
    if args.strategy == 'ma':
        result = backtest_ma(df, args.fast, args.slow, args.capital)
    elif args.strategy == 'rsi':
        result = backtest_rsi(df, args.oversold, args.overbought, args.capital)
    else:
        print(f"不支持的策略: {args.strategy}")
        sys.exit(1)

    output = format_result(result, symbol)
    print(output)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"\n已保存至: {args.output}")


if __name__ == '__main__':
    main()
