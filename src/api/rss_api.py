"""
豆瓣电影/剧集 RSS API 模块
提供RSS格式的API接口，与主程序分离便于维护
"""

from flask import request, Response, Flask
import os
import json
from datetime import datetime
import xml.etree.ElementTree as ET
from xml.dom import minidom

# 获取当前文件所在目录的父级的父级目录（项目根目录）
app_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))

# 如果有单独的RSS API Flask应用，确保它也能找到模板和静态文件
rss_app = Flask(__name__, 
               template_folder=os.path.join(app_root, 'templates'),
               static_folder=os.path.join(app_root, 'static'))

# 获取配置目录
CONFIG_DIR = os.getenv('CONFIG_DIR', '.')
MOVIES_FILE = os.path.join(CONFIG_DIR, 'movies.json')
NEW_MOVIES_FILE = os.path.join(CONFIG_DIR, 'new_movies.json')
HOT_MOVIES_FILE = os.path.join(CONFIG_DIR, 'hot_movies.json')
HIDDEN_GEMS_FILE = os.path.join(CONFIG_DIR, 'hidden_gems.json')
STATUS_FILE = os.path.join(CONFIG_DIR, 'status.json')
DOULIST_FILE = os.path.join(CONFIG_DIR, 'doulists.json')

def load_json_file(file_path):
    """加载指定的 JSON 文件"""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"加载数据失败: {e}")
    return {}

def get_unique_items(data, item_type='movies'):
    """获取去重后的条目列表"""
    all_items = []
    
    # 遍历所有用户的数据
    for user_data in data.values():
        items = user_data.get(item_type, [])
        all_items.extend(items)
    
    # 去重（基于标题）
    seen = set()
    unique_items = []
    for item in all_items:
        title = item.get('title', '')
        if title and title not in seen:
            seen.add(title)
            unique_items.append(item)
    
    return unique_items

def generate_rss(items, title, description, link):
    """生成符合 RSSHub 格式的 RSS XML"""
    # 创建 RSS 根元素
    rss = ET.Element('rss', version='2.0')
    rss.set('xmlns:atom', 'http://www.w3.org/2005/Atom')
    rss.set('xmlns:content', 'http://purl.org/rss/1.0/modules/content/')
    
    # 创建 channel 元素
    channel = ET.SubElement(rss, 'channel')
    
    # 添加频道基本信息
    ET.SubElement(channel, 'title').text = title
    ET.SubElement(channel, 'link').text = link
    ET.SubElement(channel, 'description').text = description
    ET.SubElement(channel, 'language').text = 'zh-cn'
    ET.SubElement(channel, 'lastBuildDate').text = datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT')
    
    # 添加 atom:link
    atom_link = ET.SubElement(channel, '{http://www.w3.org/2005/Atom}link')
    atom_link.set('href', link)
    atom_link.set('rel', 'self')
    atom_link.set('type', 'application/rss+xml')
    
    # 添加条目
    for item in items:
        item_element = ET.SubElement(channel, 'item')
        
        # 标题
        title_text = item.get('title', '')
        ET.SubElement(item_element, 'title').text = title_text
        
        # 链接
        link_text = item.get('url', '')
        ET.SubElement(item_element, 'link').text = link_text
        
        # GUID (使用链接作为唯一标识)
        guid = ET.SubElement(item_element, 'guid')
        guid.text = link_text
        guid.set('isPermaLink', 'true')
        
        # 发布日期
        pub_date = item.get('pub_date', datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT'))
        ET.SubElement(item_element, 'pubDate').text = pub_date
        
        # 描述和内容
        description_text = f"""
        <img src="{item.get('cover_url', item.get('cover', ''))}" />
        <p>评分: {item.get('rating', 'N/A')}</p>
        <p>{item.get('intro', '')}</p>
        """
        ET.SubElement(item_element, 'description').text = description_text
        
        content = ET.SubElement(item_element, '{http://purl.org/rss/1.0/modules/content/}encoded')
        content.text = description_text
    
    # 将 XML 转换为字符串并格式化
    rough_string = ET.tostring(rss, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

def register_rss_routes(app):
    """注册所有RSS路由"""
    
    @app.route('/rsshub/wish')
    def rss_douban_wish():
        """获取用户想看的电影和电视剧的 RSS"""
        data = load_json_file(MOVIES_FILE)
        movies = get_unique_items(data, 'movies')
        tv_shows = get_unique_items(data, 'tv_shows')
        
        # 合并电影和电视剧
        all_items = movies + tv_shows
        
        # 为每个项目添加 URL
        for item in all_items:
            item['url'] = item.get('url', f"https://movie.douban.com/subject/{item.get('id', '')}/")
        
        # 生成 RSS
        title = "豆瓣用户想看"
        description = "豆瓣用户想看的电影和电视剧"
        link = request.url_root + "rsshub/wish"
        
        rss_xml = generate_rss(all_items, title, description, link)
        return Response(rss_xml, mimetype='application/xml')

    @app.route('/rsshub/movies')
    def rss_douban_wish_movies():
        """获取用户想看的电影的 RSS"""
        data = load_json_file(MOVIES_FILE)
        movies = get_unique_items(data, 'movies')
        
        # 为每个项目添加 URL
        for item in movies:
            item['url'] = item.get('url', f"https://movie.douban.com/subject/{item.get('id', '')}/")
        
        # 生成 RSS
        title = "豆瓣用户想看的电影"
        description = "豆瓣用户想看的电影"
        link = request.url_root + "rsshub/movies"
        
        rss_xml = generate_rss(movies, title, description, link)
        return Response(rss_xml, mimetype='application/xml')

    @app.route('/rsshub/tv')
    def rss_douban_wish_tv():
        """获取用户想看的电视剧的 RSS"""
        data = load_json_file(MOVIES_FILE)
        tv_shows = get_unique_items(data, 'tv_shows')
        
        # 为每个项目添加 URL
        for item in tv_shows:
            item['url'] = item.get('url', f"https://movie.douban.com/subject/{item.get('id', '')}/")
        
        # 生成 RSS
        title = "豆瓣用户想看的电视剧"
        description = "豆瓣用户想看的电视剧"
        link = request.url_root + "rsshub/tv"
        
        rss_xml = generate_rss(tv_shows, title, description, link)
        return Response(rss_xml, mimetype='application/xml')

    @app.route('/rsshub/new_movies')
    def rss_douban_new_movies():
        """获取最新电影的 RSS"""
        data = load_json_file(NEW_MOVIES_FILE)
        movies = data.get('movies', [])
        
        # 为每个项目添加 URL
        for item in movies:
            item['url'] = item.get('url', f"https://movie.douban.com/subject/{item.get('id', '')}/")
        
        # 生成 RSS
        title = "豆瓣最新电影"
        description = "豆瓣最新上映的电影"
        link = request.url_root + "rsshub/new_movies"
        
        rss_xml = generate_rss(movies, title, description, link)
        return Response(rss_xml, mimetype='application/xml')

    @app.route('/rsshub/hot_movies')
    def rss_douban_hot_movies():
        """获取热门电影的 RSS"""
        data = load_json_file(HOT_MOVIES_FILE)
        movies = data.get('movies', [])
        
        # 为每个项目添加 URL
        for item in movies:
            item['url'] = item.get('url', f"https://movie.douban.com/subject/{item.get('id', '')}/")
        
        # 生成 RSS
        title = "豆瓣热门电影"
        description = "豆瓣热门的电影"
        link = request.url_root + "rsshub/hot_movies"
        
        rss_xml = generate_rss(movies, title, description, link)
        return Response(rss_xml, mimetype='application/xml')

    @app.route('/rsshub/hot_tv')
    def rss_douban_hot_tv():
        """获取热门电视剧的 RSS"""
        data = load_json_file(HOT_MOVIES_FILE)
        tv_shows = data.get('tv_shows', [])
        
        # 为每个项目添加 URL
        for item in tv_shows:
            item['url'] = item.get('url', f"https://movie.douban.com/subject/{item.get('id', '')}/")
        
        # 生成 RSS
        title = "豆瓣热门电视剧"
        description = "豆瓣热门的电视剧"
        link = request.url_root + "rsshub/hot_tv"
        
        rss_xml = generate_rss(tv_shows, title, description, link)
        return Response(rss_xml, mimetype='application/xml')

    @app.route('/rsshub/hidden_gems_movies')
    def rss_douban_hidden_gems_movies():
        """获取冷门佳片电影的 RSS"""
        data = load_json_file(HIDDEN_GEMS_FILE)
        movies = data.get('movies', [])
        
        # 为每个项目添加 URL
        for item in movies:
            item['url'] = item.get('url', f"https://movie.douban.com/subject/{item.get('id', '')}/")
        
        # 生成 RSS
        title = "豆瓣冷门佳片电影"
        description = "豆瓣冷门但评分很高的电影"
        link = request.url_root + "rsshub/hidden_gems_movies"
        
        rss_xml = generate_rss(movies, title, description, link)
        return Response(rss_xml, mimetype='application/xml')

    # 添加广播RSS接口
    @app.route('/rsshub/status_movies')
    def rss_douban_status_movies():
        """获取从广播中提取的电影的 RSS"""
        data = load_json_file(STATUS_FILE)
        movies = get_unique_items(data, 'movies')
        
        # 为每个项目添加 URL
        for item in movies:
            item['url'] = item.get('url', f"https://movie.douban.com/subject/{item.get('id', '')}/")
        
        # 生成 RSS
        title = "豆瓣广播电影"
        description = "从豆瓣用户广播中提取的电影"
        link = request.url_root + "rsshub/status_movies"
        
        rss_xml = generate_rss(movies, title, description, link)
        return Response(rss_xml, mimetype='application/xml')

    @app.route('/rsshub/status_tv')
    def rss_douban_status_tv():
        """获取从广播中提取的电视剧的 RSS"""
        data = load_json_file(STATUS_FILE)
        tv_shows = get_unique_items(data, 'tv_shows')
        
        # 为每个项目添加 URL
        for item in tv_shows:
            item['url'] = item.get('url', f"https://movie.douban.com/subject/{item.get('id', '')}/")
        
        # 生成 RSS
        title = "豆瓣广播剧集"
        description = "从豆瓣用户广播中提取的电视剧"
        link = request.url_root + "rsshub/status_tv"
        
        rss_xml = generate_rss(tv_shows, title, description, link)
        return Response(rss_xml, mimetype='application/xml')

    @app.route('/rsshub/doulists')
    def rss_douban_doulists():
        """获取所有片单中的电影/剧集的综合 RSS"""
        data = load_json_file(DOULIST_FILE)
        all_items = []
        
        # 收集所有片单中的条目
        for doulist_id, doulist_data in data.get('lists', {}).items():
            items = doulist_data.get('items', [])
            # 添加片单信息到每个条目
            for item in items:
                item['doulist_info'] = doulist_data.get('list_info', {})
                all_items.append(item)
        
        # 按添加时间排序（最新的在前）
        all_items.sort(key=lambda x: x.get('add_time', ''), reverse=True)
        
        # 生成 RSS
        title = "豆瓣片单合集"
        description = "所有关注的豆瓣片单中的电影和剧集"
        link = request.url_root + "rsshub/doulists"
        
        rss_xml = generate_rss(all_items, title, description, link)
        return Response(rss_xml, mimetype='application/xml')

    @app.route('/rsshub/doulist/<doulist_id>')
    def rss_douban_doulist(doulist_id):
        """获取指定片单的 RSS"""
        data = load_json_file(DOULIST_FILE)
        doulist_data = data.get('lists', {}).get(doulist_id, {})
        
        if not doulist_data:
            return Response(f"片单 {doulist_id} 未找到", status=404)
            
        items = doulist_data.get('items', [])
        list_info = doulist_data.get('list_info', {})
        
        # 生成 RSS
        title = list_info.get('title', f"豆瓣片单 {doulist_id}")
        description = list_info.get('description', "豆瓣片单中的电影和剧集")
        link = list_info.get('url', request.url_root + f"rsshub/doulist/{doulist_id}")
        
        rss_xml = generate_rss(items, title, description, link)
        return Response(rss_xml, mimetype='application/xml')

    print("已注册 RSS 相关路由") 