import json
import requests
import time
import os
import re
import random
# 导入豆瓣工具模块
from src.utils.douban_utils import extract_subject_id, load_config, check_cookie_valid, send_telegram_message, send_wecom_message, make_douban_headers, get_api_data, parse_api_item, load_json_data, save_json_data

# 获取配置目录
CONFIG_DIR = os.getenv('CONFIG_DIR', 'config')
CONFIG_FILE = os.path.join(CONFIG_DIR, 'config.json')
NEW_MOVIES_FILE = os.path.join(CONFIG_DIR, 'new_movies.json')

def load_new_data():
    """加载现有的最新电影数据"""
    return load_json_data(NEW_MOVIES_FILE)

def get_douban_new_movies(cookie):
    """获取豆瓣最新电影数据"""
    return get_api_data('movie', '最新', cookie)

def get_douban_new_tv(cookie):
    """获取豆瓣最新电视剧数据"""
    return get_api_data('tv', '最新', cookie)

def parse_new_movies(cookie):
    """解析最新电影和电视剧数据"""
    # 加载现有数据
    data = load_new_data()
    
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
        # 添加一个新字段，记录这次实际新增的数量，便于后续处理
        data['new_added'] = {
            'movies': new_movies,
            'tv_shows': new_tv_shows,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'batch_id': batch_id  # 保存本次批次ID
        }
    
    return data

def save_new_data(data):
    """保存最新数据到文件"""
    save_json_data(data, NEW_MOVIES_FILE)

def send_telegram_message(message, config, has_new_content=False):
    """发送Telegram消息，这是一个转发函数"""
    # 使用工具模块中的函数
    from src.utils.douban_utils import send_telegram_message as utils_send_telegram_message
    utils_send_telegram_message(message, config, has_new_content)
    
def send_wecom_message(message, config, has_new_content=False):
    """发送企业微信消息，这是一个转发函数"""
    from src.utils.douban_utils import send_wecom_message as utils_send_wecom_message
    utils_send_wecom_message(message, config, has_new_content)

# 使用工具模块的函数，以下代码可能导致递归，删除它
# extract_subject_id = extract_subject_id

def check_cookie_valid(cookie):
    """检查 cookie 是否有效"""
    # 使用从utils导入的check_cookie_valid函数，添加别名避免递归
    from src.utils.douban_utils import check_cookie_valid as utils_check_cookie_valid
    return utils_check_cookie_valid(cookie)

def main():
    try:
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
        
        print("\n开始获取豆瓣最新数据...")
        
        # 解析数据
        data = parse_new_movies(cookie)
        
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
            f"🎬 *豆瓣最新数据更新完成*\n\n"
        )

        # 根据实际新增数量展示消息
        if new_movies_count == 0 and new_tv_shows_count == 0:
            # 没有新内容时的消息
            message += "⚠️ 本次更新没有发现新的最新电影内容。\n\n"
        else:
            message += f"📊 本次新增: {new_movies_count} 部电影, {new_tv_shows_count} 部剧集\n\n"
        
        message += (
            f"更新时间: {data['update_time']}\n"
            f"总电影数: {movies_count} 部\n"
            f"总剧集数: {tv_shows_count} 部\n\n"
        )
        
        # 添加新更新的电影信息 - 只显示实际新增的电影
        if has_updates and (len(new_movies) > 0 or len(new_tv_shows) > 0):
            if new_movies:
                message += "*新增电影:*\n"
                for movie in new_movies[:5]:  # 最多显示5部新电影
                    movie_link = movie.get('url', f"https://movie.douban.com/subject/{movie.get('id', '')}/")
                    message += f"• <a href='{movie_link}'>{movie['title']}</a> - ⭐{movie['rating']}\n"
                    movie['notified'] = True  # 标记为已通知
                    
                # 如果新电影超过5部，添加"等"字样
                if len(new_movies) > 5:
                    message += f"等 {len(new_movies)} 部新电影\n"
                
                message += "\n"
            
            # 如果有新增剧集
            if new_tv_shows:
                message += "*新增剧集:*\n"
                for tv in new_tv_shows[:5]:  # 最多显示5部新剧集
                    tv_link = tv.get('url', f"https://movie.douban.com/subject/{tv.get('id', '')}/")
                    message += f"• <a href='{tv_link}'>{tv['title']}</a> - ⭐{tv['rating']}\n"
                    tv['notified'] = True  # 标记为已通知
                    
                # 如果新剧集超过5部，添加"等"字样
                if len(new_tv_shows) > 5:
                    message += f"等 {len(new_tv_shows)} 部新剧集\n"
                
                message += "\n"
                
            # 保存数据，确保notified状态被保存
            save_new_data(data)
            
        message += "*最新电影 TOP 5:*\n"
        
        # 添加最新电影信息
        for i, movie in enumerate(sorted(data['movies'], key=lambda x: float(x['rating'] or 0), reverse=True)[:5], 1):
            movie_link = movie.get('url', f"https://movie.douban.com/subject/{movie.get('id', '')}/")
            message += f"{i}. <a href='{movie_link}'>{movie['title']}</a> - ⭐{movie['rating']}\n"
            
        # 只有在有电视剧时才显示电视剧部分
        if tv_shows_count > 0:
            message += "\n*最新剧集 TOP 5:*\n"
            
            # 添加最新剧集信息
            for i, tv in enumerate(sorted(data['tv_shows'], key=lambda x: float(x['rating'] or 0), reverse=True)[:5], 1):
                tv_link = tv.get('url', f"https://movie.douban.com/subject/{tv.get('id', '')}/")
                message += f"{i}. <a href='{tv_link}'>{tv['title']}</a> - ⭐{tv['rating']}\n"
        
        # 发送通知 - 根据是否有新内容设置has_new_content参数
        send_telegram_message(message, config, has_updates)
        send_wecom_message(message, config, has_updates)
        
        print(f"\n数据获取完成！总计 {movies_count} 部最新电影和 {tv_shows_count} 部最新电视剧")
        print(f"本次新增: {new_movies_count} 部电影, {new_tv_shows_count} 部剧集")
        
    except Exception as e:
        error_message = f"❌ 获取豆瓣最新数据时出错: {str(e)}"
        print(error_message)
        send_telegram_message(error_message, config, False)
        send_wecom_message(error_message, config, False)
    finally:
        # 无论成功还是失败，都清理临时文件
        cleanup_temp_files()

if __name__ == "__main__":
    main() 