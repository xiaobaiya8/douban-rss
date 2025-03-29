import os
import json
import requests
import time
import re
from typing import Dict, List, Any, Optional, Union, Tuple
from bs4 import BeautifulSoup
import random

# 定义可导出的函数列表
__all__ = [
    'load_config', 
    'check_cookie_valid',
    'extract_subject_id',
    'get_subject_info',
    'get_api_data',
    'parse_api_item',
    'send_telegram_message',
    'make_douban_headers',
    'load_json_data',
    'save_json_data'
]

# 添加版本信息
__version__ = '1.0.0'

# 获取配置目录
CONFIG_DIR = os.getenv('CONFIG_DIR', 'config')
CONFIG_FILE = os.path.join(CONFIG_DIR, 'config.json')

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

def extract_subject_id(url):
    """从 URL 中提取豆瓣 ID"""
    match = re.search(r'subject/(\d+)', url)
    if match:
        return match.group(1)
    return None

def get_subject_info(subject_id, cookie, max_retries=3):
    """获取条目详细信息"""
    for attempt in range(max_retries):
        try:
            url = f'https://movie.douban.com/subject/{subject_id}/'
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Cookie': cookie
            }
            
            print(f"正在获取条目 {subject_id} 的信息...")
            
            # 随机延迟2-5秒，避免请求过快
            delay = random.uniform(2, 5)
            time.sleep(delay)
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 初始化条目信息
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
                    'episodes_info': {}
                }
                
                # 判断类型（电影/电视剧）
                # 检查是否有分集短评（电视剧特有）
                is_tv = '的分集短评' in response.text
                episode_info = soup.find('span', text=re.compile(r'集数:|共\d+集'))
                episode_duration = soup.find(text=re.compile(r'单集片长:'))
                
                if is_tv or episode_info or episode_duration:
                    info['type'] = 'tv'
                    if episode_info and episode_info.next_sibling:
                        info['episodes_info']['count'] = episode_info.next_sibling.strip()
                    if episode_duration and episode_duration.next_sibling:
                        info['episodes_info']['duration'] = episode_duration.next_sibling.strip()
                
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
                            info['actors'] = [link.text.strip() for link in actor_links.find_all('a')][:3]  # 只取前三个主演
                    
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
            elif response.status_code == 404:
                print(f"条目 {subject_id} 不存在")
                return None
            else:
                print(f"获取条目 {subject_id} 失败: HTTP {response.status_code}")
                if attempt < max_retries - 1:
                    time.sleep(random.uniform(2, 5))
                    continue
                return None
                
        except Exception as e:
            print(f"获取条目 {subject_id} 时出错: {e}")
            if attempt < max_retries - 1:
                time.sleep(random.uniform(2, 5))
                continue
            return None
    
    print(f"已达到最大重试次数 ({max_retries})")
    return None

def get_api_data(type_value, tag_value, cookie, page_limit=50, page_start=0):
    """获取豆瓣API数据，用于热门、最新、冷门佳片等标签
    
    参数:
        type_value: 'movie' 或 'tv'
        tag_value: '热门', '最新', '冷门佳片' 等标签
        cookie: 豆瓣cookie
        page_limit: 每页条目数量
        page_start: 起始位置
    
    返回:
        API返回的json数据
    """
    url = 'https://movie.douban.com/j/search_subjects'
    params = {
        'type': type_value,
        'tag': tag_value,
        'page_limit': page_limit,
        'page_start': page_start
    }
    headers = make_douban_headers(cookie)
    
    response = requests.get(url, params=params, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        raise requests.RequestException(f"获取数据失败: HTTP {response.status_code}")

def parse_api_item(item, cookie):
    """解析 API 返回的条目数据"""
    try:
        # 获取详细信息
        subject_id = item['id']
        info = get_subject_info(subject_id, cookie)
        
        if not info:
            return None
            
        # 合并基本信息
        result = {
            'id': subject_id,
            'title': item['title'],
            'url': item['url'],
            'cover': item['cover'],
            'rate': item['rate'],
            'rating': item.get('rating', {}).get('value', item['rate']),
            'type': info['type'],
            'imdb_id': info['imdb_id'],
            'year': info['year'],
            'director': info['director'],
            'actors': info['actors'],
            'genres': info['genres'],
            'region': info['region'],
            'languages': info['languages'],
            'duration': info['duration'],
            'release_date': info['release_date'],
            'vote_count': info['vote_count']
        }
        
        # 如果是电视剧，添加剧集信息
        if info['type'] == 'tv':
            result['episodes_info'] = info['episodes_info']
            
        return result
        
    except Exception as e:
        print(f"解析条目 {item['id']} 时出错: {e}")
        return None

def send_telegram_message(message, config, has_new_content=False):
    """发送 Telegram 消息"""
    if not config.get('telegram', {}).get('enabled'):
        return
    
    bot_token = config['telegram']['bot_token']
    chat_id = config['telegram']['chat_id']
    notify_mode = config['telegram'].get('notify_mode', 'always')
    
    # 检查是否应该发送消息（基于通知模式）
    if notify_mode == 'new_only' and not has_new_content:
        print("没有新内容，根据通知设置跳过发送消息")
        return
    
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
            error_msg = response.json().get('description', '未知错误')
            print(f"发送 Telegram 消息失败: {error_msg}")
            
            # 如果是认证错误，给出更详细的提示
            if response.status_code == 401:
                print("Bot Token 无效，请检查是否正确配置")
            elif response.status_code == 404:
                print("Bot Token 格式错误或已失效")
            elif response.status_code == 400:
                print("Chat ID 无效，请检查是否正确配置")
                
    except requests.exceptions.Timeout:
        print("发送 Telegram 消息超时")
    except requests.exceptions.RequestException as e:
        print(f"发送 Telegram 消息出错: {e}")
    except Exception as e:
        print(f"发送 Telegram 消息时发生未知错误: {e}")

def make_douban_headers(cookie):
    """生成带有cookie的请求头"""
    return {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Cookie': cookie
    }

def load_json_data(file_path, default_value=None):
    """加载JSON数据文件"""
    if default_value is None:
        default_value = {'movies': [], 'tv_shows': [], 'update_time': ''}
        
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"加载数据失败: {e}")
    return default_value

def save_json_data(data, file_path):
    """保存JSON数据到文件"""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2) 