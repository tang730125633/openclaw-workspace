#!/usr/bin/env python3
"""
零碳电力圈 - 每日早报爬虫
爬取发改委、能源局、华中监管局、铜价，输出六板块早报 Markdown
"""
import json, urllib.request, urllib.parse, re, time
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
TODAY = datetime.now().strftime('%Y-%m-%d')
TODAY_NDRC = datetime.now().strftime('%Y/%m/%d')
TODAY_NEA = datetime.now().strftime('%Y%m%d')

def fetch(url, referer=''):
    req = urllib.request.Request(url, headers={
        'User-Agent': UA, 'Referer': referer,
        'Accept': 'application/json, text/html, */*'
    })
    return urllib.request.urlopen(req, timeout=15).read()

# ── 板块一二：能源局 主页爬取（近7日） ───────────────────────
def fetch_nea():
    from bs4 import BeautifulSoup
    INDUSTRY = ['电网','电力','电价','光伏','绿电','零碳','低碳','新能源',
                 '分布式','集中式','储能','氢能','充电桩','碳中和','碳达峰',
                 '可再生能源','风电','抽水蓄能','碳排放','节能','能源','水电',
                 '输电','配电','电站','电气','市场化','标准','政策','规划']
    EXCLUDE  = ['专家名单','人员名单','面试公告','录用','招聘','人事',
                 '公示名单','执法案例','投诉举报','公务员','注销登记','安全注册']

    cutoff = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    html = fetch('https://www.nea.gov.cn/', 'https://www.nea.gov.cn/').decode('utf-8', errors='ignore')
    soup = BeautifulSoup(html, 'html.parser')

    seen, results = set(), []
    for a in soup.find_all('a', href=True):
        href = a.get('href', '')
        if not re.search(r'/2026\d{4}/', href): continue
        if 'nea.gov.cn' not in href and not href.startswith('/'): continue
        title = a.get_text(strip=True)
        if len(title) < 6: continue
        if href.startswith('/'): href = 'https://www.nea.gov.cn' + href
        if href.startswith('http://'): href = href.replace('http://', 'https://')
        if href in seen: continue
        seen.add(href)
        m = re.search(r'/(2026\d{4})/', href)
        if not m: continue
        raw = m.group(1)
        date_ = f'{raw[:4]}-{raw[4:6]}-{raw[6:]}'
        if date_ < cutoff: continue
        if any(kw in title for kw in EXCLUDE): continue
        results.append({'title': title, 'url': href, 'date': date_, 'src': '国家能源局'})

    # 同时查公告JSON（更多政策文件）
    try:
        json_url = 'https://www.nea.gov.cn/policy/ds_6db2ed2a0ae946d882bcc769494c99be.json'
        data = json.loads(fetch(json_url, 'https://www.nea.gov.cn/').decode('utf-8'))
        for item in data.get('datasource', []):
            title = re.sub(r'<[^>]+>', '', item.get('showTitle') or item.get('title', '')).strip()
            url_  = item.get('publishUrl', '')
            date_ = item.get('publishTime', '')[:10]
            if date_ < cutoff: continue
            if any(kw in title for kw in EXCLUDE): continue
            if not title or len(title) < 6: continue
            if url_.startswith('../'): url_ = 'https://www.nea.gov.cn/policy/' + url_
            if url_.startswith('http://'): url_ = url_.replace('http://', 'https://')
            if url_ in seen: continue
            seen.add(url_)
            results.append({'title': title, 'url': url_, 'date': date_, 'src': '国家能源局'})
    except Exception:
        pass

    results.sort(key=lambda x: x['date'], reverse=True)
    return results[:10]

# ── 板块一二：发改委 HTML ──────────────────────────────────
def fetch_ndrc():
    results = []
    for page_url in [
        'https://www.ndrc.gov.cn/xwdt/xwfb/',
        'https://www.ndrc.gov.cn/xxgk/zcfb/tz/',
    ]:
        html = fetch(page_url).decode('utf-8', errors='ignore')
        soup = BeautifulSoup(html, 'html.parser')
        for li in soup.select('li'):
            a = li.find('a', href=True)
            span = li.find('span')
            if not (a and span and '/' in span.text): continue
            if span.text.strip() != TODAY_NDRC: continue
            title = a.get('title') or a.text.strip()
            href  = urllib.parse.urljoin(page_url, a['href'])
            results.append({'title': title, 'url': href, 'date': TODAY, 'src': '国家发改委'})
    return results

# ── 板块三：华中监管局 ────────────────────────────────────
def fetch_hzj():
    results = []
    html = fetch('https://hzj.nea.gov.cn/dtyw/jgdt/').decode('utf-8', errors='ignore')
    soup = BeautifulSoup(html, 'html.parser')
    today_mm_dd = datetime.now().strftime('%m-%d')
    for li in soup.select('li'):
        a = li.find('a', href=True)
        text = li.get_text()
        if today_mm_dd not in text: continue
        if not a or len(a.text.strip()) < 5: continue
        href = urllib.parse.urljoin('https://hzj.nea.gov.cn/', a['href'])
        results.append({'title': a.text.strip(), 'url': href, 'date': TODAY, 'src': '华中能源监管局'})
    return results

# ── 板块五：铜价 ──────────────────────────────────────────
def fetch_copper():
    def latest_workday():
        d = datetime.now()
        w = d.weekday()
        if w == 0: d -= timedelta(days=3)
        elif w in (5, 6): d -= timedelta(days=w - 4)
        else: d -= timedelta(days=1)
        return d.strftime('%Y-%m-%d')

    target = latest_workday()
    html = fetch('https://copper.ccmn.cn/copperprice/').decode('utf-8', errors='ignore')
    soup = BeautifulSoup(html, 'html.parser')
    for tr in soup.select('table.purchase tr'):
        td2 = tr.select_one('td.purchase_width2 a')
        td3 = tr.select_one('td.purchase_width3')
        if td2 and td3 and target in td3.text:
            href = td2['href']
            if href.startswith('//'): href = 'https:' + href
            return {'title': f'长江现货铜价（{target}）', 'url': href, 'date': target, 'src': '长江有色金属网'}
    return None

# ── 生成早报 Markdown ─────────────────────────────────────
def generate_report(nea, ndrc, hzj, copper):
    lines = [f'# 📊 零碳能源早报 | {TODAY}\n']

    # 板块一：今日最重要（能源局+发改委前3条）
    top = (nea + ndrc)[:3]
    lines.append('## 📌 一、今日最重要（3条）\n')
    for i, item in enumerate(top, 1):
        lines.append(f'**{i}. [{item["title"]}]({item["url"]})**')
        lines.append(f'来源：{item["src"]}\n')

    # 板块二：政策与行业（再取3条）
    pol = (nea + ndrc)[3:6]
    lines.append('\n## 📋 二、政策与行业（3条）\n')
    for i, item in enumerate(pol, 1):
        lines.append(f'**{i}. [{item["title"]}]({item["url"]})**')
        lines.append(f'来源：{item["src"]}\n')

    # 板块三：湖北本地
    lines.append('\n## 🏠 三、湖北本地（2条）\n')
    for i, item in enumerate(hzj[:2], 1):
        lines.append(f'**{i}. [{item["title"]}]({item["url"]})**')
        lines.append(f'来源：{item["src"]}\n')
    if not hzj:
        lines.append('*今日暂无华中监管局更新*\n')

    # 板块四：AI+电力（占位）
    lines.append('\n## 🤖 四、AI + 电力（2条）\n')
    lines.append('*（需百度搜索接口，待接入）*\n')

    # 板块五：铜价
    lines.append('\n## 💰 五、铜价与材料（1条）\n')
    if copper:
        lines.append(f'**1. [{copper["title"]}]({copper["url"]})**')
        lines.append(f'来源：{copper["src"]}\n')
    else:
        lines.append('*今日暂无铜价数据*\n')

    # 板块六：机会提示（AI综合）
    lines.append('\n## 🎯 六、重点机会提示\n')
    all_titles = ' '.join(i['title'] for i in top + pol)
    hints = []
    if '抽水蓄能' in all_titles or '储能' in all_titles: hints.append('✅ 关注储能/抽蓄建设机会')
    if '光伏' in all_titles or '新能源' in all_titles: hints.append('✅ 关注新能源装机政策落地')
    if '现货市场' in all_titles or '电价' in all_titles: hints.append('✅ 关注电力市场化改革动向')
    if '充电桩' in all_titles: hints.append('✅ 关注充电基础设施配套机会')
    if not hints: hints.append('✅ 今日政策面平稳，持续跟踪能源局动态')
    for h in hints: lines.append(h)

    lines.append(f'\n---\n⏰ {TODAY} 08:00 | 来源：国家能源局、发改委、华中监管局、长江有色\n\n——小琳（零碳能源总经理AI助理）')
    return '\n'.join(lines)

# ── 主程序 ────────────────────────────────────────────────
if __name__ == '__main__':
    print(f'开始爬取 {TODAY} 早报数据...')
    nea   = fetch_nea();   print(f'能源局: {len(nea)} 条')
    ndrc  = fetch_ndrc();  print(f'发改委: {len(ndrc)} 条')
    hzj   = fetch_hzj();   print(f'华中局: {len(hzj)} 条')
    copper = fetch_copper(); print(f'铜价: {"有" if copper else "无"}')

    report = generate_report(nea, ndrc, hzj, copper)

    import os
    workspace = os.path.expanduser('~/.openclaw/workspace')
    out_dir = os.path.join(workspace, 'knowledge-base', '早报')
    if not os.path.exists(workspace):
        out_dir = '/tmp/早报'
    os.makedirs(out_dir, exist_ok=True)
    out_path = f'{out_dir}/{TODAY}_早报.md'
    with open(out_path, 'w') as f:
        f.write(report)
    print(f'\n✅ 早报已生成: {out_path}')
    print(report[:500])
