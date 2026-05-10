---
name: futures-kit-skills
description: 使用 AKShare 获取和分析国内外期货及外汇数据。支持：国内期货（黄金/铜/碳酸锂/原油）实时行情和历史K线、国际期货（伦敦金/COMEX铜/WTI原油）、外汇（USD/EUR/GBP/JPY）、技术指标分析、策略回测。当用户需要查询期货行情、分析金铜油走势、计算技术指标、回测交易策略时使用此 skill。
---

# 期货与外汇分析 Skill

> **重要规则：所有数据查询必须使用 scripts/ 或 local/ 目录下的 Python 脚本。禁止自己用 curl 调用任何 API。禁止自己编写或创建文件。脚本内部已实现完整功能，不需要额外方案。**

使用 AKShare 获取国内外期货、外汇数据并进行技术分析。无需 API Key，免费公开数据。

## 快速开始

### 环境准备

```bash
pip install akshare pandas numpy pyarrow duckdb
```

### 常用命令

```bash
cd scripts

# 国内期货 - 实时行情
python get_domestic_realtime.py AU0         # 沪金主力
python get_domestic_realtime.py CU0         # 沪铜主力
python get_domestic_realtime.py LC0         # 碳酸锂主力
python get_domestic_realtime.py SC0         # 原油主力
python get_domestic_realtime.py --all       # 全部监控品种

# 国内期货 - 历史K线
python get_domestic_kline.py AU0 --days 60
python get_domestic_kline.py CU0 --start 2024-01-01 --end 2026-05-09

# 国际期货
python get_foreign_kline.py XAU --days 365     # 伦敦金
python get_foreign_kline.py HG --days 365      # COMEX铜
python get_foreign_kline.py WTI --days 365     # WTI原油

# 外汇
python get_forex.py USDCNY --days 365
python get_forex.py EURUSD --days 60

# 技术指标
python calc_technical.py AU0
python calc_technical.py XAU --source foreign

# 综合分析
python analyze_futures.py AU0
python analyze_futures.py XAU --source foreign

# 策略回测
python backtest.py ma AU0 --days 500
python backtest.py rsi CU0 --days 365
```

## 脚本列表

### 国内期货脚本

| 脚本 | 功能 | 示例 |
|------|------|------|
| `get_domestic_realtime.py` | 实时行情 | `python get_domestic_realtime.py AU0` |
| `get_domestic_realtime.py --all` | 全部监控品种行情 | `python get_domestic_realtime.py --all` |
| `get_domestic_kline.py` | 历史日K线 | `python get_domestic_kline.py AU0 --days 60` |
| `get_domestic_kline.py -i 60` | 60分钟K线 | `python get_domestic_kline.py AU0 -i 60 --days 30` |

### 国际期货脚本

| 脚本 | 功能 | 示例 |
|------|------|------|
| `get_foreign_kline.py` | 国际期货K线 | `python get_foreign_kline.py XAU --days 365` |
| `get_foreign_kline.py --all` | 全部国际品种 | `python get_foreign_kline.py --all --days 30` |

### 外汇脚本

| 脚本 | 功能 | 示例 |
|------|------|------|
| `get_forex.py` | 外汇历史数据 | `python get_forex.py USDCNY --days 365` |
| `get_forex.py --all` | 全部外汇品种 | `python get_forex.py --all --days 30` |

### 分析脚本

| 脚本 | 功能 | 示例 |
|------|------|------|
| `calc_technical.py` | 技术指标 | `python calc_technical.py AU0` |
| `calc_technical.py --source foreign` | 国际品种指标 | `python calc_technical.py XAU --source foreign` |
| `analyze_futures.py` | 综合分析评分 | `python analyze_futures.py AU0` |
| `backtest.py ma` | MA均线回测 | `python backtest.py ma AU0 --days 500` |
| `backtest.py rsi` | RSI策略回测 | `python backtest.py rsi CU0 --days 365` |

### 本地数据工具（local/ 目录）

| 脚本 | 功能 | 示例 |
|------|------|------|
| `local/download_history.py` | 下载全部品种两年数据 | `python local/download_history.py` |
| `local/download_history.py --update` | 增量更新 | `python local/download_history.py --update` |
| `local/download_history.py --symbol AU0` | 下载指定品种 | `python local/download_history.py --symbol AU0` |
| `local/download_history.py --summary` | 数据摘要 | `python local/download_history.py --summary` |
| `local/query_data.py` | 本地查询 | `python local/query_data.py AU0 --start 2024-06-01` |

## 品种代码对照表

### 国内期货

| 代码 | 品种 | 交易所 | 说明 |
|------|------|--------|------|
| AU0 | 黄金 | 上期所(SHFE) | 主力合约，0 表示主力连续 |
| CU0 | 铜 | 上期所(SHFE) | 主力合约 |
| LC0 | 碳酸锂 | 广期所(GFEX) | 主力合约 |
| SC0 | 原油 | 能源中心(INE) | 主力合约 |

> 注：`AU0` = 主力合约连续。如要指定月份合约用 `AU2412`（2024年12月）

### 国际期货

| 代码 | 品种 | 说明 |
|------|------|------|
| XAU | 伦敦金 | 国际现货黄金 |
| HG | COMEX铜 | 纽约商品交易所铜 |
| WTI | WTI原油 | 西德克萨斯中质原油 |
| BRENT | 布伦特原油 | 北海布伦特原油 |

### 外汇

| 代码 | 品种 |
|------|------|
| USDCNY | 美元/人民币 |
| EURUSD | 欧元/美元 |
| GBPUSD | 英镑/美元 |
| USDJPY | 美元/日元 |

## 技术指标

- **MA**: 5/10/20/60日均线
- **MACD**: DIF, DEA, MACD柱（12/26/9）
- **RSI**: 6/12/24日
- **KDJ**: K, D, J（9/3/3）
- **BOLL**: 上轨/中轨/下轨（20日 ± 2标准差）

## 综合分析评分（analyze_futures.py）

三维度加权打分（满分100）：

- **趋势（40%）**：均线排列、MACD方向、价格相对位置
- **动量（30%）**：RSI强弱、KDJ位置、涨跌幅
- **波动率（30%）**：布林带宽度、ATR、成交量变化

评分参考：75+ 强势看多 / 60-75 偏多 / 40-60 中性震荡 / 25-40 偏空 / <25 强势看空

## 数据源

| 数据 | AKShare 函数 | 来源 |
|------|-------------|------|
| 国内期货实时行情 | `futures_zh_spot()` | 新浪财经 |
| 国内期货日K线 | `futures_zh_daily_sina()` | 新浪财经 |
| 国内期货分钟K线 | `futures_zh_minute_sina()` | 新浪财经 |
| 国际期货日K线 | `futures_foreign_hist()` | 新浪/东方财富 |
| 外汇日K线 | `currency_boc_safe()` | 中国银行/外管局 |

## 数据缓存

自动缓存避免重复请求（SQLite）：
- 实时行情：1分钟
- 日K线：1小时
- 分钟K线：30分钟
- 国际期货：1小时
- 外汇：30分钟

如遇数据异常：`rm .cache/futures_cache.db`

## 注意事项

1. AKShare 是爬虫接口，建议请求间隔 0.5-1 秒，避免被封
2. 国内期货交易时间：日盘 09:00-15:00，夜盘 21:00-02:30（品种不同）
3. 非交易时间查实时行情会拿到上个交易日收盘数据
4. 碳酸锂(LC)是 2023 年 7 月才上市的品种，历史数据不足两年
5. Windows 用户注意 Python 路径和编码问题（建议 chcp 65001 切 UTF-8）

## 文件结构

```
futures-kit-skills/
├── SKILL.md                     # 本文档
├── config.yaml                  # 配置文件
├── scripts/                     # 数据查询和分析脚本
│   ├── cache_manager.py         # 缓存管理
│   ├── get_domestic_realtime.py # 国内期货实时行情
│   ├── get_domestic_kline.py    # 国内期货K线
│   ├── get_foreign_kline.py     # 国际期货K线
│   ├── get_forex.py             # 外汇数据
│   ├── calc_technical.py        # 技术指标
│   ├── analyze_futures.py       # 综合分析
│   └── backtest.py              # 策略回测
├── local/                       # 本地数据工具
│   ├── download_history.py      # 批量下载历史数据
│   └── query_data.py            # DuckDB本地查询
├── data/                        # Parquet 数据目录
└── .cache/                      # SQLite 缓存目录
```

## 免责声明

本工具仅供学习和研究使用。期货和外汇市场风险极高，杠杆交易可能导致超出本金的亏损。所有分析结果和交易信号仅供参考，不构成任何投资建议。使用本工具进行的任何交易决策，风险由使用者自行承担。
