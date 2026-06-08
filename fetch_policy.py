import requests
from bs4 import BeautifulSoup
import re
import os
from datetime import datetime

# 从环境变量读取机器人 key（安全）
WEBHOOK_KEY = os.environ.get('WECHAT_KEY')
WEBHOOK_URL = f'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={WEBHOOK_KEY}'

# 要监控的网站列表（RSS或公告页）
SOURCES = [
    {
        'name': '国家发改委',
        'url': 'https://www.ndrc.gov.cn/xwdt/tzgg/',
        'rss': False
    },
    {
        'name': '生态环境部',
        'url': 'https://www.mee.gov.cn/xxgk2018/xxgk/xxgk01/',
        'rss': False
    },
    {
        'name': '国家能源局',
        'url': 'http://www.nea.gov.cn/xxgk/',
        'rss': False
    },
    # 可继续添加
]

# 发送消息到企业微信
def send_to_wechat(text):
    headers = {'Content-Type': 'application/json'}
    data = {
        "msgtype": "text",
        "text": {
            "content": text
        }
    }
    res = requests.post(WEBHOOK_URL, json=data, headers=headers)
    return res.status_code == 200

# 简单的 HTML 页面解析（通用方法，具体网站可能需要微调）
def fetch_from_html(source):
    try:
        resp = requests.get(source['url'], timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(resp.content, 'html.parser')
        # 尝试抓取所有链接
        links = soup.find_all('a', href=True)
        results = []
        for link in links:
            title = link.get_text(strip=True)
            href = link['href']
            # 过滤掉导航等无关链接
            if not title or len(title) < 5:
                continue
            # 补全相对路径
            if not href.startswith('http'):
                href = source['url'].rstrip('/') + '/' + href.lstrip('/')
            # 简单关键词过滤：包含 碳/储能/新能源/双碳/能耗
            keywords = ['碳', '储能', '新能源', '双碳', '能耗', '光热', '熔盐', '调峰']
            if any(kw in title for kw in keywords):
                results.append(f"【{source['name']}】{title}\n{href}")
        return results[:3]  # 每个源最多返回3条
    except Exception as e:
        return [f"【{source['name']}】抓取失败：{str(e)}"]

def main():
    all_news = []
    for source in SOURCES:
        news = fetch_from_html(source)
        all_news.extend(news)
    if not all_news:
        all_news.append("今日暂无更新。")
    content = f"{datetime.now().strftime('%Y-%m-%d')} 政策速递\n\n" + "\n\n".join(all_news)
    if WEBHOOK_KEY:
        success = send_to_wechat(content)
        if success:
            print("推送成功")
        else:
            print("推送失败")
    else:
        print("未设置机器人key，仅打印内容：")
        print(content)

if __name__ == '__main__':
    main()
