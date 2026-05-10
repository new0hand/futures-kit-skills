# futures-kit-skills

期货与外汇分析工具包，基于 AKShare 免费数据接口，为 Hermes Agent 提供国内外期货和外汇的行情查询、技术分析、策略回测能力。

**GitHub**: [new0hand/futures-kit-skills](https://github.com/new0hand/futures-kit-skills)

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

## 安装

### 依赖

```bash
pip install akshare pandas numpy pyarrow duckdb
```

### Hermes Skill 安装

```bash
hermes skills install ./futures-kit-skills
```

## 快速使用

```bash
cd futures-kit-skills/scripts

# 国内期货
python get_domestic_realtime.py AU0         # 实时行情
python get_domestic_kline.py AU0 --days 60  # 日K线

# 国际期货
python get_foreign_kline.py XAU --days 365  # 伦敦金K线

# 外汇
python get_forex.py USDCNY --days 365       # 美元人民币

# 技术分析
python calc_technical.py AU0                # 技术指标
python analyze_futures.py AU0               # 综合分析

# 策略回测
python backtest.py ma AU0 --days 500        # MA均线回测
python backtest.py rsi CU0 --days 365       # RSI回测
```

### 本地数据

```bash
# 下载全部品种两年数据
python local/download_history.py

# 增量更新
python local/download_history.py --update

# 查询本地数据
python local/query_data.py AU0 --max        # 查历史最高价
```

## 数据源

所有数据通过 AKShare 获取，底层来源：

| 数据 | 来源 | 说明 |
|------|------|------|
| 国内期货行情 | 新浪财经 | 免费公开，爬虫接口 |
| 国内期货K线 | 新浪财经 | 日K/分钟K均支持 |
| 国际期货K线 | 新浪/东方财富 | 主要外盘品种 |
| 外汇数据 | 中国银行/外管局 | 中间价 |

**注意**：
- AKShare 是爬虫接口，建议请求间隔 0.5-1 秒
- 非交易时间查实时行情会拿到上个交易日收盘数据
- 碳酸锂(LC)于 2023 年 7 月上市，历史数据不足两年

## 测试

```bash
bash test_all.sh
```

测试项包括：环境检查(4项)、缓存管理(1项)、国内实时行情(3项)、国内K线(4项)、国际K线(4项)、外汇(4项)、技术指标(2项)、综合分析(2项)、回测(3项)、本地数据(1项)，共 28 项。

## 与客户需求对应

| 客户需求 | 实现方案 |
|---------|---------|
| 国内期货：金铜碳酸锂原油 | AKShare 国内期货接口，AU0/CU0/LC0/SC0 |
| 国外期货：金铜油 | AKShare 国际期货接口，XAU/HG/WTI |
| 外汇 | AKShare 外汇接口，USDCNY/EURUSD 等 |
| 拉两年数据 | download_history.py --days 730 |
| 技术分析 | calc_technical.py + analyze_futures.py |
| 回测 | backtest.py ma/rsi |

## 定时更新（可选）

如需每天自动增量更新本地数据，配置 crontab：

```bash
crontab -e
```

添加以下内容（周一到周五收盘后 16:00 执行）：

```cron
0 16 * * 1-5 cd ~/futures-kit-skills/futures-kit-skills && python3 local/download_history.py --update >> /tmp/futures_update.log 2>&1
```

**说明**：
- 国内期货 15:00 收盘，16:00 更新确保数据源已同步
- 国际期货和外汇交易时间不同，如需更频繁可改为每小时：`0 * * * 1-5`
- macOS 需给 cron 授予"完全磁盘访问权限"（系统设置 → 隐私与安全性 → 完全磁盘访问权限 → 添加 `/usr/sbin/cron`）
- Linux 服务器无需额外权限，直接生效

## 目录结构

```
futures-kit-skills/
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
