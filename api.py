from flask import Flask, jsonify, render_template, request, session, redirect, url_for
import json
import re
import os
import subprocess
import threading
import time
import sys
import requests
from datetime import datetime
import schedule

app = Flask(__name__)

# 全局定时器
scheduler_thread = None
stop_scheduler = False

# 全局变量来跟踪解析进程状态
parser_status = {
    "is_running": False,
    "last_run": None,
    "next_run": None,
    "current_process": None
}

# 获取配置目录
CONFIG_DIR = os.getenv('CONFIG_DIR', '.')
CONFIG_FILE = os.path.join(CONFIG_DIR, 'config.json')
MOVIES_FILE = os.path.join(CONFIG_DIR, 'movies.json')
NEW_MOVIES_FILE = os.path.join(CONFIG_DIR, 'new_movies.json')
HOT_MOVIES_FILE = os.path.join(CONFIG_DIR, 'hot_movies.json')
HIDDEN_GEMS_FILE = os.path.join(CONFIG_DIR, 'hidden_gems.json')

# 添加 session 密钥
app.secret_key = os.urandom(24)

def run_parser(is_manual=False):
    """运行解析程序"""
    try:
        parser_status["is_running"] = True
        config = load_config()
        
        # 获取监控配置
        monitors = config.get('monitors', {})
        
        # 计算总任务数
        total_tasks = sum([
            monitors.get('user_wish', False),
            monitors.get('latest', False),
            monitors.get('popular', False),
            monitors.get('hidden_gems', False)
        ])
        current_task = 0
        
        parser_status["total_users"] = total_tasks
        parser_status["current_user"] = 0
        
        def run_monitor(cmd, name):
            nonlocal current_task
            parser_status["current_user"] = current_task + 1
            parser_status["current_user_name"] = f"正在运行{name}..."
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1
            )
            
            # 实时读取输出
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    print(output.strip())
                    sys.stdout.flush()
            
            # 获取返回码和错误信息
            returncode = process.poll()
            if returncode != 0:
                stderr = process.stderr.read()
                print(f"{name}运行失败: {stderr}")
            
            current_task += 1
        
        # 按顺序运行各个监控程序
        if monitors.get('user_wish'):
            print("\n开始运行用户想看监控...")
            run_monitor([sys.executable, "parse_douban.py"], "用户想看监控")
        
        if monitors.get('latest'):
            print("\n开始运行最新电影监控...")
            run_monitor([sys.executable, "parse_douban_new.py"], "最新电影监控")
        
        if monitors.get('popular'):
            print("\n开始运行热门电影监控...")
            run_monitor([sys.executable, "parse_douban_hot.py"], "热门电影监控")
        
        if monitors.get('hidden_gems'):
            print("\n开始运行冷门佳片监控...")
            run_monitor([sys.executable, "parse_douban_hidden_gems.py"], "冷门佳片监控")
        
        print("\n所有监控程序运行完成")
        
    except Exception as e:
        print(f"运行监控程序时出错: {e}")
        raise
    finally:
        parser_status["is_running"] = False
        parser_status["last_run"] = time.strftime("%Y-%m-%d %H:%M:%S")
        parser_status["current_process"] = None
        
        # 如果是手动更新完成，重新启动自动更新
        if is_manual:
            start_scheduler()
        else:
            # 自动更新完成后，更新下次运行时间
            interval = config.get('update_interval', 3600)
            parser_status["next_run"] = time.strftime("%Y-%m-%d %H:%M:%S", 
                time.localtime(time.time() + interval))

def start_scheduler():
    """启动定时器"""
    global scheduler_thread, stop_scheduler
    
    # 停止现有的定时器
    if scheduler_thread and scheduler_thread.is_alive():
        stop_scheduler = True
        scheduler_thread.join()
    
    # 重置停止标志
    stop_scheduler = False
    
    # 更新下次运行时间
    config = load_config()
    interval = config.get('update_interval', 3600)
    parser_status["next_run"] = time.strftime("%Y-%m-%d %H:%M:%S", 
        time.localtime(time.time() + interval))
    
    # 创建新的定时器线程
    scheduler_thread = threading.Thread(target=scheduler_loop)
    scheduler_thread.daemon = True
    scheduler_thread.start()

def scheduler_loop():
    """定时器循环"""
    while not stop_scheduler:
        config = load_config()
        interval = config.get('update_interval', 3600)
        
        # 等待指定的时间间隔
        for _ in range(interval):
            if stop_scheduler:
                break
            time.sleep(1)
            
        if not stop_scheduler and not parser_status["is_running"]:
            try:
                run_parser()
            except Exception as e:
                print(f"定时任务执行出错: {e}")

def stop_existing_scheduler():
    """停止现有的定时器"""
    global scheduler_thread, stop_scheduler
    if scheduler_thread and scheduler_thread.is_alive():
        stop_scheduler = True
        scheduler_thread.join(timeout=1)
        print("已停止现有定时器")

@app.route('/run_parser', methods=['POST'])
def start_parser():
    """启动解析程序"""
    if parser_status["is_running"]:
        return jsonify({
            "status": "error",
            "message": "解析程序正在运行中"
        })
    
    # 停止自动更新
    stop_existing_scheduler()
    
    # 在新线程中运行解析程序
    thread = threading.Thread(target=run_parser, kwargs={"is_manual": True})
    thread.start()
    
    return jsonify({
        "status": "success",
        "message": "解析程序已启动"
    })

@app.route('/parser_status')
def get_parser_status():
    """获取解析程序状态"""
    return jsonify({
        "is_running": parser_status["is_running"],
        "last_run": parser_status["last_run"],
        "next_run": parser_status["next_run"],
        "total_users": parser_status.get("total_users", 0),
        "current_user": parser_status.get("current_user", 0),
        "current_user_name": parser_status.get("current_user_name", "")
    })

def load_config():
    """加载配置"""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # 转换旧格式到新格式
                if isinstance(config.get('user_ids'), list):
                    config['users'] = [{'id': uid, 'note': ''} for uid in config['user_ids']]
                    del config['user_ids']
                # 确保监控选项存在
                if 'monitors' not in config:
                    config['monitors'] = {
                        'user_wish': True,      # 监控用户想看
                        'latest': False,        # 监控最新
                        'popular': False,       # 监控最热
                        'hidden_gems': False    # 监控冷门佳片
                    }
                return config
    except Exception as e:
        print(f"加载配置失败: {e}")
    
    # 默认配置（新格式）
    return {
        "cookie": "",
        "users": [],
        "update_interval": 3600,  # 默认1小时
        "monitors": {
            "user_wish": True,     # 监控用户想看
            "latest": False,       # 监控最新
            "popular": False,      # 监控最热
            "hidden_gems": False   # 监控冷门佳片
        }
    }

def save_config(config):
    """保存配置"""
    try:
        # 确保配置目录存在
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"保存配置失败: {e}")
        return False

@app.route('/setup_password', methods=['GET', 'POST'])
def setup_password():
    """首次设置密码"""
    config = load_config()
    
    # 如果已经设置了密码，重定向到登录页
    if config.get('password'):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        confirm = request.form.get('confirm')
        
        if not password:
            return render_template('setup_password.html', error='请输入密码')
        
        if password != confirm:
            return render_template('setup_password.html', error='两次输入的密码不一致')
        
        # 保存密码（实际应用中应该保存哈希值）
        config['password'] = password
        save_config(config)
        
        # 设置登录状态
        session['logged_in'] = True
        return redirect(url_for('config_page'))
    
    return render_template('setup_password.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """登录页面"""
    config = load_config()
    
    # 如果还没设置密码，重定向到设置密码页面
    if not config.get('password'):
        return redirect(url_for('setup_password'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        
        if password == config.get('password'):
            session['logged_in'] = True
            return redirect(url_for('config_page'))
        else:
            return render_template('login.html', error='密码错误')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """登出"""
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/')
def config_page():
    """配置页面"""
    config = load_config()
    
    # 如果还没设置密码，重定向到设置密码页面
    if not config.get('password'):
        return redirect(url_for('setup_password'))
    
    # 如果未登录，重定向到登录页面
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    # 为了兼容性，确保返回的config包含user_ids
    if 'users' in config:
        config['user_ids'] = [user['id'] for user in config['users']]
    return render_template('config.html', config=config)

@app.route('/save_config', methods=['POST'])
def save_config_handler():
    """保存配置处理"""
    try:
        # 先加载现有配置
        current_config = load_config()
        
        # 获取用户列表
        user_ids = request.form.get('user_ids', '').split(',')
        user_notes = request.form.get('user_notes', '').split(',')
        
        # 构建用户列表
        users = []
        for i, uid in enumerate(user_ids):
            uid = uid.strip()
            if uid:  # 只添加非空ID
                note = user_notes[i] if i < len(user_notes) else ''
                users.append({"id": uid, "note": note.strip()})
        
        # 获取监控配置
        monitors = {
            "user_wish": request.form.get('monitor_user_wish') == 'true',
            "latest": request.form.get('monitor_latest') == 'true',
            "popular": request.form.get('monitor_popular') == 'true',
            "hidden_gems": request.form.get('monitor_hidden_gems') == 'true'
        }
        
        # 获取 Telegram 配置
        telegram_config = {
            "enabled": request.form.get('telegram_enabled') == 'true',
            "bot_token": request.form.get('telegram_bot_token', ''),
            "chat_id": request.form.get('telegram_chat_id', '')
        }
        
        config = {
            # 保留原有密码
            "password": current_config.get('password'),
            "cookie": request.form.get('cookie', ''),
            "users": users,
            "update_interval": int(request.form.get('update_interval', 3600)),
            "telegram": telegram_config,
            "monitors": monitors
        }
        
        save_config(config)
        
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

def load_json_file(file_path):
    """加载指定的 JSON 文件"""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"加载数据失败: {e}")
    return {}

def clean_title(title, info, is_tv=False):
    """清理标题并添加年份"""
    # 获取主标题（/前的部分）
    main_title = title.split(' / ')[0].strip()
    
    # 如果是剧集，去掉"第x季"的部分
    if is_tv:
        main_title = re.sub(r'\s*第[一二三四五六七八九十\d]+季.*$', '', main_title)
        return main_title  # 电视剧直接返回标题，不添加年份
    
    # 电影才添加年份
    year = None
    for info_item in info:
        # 匹配年份格式 YYYY-MM-DD 或 YYYY
        if isinstance(info_item, str):
            match = re.search(r'(\d{4})(?:-\d{2}-\d{2})?(?:\(|$)', info_item)
            if match:
                year = match.group(1)
                break
    
    # 如果找到年份，添加到标题中（仅对电影）
    if year:
        return f"{main_title} {year}"
    return main_title

def convert_to_radarr_format(items, is_tv=False):
    """转换为Radarr格式"""
    result = []
    for item in items:
        # 获取标题和年份
        title = item.get('title', '')
        year = item.get('year')  # 直接从item中获取year字段
        
        # 处理标题
        main_title = title.split(' / ')[0].strip()
        if is_tv:
            # 电视剧去掉"第x季"的部分
            main_title = re.sub(r'\s*第[一二三四五六七八九十\d]+季.*$', '', main_title)
        elif year:
            # 电影添加年份
            main_title = f"{main_title} {year}"
            
        # 构建返回数据
        media_data = {
            "title": main_title,
            "poster_url": item.get('cover_url', '')
        }
        
        # 只有在有 imdb_id 时才添加该字段
        if item.get('imdb_id'):
            media_data["imdb_id"] = item.get('imdb_id')
            
        result.append(media_data)
    return result

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

@app.route('/movies')
def get_movies():
    """获取所有用户想看的电影"""
    data = load_json_file(MOVIES_FILE)
    unique_movies = get_unique_items(data, 'movies')
    return jsonify(convert_to_radarr_format(unique_movies))

@app.route('/tv')
def get_tv_shows():
    """获取所有用户想看的电视剧"""
    data = load_json_file(MOVIES_FILE)
    unique_shows = get_unique_items(data, 'tv_shows')
    return jsonify(convert_to_radarr_format(unique_shows, is_tv=True))

@app.route('/new_movies')
def get_new_movies():
    """获取最新电影"""
    data = load_json_file(NEW_MOVIES_FILE)
    movies = data.get('movies', [])
    return jsonify(convert_to_radarr_format(movies))

@app.route('/new_tv')
def get_new_tv():
    """获取最新电视剧"""
    data = load_json_file(NEW_MOVIES_FILE)
    tv_shows = data.get('tv_shows', [])
    return jsonify(convert_to_radarr_format(tv_shows, is_tv=True))

@app.route('/hot_movies')
def get_hot_movies():
    """获取热门电影"""
    data = load_json_file(HOT_MOVIES_FILE)
    movies = data.get('movies', [])
    return jsonify(convert_to_radarr_format(movies))

@app.route('/hot_tv')
def get_hot_tv():
    """获取热门电视剧"""
    data = load_json_file(HOT_MOVIES_FILE)
    tv_shows = data.get('tv_shows', [])
    return jsonify(convert_to_radarr_format(tv_shows, is_tv=True))

@app.route('/hidden_gems_movies')
def get_hidden_gems_movies():
    """获取冷门佳片电影"""
    data = load_json_file(HIDDEN_GEMS_FILE)
    movies = data.get('movies', [])
    return jsonify(convert_to_radarr_format(movies))

@app.route('/hidden_gems_tv')
def get_hidden_gems_tv():
    """获取冷门佳片电视剧"""
    data = load_json_file(HIDDEN_GEMS_FILE)
    tv_shows = data.get('tv_shows', [])
    return jsonify(convert_to_radarr_format(tv_shows, is_tv=True))

@app.route('/health')
def health_check():
    """健康检查"""
    return jsonify({"status": "healthy"})

@app.route('/change_password', methods=['POST'])
def change_password():
    """修改密码"""
    if not session.get('logged_in'):
        return jsonify({"status": "error", "message": "未登录"})
        
    try:
        config = load_config()
        current = request.form.get('current')
        new_password = request.form.get('new_password')
        confirm = request.form.get('confirm')
        
        if not current or not new_password or not confirm:
            return jsonify({"status": "error", "message": "所有字段都必须填写"})
            
        if current != config.get('password'):
            return jsonify({"status": "error", "message": "当前密码错误"})
            
        if new_password != confirm:
            return jsonify({"status": "error", "message": "两次输入的新密码不一致"})
            
        config['password'] = new_password
        save_config(config)
        
        return jsonify({"status": "success", "message": "密码修改成功"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/check_cookie', methods=['POST'])
def check_cookie():
    """检测 Cookie 有效性"""
    try:
        data = request.get_json()
        cookie = data.get('cookie', '')
        
        if not cookie:
            return jsonify({
                "status": "error",
                "message": "请输入 Cookie"
            })
        
        # 使用一个简单的豆瓣请求来测试 cookie
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Cookie': cookie
        }
        
        # 尝试访问豆瓣电影主页
        response = requests.get('https://movie.douban.com/', headers=headers, timeout=10)
        
        # 调试输出
        print("\n=== 调试信息 ===")
        print(f"状态码: {response.status_code}")
        print(f"URL: {response.url}")
        print("\n=== 页面内容片段 ===")
        print(response.text[:1000])  # 只打印前1000个字符
        print("\n=== 页面包含的关键词 ===")
        keywords = ['登录豆瓣', '我的豆瓣', '退出']
        for keyword in keywords:
            print(f"'{keyword}' 是否存在: {keyword in response.text}")
        print("=== 调试信息结束 ===\n")
        
        # 检查登录状态
        if response.status_code in [401, 403] or '登录豆瓣' in response.text:
            return jsonify({
                "status": "error",
                "message": "Cookie 已失效，需要重新登录"
            })
        
        # 检查是否包含已登录用户才能看到的元素
        if '我的豆瓣' not in response.text and '退出' not in response.text:
            return jsonify({
                "status": "error",
                "message": "Cookie 无效或权限不足"
            })
        
        return jsonify({
            "status": "success",
            "message": "Cookie 有效"
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"检测出错: {str(e)}"
        })

@app.route('/restart_scheduler', methods=['POST'])
def restart_scheduler():
    """重启定时器"""
    try:
        # 停止现有定时器
        stop_existing_scheduler()
        
        # 启动新的定时器
        start_scheduler()
        
        return jsonify({
            "status": "success",
            "message": "定时器已重启"
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        })

if __name__ == '__main__':
    # 启动定时器
    start_scheduler()
    
    app.run(host='0.0.0.0', port=9150, debug=True) 