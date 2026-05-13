# futures-kit

期货与外汇分析工具包，基于 AKShare 免费数据接口，为 Hermes Agent 提供国内外期货和外汇的行情查询、技术分析、策略回测能力。

**GitHub**: [new0hand/futures-kit](https://github.com/new0hand/futures-kit)

## 支持品种

### 国内期货（中信期货对标品种）

| 代码 | 品种 | 交易所 | 单位 |
|------|------|--------|------|
| AU0 | 黄金 | 上期所(SHFE) | 元/克 |
| CU0 | 铜 | 上期所(SHFE) | 元/吨 |
| LC0 | 碳酸锂 | 广期所(GFEX) | 元/吨 |
| SC0 | 原油 | 能源中心(INE) | 元/桶 |

### 国际期货（DecodeFX 对标品种）

| 代码 | 品种 | 单位 |
|------|------|------|
| XAU | 伦敦金 | 美元/盎司 |
| HG | COMEX铜 | 美分/磅 |
| WTI | WTI原油 | 美元/桶 |
| BRENT | 布伦特原油 | 美元/桶 |

### 外汇

| 代码 | 品种 |
|------|------|
| USDCNY | 美元/人民币 |
| EURUSD | 欧元/美元 |
| GBPUSD | 英镑/美元 |
| USDJPY | 美元/日元 |

## Hermes 部署

### 安装 Skill

```bash
# 安装 Python 依赖
pip3 install akshare pandas numpy pyarrow duckdb

# 从 GitHub 安装 Skill 到 Hermes
hermes skills install new0hand/futures-kit/futures-kit-skills --force
```

### 下载历史数据（可选）

```bash
# 克隆仓库
git clone https://github.com/new0hand/futures-kit.git
cd futures-kit/futures-kit-skills/local

# 下载全部品种两年数据
python3 download_history.py

# 验证
cd ../..
bash test_all.sh
```

### 更新 Skill

```bash
hermes skills install new0hand/futures-kit/futures-kit-skills --force
```

### 微信网关

```bash
hermes gateway setup
hermes pairing approve weixin XXXX
```

## 快速使用

```bash
cd futures-kit-skills/scripts

# 国内期货
python3 get_domestic_realtime.py AU0         # 实时行情
python3 get_domestic_kline.py AU0 --days 60  # 日K线

# 国际期货
python3 get_foreign_kline.py XAU --days 365  # 伦敦金K线

# 外汇
python3 get_forex.py USDCNY --days 365       # 美元人民币

# 技术分析
python3 calc_technical.py AU0                # 技术指标
python3 analyze_futures.py AU0               # 综合分析

# 策略回测
python3 backtest.py ma AU0 --days 500        # MA均线回测
python3 backtest.py rsi CU0 --days 365       # RSI回测
```

### 本地数据

```bash
# 下载全部品种两年数据
python3 local/download_history.py

# 增量更新
python3 local/download_history.py --update

# 查询本地数据
python3 local/query_data.py AU0 --max        # 查历史最高价
```

## 数据源

所有数据通过 AKShare 获取，底层来源：

| 数据 | 来源 | 说明 |
|------|------|------|
| 国内期货行情 | 新浪财经 | 免费公开，爬虫接口 |
| 国内期货K线 | 新浪财经 | 日K/分钟K均支持 |
| 国际期货K线 | 新浪/东方财富 | 主要外盘品种 |
| 外汇数据 | 东方财富/中国银行 | 双源自动回退 |

**注意**：
- AKShare 是爬虫接口，建议请求间隔 0.5-1 秒
- 非交易时间查实时行情会提示数据不可用，日K线和回测不受影响
- 碳酸锂(LC)于 2023 年 7 月上市，历史数据不足两年

## 测试

```bash
bash test_all.sh
```

测试项包括：环境检查(4项)、缓存管理(1项)、国内实时行情(3项)、国内K线(4项)、国际K线(4项)、外汇(4项)、技术指标(2项)、综合分析(2项)、回测(3项)、本地数据(1项)，共 28 项。

## Hermes 对话测试

安装完成后，在 Hermes 对话中（微信或终端）发送以下提示词验证功能：

### 国内期货行情

| 提示词 | 对应功能 | 耗时 |
|--------|---------|------|
| 查一下黄金期货现在多少钱 | 实时行情 `get_domestic_realtime.py AU0` | 1-2秒 |
| 看看国内期货行情 | 全部监控品种 `get_domestic_realtime.py --all` | 2-3秒 |
| 沪铜最近60天的K线 | 日K线 `get_domestic_kline.py CU0 --days 60` | 1-2秒 |
| 原油5分钟K线 | 分钟K线 `get_domestic_kline.py SC0 -i 5` | 1-2秒 |

### 国际期货

| 提示词 | 对应功能 | 耗时 |
|--------|---------|------|
| 伦敦金最近一年的走势 | 国际金 `get_foreign_kline.py XAU --days 365` | 1-2秒 |
| COMEX铜最近半年K线 | 国际铜 `get_foreign_kline.py HG --days 180` | 1-2秒 |
| WTI原油最近一年走势 | 原油 `get_foreign_kline.py WTI --days 365` | 1-2秒 |

### 外汇

| 提示词 | 对应功能 | 耗时 |
|--------|---------|------|
| 美元兑人民币最近一年走势 | 外汇 `get_forex.py USDCNY --days 365` | 1-2秒 |
| 欧元兑美元最近半年 | 外汇 `get_forex.py EURUSD --days 180` | 1-2秒 |

### 技术分析

| 提示词 | 对应功能 | 耗时 |
|--------|---------|------|
| 分析一下黄金期货的技术指标 | 技术指标 `calc_technical.py AU0` | 1-2秒 |
| 帮我综合分析一下沪铜 | 综合评分 `analyze_futures.py CU0` | 2-3秒 |
| 伦敦金技术面怎么样 | 国际期货指标 `calc_technical.py XAU` | 1-2秒 |

### 策略回测

| 提示词 | 对应功能 | 耗时 |
|--------|---------|------|
| 帮我回测黄金的均线策略，最近两年 | MA回测 `backtest.py ma AU0 --days 730` | 1-2秒 |
| 用RSI策略回测一下沪铜 | RSI回测 `backtest.py rsi CU0 --days 365` | 1-2秒 |
| 回测伦敦金的MA策略 | 国际期货回测 `backtest.py ma XAU --days 365` | 1-2秒 |

### 本地数据

| 提示词 | 对应功能 | 耗时 |
|--------|---------|------|
| 黄金期货历史最高价是哪天 | 本地查询 `local/query_data.py AU0 --max` | 秒级 |
| 下载全部品种两年数据 | 批量下载 `local/download_history.py` | 30-60秒 |

> **注意**：实时行情仅在交易时间可用（国内期货周一到周五 9:00-15:00，夜盘 21:00-次日2:30）。非交易时间查询会提示数据不可用，日K线和回测不受影响。

## 定时更新（可选）

如需每天自动增量更新本地数据，配置 crontab：

```bash
crontab -e
```

添加以下内容（北京时间 18:00，根据你的时区换算）：

```bash
# 北京时间（UTC+8）：
0 18 * * 1-5 cd ~/.hermes/skills/futures-kit-skills/local && python3 download_history.py --update >> /tmp/futures_update.log 2>&1

# 夏威夷时间（UTC-10，北京18:00 = 夏威夷00:00）：
0 0 * * 1-5 cd ~/.hermes/skills/futures-kit-skills/local && python3 download_history.py --update >> /tmp/futures_update.log 2>&1
```

**说明**：
- 国内期货 15:00 收盘（夜盘归入下一交易日），国际期货/外汇日 K 按前一日结算，18:00 数据源均已更新
- macOS 需给 cron 授予"完全磁盘访问权限"（系统设置 → 隐私与安全性 → 完全磁盘访问权限 → 添加 `/usr/sbin/cron`）
- Linux 服务器无需额外权限，直接生效

## 目录结构

```
futures-kit/
├── README.md                        # 本文件
├── test_all.sh                      # 全量测试（28项）
├── .gitignore
└── futures-kit-skills/              # Hermes Skill 目录
    ├── SKILL.md                     # Skill 定义
    ├── config.yaml                  # 配置
    ├── scripts/                     # 数据查询和分析脚本
    │   ├── cache_manager.py         # 缓存管理
    │   ├── get_domestic_realtime.py # 国内期货实时行情
    │   ├── get_domestic_kline.py    # 国内期货K线
    │   ├── get_foreign_kline.py     # 国际期货K线
    │   ├── get_forex.py             # 外汇数据
    │   ├── calc_technical.py        # 技术指标
    │   ├── analyze_futures.py       # 综合分析评分
    │   └── backtest.py              # 策略回测
    ├── local/                       # 本地数据工具
    │   ├── download_history.py      # 批量下载历史数据
    │   └── query_data.py            # DuckDB本地查询
    ├── data/                        # Parquet 数据
    └── .cache/                      # SQLite 缓存
```

## 免责声明

本工具仅供学习和研究使用。期货和外汇市场风险极高，杠杆交易可能导致超出本金的亏损。所有分析结果和交易信号仅供参考，不构成任何投资建议。使用本工具进行的任何交易决策，风险由使用者自行承担。
