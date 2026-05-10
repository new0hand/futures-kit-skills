#!/bin/bash
# futures-kit 全量测试脚本
# 用法: bash test_all.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$SCRIPT_DIR/futures-kit-skills"
SCRIPTS_DIR="$SKILL_DIR/scripts"
LOCAL_DIR="$SKILL_DIR/local"
CACHE_DB="$SKILL_DIR/.cache/futures_cache.db"

# 颜色
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASS=0
FAIL=0
SKIP=0
TOTAL=0

run_test() {
    local name="$1"
    local cmd="$2"
    local check_str="${3:-}"  # 可选：输出中应包含的字符串
    TOTAL=$((TOTAL + 1))

    echo -n "[$TOTAL] $name ... "

    # 清缓存
    [ -f "$CACHE_DB" ] && rm -f "$CACHE_DB"

    # 运行命令，捕获输出
    output=$(cd "$SCRIPTS_DIR" && eval "$cmd" 2>&1) || true
    exit_code=$?

    # 检查失败关键词
    if echo "$output" | grep -qi "获取.*失败\|Traceback\|Error\|ImportError\|ModuleNotFoundError"; then
        # 看是否是可接受的失败（如非交易时间）
        if echo "$output" | grep -qi "非交易时间\|市场休市"; then
            echo -e "${YELLOW}SKIP${NC} (非交易时间)"
            SKIP=$((SKIP + 1))
            return
        fi
        echo -e "${RED}FAIL${NC}"
        echo "  输出: $(echo "$output" | head -5)"
        FAIL=$((FAIL + 1))
        return
    fi

    # 检查特定字符串
    if [ -n "$check_str" ]; then
        if ! echo "$output" | grep -q "$check_str"; then
            echo -e "${RED}FAIL${NC} (未包含: $check_str)"
            echo "  输出: $(echo "$output" | head -5)"
            FAIL=$((FAIL + 1))
            return
        fi
    fi

    # 检查是否有有效输出
    if [ -z "$output" ]; then
        echo -e "${RED}FAIL${NC} (无输出)"
        FAIL=$((FAIL + 1))
        return
    fi

    echo -e "${GREEN}PASS${NC}"
    PASS=$((PASS + 1))
}

echo "========================================"
echo "  futures-kit 全量测试"
echo "  $(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================"
echo ""

# 检查依赖
echo "== 环境检查 =="
run_test "Python 可用" "python3 --version"
run_test "AKShare 已安装" "python3 -c 'import akshare; print(f\"AKShare {akshare.__version__}\")'"
run_test "pandas 已安装" "python3 -c 'import pandas; print(f\"pandas {pandas.__version__}\")'"
run_test "numpy 已安装" "python3 -c 'import numpy; print(f\"numpy {numpy.__version__}\")'"
echo ""

# 缓存管理器
echo "== 缓存管理器 =="
run_test "缓存管理器" "python3 cache_manager.py" "缓存统计"
echo ""

# 国内期货 - 实时行情
echo "== 国内期货实时行情 =="
run_test "沪金实时(AU0)" "python3 get_domestic_realtime.py AU0" "黄金"
sleep 1
run_test "沪铜实时(CU0)" "python3 get_domestic_realtime.py CU0" "铜"
sleep 1
run_test "全部监控品种" "python3 get_domestic_realtime.py --all" "概览"
echo ""

# 国内期货 - K线
echo "== 国内期货K线 =="
run_test "沪金日K(AU0)" "python3 get_domestic_kline.py AU0 --days 30" "日K线"
sleep 1
run_test "沪铜日K(CU0)" "python3 get_domestic_kline.py CU0 --days 30" "日K线"
sleep 1
run_test "碳酸锂日K(LC0)" "python3 get_domestic_kline.py LC0 --days 30" "日K线"
sleep 1
run_test "原油日K(SC0)" "python3 get_domestic_kline.py SC0 --days 30" "日K线"
echo ""

# 国际期货 - K线
echo "== 国际期货K线 =="
run_test "伦敦金(XAU)" "python3 get_foreign_kline.py XAU --days 60" "伦敦金"
sleep 1
run_test "COMEX铜(HG)" "python3 get_foreign_kline.py HG --days 60" "COMEX铜"
sleep 1
run_test "WTI原油" "python3 get_foreign_kline.py WTI --days 60" "WTI"
sleep 1
run_test "布伦特原油" "python3 get_foreign_kline.py BRENT --days 60" "布伦特"
echo ""

# 外汇
echo "== 外汇数据 =="
run_test "美元/人民币(USDCNY)" "python3 get_forex.py USDCNY --days 30" "美元"
sleep 1
run_test "欧元/美元(EURUSD)" "python3 get_forex.py EURUSD --days 30" "欧元"
sleep 1
run_test "英镑/美元(GBPUSD)" "python3 get_forex.py GBPUSD --days 30" "英镑"
sleep 1
run_test "美元/日元(USDJPY)" "python3 get_forex.py USDJPY --days 30" "日元"
echo ""

# 技术指标
echo "== 技术指标 =="
run_test "沪金技术指标" "python3 calc_technical.py AU0 --days 60" "技术分析"
sleep 1
run_test "伦敦金技术指标" "python3 calc_technical.py XAU --source foreign --days 60" "技术分析"
echo ""

# 综合分析
echo "== 综合分析 =="
run_test "沪金综合分析" "python3 analyze_futures.py AU0 --days 60" "综合分析"
sleep 1
run_test "伦敦金综合分析" "python3 analyze_futures.py XAU --source foreign --days 60" "综合分析"
echo ""

# 回测
echo "== 策略回测 =="
run_test "沪金MA回测" "python3 backtest.py ma AU0 --days 200" "回测报告"
sleep 1
run_test "沪铜RSI回测" "python3 backtest.py rsi CU0 --days 200" "回测报告"
sleep 1
run_test "伦敦金MA回测" "python3 backtest.py ma XAU --source foreign --days 200" "回测报告"
echo ""

# 本地数据工具
echo "== 本地数据工具 =="
run_test "数据摘要(可能为空)" "cd $SCRIPTS_DIR && python3 $LOCAL_DIR/download_history.py --summary" "本地数据"
echo ""

# 总结
echo "========================================"
echo "  测试结果"
echo "========================================"
echo -e "  通过: ${GREEN}${PASS}${NC}"
echo -e "  失败: ${RED}${FAIL}${NC}"
echo -e "  跳过: ${YELLOW}${SKIP}${NC}"
echo -e "  总计: ${TOTAL}"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}全部测试通过！${NC}"
    exit 0
else
    echo -e "${RED}有 ${FAIL} 项测试失败${NC}"
    exit 1
fi
