#!/usr/bin/env python
"""
启动豆瓣RSS API服务
使用方法: python run_api.py
"""

import sys
import os
import logging

# 添加父目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def main():
    """主函数"""
    try:
        from src.api.api import app, start_scheduler
        
        # 设置环境变量 - 如果未设置CONFIG_DIR则使用默认路径
        if 'CONFIG_DIR' not in os.environ:
            os.environ['CONFIG_DIR'] = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config'))
            print(f"已设置CONFIG_DIR环境变量为: {os.environ['CONFIG_DIR']}")
        else:
            print(f"使用已设置的CONFIG_DIR: {os.environ['CONFIG_DIR']}")
        
        # 导入和注册RSS路由
        try:
            from src.api.rss_api import register_rss_routes
            register_rss_routes(app)
            print("✅ RSS 模块已成功加载并注册路由")
        except ImportError as e:
            print(f"❌ RSS 模块加载失败: {e}")
        
        # 启动定时任务调度器
        start_scheduler()
        print("✅ 定时任务调度器已启动")
        
        # 禁用Werkzeug默认的日志输出，减少控制台信息
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)  # 只记录错误级别的日志
        
        # 启动应用，使用9150端口与Dockerfile中的EXPOSE设置一致
        app.run(host='0.0.0.0', port=9150, debug=True)
    except Exception as e:
        print(f"启动API服务时出错: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 