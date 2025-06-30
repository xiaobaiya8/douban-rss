import json
import requests
from bs4 import BeautifulSoup
import time
import os
import re
import random
import logging
# 导入豆瓣工具模块
from src.utils.douban_utils import extract_subject_id, load_config, check_cookie_valid, send_telegram_message, send_wecom_message, make_douban_headers, load_json_data, save_json_data, migrate_legacy_cache_data

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('douban_status')

# 获取配置目录
CONFIG_DIR = os.getenv('CONFIG_DIR', 'config')
CONFIG_FILE = os.path.join(CONFIG_DIR, 'config.json')
STATUS_FILE = os.path.join(CONFIG_DIR, 'status.json')
URL_CACHE_FILE = os.path.join(CONFIG_DIR, 'url_cache.json')  # 添加URL缓存文件

# 全局缓存变量
url_cache = {
    'short_urls': {},  # 短链接 -> 实际URL
    'trailer_urls': {},  # 预告片URL -> 电影/剧集信息
    'subject_types': {},  # 条目ID -> 类型(movie/tv)
    'subject_details': {}  # 条目ID -> 完整详情
}

# 全局URL缓存
URL_CACHE = {}

# 使用已导入的函数替换原有的引用
def extract_trailer_id(url):
    """从预告片URL中提取ID"""
    match = re.search(r'/trailer/(\d+)', url)
    if match:
        return match.group(1)
    return None

def get_subject_info_from_trailer(trailer_id, cookie, max_retries=3):
    """从预告片页面获取电影/剧集信息，使用缓存"""
    # 构建预告片URL
    trailer_url = f'https://movie.douban.com/trailer/{trailer_id}/'
    
    # 先检查缓存
    global url_cache
    if trailer_url in url_cache['trailer_urls']:
        cached_info = url_cache['trailer_urls'][trailer_url]
        print(f"从缓存获取预告片信息: {trailer_id} -> {cached_info['title']} (ID: {cached_info['id']})")
        return cached_info
    
    # 缓存不存在，进行请求
    for attempt in range(max_retries):
        try:
            headers = make_douban_headers(cookie)
            
            print(f"正在从预告片 {trailer_id} 获取电影信息...")
            
            # 随机延迟1-3秒
            delay = random.uniform(1, 3)
            time.sleep(delay)
            
            response = requests.get(trailer_url, headers=headers)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 查找电影链接
                h1_elem = soup.find('h1')
                if h1_elem:
                    movie_link = h1_elem.find('a')
                    if movie_link and 'href' in movie_link.attrs:
                        movie_url = movie_link['href']
                        subject_id = extract_subject_id(movie_url)
                        title = movie_link.text.strip()
                        
                        print(f"从预告片找到电影: {title} (ID: {subject_id})")
                        
                        # 创建结果并保存到缓存
                        result = {
                            'id': subject_id,
                            'title': title,
                            'url': movie_url
                        }
                        url_cache['trailer_urls'][trailer_url] = result
                        return result
                
                print(f"无法从预告片 {trailer_id} 获取电影信息")
                return None
                
            else:
                print(f"获取预告片 {trailer_id} 失败: HTTP {response.status_code}")
                if attempt < max_retries - 1:
                    print(f"将在 3 秒后重试...")
                    time.sleep(3)
                    continue
                else:
                    raise requests.RequestException(f"获取预告片信息失败: HTTP {response.status_code}")
                    
        except Exception as e:
            print(f"获取预告片 {trailer_id} 时出错: {e}")
            if attempt < max_retries - 1:
                print(f"将在 3 秒后重试...")
                time.sleep(3)
                continue
            else:
                raise
    
    return None

def get_subject_type(subject_id, cookie, max_retries=3):
    """获取条目类型（电影或电视剧），使用缓存"""
    # 先检查缓存
    global url_cache
    if subject_id in url_cache['subject_types']:
        cached_type = url_cache['subject_types'][subject_id]
        print(f"从缓存获取条目类型: {subject_id} -> {cached_type}")
        return cached_type
    
    # 缓存不存在，进行请求
    for attempt in range(max_retries):
        try:
            url = f'https://movie.douban.com/subject/{subject_id}/'
            headers = make_douban_headers(cookie)
            
            print(f"正在获取条目 {subject_id} 的类型...")
            
            # 随机延迟1-3秒
            delay = random.uniform(1, 3)
            time.sleep(delay)
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 查找"谁在看"标题来判断类型
                others_interests = soup.find('div', {'id': 'subject-others-interests'})
                if others_interests:
                    title = others_interests.find('i')
                    if title:
                        title_text = title.text.strip()
                        # 根据标题判断类型
                        if '这部剧集' in title_text:
                            # 保存到缓存
                            url_cache['subject_types'][subject_id] = 'tv'
                            return 'tv'
                        elif '这部电影' in title_text:
                            # 保存到缓存
                            url_cache['subject_types'][subject_id] = 'movie'
                            return 'movie'
                
                # 如果无法从"谁在看"判断，则检查类型标签
                info_div = soup.find('div', {'id': 'info'})
                if info_div:
                    genre_span = info_div.find('span', text='类型:')
                    if genre_span:
                        genre = genre_span.find_next('span', property='v:genre')
                        if genre and genre.text.strip() in ['真人秀', '纪录片', '综艺']:
                            # 保存到缓存
                            url_cache['subject_types'][subject_id] = 'tv'
                            return 'tv'
                
                # 从页面标题判断
                title = soup.find('title')
                if title:
                    title_text = title.text.strip()
                    if '剧集' in title_text or '电视剧' in title_text:
                        # 保存到缓存
                        url_cache['subject_types'][subject_id] = 'tv'
                        return 'tv'
                
                # 默认为电影
                # 保存到缓存
                url_cache['subject_types'][subject_id] = 'movie'
                return 'movie'
                
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
    
    # 默认返回电影并保存到缓存
    url_cache['subject_types'][subject_id] = 'movie'
    return 'movie'

def get_redirect_url(short_url, headers, max_retries=3):
    """获取短链接的重定向目标URL，使用缓存"""
    # 先检查缓存
    global url_cache
    if short_url in url_cache['short_urls']:
        cached_url = url_cache['short_urls'][short_url]
        print(f"从缓存获取短链接重定向: {short_url} -> {cached_url}")
        return cached_url
    
    # 缓存不存在，进行请求
    for attempt in range(max_retries):
        try:
            response = requests.head(short_url, headers=headers, allow_redirects=False, timeout=10)
            
            # 检查是否有重定向
            if response.status_code in (301, 302, 303, 307, 308) and 'Location' in response.headers:
                redirect_url = response.headers['Location']
                # 保存到缓存
                url_cache['short_urls'][short_url] = redirect_url
                return redirect_url
            
            # 如果没有重定向但返回成功，直接返回原URL
            if response.status_code == 200:
                # 保存到缓存
                url_cache['short_urls'][short_url] = short_url
                return short_url
                
            # 其他情况，尝试完整GET请求
            response = requests.get(short_url, headers=headers, allow_redirects=True, timeout=10)
            final_url = response.url
            # 保存到缓存
            url_cache['short_urls'][short_url] = final_url
            return final_url
                
        except Exception as e:
            print(f"获取重定向URL时出错: {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
            else:
                return None
    
    return None

def get_subject_details(subject_id, cookie, max_retries=3):
    """获取条目的完整详情信息，使用缓存"""
    # 先检查缓存
    global url_cache
    if subject_id in url_cache['subject_details']:
        cached_details = url_cache['subject_details'][subject_id]
        print(f"从缓存获取条目详情: {subject_id} -> {cached_details['title']}")
        return cached_details
    
    # 缓存不存在，进行请求
    for attempt in range(max_retries):
        try:
            url = f'https://movie.douban.com/subject/{subject_id}/'
            headers = make_douban_headers(cookie)
            
            print(f"正在获取条目 {subject_id} 的完整详情...")
            
            # 随机延迟1-3秒
            delay = random.uniform(1, 3)
            time.sleep(delay)
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 获取标题
                title = ""
                title_elem = soup.find('span', property='v:itemreviewed')
                if title_elem:
                    title = title_elem.text.strip()
                
                # 分割主标题和副标题
                main_title = title
                subtitle = ""
                full_title = title
                if " " in title and not title.startswith(" "):
                    parts = title.split(" ", 1)
                    main_title = parts[0].strip()
                    subtitle = parts[1].strip()
                
                # 获取评分
                rating = ""
                rating_elem = soup.find('strong', property='v:average')
                if rating_elem:
                    rating = rating_elem.text.strip()
                
                # 获取年份
                year = ""
                year_elem = soup.find('span', class_='year')
                if year_elem:
                    year_text = year_elem.text.strip()
                    year_match = re.search(r'\((\d{4})\)', year_text)
                    if year_match:
                        year = year_match.group(1)
                
                # 获取海报URL
                cover_url = ""
                cover_elem = soup.find('img', rel='v:image')
                if cover_elem and 'src' in cover_elem.attrs:
                    cover_url = cover_elem['src']
                
                # 获取IMDb ID
                imdb_id = ""
                info_div = soup.find('div', {'id': 'info'})
                if info_div:
                    imdb_link = info_div.find('a', href=re.compile(r'https?://www.imdb.com/title/(tt\d+)'))
                    if imdb_link:
                        imdb_match = re.search(r'tt\d+', imdb_link['href'])
                        if imdb_match:
                            imdb_id = imdb_match.group(0)
                    else:
                        # 尝试从文本中提取IMDb信息
                        imdb_text = info_div.text
                        imdb_match = re.search(r'IMDb:\s*(tt\d+)', imdb_text)
                        if imdb_match:
                            imdb_id = imdb_match.group(1)
                
                # 获取所有信息项
                info = []
                if info_div:
                    # 获取所有信息文本，并进行清理
                    info_text = info_div.text.strip().replace('\n', ' ')
                    info_text = re.sub(r'\s+', ' ', info_text)  # 压缩多余空格
                    
                    # 提取导演
                    director_match = re.search(r'导演:\s*([^:]+?)(?:主演|编剧|制片国家|地区)', info_text)
                    if director_match:
                        directors = director_match.group(1).strip().split(' / ')
                        for director in directors:
                            if director.strip():
                                info.append(director.strip())
                    
                    # 提取主演
                    actor_match = re.search(r'主演:\s*([^:]+?)(?:类型|上映日期|片长)', info_text)
                    if actor_match:
                        actors = actor_match.group(1).strip().split(' / ')
                        for actor in actors[:8]:  # 限制主演数量
                            if actor.strip():
                                info.append(actor.strip())
                    
                    # 提取制片国家/地区
                    region_match = re.search(r'制片国家/地区:\s*([^:]+?)(?:语言|类型|上映日期)', info_text)
                    if region_match:
                        regions = region_match.group(1).strip().split(' / ')
                        for region in regions:
                            if region.strip():
                                info.append(region.strip())
                    
                    # 提取导演（再次尝试，以确保能够提取到）
                    if len(info) < 3:
                        director_spans = info_div.find_all('span', class_='attrs')
                        for span in director_spans:
                            prev_span = span.find_previous('span')
                            if prev_span and '导演' in prev_span.text:
                                directors = span.text.strip().split(' / ')
                                for director in directors:
                                    if director.strip() and director.strip() not in info:
                                        info.append(director.strip())
                    
                    # 提取上映日期
                    date_spans = info_div.find_all('span', property='v:initialReleaseDate')
                    if date_spans:
                        dates = []
                        for date_span in date_spans:
                            date_text = date_span.text.strip()
                            if date_text:
                                dates.append(date_text)
                        if dates:
                            # 优先选择中国大陆上映日期
                            cn_date = None
                            for date in dates:
                                if '中国大陆' in date:
                                    cn_date = date
                                    break
                            info.insert(0, cn_date if cn_date else dates[0])
                    
                    # 提取片长
                    duration_span = info_div.find('span', property='v:runtime')
                    if duration_span:
                        duration = duration_span.text.strip()
                        if duration:
                            info.append(duration)
                    
                    # 提取类型
                    genre_spans = info_div.find_all('span', property='v:genre')
                    if genre_spans:
                        genres = []
                        for genre_span in genre_spans:
                            genre = genre_span.text.strip()
                            if genre:
                                genres.append(genre)
                        if genres:
                            info.append('/'.join(genres))
                    
                    # 提取语言
                    language_match = re.search(r'语言:\s*([^:]+?)(?:类型|上映日期|片长|官方网站|制片国家)', info_text)
                    if language_match:
                        languages = language_match.group(1).strip().split(' / ')
                        if languages:
                            info.append(languages[0].strip())
                
                # 获取详情描述
                description = ""
                desc_span = soup.find('span', property='v:summary')
                if desc_span:
                    description = desc_span.text.strip()
                
                # 构建结果
                result = {
                    'id': subject_id,
                    'title': main_title,
                    'subtitle': subtitle,
                    'full_title': full_title,
                    'info': info,
                    'year': year,
                    'description': description,
                    'cover_url': cover_url,
                    'url': url,
                    'rating': rating,
                    'playable': True,
                    'imdb_id': imdb_id if imdb_id else None
                }
                
                # 确定类型
                media_type = "movie"
                others_interests = soup.find('div', {'id': 'subject-others-interests'})
                if others_interests:
                    title = others_interests.find('i')
                    if title and '这部剧集' in title.text.strip():
                        media_type = "tv"
                
                result['type'] = media_type
                
                # 保存到缓存
                url_cache['subject_details'][subject_id] = result
                url_cache['subject_types'][subject_id] = media_type
                
                return result
                
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
    
    return None

def process_status(status, cookie, early_check=False):
    """处理单条广播，尝试提取电影/剧集信息
    
    当early_check为True时，只提取subject_id并返回，不获取详细信息
    """
    try:
        # 自定义请求头
        headers = make_douban_headers(cookie)
        
        # 查找可能的电影/剧集链接
        subject_info = None
        subject_id = None
        
        # 检查是否包含电影/剧集链接
        if 'block-subject' in str(status):
            # 从分享的电影/剧集卡片中提取
            subject_block = status.find('div', class_='block-subject')
            if subject_block:
                subject_link = subject_block.find('a', href=True)
                if subject_link:
                    subject_url = subject_link['href']
                    subject_id = extract_subject_id(subject_url)
                    if subject_id and early_check:
                        return {"id": subject_id, "title": subject_link.text.strip()}
                    elif subject_id:
                        # 获取完整电影信息
                        subject_info = get_subject_details(subject_id, cookie)
        
        # 检查是否包含预告片链接
        elif 'block-video' in str(status):
            # 从预告片中提取
            video_block = status.find('div', class_='block-video')
            if video_block:
                # 获取预告片ID
                video_player = video_block.find('div', class_='video-player')
                if video_player:
                    # 尝试从onclick或其他属性中找到预告片ID
                    match = re.search(r'/trailer/(\d+)', str(status))
                    if match:
                        trailer_id = match.group(1)
                        if early_check:
                            # 仅获取基本信息以检查ID
                            subject_info_from_trailer = get_subject_info_from_trailer(trailer_id, cookie)
                            if subject_info_from_trailer:
                                return {"id": subject_info_from_trailer['id'], "title": subject_info_from_trailer['title']}
                        else:
                            subject_info_from_trailer = get_subject_info_from_trailer(trailer_id, cookie)
                            if subject_info_from_trailer:
                                subject_id = subject_info_from_trailer['id']
                                if subject_id:
                                    # 获取完整电影信息
                                    subject_info = get_subject_details(subject_id, cookie)
        
        # 查找纯文本形式的链接
        if not subject_info and not (early_check and subject_id):
            links = status.find_all('a', href=True)
            for link in links:
                url = link['href']
                
                # 处理豆瓣链接
                if 'movie.douban.com/subject/' in url:
                    subject_id = extract_subject_id(url)
                    if subject_id and early_check:
                        return {"id": subject_id, "title": link.text.strip()}
                    elif subject_id:
                        # 获取完整电影信息
                        subject_info = get_subject_details(subject_id, cookie)
                        break
                
                # 处理预告片链接
                elif 'movie.douban.com/trailer/' in url:
                    trailer_id = extract_trailer_id(url)
                    if trailer_id:
                        if early_check:
                            subject_info_from_trailer = get_subject_info_from_trailer(trailer_id, cookie)
                            if subject_info_from_trailer:
                                return {"id": subject_info_from_trailer['id'], "title": subject_info_from_trailer['title']}
                        else:
                            subject_info_from_trailer = get_subject_info_from_trailer(trailer_id, cookie)
                            if subject_info_from_trailer:
                                subject_id = subject_info_from_trailer['id']
                                if subject_id:
                                    # 获取完整电影信息
                                    subject_info = get_subject_details(subject_id, cookie)
                                    break
                
                # 处理短链接（douc.cc）
                elif 'douc.cc' in url and not early_check:  # 早期检查跳过短链接处理
                    print(f"发现短链接: {url}")
                    actual_url = get_redirect_url(url, headers)
                    print(f"短链接重定向到: {actual_url}")
                    
                    if actual_url:
                        # 检查是否是电影/剧集页面
                        if 'movie.douban.com/subject/' in actual_url:
                            subject_id = extract_subject_id(actual_url)
                            if subject_id:
                                # 获取完整电影信息
                                subject_info = get_subject_details(subject_id, cookie)
                                break
                        
                        # 检查是否是预告片页面
                        elif 'movie.douban.com/trailer/' in actual_url:
                            trailer_id = extract_trailer_id(actual_url)
                            if trailer_id:
                                subject_info_from_trailer = get_subject_info_from_trailer(trailer_id, cookie)
                                if subject_info_from_trailer:
                                    subject_id = subject_info_from_trailer['id']
                                    if subject_id:
                                        # 获取完整电影信息
                                        subject_info = get_subject_details(subject_id, cookie)
                                        break
        
        if early_check and subject_id:
            return {"id": subject_id, "title": "未知标题"}
        
        if subject_info and subject_id:
            # 获取发布日期
            date_elem = status.find('span', class_='created_at')
            date = date_elem.text.strip() if date_elem else ''
            
            # 获取广播ID和内容
            status_id = ''
            status_div = status.find('div', {'data-status-id': True})
            if status_div:
                status_id = status_div['data-status-id']
            
            # 获取广播内容
            content = ''
            blockquote = status.find('blockquote')
            if blockquote:
                p = blockquote.find('p')
                if p:
                    content = p.text.strip()
            
            # 添加广播特有的信息
            subject_info['date_added'] = date
            subject_info['status_id'] = status_id
            subject_info['status_content'] = content
            subject_info['notified'] = False
            
            return subject_info
    
    except Exception as e:
        print(f"处理广播时出错: {e}")
    
    return None

def get_douban_status_html(user_id, cookie, pages=1):
    """获取豆瓣用户广播的HTML内容"""
    all_html = ""
    page_count = 0
    
    # 使用douban_utils生成请求头
    headers = make_douban_headers(cookie)
    
    try:
        for page in range(1, pages + 1):
            url = f"https://www.douban.com/people/{user_id}/statuses?p={page}"
            print(f"获取第 {page}/{pages} 页广播")
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                all_html += response.text
                page_count += 1
                
                # 在获取多页时添加随机延迟
                if page < pages:
                    delay = random.uniform(1, 3)  # 1-3秒随机延迟
                    print(f"等待 {delay:.1f} 秒...")
                    time.sleep(delay)
            else:
                print(f"获取第 {page} 页失败: HTTP状态码 {response.status_code}")
                break
                
        print(f"成功获取了 {page_count} 页广播")
        return all_html
    except Exception as e:
        print(f"获取广播时出错: {e}")
        return ""

def load_config():
    """加载配置文件"""
    # 使用从utils导入的load_config函数，添加别名避免递归
    from src.utils.douban_utils import load_config as load_config_from_utils
    return load_config_from_utils()

def load_all_status_data():
    """加载所有广播数据"""
    return load_json_data(STATUS_FILE, {})

def save_all_status_data(all_data):
    """保存所有广播数据到文件"""
    save_json_data(all_data, STATUS_FILE)

def is_duplicate(subject_id, user_id, all_data):
    """检查条目是否重复"""
    user_data = all_data.get(user_id, {'movies': [], 'tv_shows': []})
    all_items = user_data['movies'] + user_data['tv_shows']
    
    for item in all_items:
        if subject_id == item.get('id'):
            return True
    return False

def parse_status_html(html_content, user_id, all_data, cookie):
    """解析HTML内容并提取广播中的电影/剧集"""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 获取或初始化用户数据
    user_data = all_data.get(user_id, {'movies': [], 'tv_shows': []})
    movies = user_data['movies']
    tv_shows = user_data['tv_shows']
    
    # 找到广播列表
    status_items = soup.find_all('div', class_='status-wrapper')
    total_items = len(status_items)
    new_items = 0
    
    print(f"\n开始处理 {total_items} 条广播...")
    
    for index, status in enumerate(status_items, 1):
        try:
            # 先进行快速检查，只提取条目ID和简单标题
            subject_basic = process_status(status, cookie, early_check=True)
            
            if subject_basic and subject_basic['id']:
                # 检查是否重复
                if is_duplicate(subject_basic['id'], user_id, all_data):
                    print(f"\n条目已存在，跳过: {subject_basic['title']}")
                    continue  # 跳过下面的处理，直接进入下一次循环，不添加任何延迟
                
                # 条目不重复，获取完整信息
                subject = process_status(status, cookie)
                
                if subject and subject['id']:
                    print(f"\n处理新条目: {subject['title']}")
                    new_items += 1
                    
                    # 设置notified为False，表示这是一个新条目需要通知
                    subject['notified'] = False
                    
                    # 根据类型添加到对应列表
                    if subject["type"] == "movie":
                        movies.append(subject)
                        print(f"已添加到电影列表: {subject['title']}")
                    else:
                        tv_shows.append(subject)
                        print(f"已添加到电视剧列表: {subject['title']}")
                    
                    # 实时保存数据
                    all_data[user_id] = {'movies': movies, 'tv_shows': tv_shows}
                    save_all_status_data(all_data)
                    print("数据已保存")
                    
                    # 只在成功处理新条目后添加延迟
                    if index < total_items:
                        delay = random.uniform(3, 7)
                        print(f"等待 {delay:.1f} 秒后继续...")
                        time.sleep(delay)
                
        except Exception as e:
            print(f"处理广播条目时出错: {e}")
            continue
    
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

def send_telegram_message(message, config, has_new_content=False):
    """发送Telegram消息，这是一个转发函数"""
    # 使用从utils导入的send_telegram_message函数，添加别名避免递归
    from src.utils.douban_utils import send_telegram_message as send_telegram_message_from_utils
    send_telegram_message_from_utils(message, config, has_new_content)

def send_wecom_message(message, config, has_new_content=False):
    """发送企业微信消息，这是一个转发函数"""
    from src.utils.douban_utils import send_wecom_message as send_wecom_message_from_utils
    send_wecom_message_from_utils(message, config, has_new_content)

def cleanup_temp_files():
    """清理临时文件"""
    # 清理其他可能的临时文件
    pass

def load_url_cache():
    """加载URL缓存"""
    global URL_CACHE
    URL_CACHE = load_json_data(URL_CACHE_FILE, {})
    print(f"已加载 {len(URL_CACHE)} 条URL缓存")

def save_url_cache():
    """保存URL缓存"""
    try:
        save_json_data(URL_CACHE, URL_CACHE_FILE)
        print(f"已保存 {len(URL_CACHE)} 条URL缓存")
    except Exception as e:
        print(f"保存URL缓存失败: {e}")

def fetch_user_status(user_id, cookie, pages=1):
    """获取用户广播状态并处理"""
    try:
        # 加载现有数据
        all_data = load_all_status_data()
        
        # 获取广播HTML内容
        html_content = get_douban_status_html(user_id, cookie, pages)
        
        if not html_content:
            print(f"未能获取用户 {user_id} 的广播内容")
            return False
            
        # 解析HTML并提取电影/剧集
        result = parse_status_html(html_content, user_id, all_data, cookie)
        
        # 更新用户数据
        all_data[user_id] = result
        save_all_status_data(all_data)
        
        # 检查是否有新内容
        return result.get('new_items_count', 0) > 0
        
    except Exception as e:
        print(f"获取用户 {user_id} 广播状态时出错: {e}")
        return False

def main():
    try:
        # 在开始时进行缓存迁移
        print("检查并迁移旧缓存数据...")
        migrate_legacy_cache_data()
        
        # 加载URL缓存
        load_url_cache()
        
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
        
        print("\n开始获取豆瓣广播数据...")
        
        # 记录是否有任何用户数据更新
        any_updates = False
        
        # 处理每个用户的数据
        statuses = config.get('statuses', [])
        total_users = len(statuses)
        
        for i, status in enumerate(statuses, 1):
            user_id = status['id']
            note = status.get('note', '')
            pages = status.get('pages', 1)
            try:
                print(f"\n[{i}/{total_users}] 处理用户广播: {note or user_id}")
                
                # 获取更新
                has_updates = fetch_user_status(user_id, cookie, pages)
                
                if has_updates:
                    any_updates = True
                
                # 如果不是最后一个用户，添加随机延迟
                if i < total_users:
                    delay = random.uniform(1, 3)  # 1-3秒的随机延迟
                    print(f"等待 {delay:.1f} 秒后处理下一个用户...")
                    time.sleep(delay)
                    
            except Exception as e:
                print(f"处理用户广播 {user_id} 时出错: {e}")
                continue
        
        # 重新加载所有数据，用于生成统计信息
        all_data = load_all_status_data()
        
        # 统计总数和新增内容
        total_movies = 0
        total_tv_shows = 0
        new_movies = []
        new_tv_shows = []
        
        # 遍历所有用户数据，统计总数和查找未通知的新项目
        for user_id, user_data in all_data.items():
            # 统计总数
            total_movies += len(user_data.get('movies', []))
            total_tv_shows += len(user_data.get('tv_shows', []))
            
            # 查找未通知的项目
            for movie in user_data.get('movies', []):
                if not movie.get('notified', True):
                    new_movies.append(movie)
            
            for tv in user_data.get('tv_shows', []):
                if not tv.get('notified', True):
                    new_tv_shows.append(tv)
        
        # 新增数量
        new_movies_count = len(new_movies)
        new_tv_shows_count = len(new_tv_shows)
        has_new_content = new_movies_count > 0 or new_tv_shows_count > 0
        
        # 构建通知消息
        message = (
            f"🎬 *豆瓣广播更新完成*\n\n"
        )
        
        # 根据实际新增数量展示消息
        if not has_new_content:
            # 没有新内容时的消息
            message += "⚠️ 本次更新没有发现新的内容。\n\n"
        else:
            message += f"📊 本次新增: {new_movies_count} 部电影, {new_tv_shows_count} 部剧集\n\n"
        
        # 更新时间和总计数
        update_time = time.strftime('%Y-%m-%d %H:%M:%S')
        message += (
            f"更新时间: {update_time}\n"
            f"总电影数: {total_movies} 部\n"
            f"总剧集数: {total_tv_shows} 部\n\n"
        )
        
        # 添加新更新的电影信息
        if has_new_content:
            if new_movies:
                message += "*新增电影:*\n"
                for movie in new_movies:  # 显示所有新电影，不限制数量
                    movie_link = movie.get('url', f"https://movie.douban.com/subject/{movie.get('id', '')}/")
                    rating = movie.get('rating', '')
                    rating_text = f" - ⭐{rating}" if rating else ""
                    message += f"• <a href='{movie_link}'>{movie['title']}</a>{rating_text}\n"
                    movie['notified'] = True  # 标记为已通知
                
                message += "\n"
            
            # 如果有新增剧集
            if new_tv_shows:
                message += "*新增剧集:*\n"
                for tv in new_tv_shows:  # 显示所有新剧集，不限制数量
                    tv_link = tv.get('url', f"https://movie.douban.com/subject/{tv.get('id', '')}/")
                    rating = tv.get('rating', '')
                    rating_text = f" - ⭐{rating}" if rating else ""
                    message += f"• <a href='{tv_link}'>{tv['title']}</a>{rating_text}\n"
                    tv['notified'] = True  # 标记为已通知
                
                message += "\n"
            
            # 保存已标记的数据
            save_all_status_data(all_data)
        
        # 发送通知消息
        send_telegram_message(message, config, has_new_content)
        send_wecom_message(message, config, has_new_content)
        
        print("\n广播数据获取完成！")
        
    except Exception as e:
        error_message = f"❌ 获取豆瓣广播数据时出错: {str(e)}"
        print(error_message)
        send_telegram_message(error_message, config, False)
        send_wecom_message(error_message, config, False)
    finally:
        # 保存URL缓存
        save_url_cache()
        
        # 无论成功还是失败，都清理临时文件
        cleanup_temp_files()

if __name__ == "__main__":
    main() 