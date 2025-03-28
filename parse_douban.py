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
MOVIES_FILE = os.path.join(CONFIG_DIR, 'movies.json')

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
            
            # 随机延迟1-3秒
            delay = random.uniform(1, 3)
            time.sleep(delay)
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 输出原始数据，查看页面结构
                print("\n=== 页面信息 ===")
                info_div = soup.find('div', {'id': 'info'})
                if info_div:
                    print(info_div.prettify())
                else:
                    print("未找到info div")
                
                # 获取IMDB ID - 方法1：从链接获取
                imdb_link = soup.find('a', {'href': re.compile(r'www\.imdb\.com/title/(tt\d+)')})
                imdb_id = None
                if imdb_link:
                    print("\n=== IMDB链接 ===")
                    print(imdb_link.prettify())
                    match = re.search(r'tt\d+', imdb_link['href'])
                    if match:
                        imdb_id = match.group()
                        print(f"从链接找到IMDB ID: {imdb_id}")
                
                # 获取IMDB ID - 方法2：从文本获取
                if not imdb_id and info_div:
                    # 先找到IMDb:标签
                    imdb_span = info_div.find('span', text=re.compile(r'IMDb:'))
                    if imdb_span:
                        # 获取IMDb标签后面的文本
                        imdb_text = imdb_span.next_sibling
                        if imdb_text:
                            match = re.search(r'tt\d+', imdb_text.strip())
                            if match:
                                imdb_id = match.group()
                                print(f"从文本找到IMDB ID: {imdb_id}")
                
                # 查找"谁在看"标题来判断类型
                others_interests = soup.find('div', {'id': 'subject-others-interests'})
                if others_interests:
                    title = others_interests.find('i')
                    if title:
                        title_text = title.text.strip()
                        print(f"\n=== 页面标题 ===")
                        print(title_text)
                        # 根据标题判断类型
                        if '这部剧集' in title_text:
                            media_type = 'tv'
                        elif '这部电影' in title_text:
                            media_type = 'movie'
                        else:
                            # 如果无法从标题判断，则检查类型标签
                            genre_span = info_div.find('span', text='类型:') if info_div else None
                            if genre_span:
                                genre = genre_span.find_next('span', property='v:genre')
                                if genre and genre.text.strip() in ['真人秀', '纪录片', '综艺']:
                                    media_type = 'tv'
                                else:
                                    media_type = 'movie'
                            else:
                                media_type = 'movie'  # 默认为电影
                else:
                    # 如果找不到"谁在看"区域，使用类型标签判断
                    genre_span = info_div.find('span', text='类型:') if info_div else None
                    if genre_span:
                        genre = genre_span.find_next('span', property='v:genre')
                        if genre and genre.text.strip() in ['真人秀', '纪录片', '综艺']:
                            media_type = 'tv'
                        else:
                            media_type = 'movie'
                    else:
                        media_type = 'movie'  # 默认为电影
                    
                print(f"\n条目 {subject_id} 的类型为: {media_type}")
                if imdb_id:
                    print(f"IMDB ID为: {imdb_id}")
                
                return {
                    'type': media_type,
                    'imdb_id': imdb_id
                }
            else:
                print(f"获取条目 {subject_id} 失败: HTTP {response.status_code}")
                if attempt < max_retries - 1:
                    print(f"将在 3 秒后重试...")
                    time.sleep(3)
                    continue
                else:
                    raise requests.RequestException(f"获取条目信息失败: HTTP {response.status_code}")
                    
        except Exception as e:
            print(f"获取条目 {subject_id} 时出错: {e}")
            if attempt < max_retries - 1:
                print(f"将在 3 秒后重试...")
                time.sleep(3)
                continue
            else:
                raise
    
    return {
        'type': 'movie',  # 默认为电影
        'imdb_id': None
    }

def extract_subject_id(url):
    """从URL中提取豆瓣ID"""
    match = re.search(r'subject/(\d+)', url)
    return match.group(1) if match else None

def load_cache():
    """加载缓存数据"""
    try:
        if os.path.exists('movies.json'):
            with open('movies.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 构建缓存字典 {title: {type, imdb_id}}
                cache = {}
                for item in data.get('movies', []) + data.get('tv_shows', []):
                    cache[item['title']] = {
                        'type': item['type'],
                        'imdb_id': item['imdb_id'],
                        'info': item['info']
                    }
                print(f"已加载缓存数据: {len(cache)} 条记录")
                return cache
    except Exception as e:
        print(f"加载缓存失败: {e}")
    return {}

def parse_movie_item(item, cache, cookie):
    """解析电影条目"""
    # 获取标题
    title_elem = item.find('li', class_='title')
    if not title_elem or not title_elem.find('em'):
        return None
        
    # 拆分主标题和副标题
    full_title = title_elem.find('em').text.strip()
    titles = full_title.split(' / ', 1)
    title = titles[0].strip()  # 主标题
    subtitle = titles[1].strip() if len(titles) > 1 else ''  # 副标题
    
    # 检查缓存
    if title in cache:
        print(f"\n从缓存获取: {title}")
        cached_data = cache[title]
        media_type = cached_data['type']
        imdb_id = cached_data['imdb_id']
    else:
        print(f"\n未找到缓存，需要请求: {title}")
        # 获取链接和ID
        url = ''
        link_elem = item.find('a', href=True)
        if link_elem:
            url = link_elem['href']
        
        # 从URL中提取ID并获取类型
        subject_id = extract_subject_id(url)
        if subject_id:
            print(f"处理条目: {title} (ID: {subject_id})")
            info = get_subject_info(subject_id, cookie)
            media_type = info['type']
            imdb_id = info['imdb_id']
        else:
            print(f"警告: 无法从URL {url} 中提取ID")
            media_type = 'movie'
            imdb_id = None
    
    # 获取其他信息
    intro_elem = item.find('li', class_='intro')
    info = intro_elem.text.strip().split(' / ') if intro_elem else []
    
    date_elem = item.find('span', class_='date')
    date = date_elem.text.strip() if date_elem else ''
    
    img_elem = item.find('img')
    cover_url = img_elem.get('src', '') if img_elem else ''
    
    url = ''
    link_elem = item.find('a', href=True)
    if link_elem:
        url = link_elem['href']
    
    playable = bool(item.find('span', class_='playable'))
    
    subject_id = extract_subject_id(url)
    
    return {
        "title": title,
        "subtitle": subtitle,
        "full_title": full_title,
        "info": info,
        "date_added": date,
        "cover_url": cover_url,
        "url": url,
        "playable": playable,
        "type": media_type,
        "id": subject_id,
        "imdb_id": imdb_id
    }

def load_all_data():
    """加载所有用户的数据"""
    try:
        if os.path.exists(MOVIES_FILE):
            with open(MOVIES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"加载数据失败: {e}")
    return {}

def save_all_data(all_data):
    """保存所有数据到文件"""
    # 确保配置目录存在
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(MOVIES_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

def is_duplicate(title, user_id, all_data):
    """检查条目是否重复"""
    user_data = all_data.get(user_id, {'movies': [], 'tv_shows': []})
    all_items = user_data['movies'] + user_data['tv_shows']
    
    # 同时检查主标题和完整标题
    for item in all_items:
        if title == item.get('title') or title == item.get('full_title'):
            return True
    return False

def generate_movies_json(html_content, user_id, all_data, cookie):
    """解析HTML内容并生成JSON数据"""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 获取或初始化用户数据
    user_data = all_data.get(user_id, {'movies': [], 'tv_shows': []})
    movies = user_data['movies']
    tv_shows = user_data['tv_shows']
    
    # 找到电影列表容器
    items = soup.find_all('div', class_='item')
    total_items = len(items)
    new_items = 0
    
    print(f"\n开始处理 {total_items} 个条目...")
    
    for index, item in enumerate(items, 1):
        # 获取标题
        title_elem = item.find('li', class_='title')
        if title_elem and title_elem.find('em'):
            full_title = title_elem.find('em').text.strip()
            titles = full_title.split(' / ', 1)
            title = titles[0].strip()
            
            # 检查是否重复
            if is_duplicate(title, user_id, all_data):
                print(f"\n条目已存在，跳过: {title}")
                continue
                
            print(f"\n处理新条目: {title}")
            new_items += 1
            data = parse_movie_item(item, {}, cookie)
            
            # 设置notified为False，表示这是一个新条目需要通知
            data['notified'] = False
            
            # 根据类型添加到对应列表
            if data["type"] == "movie":
                movies.append(data)
                print(f"已添加到电影列表: {data['title']}")
            else:
                tv_shows.append(data)
                print(f"已添加到电视剧列表: {data['title']}")
            
            # 实时保存数据
            all_data[user_id] = {'movies': movies, 'tv_shows': tv_shows}
            save_all_data(all_data)
            print("数据已保存")
            
            # 只在处理新条目时添加延迟
            if index < total_items:
                delay = random.uniform(1, 3)
                print(f"等待 {delay:.1f} 秒后继续...")
                time.sleep(delay)
    
    print(f"\n处理完成! 发现 {new_items} 个新条目")
    print(f"当前用户共有 {len(movies)} 部电影, {len(tv_shows)} 部电视剧")
    
    # 添加更新时间和新条目数量
    result = {
        'movies': movies,
        'tv_shows': tv_shows,
        'update_time': time.strftime('%Y-%m-%d %H:%M:%S'),
        'new_items_count': new_items
    }
    
    return result

def get_douban_html(user_id, cookie):
    """获取豆瓣HTML内容"""
    url = f'https://movie.douban.com/people/{user_id}/wish'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Cookie': cookie
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.text
    else:
        raise requests.RequestException(f"获取HTML失败: HTTP {response.status_code}")

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

def fetch_user_data(user_id, cookie):
    """获取用户数据"""
    try:
        print(f"\n处理用户 {user_id} 的数据...")
        
        # 获取HTML内容
        html_file = f'douban_{user_id}.html'
        if os.path.exists(html_file):
            os.remove(html_file)
            print(f"已删除旧的HTML文件: {html_file}")
        
        print("从网页获取数据...")
        html_content = get_douban_html(user_id, cookie)
        
        # 保存HTML内容到文件
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
            print(f"已保存新的HTML文件: {html_file}")
        
        print("开始解析数据...")
        all_data = load_all_data()
        user_data = generate_movies_json(html_content, user_id, all_data, cookie)
        
        # 检查是否有更新
        has_updates = user_data['new_items_count'] > 0
        
        user_data['has_updates'] = has_updates
        all_data[user_id] = user_data
        save_all_data(all_data)
        
        if has_updates:
            print(f"用户 {user_id} 数据有更新")
        else:
            print(f"用户 {user_id} 数据无变化")
        
        return has_updates
        
    except Exception as e:
        print(f"处理用户 {user_id} 时出错: {e}")
        raise

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
    
    # 检查 bot_token 和 chat_id 是否有效
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
        response = requests.post(url, json=data, timeout=10)  # 添加超时设置
        
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

def cleanup_temp_files():
    """清理临时文件"""
    try:
        # 删除所有 douban_*.html 文件
        for file in os.listdir():
            if file.startswith('douban_') and file.endswith('.html'):
                os.remove(file)
                print(f"已删除临时文件: {file}")
    except Exception as e:
        print(f"清理临时文件时出错: {e}")

def check_cookie_valid(cookie):
    """检查 cookie 是否有效"""
    try:
        # 使用一个简单的豆瓣请求来测试 cookie
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Cookie': cookie
        }
        
        # 尝试访问豆瓣主页
        response = requests.get('https://www.douban.com', headers=headers, timeout=10)
        
        # 检查是否需要登录
        if 'login' in response.url or response.status_code == 403:
            print("\n❌ Cookie 已失效，需要重新登录")
            return False
            
        print("\n✅ Cookie 验证通过")
        return True
        
    except Exception as e:
        print(f"\n❌ 验证 Cookie 时出错: {e}")
        return False

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
        
        print("\n开始获取豆瓣想看数据...")
        
        # 记录是否有任何用户数据更新
        any_updates = False
        # 获取所有数据
        all_data = load_all_data()
        
        # 处理每个用户的数据
        users = config.get('users', [])
        total_users = len(users)
        
        for i, user in enumerate(users, 1):
            user_id = user['id']
            note = user.get('note', '')
            try:
                print(f"\n[{i}/{total_users}] 处理用户: {note or user_id}")
                
                # 获取更新
                has_updates = fetch_user_data(user_id, cookie)
                
                if has_updates:
                    any_updates = True
                
                # 如果不是最后一个用户，添加随机延迟
                if i < total_users:
                    delay = random.uniform(1, 3)  # 1-3秒的随机延迟
                    print(f"等待 {delay:.1f} 秒后处理下一个用户...")
                    time.sleep(delay)
                    
            except Exception as e:
                print(f"处理用户 {user_id} 时出错: {e}")
                continue
        
        # 构建消息内容，但根据情况决定是否发送
        # 无论是否有更新，都构建消息
        message = "🎬 <b>豆瓣想看更新提醒</b>\n\n"
        
        # 重新加载所有数据，确保获取最新的数据
        all_data = load_all_data()
        
        # 检查是否有未通知的条目
        has_unnotified_items = False
        for user_id, user_data in all_data.items():
            movies = user_data.get('movies', [])
            tv_shows = user_data.get('tv_shows', [])
            unnotified_items = [item for item in movies + tv_shows if not item.get('notified', False)]
            if unnotified_items:
                has_unnotified_items = True
                break
        
        if not has_unnotified_items:
            # 没有新内容时的消息
            message += "⚠️ 本次更新没有发现新的想看内容。\n\n"
        
        message += f"更新时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        if has_unnotified_items:
            # 整理每个用户的未通知条目
            for user in users:
                user_id = user['id']
                note = user.get('note', '')
                user_data = all_data.get(user_id, {})
                movies = user_data.get('movies', [])
                tv_shows = user_data.get('tv_shows', [])
                
                # 获取未通知的条目
                unnotified_items = [item for item in movies + tv_shows if not item.get('notified', False)]
                
                if unnotified_items:
                    message += f"用户 {note or user_id} 新增想看:\n"
                    
                    for item in unnotified_items:
                        # 标记为已通知
                        item['notified'] = True
                        
                        # 获取年份信息
                        year = item.get('year', '')
                        
                        # 使用主标题和副标题，添加链接
                        url = item.get('url', f"https://movie.douban.com/subject/{item.get('id', '')}/")
                        message += f"• <a href=\"{url}\">{item['title']}"
                        if item.get('subtitle'):
                            message += f" ({item['subtitle']})"
                        if year:
                            message += f" [{year}]"
                        message += "</a>\n"
                    
                    message += "\n"
            
            # 保存更新后的数据
            save_all_data(all_data)
        else:
            # 添加统计信息
            total_movies = sum(len(user_data.get('movies', [])) for user_data in all_data.values())
            total_tv_shows = sum(len(user_data.get('tv_shows', [])) for user_data in all_data.values())
            
            message += f"当前总计追踪:\n"
            message += f"• {total_movies} 部电影\n"
            message += f"• {total_tv_shows} 部剧集\n"
        
        # 发送 Telegram 通知
        send_telegram_message(message, config, has_unnotified_items)
        
        print("\n数据获取完成！")
        
    except Exception as e:
        error_message = f"❌ 获取豆瓣想看数据时出错: {str(e)}"
        print(error_message)
        send_telegram_message(error_message, config, False)
    finally:
        # 无论成功还是失败，都清理临时文件
        cleanup_temp_files()

if __name__ == "__main__":
    main() 