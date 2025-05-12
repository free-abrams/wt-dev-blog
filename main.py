import time
from datetime import datetime
import requests
from bs4 import BeautifulSoup

from db import DevelopmentModel


def run(u):
    # 目标URL
    # url = "https://warthunder.com/en/news/?tags=Development"
    url = u
    # 设置请求头，模拟浏览器访问
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    dev = []
    try:
        # 发送HTTP请求
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # 检查请求是否成功

        # 解析HTML内容
        soup = BeautifulSoup(response.text, 'html.parser')

        # 查找所有class为showcase__item的元素下的a标签
        showcase_items = soup.find_all('div', class_='showcase__item')

        # 查找所有class为widget__title的div标签
        widget_titles = soup.find_all('div', class_='widget__title')

        # 提取标签中的文本内容
        titles = [title.get_text(strip=True) for title in widget_titles]

        # 提取a标签的href属性
        links = []
        for item in showcase_items:
            a_tag = item.find('a')
            if a_tag and 'href' in a_tag.attrs:
                links.append(a_tag['href'])

        widget__poster = soup.find_all('div', class_='widget__poster')

        posters = []
        for item in widget__poster:
            img = item.find('img')
            if img and 'data-src' in img.attrs:
                posters.append(f"https:{img['data-src']}")

        meta__items = soup.find_all('li', class_='widget-meta__item--right')

        published_at = [replace_chinese_month(item.get_text(strip=True)) for item in meta__items]

        published_at = [datetime.strptime(t, "%d %B %Y").isoformat() for t in published_at]

        dev = [{"title":titleStr,"link":linkStr,"poster":posterStr,"published_at":dateStr} for titleStr,linkStr,posterStr,dateStr in zip(titles,links, posters, published_at)]

        # 打印结果
        print("找到的链接:")
        for link in links:
            print(link)

        print(f"\n共找到 {len(links)} 个链接")

        # 打印结果
        print("找到的标题内容:")
        for i, title in enumerate(titles, 1):
            print(f"{i}. {title}")

        print(f"\n共找到 {len(titles)} 个标题")

        print("找到的图片链接:")
        for i, poster in enumerate(posters, 1):
            print(f"{i}. {poster}")
        print(f"\n共找到 {len(posters)} 个图片链接")

        print("找到的日期:")
        for i, date in enumerate(published_at, 1):
            print(f"{i}. {date}")
        print(f"\n共找到 {len(published_at)} 个日期")
        return dev
    except requests.exceptions.RequestException as e:
        print(f"请求出错: {e}")
        return dev
    except Exception as e:
        print(f"发生错误: {e}")
        return dev


def replace_chinese_month(date_str):
    """将中文月份替换为英文月份"""
    for cn, en in month_map.items():
        date_str = date_str.replace(cn, en)
    return date_str

month_map = {
    "一月": "January", "二月": "February", "三月": "March",
    "四月": "April", "五月": "May", "六月": "June",
    "七月": "July", "八月": "August", "九月": "September",
    "十月": "October", "十一月": "November", "十二月": "December",
    # 带"月"字和不带"月"字的变体
    "1月": "January", "2月": "February", "3月": "March",
    "4月": "April", "5月": "May", "6月": "June",
    "7月": "July", "8月": "August", "9月": "September",
    "10月": "October", "11月": "November", "12月": "December"
}

if __name__ == '__main__':
    while True:
        developmentModel = DevelopmentModel()
        url = [
            "https://warthunder.com/en/news/?tags=Development",
            "https://warthunder.com/zh/news/?tags=开发",
        ]
        langs = [
            "en",
            "zh"
        ]
        devs = []
        for k, u in enumerate(url):
            dev = run(u)
            for d in dev:
                d["lang"] = langs[k]
            devs += dev
        for dev in devs:
            developmentModel.firstOrCreate(dev, dev)
        time.sleep(60)  # 休眠60秒