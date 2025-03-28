import json
import requests
from bs4 import BeautifulSoup
import time
import os
import re
import random

# 获取配置目录
CONFIG_DIR = os.getenv('CONFIG_DIR', 'config')
CONFIG_FILE = os.path.join(CONFIG_DIR, 'config.json')
NEW_MOVIES_FILE = os.path.join(CONFIG_DIR, 'new_movies.json')

def load_config():
    """加载配置文件"""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"加载配置失败: {e}")
    return {
        "cookie": "",
        "update_interval": 3600
    }

def load_new_data():
    """加载现有的最新电影数据"""
    try:
        if os.path.exists(NEW_MOVIES_FILE):
            with open(NEW_MOVIES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"加载现有数据失败: {e}")
    return {'movies': [], 'tv_shows': [], 'update_time': ''}

def get_douban_new_movies(cookie):
    """获取豆瓣最新电影数据"""
    url = 'https://movie.douban.com/j/search_subjects'
    params = {
        'type': 'movie',
        'tag': '最新',
        'page_limit': 50,
        'page_start': 0
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Cookie': cookie
    }
    
    response = requests.get(url, params=params, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        raise requests.RequestException(f"获取最新电影数据失败: HTTP {response.status_code}")

def get_douban_new_tv(cookie):
    """获取豆瓣最新电视剧数据"""
    url = 'https://movie.douban.com/j/search_subjects'
    params = {
        'type': 'tv',
        'tag': '最新',
        'page_limit': 50,
        'page_start': 0
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Cookie': cookie
    }
    
    response = requests.get(url, params=params, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        raise requests.RequestException(f"获取最新电视剧数据失败: HTTP {response.status_code}")

def parse_new_movies(cookie):
    """解析最新电影和电视剧数据"""
    # 加载现有数据
    data = load_new_data()
    
    # 初始化计数器
    new_movies = 0
    new_tv_shows = 0
    
    # 获取最新电影数据
    movies_data = get_douban_new_movies(cookie)
    if movies_data and 'subjects' in movies_data:
        print(f"找到 {len(movies_data['subjects'])} 个最新电影")
        new_items = []
        
        # 预先检查哪些是新条目
        for item in movies_data['subjects']:
            is_exists = False
            for existing_item in data['movies'] + data['tv_shows']:
                if item['id'] == existing_item['id']:
                    print(f"条目已存在: {item['title']} (ID: {item['id']})")
                    is_exists = True
                    break
            if not is_exists:
                new_items.append(item)
                
        print(f"其中有 {len(new_items)} 个新电影")
        
        # 处理新条目
        for item in new_items:
            result = parse_api_item(item, cookie)
            if result:
                if result['type'] == 'movie':
                    data['movies'].append(result)
                    new_movies += 1
                elif result['type'] == 'tv':
                    data['tv_shows'].append(result)
                    new_tv_shows += 1
                
                # 更新时间
                data['update_time'] = time.strftime('%Y-%m-%d %H:%M:%S')
                # 立即保存数据
                save_new_data(data)
                print(f"已保存新条目: {result['title']}")
                    
            # 添加随机延迟
            delay = random.uniform(3, 7)
            print(f"等待 {delay:.1f} 秒后继续...")
            time.sleep(delay)
    
    # 获取最新电视剧数据
    tv_data = get_douban_new_tv(cookie)
    if tv_data and 'subjects' in tv_data:
        print(f"找到 {len(tv_data['subjects'])} 个最新电视剧")
        new_items = []
        
        # 预先检查哪些是新条目
        for item in tv_data['subjects']:
            is_exists = False
            for existing_item in data['movies'] + data['tv_shows']:
                if item['id'] == existing_item['id']:
                    print(f"条目已存在: {item['title']} (ID: {item['id']})")
                    is_exists = True
                    break
            if not is_exists:
                new_items.append(item)
                
        print(f"其中有 {len(new_items)} 个新电视剧")
        
        # 处理新条目
        for item in new_items:
            result = parse_api_item(item, cookie)
            if result:
                if result['type'] == 'tv':
                    data['tv_shows'].append(result)
                    new_tv_shows += 1
                elif result['type'] == 'movie':
                    data['movies'].append(result)
                    new_movies += 1
                
                # 更新时间
                data['update_time'] = time.strftime('%Y-%m-%d %H:%M:%S')
                # 立即保存数据
                save_new_data(data)
                print(f"已保存新条目: {result['title']}")
                    
            # 添加随机延迟
            delay = random.uniform(3, 7)
            print(f"等待 {delay:.1f} 秒后继续...")
            time.sleep(delay)
    
    if new_movies == 0 and new_tv_shows == 0:
        print("没有发现新的内容，无需更新")
        data['has_updates'] = False
    else:
        print(f"新增 {new_movies} 部最新电影和 {new_tv_shows} 部最新电视剧")
        data['has_updates'] = True
    
    return data

def save_new_data(data):
    """保存最新数据到文件"""
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(NEW_MOVIES_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def check_cookie_valid(cookie):
    """检查 cookie 是否有效"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Cookie': cookie
        }
        
        response = requests.get('https://www.douban.com', headers=headers, timeout=10)
        
        if 'login' in response.url or response.status_code == 403:
            print("\n❌ Cookie 已失效，需要重新登录")
            return False
            
        print("\n✅ Cookie 验证通过")
        return True
        
    except Exception as e:
        print(f"\n❌ 验证 Cookie 时出错: {e}")
        return False

def send_telegram_message(message, config):
    """发送 Telegram 消息"""
    if not config.get('telegram', {}).get('enabled'):
        return
    
    bot_token = config['telegram']['bot_token']
    chat_id = config['telegram']['chat_id']
    
    if not bot_token or bot_token == 'your_bot_token_here' or \
       not chat_id or chat_id == 'your_chat_id_here':
        print("Telegram 配置无效，跳过发送消息")
        return
    
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML"
        }
        response = requests.post(url, json=data, timeout=10)
        
        if response.status_code == 200:
            print("Telegram 消息发送成功")
        else:
            print(f"发送 Telegram 消息失败: {response.json().get('description', '未知错误')}")
            
    except Exception as e:
        print(f"发送 Telegram 消息时出错: {e}")

def get_subject_info(subject_id, cookie, max_retries=3):
    """获取条目信息"""
    for attempt in range(max_retries):
        try:
            url = f'https://movie.douban.com/subject/{subject_id}/'
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Cookie': cookie
            }
            
            print(f"正在获取条目 {subject_id} 的信息...")
            
            # 随机延迟2-5秒
            delay = random.uniform(2, 5)
            time.sleep(delay)
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 初始化其他信息
                info = {
                    'type': 'movie',  # 默认为电影
                    'imdb_id': None,
                    'year': '',
                    'duration': '',
                    'region': '',
                    'director': [],
                    'actors': [],
                    'genres': [],
                    'languages': [],
                    'release_date': '',
                    'vote_count': '',
                    'episodes_info': ''
                }
                
                # 判断类型（电影/电视剧）
                # 1. 检查是否有分集短评
                episode_comments = soup.find('i', text=re.compile(r'的分集短评'))
                if episode_comments:
                    info['type'] = 'tv'
                else:
                    # 2. 检查是否有集数信息
                    episode_info = soup.find('span', text=re.compile(r'集数:|共\d+集'))
                    episode_duration = soup.find('span', text=re.compile(r'单集片长:'))
                    if episode_info or episode_duration:
                        info['type'] = 'tv'
                        if episode_info and episode_info.next_sibling:
                            info['episodes_info'] = episode_info.next_sibling.strip()
                
                info_div = soup.find('div', {'id': 'info'})
                if info_div:
                    # 获取IMDB ID
                    imdb_link = soup.find('a', {'href': re.compile(r'www\.imdb\.com/title/(tt\d+)')})
                    if imdb_link:
                        match = re.search(r'tt\d+', imdb_link['href'])
                        if match:
                            info['imdb_id'] = match.group()
                    
                    if not info['imdb_id']:
                        imdb_span = info_div.find('span', text=re.compile(r'IMDb:'))
                        if imdb_span and imdb_span.next_sibling:
                            imdb_text = imdb_span.next_sibling.strip()
                            match = re.search(r'tt\d+', imdb_text)
                            if match:
                                info['imdb_id'] = match.group()
                    
                    # 获取年份
                    year_span = soup.find('span', {'class': 'year'})
                    if year_span:
                        year_match = re.search(r'\d{4}', year_span.text)
                        if year_match:
                            info['year'] = year_match.group()
                    
                    # 获取导演
                    director_span = info_div.find('span', text='导演')
                    if director_span:
                        director_links = director_span.find_next('span')
                        if director_links:
                            info['director'] = [link.text.strip() for link in director_links.find_all('a')]
                    
                    # 获取主演
                    actors_span = info_div.find('span', text='主演')
                    if actors_span:
                        actor_links = actors_span.find_next('span')
                        if actor_links:
                            info['actors'] = [link.text.strip() for link in actor_links.find_all('a')]
                    
                    # 获取类型
                    genre_spans = info_div.find_all('span', {'property': 'v:genre'})
                    if genre_spans:
                        info['genres'] = [span.text.strip() for span in genre_spans]
                    
                    # 获取制片国家/地区
                    region_text = info_div.find(text=re.compile(r'制片国家/地区:'))
                    if region_text and region_text.next_sibling:
                        info['region'] = region_text.next_sibling.strip()
                    
                    # 获取语言
                    language_text = info_div.find(text=re.compile(r'语言:'))
                    if language_text and language_text.next_sibling:
                        languages = language_text.next_sibling.strip()
                        if languages:
                            info['languages'] = [lang.strip() for lang in languages.split('/') if lang.strip()]
                    
                    # 获取片长
                    duration_span = info_div.find('span', {'property': 'v:runtime'})
                    if duration_span:
                        info['duration'] = duration_span.text.strip()
                    
                    # 获取上映日期
                    release_date_span = info_div.find('span', {'property': 'v:initialReleaseDate'})
                    if release_date_span:
                        info['release_date'] = release_date_span.text.strip()
                
                # 获取评分人数
                votes_span = soup.find('span', {'property': 'v:votes'})
                if votes_span:
                    info['vote_count'] = votes_span.text.strip()
                
                print(f"条目 {subject_id} 的类型为: {info['type']}")
                if info['imdb_id']:
                    print(f"IMDB ID为: {info['imdb_id']}")
                    
                return info
            
            elif response.status_code == 403:
                print(f"请求被限制，等待后重试 (尝试 {attempt + 1}/{max_retries})")
                time.sleep(random.uniform(5, 10))
                continue
            else:
                print(f"获取条目 {subject_id} 失败: HTTP {response.status_code}")
                if attempt < max_retries - 1:
                    continue
                return None
                
        except Exception as e:
            print(f"获取条目 {subject_id} 时出错: {e}")
            if attempt < max_retries - 1:
                continue
            return None
    
    print(f"已达到最大重试次数 ({max_retries})")
    return None

def parse_api_item(item, cookie):
    """解析API返回的条目"""
    try:
        subject_id = item['id']
        
        # 获取详细信息
        info = get_subject_info(subject_id, cookie)
        if not info:
            return None
            
        return {
            "title": item['title'],
            "rating": item['rate'],
            "vote_count": info['vote_count'],
            "duration": info['duration'],
            "region": info['region'],
            "director": info['director'],
            "actors": info['actors'],
            "cover_url": item['cover'],
            "url": item['url'],
            "id": subject_id,
            "type": info['type'],
            "imdb_id": info['imdb_id'],
            "year": info['year'],
            "genres": info['genres'],
            "languages": info['languages'],
            "release_date": info['release_date'],
            "episodes_info": info['episodes_info']
        }
        
    except Exception as e:
        print(f"解析条目时出错: {e}")
        return None

def extract_subject_id(url):
    """从URL中提取豆瓣ID"""
    match = re.search(r'subject/(\d+)', url)
    return match.group(1) if match else None

def main():
    try:
        config = load_config()
        cookie = config.get('cookie', '')
        
        # 验证 cookie
        if not cookie:
            message = "❌ Cookie 未配置，请先配置 Cookie"
            print(message)
            send_telegram_message(message, config)
            return
            
        if not check_cookie_valid(cookie):
            message = "❌ Cookie 已失效，请更新 Cookie"
            print(message)
            send_telegram_message(message, config)
            return
        
        print("\n开始获取豆瓣最新数据...")
        
        # 解析数据
        data = parse_new_movies(cookie)
        
        # 生成统计信息
        movies_count = len(data['movies'])
        tv_shows_count = len(data['tv_shows'])
        
        # 只在有更新时才发送消息
        if data.get('has_updates', False):
            # 生成通知消息
            message = (
                f"🎬 <b>豆瓣最新数据更新完成</b>\n\n"
                f"更新时间: {data['update_time']}\n"
                f"总电影数: {movies_count} 部\n"
                f"总剧集数: {tv_shows_count} 部\n\n"
            )
            
            # 新增内容：添加新更新的电影信息
            if data.get('has_updates', False):
                message += "<b>新增电影:</b>\n"
                new_movies = [movie for movie in data['movies'] if not movie.get('notified', False)]
                for movie in new_movies[:5]:  # 最多显示5部新电影
                    movie_link = movie.get('url', f"https://movie.douban.com/subject/{movie.get('id', '')}/")
                    message += f"• <a href='{movie_link}'>{movie['title']}</a> - ⭐{movie['rating']}\n"
                    movie['notified'] = True  # 标记为已通知
                    
                # 如果新电影超过5部，添加"等"字样
                if len(new_movies) > 5:
                    message += f"等 {len(new_movies)} 部新电影\n"
                    
                message += "\n"
                
            message += "<b>最新电影 TOP 5:</b>\n"
            
            # 添加最新电影信息
            for i, movie in enumerate(sorted(data['movies'], key=lambda x: float(x['rating'] or 0), reverse=True)[:5], 1):
                movie_link = movie.get('url', f"https://movie.douban.com/subject/{movie.get('id', '')}/")
                message += f"{i}. <a href='{movie_link}'>{movie['title']}</a> - ⭐{movie['rating']}\n"
                
            # 只有在有电视剧时才显示电视剧部分
            if tv_shows_count > 0:
                message += "\n<b>最新剧集 TOP 5:</b>\n"
                
                # 添加最新剧集信息
                for i, tv in enumerate(sorted(data['tv_shows'], key=lambda x: float(x['rating'] or 0), reverse=True)[:5], 1):
                    tv_link = tv.get('url', f"https://movie.douban.com/subject/{tv.get('id', '')}/")
                    message += f"{i}. <a href='{tv_link}'>{tv['title']}</a> - ⭐{tv['rating']}\n"
            
            # 发送 Telegram 通知
            send_telegram_message(message, config)
        
        print(f"\n数据获取完成！总计 {movies_count} 部最新电影和 {tv_shows_count} 部最新电视剧")
        
    except Exception as e:
        error_message = f"❌ 获取豆瓣最新数据时出错: {str(e)}"
        print(error_message)
        send_telegram_message(error_message, config)

if __name__ == "__main__":
    main() 