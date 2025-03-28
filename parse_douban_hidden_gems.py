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
HIDDEN_GEMS_FILE = os.path.join(CONFIG_DIR, 'hidden_gems.json')

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

def load_hidden_gems_data():
    """加载现有的冷门佳片数据"""
    try:
        if os.path.exists(HIDDEN_GEMS_FILE):
            with open(HIDDEN_GEMS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"加载现有数据失败: {e}")
    return {'movies': [], 'tv_shows': [], 'update_time': ''}

def get_douban_hidden_gems(cookie):
    """获取豆瓣冷门佳片数据"""
    url = 'https://movie.douban.com/j/search_subjects'
    params = {
        'type': 'movie',
        'tag': '冷门佳片',
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
        raise requests.RequestException(f"获取冷门佳片数据失败: HTTP {response.status_code}")

def get_douban_hidden_tv(cookie):
    """获取豆瓣冷门剧集数据"""
    url = 'https://movie.douban.com/j/search_subjects'
    params = {
        'type': 'tv',
        'tag': '冷门佳片',
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
        raise requests.RequestException(f"获取冷门剧集数据失败: HTTP {response.status_code}")

def parse_hidden_gems(cookie):
    """解析冷门佳片数据"""
    # 加载现有数据
    data = load_hidden_gems_data()
    
    # 初始化计数器
    new_movies = 0
    new_tv_shows = 0
    
    # 生成本次更新的批次ID，用于标记这次添加的内容
    batch_id = int(time.time())
    
    # 重置new_added信息，确保每次运行都是从零开始
    data['has_updates'] = False
    data['new_added'] = {
        'movies': 0,
        'tv_shows': 0,
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'batch_id': batch_id
    }
    
    # 获取冷门佳片数据
    movies_data = get_douban_hidden_gems(cookie)
    if movies_data and 'subjects' in movies_data:
        print(f"找到 {len(movies_data['subjects'])} 个冷门佳片")
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
                
        print(f"其中有 {len(new_items)} 个新佳片")
        
        # 处理新条目
        for item in new_items:
            result = parse_api_item(item, cookie)
            if result:
                # 明确设置notified为False，这是一个新条目需要通知
                result['notified'] = False
                # 添加批次ID，用于标识本次更新添加的内容
                result['batch_id'] = batch_id
                
                if result['type'] == 'movie':
                    data['movies'].append(result)
                    new_movies += 1
                elif result['type'] == 'tv':
                    data['tv_shows'].append(result)
                    new_tv_shows += 1
                
                # 更新时间
                data['update_time'] = time.strftime('%Y-%m-%d %H:%M:%S')
                # 立即保存数据
                save_hidden_gems_data(data)
                print(f"已保存新条目: {result['title']}")
                    
            # 添加随机延迟
            delay = random.uniform(3, 7)
            print(f"等待 {delay:.1f} 秒后继续...")
            time.sleep(delay)
    
    # 获取冷门剧集数据
    tv_data = get_douban_hidden_tv(cookie)
    if tv_data and 'subjects' in tv_data:
        print(f"找到 {len(tv_data['subjects'])} 个冷门剧集")
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
                
        print(f"其中有 {len(new_items)} 个新剧集")
        
        # 处理新条目
        for item in new_items:
            result = parse_api_item(item, cookie)
            if result:
                # 明确设置notified为False，这是一个新条目需要通知
                result['notified'] = False
                # 添加批次ID，用于标识本次更新添加的内容
                result['batch_id'] = batch_id
                
                if result['type'] == 'tv':
                    data['tv_shows'].append(result)
                    new_tv_shows += 1
                elif result['type'] == 'movie':
                    data['movies'].append(result)
                    new_movies += 1
                
                # 更新时间
                data['update_time'] = time.strftime('%Y-%m-%d %H:%M:%S')
                # 立即保存数据
                save_hidden_gems_data(data)
                print(f"已保存新条目: {result['title']}")
                    
            # 添加随机延迟
            delay = random.uniform(3, 7)
            print(f"等待 {delay:.1f} 秒后继续...")
            time.sleep(delay)
    
    if new_movies == 0 and new_tv_shows == 0:
        print("没有发现新的内容，无需更新")
        data['has_updates'] = False
    else:
        print(f"新增 {new_movies} 部冷门佳片和 {new_tv_shows} 部冷门剧集")
        data['has_updates'] = True
        # 添加一个新字段，记录这次实际新增的数量，便于后续处理
        data['new_added'] = {
            'movies': new_movies,
            'tv_shows': new_tv_shows,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'batch_id': batch_id  # 保存本次批次ID
        }
    
    return data

def save_hidden_gems_data(data):
    """保存冷门佳片数据到文件"""
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(HIDDEN_GEMS_FILE, 'w', encoding='utf-8') as f:
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

def extract_subject_id(url):
    """从 URL 中提取豆瓣 ID"""
    match = re.search(r'subject/(\d+)', url)
    if match:
        return match.group(1)
    return None

def get_subject_info(subject_id, cookie, max_retries=3):
    """获取条目详细信息"""
    url = f'https://movie.douban.com/subject/{subject_id}/'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Cookie': cookie
    }
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                info = {}
                
                # 检查是否为电视剧
                is_tv = '的分集短评' in response.text
                info['type'] = 'tv' if is_tv else 'movie'
                
                # 获取 IMDb ID
                imdb_span = soup.find('span', string='IMDb:')
                if imdb_span and imdb_span.next_sibling:
                    info['imdb_id'] = imdb_span.next_sibling.strip()
                else:
                    info['imdb_id'] = ''
                
                # 获取年份
                year_span = soup.find('span', class_='year')
                if year_span:
                    year_text = year_span.text.strip('()')
                    info['year'] = year_text
                else:
                    info['year'] = ''
                
                # 获取导演
                info['director'] = []
                director_text = soup.find('a', rel='v:directedBy')
                if director_text:
                    info['director'].append(director_text.text.strip())
                
                # 获取主演
                info['actors'] = []
                actor_links = soup.find_all('a', rel='v:starring')
                for actor in actor_links[:3]:  # 只取前三个主演
                    info['actors'].append(actor.text.strip())
                
                # 获取类型
                info['genres'] = []
                genre_links = soup.find_all('span', property='v:genre')
                for genre in genre_links:
                    info['genres'].append(genre.text.strip())
                
                # 获取制片国家/地区
                info['region'] = ''
                region_text = soup.find(string=re.compile('制片国家/地区:'))
                if region_text and region_text.next_sibling:
                    info['region'] = region_text.next_sibling.strip()
                
                # 获取语言
                info['languages'] = ''
                language_text = soup.find(string=re.compile('语言:'))
                if language_text and language_text.next_sibling:
                    info['languages'] = language_text.next_sibling.strip()
                
                # 获取片长
                info['duration'] = ''
                duration_span = soup.find('span', property='v:runtime')
                if duration_span:
                    info['duration'] = duration_span.text.strip()
                
                # 获取上映日期
                info['release_date'] = ''
                release_date = soup.find('span', property='v:initialReleaseDate')
                if release_date:
                    info['release_date'] = release_date.text.strip()
                
                # 获取评分人数
                info['vote_count'] = ''
                votes = soup.find('span', property='v:votes')
                if votes:
                    info['vote_count'] = votes.text.strip()
                
                # 获取剧集信息
                info['episodes_info'] = {}
                if is_tv:
                    episode_info = soup.find('div', class_='episode_info')
                    if episode_info:
                        info['episodes_info']['count'] = episode_info.text.strip()
                    
                    episode_duration = soup.find(string=re.compile('单集片长:'))
                    if episode_duration and episode_duration.next_sibling:
                        info['episodes_info']['duration'] = episode_duration.next_sibling.strip()
                
                return info
                
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
    
    return None

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

def main():
    try:
        config = load_config()
        cookie = config.get('cookie', '')
        
        # 验证 cookie
        if not cookie:
            message = "❌ Cookie 未配置，请先配置 Cookie"
            print(message)
            send_telegram_message(message, config, False)
            return
            
        if not check_cookie_valid(cookie):
            message = "❌ Cookie 已失效，请更新 Cookie"
            print(message)
            send_telegram_message(message, config, False)
            return
        
        print("\n开始获取豆瓣冷门佳片数据...")
        
        # 解析数据
        data = parse_hidden_gems(cookie)
        
        # 生成统计信息
        movies_count = len(data['movies'])
        tv_shows_count = len(data['tv_shows'])
        
        # 获取本次运行实际新增的电影和剧集数量
        has_updates = data.get('has_updates', False)
        new_added = data.get('new_added', {'movies': 0, 'tv_shows': 0, 'batch_id': 0})
        new_movies_count = new_added.get('movies', 0)
        new_tv_shows_count = new_added.get('tv_shows', 0)
        current_batch_id = new_added.get('batch_id', 0)
        
        # 使用batch_id精确获取本次新增的条目
        new_movies = []
        new_tv_shows = []
        
        if has_updates and current_batch_id > 0:
            # 使用batch_id筛选本次新增的条目
            new_movies = [movie for movie in data['movies'] 
                         if movie.get('batch_id') == current_batch_id]
            new_tv_shows = [tv for tv in data['tv_shows'] 
                           if tv.get('batch_id') == current_batch_id]
            
            # 确认找到的条目数量与记录的数量一致
            if len(new_movies) != new_movies_count or len(new_tv_shows) != new_tv_shows_count:
                print(f"警告: 通过batch_id找到的条目数量({len(new_movies)}/{len(new_tv_shows)})与记录的数量({new_movies_count}/{new_tv_shows_count})不一致")
        
        # 生成通知消息
        message = (
            f"🎬 <b>豆瓣冷门佳片数据更新完成</b>\n\n"
        )
        
        # 根据实际新增数量展示消息
        if new_movies_count == 0 and new_tv_shows_count == 0:
            # 没有新内容时的消息
            message += "⚠️ 本次更新没有发现新的冷门佳片内容。\n\n"
        else:
            message += f"📊 本次新增: {new_movies_count} 部冷门佳片, {new_tv_shows_count} 部冷门剧集\n\n"
        
        message += (
            f"更新时间: {data['update_time']}\n"
            f"总佳片数: {movies_count} 部\n"
            f"总剧集数: {tv_shows_count} 部\n\n"
        )
        
        # 新增内容：添加新更新的电影信息
        if has_updates and (len(new_movies) > 0 or len(new_tv_shows) > 0):
            if new_movies:
                message += "<b>新增佳片:</b>\n"
                for movie in new_movies[:5]:  # 最多显示5部新电影
                    movie_link = movie.get('url', f"https://movie.douban.com/subject/{movie.get('id', '')}/")
                    message += f"• <a href='{movie_link}'>{movie['title']}</a> - ⭐{movie['rating']}\n"
                    movie['notified'] = True  # 标记为已通知
                    
                # 如果新电影超过5部，添加"等"字样
                if len(new_movies) > 5:
                    message += f"等 {len(new_movies)} 部新佳片\n"
                
                message += "\n"
            
            # 新增电视剧
            if new_tv_shows:
                message += "<b>新增剧集:</b>\n"
                for tv in new_tv_shows[:5]:  # 最多显示5部新剧集
                    tv_link = tv.get('url', f"https://movie.douban.com/subject/{tv.get('id', '')}/")
                    message += f"• <a href='{tv_link}'>{tv['title']}</a> - ⭐{tv['rating']}\n"
                    tv['notified'] = True  # 标记为已通知
                    
                # 如果新剧集超过5部，添加"等"字样
                if len(new_tv_shows) > 5:
                    message += f"等 {len(new_tv_shows)} 部新剧集\n"
                
                message += "\n"
            
            # 保存数据，确保标记的notified状态被保存
            save_hidden_gems_data(data)
            
        message += "<b>冷门佳片 TOP 5:</b>\n"
        
        # 添加冷门佳片信息，并添加链接
        for i, movie in enumerate(sorted(data['movies'], key=lambda x: float(x['rating'] or 0), reverse=True)[:5], 1):
            movie_link = movie.get('url', f"https://movie.douban.com/subject/{movie.get('id', '')}/")
            message += f"{i}. <a href='{movie_link}'>{movie['title']}</a> - ⭐{movie['rating']}\n"
            
        # 只有在有电视剧时才显示电视剧部分
        if tv_shows_count > 0:
            message += "\n<b>冷门剧集 TOP 5:</b>\n"
            
            # 添加冷门剧集信息，并添加链接
            for i, tv in enumerate(sorted(data['tv_shows'], key=lambda x: float(x['rating'] or 0), reverse=True)[:5], 1):
                tv_link = tv.get('url', f"https://movie.douban.com/subject/{tv.get('id', '')}/")
                message += f"{i}. <a href='{tv_link}'>{tv['title']}</a> - ⭐{tv['rating']}\n"
        
        # 发送 Telegram 通知
        # 根据实际是否有新增条目决定has_new_content参数
        has_new_content = new_movies_count > 0 or new_tv_shows_count > 0
        send_telegram_message(message, config, has_new_content)
        
        print(f"\n数据获取完成！总计 {movies_count} 部冷门佳片和 {tv_shows_count} 部冷门剧集")
        print(f"本次新增: {new_movies_count} 部冷门佳片, {new_tv_shows_count} 部冷门剧集")
        
    except Exception as e:
        error_message = f"❌ 获取豆瓣冷门佳片数据时出错: {str(e)}"
        print(error_message)
        send_telegram_message(error_message, config, False)

if __name__ == "__main__":
    main() 