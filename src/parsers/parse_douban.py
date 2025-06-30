import json
import requests
from bs4 import BeautifulSoup
import time
import os
import re
import random
import traceback
# 导入豆瓣工具模块
from src.utils.douban_utils import extract_subject_id, load_config, check_cookie_valid, send_telegram_message, send_wecom_message, make_douban_headers, load_json_data, save_json_data, get_subject_info_with_cache, migrate_legacy_cache_data, load_subject_cache, is_cache_expired

# 获取配置目录
CONFIG_DIR = os.getenv('CONFIG_DIR', 'config')
CONFIG_FILE = os.path.join(CONFIG_DIR, 'config.json')
MOVIES_FILE = os.path.join(CONFIG_DIR, 'movies.json')



def parse_movie_item(item, cookie):
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
    
    # 获取链接和ID
    url = ''
    link_elem = item.find('a', href=True)
    if link_elem:
        url = link_elem['href']
    
    # 从URL中提取ID并获取类型
    subject_id = extract_subject_id(url)
    if subject_id:
        print(f"处理条目: {title} (ID: {subject_id})")
        info = get_subject_info_with_cache(subject_id, cookie)
        if info:
            media_type = info['type']
            imdb_id = info['imdb_id']
        else:
            print(f"警告: 无法获取条目信息")
            media_type = 'movie'
            imdb_id = None
    else:
        print(f"警告: 无法从URL提取ID")
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
    return load_json_data(MOVIES_FILE, {})

def save_all_data(all_data):
    """保存所有数据到文件"""
    save_json_data(all_data, MOVIES_FILE)

def check_item_status(title, user_id, all_data):
    """检查条目状态：新增、重复、或需要更新缓存
    
    返回值:
        - ('new', None): 全新条目
        - ('duplicate', item): 重复条目，缓存未过期
        - ('cache_expired', item): 重复条目，但缓存已过期，需要更新
    """
    user_data = all_data.get(user_id, {'movies': [], 'tv_shows': []})
    all_items = user_data['movies'] + user_data['tv_shows']
    
    # 同时检查主标题和完整标题
    for item in all_items:
        if title == item.get('title') or title == item.get('full_title'):
            # 找到重复条目，检查其缓存是否过期
            subject_id = item.get('id')
            if subject_id:
                # 检查缓存是否过期
                cache_data = load_subject_cache()
                if subject_id in cache_data:
                    cached_at = cache_data[subject_id].get('cached_at')
                    if is_cache_expired(cached_at):
                        print(f"条目 {title} 缓存已过期，将更新信息（不会发送通知）")
                        return ('cache_expired', item)
                
            return ('duplicate', item)  # 缓存未过期或无缓存信息，算作重复
    
    return ('new', None)  # 全新条目

def get_douban_html(user_id, cookie, list_type='wish', page=1):
    """获取豆瓣HTML内容
    
    list_type: 列表类型，可选值：
    - wish: 想看
    - do: 在看
    - collect: 已看
    page: 页码，默认为第1页
    """
    # 计算起始位置：每页15个条目
    start = (page - 1) * 15
    
    # 根据列表类型确定URL
    if list_type == 'do':
        url = f'https://movie.douban.com/people/{user_id}/do?start={start}&sort=time&rating=all&mode=grid&type=all&filter=all'
    elif list_type == 'collect':
        url = f'https://movie.douban.com/people/{user_id}/collect?start={start}&sort=time&rating=all&mode=grid&type=all&filter=all'
    else:  # 默认为wish
        url = f'https://movie.douban.com/people/{user_id}/wish?start={start}&sort=time&rating=all&mode=grid&type=all&filter=all'
        
    headers = make_douban_headers(cookie)
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.text
    else:
        raise requests.RequestException(f"获取HTML失败: HTTP {response.status_code}")

def fetch_user_data(user_id, cookie, user_config=None):
    """获取用户数据"""
    try:
        print(f"处理用户 {user_id} 的数据...")
        user_note = user_config.get('note', '') if user_config else ''
        max_pages = user_config.get('pages', 1) if user_config else 1
        
        # 确定需要监控的列表类型
        list_types = []
        if not user_config:
            # 默认只监控想看列表
            list_types = ['wish']
        else:
            if user_config.get('monitor_wish', True):
                list_types.append('wish')
            if user_config.get('monitor_do'):
                list_types.append('do')
            if user_config.get('monitor_collect'):
                list_types.append('collect')
        
        all_data = load_all_data()
        has_updates = False
        
        print(f"用户 {user_note or user_id} 监控列表类型: {', '.join(list_types)}，抓取 {max_pages} 页")
        
        for list_type in list_types:
            try:
                print(f"获取 {list_type} 列表数据中...")
                
                # 获取所有页面的HTML内容
                all_html_content = ""
                for page in range(1, max_pages + 1):
                    print(f"  获取第 {page}/{max_pages} 页...")
                    
                    html_content = get_douban_html(user_id, cookie, list_type, page)
                    all_html_content += html_content
                    
                    # 如果不是最后一页，添加延迟
                    if page < max_pages:
                        delay = random.uniform(1, 3)
                        print(f"  等待 {delay:.1f} 秒后获取下一页...")
                        time.sleep(delay)
                
                # 保存合并后的HTML内容到文件但不输出提示
                html_file = f'douban_{user_id}_{list_type}.html'
                if os.path.exists(html_file):
                    os.remove(html_file)
                
                with open(html_file, 'w', encoding='utf-8') as f:
                    f.write(all_html_content)
                
                print(f"解析 {list_type} 列表数据中...")
                user_data = generate_movies_json(all_html_content, user_id, all_data, cookie, list_type)
                
                # 检查是否有更新
                has_list_updates = user_data['new_items_count'] > 0
                has_updates = has_updates or has_list_updates
                
                # 如果这个列表有更新才保存数据
                if has_list_updates:
                    print(f"用户 {user_id} 的 {list_type} 列表有更新: {user_data['new_items_count']} 个新条目")
                else:
                    print(f"用户 {user_id} 的 {list_type} 列表无变化")
                
                # 添加一个延迟，避免请求过于频繁
                if list_type != list_types[-1]:
                    delay = random.uniform(1, 3)
                    print(f"等待 {delay:.1f} 秒后继续获取下一个列表...")
                    time.sleep(delay)
                    
            except Exception as e:
                print(f"处理用户 {user_id} 的 {list_type} 列表时出错: {e}")
        
        # 更新用户数据的标记
        user_data = all_data.get(user_id, {})
        user_data['has_updates'] = has_updates
        user_data['update_time'] = time.strftime('%Y-%m-%d %H:%M:%S')
        all_data[user_id] = user_data
        save_all_data(all_data)
        
        return has_updates
        
    except Exception as e:
        print(f"处理用户 {user_id} 时出错: {e}")
        raise

def generate_movies_json(html_content, user_id, all_data, cookie, list_type='wish'):
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
    
    print(f"开始处理 {list_type} 列表中的 {total_items} 个条目...")
    
    for index, item in enumerate(items, 1):
        # 获取标题
        title_elem = item.find('li', class_='title')
        if title_elem and title_elem.find('em'):
            full_title = title_elem.find('em').text.strip()
            titles = full_title.split(' / ', 1)
            title = titles[0].strip()
            
            # 检查条目状态
            status, existing_item = check_item_status(title, user_id, all_data)
            
            if status == 'duplicate':
                print(f"条目已存在，跳过: {title}")
                continue
            elif status == 'cache_expired':
                # 缓存过期，需要更新信息但不算新增
                print(f"处理缓存过期条目 [{index}/{total_items}]: {title}")
                
                # 获取更新后的信息
                data = parse_movie_item(item, cookie)
                
                # 保留原有的notified状态，不改变通知状态
                data['notified'] = existing_item.get('notified', True)  # 默认为True，表示不需要通知
                
                # 添加来源标记
                data['source'] = list_type
                
                # 从原列表中移除旧条目
                if existing_item in user_data['movies']:
                    user_data['movies'].remove(existing_item)
                elif existing_item in user_data['tv_shows']:
                    user_data['tv_shows'].remove(existing_item)
                
                # 添加更新后的条目
                if data["type"] == "movie":
                    movies.append(data)
                    print(f"更新电影信息: {data['title']} (来自{list_type}列表)")
                else:
                    tv_shows.append(data)
                    print(f"更新剧集信息: {data['title']} (来自{list_type}列表)")
                
                # 实时保存数据
                all_data[user_id] = {'movies': movies, 'tv_shows': tv_shows}
                save_all_data(all_data)
                
                # 缓存更新不算新增，不增加new_items计数
                
            elif status == 'new':
                # 全新条目
                print(f"处理新条目 [{index}/{total_items}]: {title}")
                new_items += 1
                data = parse_movie_item(item, cookie)
                
                # 设置notified为False，表示这是一个新条目需要通知
                data['notified'] = False
                
                # 添加来源标记，方便后续区分数据来源
                data['source'] = list_type
                
                # 根据类型添加到对应列表
                if data["type"] == "movie":
                    movies.append(data)
                    print(f"添加电影: {data['title']} (来自{list_type}列表)")
                else:
                    tv_shows.append(data)
                    print(f"添加剧集: {data['title']} (来自{list_type}列表)")
                
                # 实时保存数据
                all_data[user_id] = {'movies': movies, 'tv_shows': tv_shows}
                save_all_data(all_data)
            
            # 只在处理新条目时添加延迟
            if index < total_items:
                delay = random.uniform(1, 3)
                print(f"等待 {delay:.1f} 秒后继续...")
                time.sleep(delay)
    
    print(f"{list_type}列表处理完成! 发现 {new_items} 个新条目，当前用户共有 {len(movies)} 部电影, {len(tv_shows)} 部电视剧")
    
    # 添加更新时间和新条目数量
    result = {
        'movies': movies,
        'tv_shows': tv_shows,
        'update_time': time.strftime('%Y-%m-%d %H:%M:%S'),
        'new_items_count': new_items
    }
    
    return result

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

def main():
    try:
        # 在开始时进行缓存迁移
        print("检查并迁移旧缓存数据...")
        migrate_legacy_cache_data()
        
        config = load_config()
        cookie = config.get('cookie', '')
        
        # 验证 cookie
        if not cookie:
            message = "❌ Cookie 未配置，请先配置 Cookie"
            print(message)
            send_telegram_message(message, config, False)
            send_wecom_message(message, config, False)
            return
            
        if not check_cookie_valid(cookie):
            message = "❌ Cookie 已失效，请更新 Cookie"
            print(message)
            send_telegram_message(message, config, False)
            send_wecom_message(message, config, False)
            return
        
        print("开始获取豆瓣用户数据...")
        
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
                print(f"[{i}/{total_users}] 处理用户: {note or user_id}")
                
                # 获取更新，传入完整的用户配置
                has_updates = fetch_user_data(user_id, cookie, user)
                
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
        message = "🎬 *豆瓣电影/剧集更新提醒*\n\n"
        
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
            message += "⚠️ 本次更新没有发现新的内容。\n\n"
        
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
                    message += f"用户 {note or user_id} 新增内容:\n"
                    
                    # 按列表类型分组
                    items_by_source = {
                        'wish': [],
                        'do': [],
                        'collect': []
                    }
                    
                    # 分组
                    for item in unnotified_items:
                        source = item.get('source', 'wish')  # 默认为wish
                        items_by_source[source].append(item)
                        
                        # 标记为已通知
                        item['notified'] = True
                    
                    # 按列表类型显示
                    source_names = {
                        'wish': '想看',
                        'do': '在看',
                        'collect': '已看'
                    }
                    
                    for source, items in items_by_source.items():
                        if items:
                            message += f"• *{source_names.get(source, '未知')}*:\n"
                            for item in items:
                                # 获取年份信息
                                year = item.get('year', '')
                                
                                # 使用主标题和副标题，添加链接
                                url = item.get('url', f"https://movie.douban.com/subject/{item.get('id', '')}/")
                                message += f"  - <a href=\"{url}\">{item['title']}"
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
        
        # 发送通知
        send_telegram_message(message, config, has_unnotified_items)
        send_wecom_message(message, config, has_unnotified_items)
        
        print("数据获取完成！")
        
    except Exception as e:
        error_message = f"❌ 获取豆瓣数据时出错: {str(e)}"
        print(error_message)
        send_telegram_message(error_message, config, False)
        send_wecom_message(error_message, config, False)
    finally:
        # 无论成功还是失败，都清理临时文件
        cleanup_temp_files()

if __name__ == "__main__":
    main() 