#!/usr/bin/env python
"""
测试导入路径
"""

import sys
import os

# 添加父目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def main():
    """主函数"""
    try:
        print(f"Python路径: {sys.path}")
        print(f"当前目录: {os.getcwd()}")
        
        # 尝试导入工具模块
        print("尝试导入 src.utils.douban_utils...")
        from src.utils import douban_utils
        print(f"成功导入 src.utils.douban_utils，版本: {getattr(douban_utils, '__version__', '未知')}")
        print(f"可用函数: {[func for func in dir(douban_utils) if not func.startswith('_') and callable(getattr(douban_utils, func))]}")
        
        # 尝试导入解析器模块
        print("\n尝试导入 src.parsers.parse_douban...")
        from src.parsers import parse_douban
        print(f"成功导入 src.parsers.parse_douban")
        
        print("\n环境变量:")
        for key, value in os.environ.items():
            print(f"{key}: {value}")
            
    except Exception as e:
        print(f"导入测试时出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 