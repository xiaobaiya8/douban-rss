#!/usr/bin/env python
"""
运行豆瓣解析器
使用方法: python run_parser.py [parser_name]
"""

import sys
import os
import importlib

# 添加父目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("请指定要运行的解析器名称。")
        print("可用解析器: douban, douban_status, douban_hot, douban_new, douban_hidden_gems, douban_doulist")
        sys.exit(1)
        
    parser_name = sys.argv[1]
    
    # 设置环境变量 - 如果未设置CONFIG_DIR则使用默认路径
    if 'CONFIG_DIR' not in os.environ:
        os.environ['CONFIG_DIR'] = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config'))
        print(f"已设置CONFIG_DIR环境变量为: {os.environ['CONFIG_DIR']}")
    else:
        print(f"使用已设置的CONFIG_DIR: {os.environ['CONFIG_DIR']}")
    
    # 映射解析器名称到模块
    parsers = {
        "douban": "src.parsers.parse_douban",
        "douban_status": "src.parsers.parse_douban_status",
        "douban_hot": "src.parsers.parse_douban_hot",
        "douban_new": "src.parsers.parse_douban_new",
        "douban_hidden_gems": "src.parsers.parse_douban_hidden_gems",
        "douban_doulist": "src.parsers.parse_douban_doulist"
    }
    
    if parser_name not in parsers:
        print(f"未知的解析器: {parser_name}")
        print("可用解析器: douban, douban_status, douban_hot, douban_new, douban_hidden_gems, douban_doulist")
        sys.exit(1)
    
    # 动态导入并运行模块
    try:
        module = importlib.import_module(parsers[parser_name])
        if hasattr(module, 'main'):
            module.main()
        else:
            print(f"错误: {parser_name} 模块没有 main 函数")
    except Exception as e:
        print(f"运行解析器时出错: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 