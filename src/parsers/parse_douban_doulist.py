import json
import requests
from bs4 import BeautifulSoup
import time
import os
import re
import random
# 导入豆瓣工具模块
from src.utils.douban_utils import extract_subject_id, load_config, check_cookie_valid, send_telegram_message, make_douban_headers, load_json_data, save_json_data, get_subject_info

# 获取配置目录
CONFIG_DIR = os.getenv('CONFIG_DIR', 'config')
CONFIG_FILE = os.path.join(CONFIG_DIR, 'config.json')
DOULIST_FILE = os.path.join(CONFIG_DIR, 'doulists.json')

def load_doulist_data():
    """加载现有的片单数据"""
    try:
        data = load_json_data(DOULIST_FILE, {"lists": {}, "update_time": ""})
        list_count = len(data.get("lists", {}))
        print(f"加载豆列数据成功: 包含 {list_count} 个片单")
        return data
    except Exception as e:
        print(f"加载豆列数据失败: {e}")
        return {"lists": {}, "update_time": ""}

def save_doulist_data(data):
    """保存片单数据"""
    try:
        if not data or not isinstance(data, dict):
            print(f"错误: 保存的数据格式不正确: {type(data)}")
            return False
            
        list_count = len(data.get("lists", {}))
        total_items = sum(len(doulist_data.get("items", [])) for doulist_id, doulist_data in data.get("lists", {}).items())
        
        save_json_data(data, DOULIST_FILE)
        print(f"豆列数据保存成功: {list_count} 个片单, {total_items} 个条目")
        return True
    except Exception as e:
        print(f"保存豆列数据失败: {e}")
        return False

def get_doulist_html(doulist_id, cookie, page=1):
    """获取片单HTML内容
    
    doulist_id: 片单ID
    page: 页码，默认为第1页
    """
    # 计算起始位置：每页25个条目
    start = (page - 1) * 25
    
    # 按时间排序，使用start参数而不是page参数
    url = f'https://www.douban.com/doulist/{doulist_id}/?start={start}&sort=time&playable=0&sub_type='
    headers = make_douban_headers(cookie)
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.text
    else:
        raise requests.RequestException(f"获取片单HTML失败: HTTP {response.status_code}")

def get_doulist_info(doulist_id, cookie):
    """获取片单基本信息"""
    try:
        html_content = get_doulist_html(doulist_id, cookie)
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 获取片单标题
        title_elem = soup.find('h1')
        title = title_elem.text.strip() if title_elem else f"豆列 {doulist_id}"
        
        # 获取片单描述
        desc_elem = soup.find('div', class_='doulist-about')
        description = desc_elem.text.strip() if desc_elem else ""
        
        # 获取作者信息
        author_elem = soup.select_one('.doulist-owner a')
        author_name = author_elem.text.strip() if author_elem else ""
        author_url = author_elem['href'] if author_elem and 'href' in author_elem.attrs else ""
        author_id = ""
        if author_url:
            match = re.search(r'people/([^/]+)', author_url)
            if match:
                author_id = match.group(1)
        
        return {
            "id": doulist_id,
            "title": title,
            "description": description,
            "author": {
                "id": author_id,
                "name": author_name,
                "url": author_url
            },
            "url": f"https://www.douban.com/doulist/{doulist_id}/?start=0&sort=time&playable=0&sub_type="
        }
    except Exception as e:
        print(f"获取片单信息时出错: {e}")
        return {
            "id": doulist_id,
            "title": f"豆列 {doulist_id}",
            "description": "",
            "author": {"id": "", "name": "", "url": ""},
            "url": f"https://www.douban.com/doulist/{doulist_id}/?start=0&sort=time&playable=0&sub_type="
        }

def is_movie_or_tv(item_url):
    """判断条目是否为电影/剧集"""
    return "movie.douban.com/subject/" in item_url

def parse_doulist_item(item, cookie):
    """解析片单中的单个条目"""
    try:
        # 获取链接和标题
        title_elem = item.select_one('.title a')
        if not title_elem:
            return None
            
        url = title_elem.get('href', '')
        title = title_elem.text.strip()
        
        # 跳过非电影/剧集条目
        if not is_movie_or_tv(url):
            return None
            
        # 获取封面图片
        img_elem = item.select_one('.post img')
        cover_url = img_elem.get('src', '') if img_elem else ''
        
        # 获取评分
        rating_elem = item.select_one('.rating_nums')
        rating = rating_elem.text.strip() if rating_elem else "N/A"
        
        # 获取描述
        abstract_elem = item.select_one('.abstract')
        abstract = abstract_elem.text.strip() if abstract_elem else ""
        
        # 从URL中提取ID
        subject_id = extract_subject_id(url)
        if not subject_id:
            return None
            
        # 获取详细信息，不使用缓存，每次都获取最新数据
        print(f"获取详细信息: {title} (ID: {subject_id})")
        info = get_subject_info(subject_id, cookie)
        
        if not info:
            print(f"无法获取详细信息，使用默认值")
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
            
        # 构建数据，添加更多字段
        result = {
            "id": subject_id,
            "title": title,
            "url": url,
            "cover_url": cover_url,
            "rating": rating,
            "intro": abstract,
            "type": info['type'],
            "imdb_id": info['imdb_id'],
            "year": info['year'],
            "director": info['director'],
            "actors": info['actors'],
            "genres": info['genres'],
            "region": info['region'],
            "languages": info['languages'],
            "duration": info['duration'],
            "release_date": info['release_date'],
            "vote_count": info['vote_count'],
            "notified": False,
            "add_time": time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # 如果是电视剧，添加剧集信息
        if info['type'] == 'tv' and 'episodes_info' in info:
            result['episodes_info'] = info['episodes_info']
            
        return result
    except Exception as e:
        print(f"解析片单条目出错: {e}")
        return None

def get_page_count(html_content):
    """获取片单的总页数"""
    soup = BeautifulSoup(html_content, 'html.parser')
    paginator = soup.select_one('.paginator')
    if not paginator:
        return 1
        
    page_links = paginator.select('a')
    max_page = 1
    
    for link in page_links:
        try:
            page_num = int(link.text.strip())
            max_page = max(max_page, page_num)
        except ValueError:
            continue
            
    return max_page

def is_duplicate(subject_id, doulist_id, all_data):
    """检查条目是否已存在（二次确认）
    
    该函数用于在保存前再次确认ID是否已存在，避免竞态条件
    """
    if doulist_id not in all_data["lists"]:
        return False
        
    existing_items = all_data["lists"][doulist_id].get("items", [])
    
    for item in existing_items:
        if item.get("id") == subject_id:
            return True
            
    return False

def fetch_doulist(doulist_id, cookie, max_pages=5):
    """获取片单中的所有条目
    
    doulist_id: 片单ID
    max_pages: 最大获取页数，默认为5页
    """
    try:
        print(f"开始获取片单 {doulist_id} 数据...")
        all_data = load_doulist_data()
        
        # 初始化列表，如果是新片单，需要创建结构
        if doulist_id not in all_data["lists"]:
            print(f"片单 {doulist_id} 不存在，创建新结构")
            all_data["lists"][doulist_id] = {
                "items": [],
                "update_time": time.strftime('%Y-%m-%d %H:%M:%S'),
                "has_update": False
            }
            save_doulist_data(all_data)
        else:
            items_count = len(all_data["lists"][doulist_id].get("items", []))
            print(f"片单 {doulist_id} 已存在，当前有 {items_count} 个条目")
        
        # 准备一个现有条目ID的集合，用于快速查找
        existing_ids = set()
        if doulist_id in all_data["lists"]:
            existing_ids = {item.get("id") for item in all_data["lists"][doulist_id].get("items", [])}
            print(f"当前片单已有 {len(existing_ids)} 个唯一条目ID")
        
        # 获取第一页并解析总页数
        first_page_html = get_doulist_html(doulist_id, cookie)
        total_pages = min(get_page_count(first_page_html), max_pages)
        
        print(f"片单共有 {total_pages} 页，将获取最多 {max_pages} 页")
        
        # 获取片单基本信息
        list_info = get_doulist_info(doulist_id, cookie)
        all_data = load_doulist_data()
        all_data["lists"][doulist_id]["list_info"] = list_info
        print(f"更新片单基本信息: {list_info.get('title', '未知')}")
        save_doulist_data(all_data)
        
        # 记录新条目和计数
        new_items = []
        new_items_count = 0
        
        # 处理所有页面
        for page in range(1, total_pages + 1):
            try:
                if page > 1:
                    print(f"\n获取第 {page}/{total_pages} 页...")
                    page_html = get_doulist_html(doulist_id, cookie, page)
                    soup = BeautifulSoup(page_html, 'html.parser')
                else:
                    print(f"\n处理第1页...")
                    soup = BeautifulSoup(first_page_html, 'html.parser')
                
                items = soup.select('.doulist-item')
                print(f"第{page}页找到 {len(items)} 个条目")
                
                # 处理页面上的所有条目
                for idx, html_item in enumerate(items, 1):
                    try:
                        # 先获取标题和链接，提取ID
                        title_elem = html_item.select_one('.title a')
                        if not title_elem:
                            continue
                        
                        url = title_elem.get('href', '')
                        title = title_elem.text.strip()
                        
                        # 跳过非电影/剧集条目
                        if not is_movie_or_tv(url):
                            continue
                        
                        # 从URL中提取ID
                        subject_id = extract_subject_id(url)
                        if not subject_id:
                            continue
                        
                        # 检查该ID是否已存在
                        if subject_id in existing_ids:
                            print(f"[{page}页-{idx}] 跳过已存在条目: {title} (ID: {subject_id})")
                            continue
                        
                        # 只有新条目才获取详细信息
                        print(f"[{page}页-{idx}] 发现新条目: {title} (ID: {subject_id})")
                        item = parse_doulist_item(html_item, cookie)
                        if not item:
                            continue
                        
                        # 每次处理新条目时都重新加载数据
                        current_data = load_doulist_data()
                        
                        # 再次检查是否重复（以防万一其他进程已添加）
                        if is_duplicate(item["id"], doulist_id, current_data):
                            continue
                        
                        # 添加到列表头部
                        current_data["lists"][doulist_id]["items"].insert(0, item)
                        current_data["lists"][doulist_id]["update_time"] = time.strftime('%Y-%m-%d %H:%M:%S')
                        current_data["lists"][doulist_id]["has_update"] = True
                        
                        # 立即保存
                        print(f"保存新条目: {item['title']}")
                        save_doulist_data(current_data)
                        
                        # 添加到新ID集合
                        existing_ids.add(subject_id)
                        new_items.append(item)
                        new_items_count += 1
                        
                    except Exception as e:
                        print(f"处理条目时出错: {e}")
                        continue
                    
                    # 处理完一个条目后添加延迟
                    if idx < len(items):
                        delay = random.uniform(0.5, 1.5)
                        time.sleep(delay)
                
                # 添加页面间随机延迟
                if page < total_pages:
                    delay = random.uniform(2, 5)
                    print(f"等待 {delay:.1f} 秒后获取下一页...")
                    time.sleep(delay)
                    
            except Exception as e:
                print(f"获取或解析第 {page} 页时出错: {e}")
                continue
        
        # 更新全局更新时间
        print("\n所有页面处理完成，更新时间戳")
        final_data = load_doulist_data()
        final_data["update_time"] = time.strftime('%Y-%m-%d %H:%M:%S')
        save_doulist_data(final_data)
        
        print(f"片单 {doulist_id} 处理完成，共新增 {new_items_count} 个条目")
        
        return {
            "success": True,
            "list_info": list_info,
            "new_items": new_items,
            "new_items_count": new_items_count,
            "update_time": time.strftime('%Y-%m-%d %H:%M:%S'),
            "has_update": new_items_count > 0
        }
    except Exception as e:
        print(f"获取片单 {doulist_id} 数据时出错: {e}")
        return {
            "success": False,
            "error": str(e)
        }

def update_doulist(doulist_id, doulist_config, cookie):
    """更新指定片单的数据"""
    # 获取配置
    max_pages = doulist_config.get("pages", 5)
    note = doulist_config.get("note", "")
    
    print(f"更新片单 {note or doulist_id}，获取 {max_pages} 页...")
    
    try:
        # 获取片单数据
        result = fetch_doulist(doulist_id, cookie, max_pages)
        
        if result["success"]:
            # 加载最新数据
            all_data = load_doulist_data()
            
            # 如果是第一次添加该片单，保存配置信息
            if "config" not in all_data["lists"].get(doulist_id, {}):
                all_data["lists"][doulist_id]["config"] = {
                    "note": note,
                    "pages": max_pages
                }
                save_doulist_data(all_data)
            
            new_items_count = result["new_items_count"]
            
            if new_items_count > 0:
                print(f"片单 {note or doulist_id} 成功添加 {new_items_count} 个新条目")
            else:
                print(f"片单 {note or doulist_id} 没有新条目")
                
            # 获取当前总条目数
            total_items = len(all_data["lists"][doulist_id]["items"])
            
            return {
                "success": True,
                "new_items_count": new_items_count,
                "total_items": total_items
            }
        else:
            return {
                "success": False,
                "error": result.get("error", "获取片单数据失败")
            }
    except Exception as e:
        print(f"更新片单 {doulist_id} 时出错: {e}")
        return {
            "success": False,
            "error": str(e)
        }

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
        
        print("\n======= 开始豆瓣片单抓取任务 =======")
        
        # 获取片单配置
        doulists = config.get('doulists', [])
        if not doulists:
            print("没有配置片单，跳过")
            return
            
        # 记录是否有任何片单更新
        any_updates = False
        new_items_total = 0
        new_items_by_list = {}
        
        # 处理每个片单
        total_lists = len(doulists)
        print(f"共有 {total_lists} 个片单需要处理")
        
        for i, doulist_config in enumerate(doulists, 1):
            doulist_id = doulist_config.get('id')
            note = doulist_config.get('note', '')
            
            if not doulist_id:
                print(f"[{i}/{total_lists}] 片单ID为空，跳过")
                continue
                
            try:
                print(f"\n---------- 处理片单 {i}/{total_lists}: {note or doulist_id} ----------")
                
                # 更新片单数据
                result = update_doulist(doulist_id, doulist_config, cookie)
                
                if result["success"]:
                    print(f"片单 {note or doulist_id} 处理结果: 成功")
                    print(f"  - 新增条目: {result['new_items_count']}")
                    print(f"  - 总条目数: {result['total_items']}")
                    
                    if result["new_items_count"] > 0:
                        any_updates = True
                        new_items_total += result["new_items_count"]
                        new_items_by_list[doulist_id] = {
                            "count": result["new_items_count"],
                            "note": note
                        }
                else:
                    print(f"片单 {note or doulist_id} 处理结果: 失败")
                    print(f"  - 错误信息: {result.get('error', '未知错误')}")
                
                # 添加随机延迟
                if i < total_lists:
                    delay = random.uniform(3, 6)
                    print(f"\n等待 {delay:.1f} 秒后处理下一个片单...")
                    time.sleep(delay)
            except Exception as e:
                print(f"处理片单 {doulist_id} 时出错: {e}")
                continue
        
        print("\n===== 所有片单处理完成 =====")
        print(f"总结: 共处理 {total_lists} 个片单，有 {len(new_items_by_list)} 个片单有更新，共 {new_items_total} 个新条目")
        
        # 构建通知消息
        if any_updates:
            # 有更新时的消息
            message = "📋 <b>豆瓣片单更新提醒</b>\n\n"
            
            # 加载最新数据
            print("\n正在构建通知消息...")
            all_data = load_doulist_data()
            
            # 添加新内容摘要
            for doulist_id, info in new_items_by_list.items():
                list_data = all_data["lists"].get(doulist_id, {})
                list_info = list_data.get("list_info", {})
                list_title = list_info.get("title", f"豆列 {doulist_id}")
                list_url = list_info.get("url", f"https://www.douban.com/doulist/{doulist_id}/?start=0&sort=time&playable=0&sub_type=")
                
                message += f"<b><a href='{list_url}'>{list_title}</a></b> 新增 {info['count']} 部作品:\n"
                
                # 获取未通知的条目
                new_items = [item for item in list_data.get("items", []) if not item.get("notified", True)][:100]  # 最多显示100个
                
                for item in new_items:
                    title = item.get("title", "")
                    url = item.get("url", "")
                    rating = item.get("rating", "N/A")
                    
                    message += f"• <a href='{url}'>{title}</a> - ⭐{rating}\n"
                    
                    # 标记为已通知
                    item["notified"] = True
                
                # 如果新增超过100个，添加"等"字样
                if info["count"] > 100:
                    message += f"等 {info['count']} 部作品\n"
                    
                message += "\n"
            
            # 保存更新后的数据（已标记通知状态）
            print("保存已通知状态...")
            save_doulist_data(all_data)
            
            # 发送通知
            print("发送通知消息...")
            try:
                send_telegram_message(message, config, True)
                print("通知消息发送成功")
            except Exception as e:
                print(f"发送通知消息失败: {e}")
            
            print(f"\n片单数据更新完成！共有 {new_items_total} 个新条目")
        else:
            print("\n片单数据更新完成！没有新内容")
            
            # 可选：发送无更新通知
            if config.get('telegram', {}).get('notify_mode') != 'new_only':
                message = "📋 <b>豆瓣片单更新提醒</b>\n\n"
                message += "⚠️ 本次更新没有发现新的内容。\n\n"
                message += f"更新时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                
                try:
                    send_telegram_message(message, config, False)
                    print("通知消息发送成功")
                except Exception as e:
                    print(f"发送通知消息失败: {e}")
    
    except Exception as e:
        error_message = f"❌ 获取豆瓣片单数据时出错: {str(e)}"
        print(error_message)
        try:
            config = load_config()
            send_telegram_message(error_message, config, False)
        except Exception as send_err:
            print(f"发送错误通知失败: {send_err}")
    
    print("\n======= 片单抓取任务结束 =======\n")

if __name__ == "__main__":
    main() 