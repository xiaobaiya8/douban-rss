import json
import requests
from bs4 import BeautifulSoup
import time
import os
import re
import random
# 导入豆瓣工具模块
from src.utils.douban_utils import extract_subject_id, load_config, check_cookie_valid, send_telegram_message, make_douban_headers, get_api_data, parse_api_item, load_json_data, save_json_data

# 获取配置目录
CONFIG_DIR = os.getenv('CONFIG_DIR', 'config')
CONFIG_FILE = os.path.join(CONFIG_DIR, 'config.json')
HOT_MOVIES_FILE = os.path.join(CONFIG_DIR, 'hot_movies.json')

def load_hot_data():
    """加载现有的热门数据"""
    return load_json_data(HOT_MOVIES_FILE)

def get_douban_home(cookie):
    """获取豆瓣首页内容"""
    url = 'https://movie.douban.com/'
    headers = make_douban_headers(cookie)
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.text
    else:
        raise requests.RequestException(f"获取HTML失败: HTTP {response.status_code}")

def get_douban_movies(cookie):
    """获取豆瓣热门电影数据"""
    return get_api_data('movie', '热门', cookie)

def get_douban_tv(cookie):
    """获取豆瓣热门电视剧数据"""
    return get_api_data('tv', '热门', cookie)

def parse_hot_movies(cookie):
    """解析热门电影和电视剧数据"""
    # 加载现有数据
    data = load_hot_data()
    
    # 初始化计数器
    new_movies = 0
    new_tv_shows = 0
    
    # 生成本次更新的批次ID，用于标记这次添加的电影
    batch_id = int(time.time())
    
    # 重置new_added信息，确保每次运行都是从零开始
    data['has_updates'] = False
    data['new_added'] = {
        'movies': 0,
        'tv_shows': 0,
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'batch_id': batch_id
    }
    
    # 获取热门电影数据
    movies_data = get_douban_movies(cookie)
    if movies_data and 'subjects' in movies_data:
        print(f"找到 {len(movies_data['subjects'])} 个热门电影")
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
                save_hot_data(data)
                print(f"已保存新条目: {result['title']}")
                    
            # 添加随机延迟
            delay = random.uniform(3, 7)
            print(f"等待 {delay:.1f} 秒后继续...")
            time.sleep(delay)
    
    # 获取热门电视剧数据
    tv_data = get_douban_tv(cookie)
    if tv_data and 'subjects' in tv_data:
        print(f"找到 {len(tv_data['subjects'])} 个热门电视剧")
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
                save_hot_data(data)
                print(f"已保存新条目: {result['title']}")
                    
            # 添加随机延迟
            delay = random.uniform(3, 7)
            print(f"等待 {delay:.1f} 秒后继续...")
            time.sleep(delay)
    
    if new_movies == 0 and new_tv_shows == 0:
        print("没有发现新的内容，无需更新")
        data['has_updates'] = False
    else:
        print(f"新增 {new_movies} 部热门电影和 {new_tv_shows} 部热门电视剧")
        data['has_updates'] = True
        # 添加一个新字段，记录这次实际新增的数量，便于后续处理
        data['new_added'] = {
            'movies': new_movies,
            'tv_shows': new_tv_shows,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'batch_id': batch_id  # 保存本次批次ID
        }
    
    return data

def save_hot_data(data):
    """保存热门数据到文件"""
    save_json_data(data, HOT_MOVIES_FILE)

def send_telegram_message(message, config, has_new_content=False):
    """发送 Telegram 消息"""
    # 直接调用导入的函数，而不是自己
    from src.utils.douban_utils import send_telegram_message as utils_send_telegram_message
    utils_send_telegram_message(message, config, has_new_content)

def check_cookie_valid(cookie):
    """检查 cookie 是否有效"""
    # 使用从utils导入的check_cookie_valid函数，添加别名避免递归
    from src.utils.douban_utils import check_cookie_valid as utils_check_cookie_valid
    return utils_check_cookie_valid(cookie)

# 使用工具模块的函数
# 以下代码可能导致递归，已通过直接导入解决问题
# extract_subject_id = extract_subject_id

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
        
        print("\n开始获取豆瓣热门数据...")
        
        # 解析数据
        data = parse_hot_movies(cookie)
        
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
            f"🎬 <b>豆瓣热门数据更新完成</b>\n\n"
        )
        
        # 根据实际新增数量展示消息
        if new_movies_count == 0 and new_tv_shows_count == 0:
            # 没有新内容时的消息
            message += "⚠️ 本次更新没有发现新的热门内容。\n\n"
        else:
            message += f"📊 本次新增: {new_movies_count} 部热门电影, {new_tv_shows_count} 部热门剧集\n\n"
        
        message += (
            f"更新时间: {data['update_time']}\n"
            f"总电影数: {movies_count} 部\n"
            f"总剧集数: {tv_shows_count} 部\n\n"
        )
        
        # 新增内容：添加新更新的电影信息
        if has_updates and (len(new_movies) > 0 or len(new_tv_shows) > 0):
            # 显示新增的电影
            if new_movies:
                message += "<b>新增热门电影:</b>\n"
                for movie in new_movies[:5]:  # 最多显示5部新电影
                    movie_link = movie.get('url', f"https://movie.douban.com/subject/{movie.get('id', '')}/")
                    message += f"• <a href='{movie_link}'>{movie['title']}</a> - ⭐{movie['rating']}\n"
                    movie['notified'] = True  # 标记为已通知
                    
                # 如果新电影超过5部，添加"等"字样
                if len(new_movies) > 5:
                    message += f"等 {len(new_movies)} 部新热门电影\n"
                
                message += "\n"
            
            # 显示新增的剧集
            if new_tv_shows:
                message += "<b>新增热门剧集:</b>\n"
                for tv in new_tv_shows[:5]:  # 最多显示5部新剧集
                    tv_link = tv.get('url', f"https://movie.douban.com/subject/{tv.get('id', '')}/")
                    message += f"• <a href='{tv_link}'>{tv['title']}</a> - ⭐{tv['rating']}\n"
                    tv['notified'] = True  # 标记为已通知
                    
                # 如果新剧集超过5部，添加"等"字样
                if len(new_tv_shows) > 5:
                    message += f"等 {len(new_tv_shows)} 部新热门剧集\n"
                
                message += "\n"
            
            # 保存数据，确保标记的notified状态被保存
            save_hot_data(data)
            
        message += "<b>热门电影 TOP 5:</b>\n"
        
        # 添加热门电影信息，并添加链接
        for i, movie in enumerate(sorted(data['movies'], key=lambda x: float(x['rating'] or 0), reverse=True)[:5], 1):
            movie_link = movie.get('url', f"https://movie.douban.com/subject/{movie.get('id', '')}/")
            message += f"{i}. <a href='{movie_link}'>{movie['title']}</a> - ⭐{movie['rating']}\n"
            
        # 只有在有电视剧时才显示电视剧部分
        if tv_shows_count > 0:
            message += "\n<b>热门剧集 TOP 5:</b>\n"
            
            # 添加热门剧集信息，并添加链接
            for i, tv in enumerate(sorted(data['tv_shows'], key=lambda x: float(x['rating'] or 0), reverse=True)[:5], 1):
                tv_link = tv.get('url', f"https://movie.douban.com/subject/{tv.get('id', '')}/")
                message += f"{i}. <a href='{tv_link}'>{tv['title']}</a> - ⭐{tv['rating']}\n"
        
        # 发送 Telegram 通知
        # 根据实际是否有新增条目决定has_new_content参数
        has_new_content = new_movies_count > 0 or new_tv_shows_count > 0
        send_telegram_message(message, config, has_new_content)
        
        print(f"\n数据获取完成！总计 {movies_count} 部热门电影和 {tv_shows_count} 部热门电视剧")
        print(f"本次新增: {new_movies_count} 部热门电影, {new_tv_shows_count} 部热门剧集")
        
    except Exception as e:
        error_message = f"❌ 获取豆瓣热门数据时出错: {str(e)}"
        print(error_message)
        send_telegram_message(error_message, config, False)

if __name__ == "__main__":
    main() 