#!/usr/bin/env python3
"""
基金管家 - 自动数据更新脚本
用法: python update_script.py
功能: 通过akshare抓取真实基金数据，更新index.html中的MARKET_DATA
"""

import akshare as ak
import json
import re
from datetime import datetime, timedelta
import time

print(f"=== 基金数据更新开始 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")

# ============ 1. 读取当前HTML ============
with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 提取当前的MARKET_DATA
match = re.search(r'let MARKET_DATA=(\{.*?\});\s*const DATA_VERSION', html, re.DOTALL)
if not match:
    print("错误: 未找到MARKET_DATA")
    exit(1)

try:
    data = json.loads(match.group(1))
    print(f"当前数据更新时间: {data.get('updateTime', 'unknown')}")
except:
    print("错误: 解析MARKET_DATA失败")
    exit(1)

# ============ 2. 定义要抓取的ETF/指数 ============
# 格式: (akshare代码, 数据字段名, 数据类型)
# 数据类型: 'etf' 或 'index'
ETF_MAP = {
    '半导体/芯片':   {'code': '512760', 'type': 'etf'},   # 国泰CES半导体ETF
    '科创50':        {'code': '000688', 'type': 'index'},  # 科创50指数
    '科技/TMT':      {'code': '515000', 'type': 'etf'},   # 科技ETF
    '数字经济':      {'code': '159658', 'type': 'etf'},   # 数字经济ETF
    '人工智能/AI':   {'code': '159819', 'type': 'etf'},   # AI ETF
    '高端制造':      {'code': '161037', 'type': 'etf'},   # 高端制造
    '医药/医疗':     {'code': '512170', 'type': 'etf'},   # 医疗ETF
    '白酒/消费':     {'code': '161725', 'type': 'etf'},   # 白酒(招商中证白酒)
    '宽基指数':      {'code': '510300', 'type': 'etf'},   # 沪深300ETF
    '红利/高股息':   {'code': '515180', 'type': 'etf'},   # 红利ETF
    '军工/国防':     {'code': '512810', 'type': 'etf'},   # 军工ETF
    '传媒/游戏':     {'code': '159869', 'type': 'etf'},   # 游戏ETF
    '金融地产':      {'code': '512200', 'type': 'etf'},   # 房地产ETF
    'QDII/海外':     {'code': '270042', 'type': 'fund'},  # 广发纳指100
    '港股/科技':     {'code': '513130', 'type': 'etf'},   # 恒生科技ETF
    '黄金/商品':     {'code': '518880', 'type': 'etf'},   # 黄金ETF
    '新能源/光伏':   {'code': '515790', 'type': 'etf'},   # 光伏ETF
    '债券/固收':     {'code': '511010', 'type': 'etf'},   # 国债ETF
}

def get_date_str(days_ago=0):
    """获取N天前的日期字符串"""
    d = datetime.now() - timedelta(days=days_ago)
    return d.strftime('%Y%m%d')

def safe_float(val):
    """安全转换浮点数"""
    try:
        return float(val)
    except:
        return 0.0

def calc_change_pct(df, days):
    """计算N天涨跌幅百分比"""
    if df is None or len(df) < 2:
        return 0.0
    try:
        if days >= len(df):
            latest = safe_float(df.iloc[-1]['close'])
            earliest = safe_float(df.iloc[0]['close'])
        else:
            latest = safe_float(df.iloc[-1]['close'])
            earliest = safe_float(df.iloc[-(days+1)]['close'])
        if earliest == 0:
            return 0.0
        return round((latest - earliest) / earliest * 100, 2)
    except Exception as e:
        print(f"  计算涨跌幅失败: {e}")
        return 0.0

def get_fund_nav_change(fund_code, days):
    """获取基金N天涨跌幅"""
    try:
        df = ak.fund_open_fund_info_em(symbol=fund_code, indicator="单位净值走势")
        if df is None or len(df) < 2:
            return 0.0
        df = df.tail(days+1)
        latest = safe_float(df.iloc[-1]['单位净值'])
        earliest = safe_float(df.iloc[0]['单位净值'])
        if earliest == 0:
            return 0.0
        return round((latest - earliest) / earliest * 100, 2)
    except Exception as e:
        print(f"  基金数据获取失败: {e}")
        return 0.0

# ============ 3. 抓取数据 ============
print("\n--- 开始抓取各行业数据 ---")
end_date = get_date_str(0)
start_date_1y = get_date_str(365)
start_date_6m = get_date_str(180)
start_date_3m = get_date_str(90)
start_date_1m = get_date_str(35)
start_date_1w = get_date_str(10)

changes = {}  # 存储各方向的涨跌幅

for direction, info in ETF_MAP.items():
    code = info['code']
    dtype = info['type']
    
    try:
        time.sleep(0.3)  # 避免请求过快
        
        if dtype == 'etf':
            df = ak.fund_etf_hist_em(symbol=code, period="daily",
                                      start_date=start_date_1y, end_date=end_date,
                                      adjust="qfq")
        elif dtype == 'index':
            df = ak.index_zh_a_hist(symbol=code, period="daily",
                                     start_date=start_date_1y, end_date=end_date)
        elif dtype == 'fund':
            # QDII基金用基金净值接口
            w1 = get_fund_nav_change(code, 7)
            m1 = get_fund_nav_change(code, 30)
            m3 = get_fund_nav_change(code, 90)
            m6 = get_fund_nav_change(code, 180)
            y1 = get_fund_nav_change(code, 365)
            changes[direction] = {'week1': w1, 'month1': m1, 'month3': m3, 
                                   'month6': m6, 'year1': y1}
            print(f"  {direction}: 近1月{m1:+.1f}% 近6月{m6:+.1f}% 近1年{y1:+.1f}%")
            continue
        
        if df is None or len(df) < 5:
            print(f"  {direction}: 数据不足，跳过")
            changes[direction] = {'week1': 0, 'month1': 0, 'month3': 0, 'month6': 0, 'year1': 0}
            continue
        
        w1 = calc_change_pct(df, 5)
        m1 = calc_change_pct(df, 22)
        m3 = calc_change_pct(df, 66)
        m6 = calc_change_pct(df, 120)
        y1 = calc_change_pct(df, len(df)-1)
        
        changes[direction] = {'week1': w1, 'month1': m1, 'month3': m3, 
                               'month6': m6, 'year1': y1}
        print(f"  {direction}: 近1月{m1:+.1f}% 近6月{m6:+.1f}% 近1年{y1:+.1f}%")
        
    except Exception as e:
        print(f"  {direction}: 获取失败 - {e}")
        changes[direction] = {'week1': 0, 'month1': 0, 'month3': 0, 'month6': 0, 'year1': 0}

print(f"\n成功获取 {len(changes)} 个方向的数据")

# ============ 4. 计算评分 ============
def calc_score(chg):
    """基于多周期涨跌幅计算综合评分 (0-100)"""
    m1 = chg.get('month1', 0)
    m3 = chg.get('month3', 0)
    m6 = chg.get('month6', 0)
    y1 = chg.get('year1', 0)
    
    # 加权: 短期40% + 中期25% + 季度15% + 长期20%
    raw = m1 * 0.40 + m3 * 0.25 + m6 * 0.15 + y1 * 0.20
    
    # 映射到0-100
    score = 50 + raw * 2
    score = max(0, min(100, round(score)))
    return score

def get_outlook(score):
    if score >= 80: return '强烈看好'
    elif score >= 65: return '看好'
    elif score >= 50: return '中性'
    elif score >= 35: return '谨慎'
    else: return '回避'

def gen_reasons(chg):
    """生成推荐理由"""
    reasons = []
    m1 = chg.get('month1', 0)
    m6 = chg.get('month6', 0)
    
    if m1 >= 10:
        reasons.append(f"近1月暴涨{m1:+.1f}%，短期momentum极强")
    elif m1 >= 3:
        reasons.append(f"近1月上涨{m1:+.1f}%，趋势向好")
    elif m1 >= 0:
        reasons.append(f"近1月微涨{m1:+.1f}%，企稳")
    elif m1 >= -5:
        reasons.append(f"近1月{m1:+.1f}%，短期调整")
    else:
        reasons.append(f"近1月{m1:+.1f}%，短期走弱")
    
    if m6 >= 15:
        reasons.append(f"近6月{m6:+.1f}%，中期极强")
    elif m6 >= 5:
        reasons.append(f"近6月{m6:+.1f}%，中期正收益")
    elif m6 >= -5:
        reasons.append(f"近6月{m6:+.1f}%，中期震荡")
    else:
        reasons.append(f"近6月{m6:+.1f}%，中期弱势")
    
    return reasons

# ============ 5. 更新predictions ============
print("\n--- 更新方向预测 ---")

# 基金数量统计（从行业数据中估算）
FUND_COUNTS = {
    '半导体/芯片': 142, '科创50': 16, '科技/TMT': 342, '数字经济': 172,
    '人工智能/AI': 176, '高端制造': 216, '医药/医疗': 428, '白酒/消费': 256,
    '宽基指数': 512, '红利/高股息': 186, '军工/国防': 98, '传媒/游戏': 64,
    '金融地产': 312, 'QDII/海外': 156, '港股/科技': 128, '黄金/商品': 72,
    '新能源/光伏': 198, '债券/固收': 896,
}

new_predictions = []
for p in data['predictions']:
    direction = p['direction']
    if direction in changes:
        chg = changes[direction]
        p['week1'] = chg['week1']
        p['month1'] = chg['month1']
        p['month3'] = chg['month3']
        p['month6'] = chg['month6']
        p['year1'] = chg['year1']
        p['score'] = calc_score(chg)
        p['outlook'] = get_outlook(p['score'])
        p['reasons'] = gen_reasons(chg)
        new_predictions.append(p)
        print(f"  {direction}: 评分{p['score']} - {p['outlook']}")

# 按评分排序
new_predictions.sort(key=lambda x: x['score'], reverse=True)
data['predictions'] = new_predictions

# ============ 6. 更新recommendations ============
print("\n--- 更新推荐基金 ---")

# 为推荐基金获取最新净值和涨跌幅
rec_funds = [
    {'name': '嘉实上证科创板芯片ETF发起联接C', 'code': '017470', 'direction': '半导体/芯片'},
    {'name': '易方达上证科创50联接C', 'code': '011609', 'direction': '科创50'},
    {'name': '诺安研究优选混合C', 'code': '014497', 'direction': '电子'},
    {'name': '国寿安保策略精选混合C', 'code': '022124', 'direction': '科技'},
    {'name': '广发远见智选混合C', 'code': '016874', 'direction': '科技'},
    {'name': '华泰柏瑞恒生科技ETF联接(QDII)C', 'code': '015311', 'direction': '科技/TMT'},
    {'name': '中航机遇领航混合发起C', 'code': '018957', 'direction': '科技/通讯设备'},
    {'name': '东方人工智能主题混合C', 'code': '017811', 'direction': '人工智能/AI'},
]

new_recs = []
for rf in rec_funds:
    direction = rf['direction']
    chg = changes.get(direction, {})
    
    # 尝试获取最新净值
    try:
        nav_df = ak.fund_open_fund_info_em(symbol=rf['code'], indicator="单位净值走势")
        latest_nav = safe_float(nav_df.iloc[-1]['单位净值']) if nav_df is not None and len(nav_df) > 0 else 1.0
    except:
        latest_nav = 1.0
    
    new_recs.append({
        'name': rf['name'],
        'code': rf['code'],
        'direction': rf['direction'],
        'month1': round(chg.get('month1', 0), 1),
        'month6': round(chg.get('month6', 0), 1),
        'year1': round(chg.get('year1', 0), 1),
        'nav': round(latest_nav, 3),
        'reasons': gen_reasons(chg)[0]  # 取第一条理由
    })
    print(f"  {rf['name']}: 近1月{chg.get('month1', 0):+.1f}%")

data['recommendations'] = new_recs

# ============ 7. 更新催化剂（自动清理过期事件） ============
print("\n--- 更新催化剂日历 ---")
today = datetime.now()

# 保留未来事件
catalysts = [c for c in data.get('catalysts', []) 
             if datetime.strptime(c['date'], '%Y-%m-%d') >= today - timedelta(days=1)]

# 如果事件少于5个，添加一些默认的未来事件
default_events = [
    {'date': (today + timedelta(days=7)).strftime('%Y-%m-%d'), 
     'event': '央行公开市场操作及MLF到期', 'type': '货币政策', 'impact': '中', 'url': 'http://www.pbc.gov.cn/'},
    {'date': (today + timedelta(days=14)).strftime('%Y-%m-%d'), 
     'event': 'LPR报价日', 'type': '货币政策', 'impact': '高', 'url': 'http://www.pbc.gov.cn/'},
    {'date': (today + timedelta(days=21)).strftime('%Y-%m-%d'), 
     'event': '月末资金面观察', 'type': '市场流动性', 'impact': '中', 'url': 'http://www.pbc.gov.cn/'},
]

if len(catalysts) < 5:
    existing_dates = {c['date'] for c in catalysts}
    for evt in default_events:
        if evt['date'] not in existing_dates:
            catalysts.append(evt)
            if len(catalysts) >= 8:
                break

# 按日期排序
catalysts.sort(key=lambda x: x['date'])
data['catalysts'] = catalysts[:10]  # 最多保留10个
print(f"  保留 {len(data['catalysts'])} 个催化剂事件")

# ============ 8. 从HTML读取持仓基金并抓取最新净值 ============
print("\n--- 从HTML读取持仓基金列表 ---")

# 从HTML的 funds 数组中提取所有基金代码和名称
# 匹配格式: {id:1,name:"...",code:"006479",...}
fund_matches = re.findall(r'\{id:\d+,name:"([^"]+)",code:"(\d{6})"', html)

if not fund_matches:
    print("  警告: 未找到持仓基金，跳过净值抓取")
    my_fund_data = []
else:
    print(f"  发现 {len(fund_matches)} 只持仓基金")
    
    my_fund_data = []
    
    for name, code in fund_matches:
        try:
            time.sleep(0.2)
            df = ak.fund_open_fund_info_em(symbol=code, indicator="单位净值走势")
            if df is None or len(df) < 2:
                my_fund_data.append({
                    'code': code, 'name': name,
                    'latest_nav': None, 'prev_nav': None,
                    'daily_change_pct': 0
                })
                continue
            
            latest_nav = safe_float(df.iloc[-1]['单位净值'])
            prev_nav = safe_float(df.iloc[-2]['单位净值'])
            
            if prev_nav > 0:
                daily_change_pct = round((latest_nav - prev_nav) / prev_nav * 100, 2)
            else:
                daily_change_pct = 0
            
            my_fund_data.append({
                'code': code, 'name': name,
                'latest_nav': round(latest_nav, 4),
                'prev_nav': round(prev_nav, 4),
                'daily_change_pct': daily_change_pct
            })
            print(f"  {name[:12]}: 净值{latest_nav:.4f} ({daily_change_pct:+.2f}%)")
            
        except Exception as e:
            print(f"  {name[:12]}: 获取失败 - {e}")
            my_fund_data.append({
                'code': code, 'name': name,
                'latest_nav': None, 'prev_nav': None,
                'daily_change_pct': 0
            })

# 保存到MARKET_DATA
data['myFundsNav'] = my_fund_data
data['navUpdateTime'] = datetime.now().strftime('%Y-%m-%d %H:%M')

# ============ 9. 更新时间戳 ============
data['updateTime'] = datetime.now().strftime('%Y-%m-%d %H:%M')

# ============ 10. 写回HTML ============
print("\n--- 写回HTML文件 ---")

# 序列化JSON（确保中文不被转义）
new_json = json.dumps(data, ensure_ascii=False, separators=(',', ':'))

# 替换HTML中的MARKET_DATA
new_html = re.sub(r'let MARKET_DATA=\{.*?\};', f'let MARKET_DATA={new_json};', html, flags=re.DOTALL)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(new_html)

print(f"\n=== 更新完成! ===")
print(f"更新时间: {data['updateTime']}")
print(f"方向预测: {len(data['predictions'])} 个方向")
print(f"推荐基金: {len(data['recommendations'])} 只")
print(f"催化剂事件: {len(data['catalysts'])} 个")
print(f"持仓净值: {len([f for f in my_fund_data if f['latest_nav']])} 只基金已更新")
