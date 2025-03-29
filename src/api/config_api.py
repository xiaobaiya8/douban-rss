import json

# 处理广播用户数据
if 'statuses_data' in request.form:
    statuses = json.loads(request.form.get('statuses_data', '[]'))
    config['statuses'] = statuses
    
# 处理片单数据
if 'doulists_data' in request.form:
    doulists = json.loads(request.form.get('doulists_data', '[]'))
    config['doulists'] = doulists
    
# 处理监控设置
monitors = config.get('monitors', {})
# 更新监控设置
monitors.update({
    'user_wish': bool(request.form.get('monitor_user_wish', False)),
    'status': bool(request.form.get('monitor_status', False)),
    'latest': bool(request.form.get('monitor_latest', False)),
    'popular': bool(request.form.get('monitor_popular', False)),
    'hidden_gems': bool(request.form.get('monitor_hidden_gems', False)),
    'doulist': bool(request.form.get('monitor_doulist', False))
})

config['monitors'] = monitors

# 处理监控设置 