try:
            if config['monitors'].get('status'):
                from src.parsers.parse_douban_status import main as parse_status
                parse_status()
                
            # 监控片单
            if config['monitors'].get('doulist'):
                from src.parsers.parse_douban_doulist import main as parse_doulist
                parse_doulist()
                
            # 监控豆瓣最新
            if config['monitors'].get('latest'): 