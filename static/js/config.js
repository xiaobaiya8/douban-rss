// 显示toast提示
function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    
    // 添加图标
    let icon = '';
    if (type === 'success') icon = '<i class="bi bi-check-circle"></i> ';
    else if (type === 'error') icon = '<i class="bi bi-x-circle"></i> ';
    else if (type === 'info') icon = '<i class="bi bi-info-circle"></i> ';
    
    toast.innerHTML = icon + message;
    toast.className = `toast toast-${type} show`;
    
    setTimeout(() => {
        toast.className = 'toast';
    }, 3000);
}

function showAlert(message, type) {
    showToast(message, type);
}

// 用户列表数据结构
let users = [];

// 广播用户列表数据结构
let statuses = [];

// 隐藏的广播用户数据
const statusesHidden = JSON.parse(document.getElementById('config-statuses-data').textContent || '[]');

// 隐藏的片单数据
let doulists = JSON.parse(document.getElementById('config-doulist-data')?.textContent || '[]');

// 初始化用户列表
function initUserList() {
    try {
        // 尝试从服务器配置中获取用户列表
        const configUsersElement = document.getElementById('config-users-data');
        if (configUsersElement) {
            const configUsersJson = configUsersElement.textContent;
            if (configUsersJson) {
                users = JSON.parse(configUsersJson);
            } else {
                users = [];
            }
        } else {
            // 兼容旧版本，直接从模板解析
            const serverUsersRaw = '{{ config.users|tojson|safe if config.users else "[]" }}';
            if (serverUsersRaw && serverUsersRaw !== '[]' && !serverUsersRaw.includes('{{')) {
                users = JSON.parse(serverUsersRaw);
            } else {
                users = [];
            }
        }
    } catch (error) {
        console.error('解析用户列表出错:', error);
        users = [];
    }
    
    renderUserList();
    
    // 初始化广播用户列表
    try {
        // 尝试从服务器配置中获取广播用户列表
        const configStatusesElement = document.getElementById('config-statuses-data');
        if (configStatusesElement) {
            const configStatusesJson = configStatusesElement.textContent;
            if (configStatusesJson) {
                statuses = JSON.parse(configStatusesJson);
            } else {
                statuses = [];
            }
        } else {
            // 兼容旧版本，直接从模板解析
            const serverStatusesRaw = '{{ config.statuses|tojson|safe if config.statuses else "[]" }}';
            if (serverStatusesRaw && serverStatusesRaw !== '[]' && !serverStatusesRaw.includes('{{')) {
                statuses = JSON.parse(serverStatusesRaw);
            } else {
                statuses = [];
            }
        }
    } catch (error) {
        console.error('解析广播用户列表出错:', error);
        statuses = [];
    }
    
    renderStatusList();
}

// 渲染用户列表
function renderUserList() {
    const userList = document.getElementById('userList');
    if (!userList) return;
    
    if (users.length === 0) {
        userList.innerHTML = '<div class="empty-state">没有添加任何用户，请添加需要监控的用户</div>';
        return;
    }
    
    userList.innerHTML = users.map((user, index) => `
        <div class="user-item">
            <span class="user-id">${user.id}</span>
            <div class="user-content">
                <input type="text" 
                       class="user-note-input" 
                       value="${user.note || ''}" 
                       placeholder="添加备注" 
                       onchange="updateUserNote(${index}, this.value)">
                <div class="input-with-label">
                    <input type="number" 
                           class="user-pages-input" 
                           value="${user.pages || 1}" 
                           min="1" 
                           max="10"
                           onchange="updateUserPages(${index}, this.value)">
                    <span class="input-label">页</span>
                </div>
                <div class="user-monitor-types">
                    <label class="checkbox-label small">
                        <input type="checkbox" 
                               ${user.monitor_wish !== false ? 'checked' : ''} 
                               onchange="updateUserMonitorType(${index}, 'wish', this.checked)">
                        <span>想看</span>
                    </label>
                    <label class="checkbox-label small">
                        <input type="checkbox" 
                               ${user.monitor_do === true ? 'checked' : ''} 
                               onchange="updateUserMonitorType(${index}, 'do', this.checked)">
                        <span>在看</span>
                    </label>
                    <label class="checkbox-label small">
                        <input type="checkbox" 
                               ${user.monitor_collect === true ? 'checked' : ''} 
                               onchange="updateUserMonitorType(${index}, 'collect', this.checked)">
                        <span>已看</span>
                    </label>
                </div>
            </div>
            <button type="button" 
                    class="btn-delete" 
                    onclick="removeUser(${index})">
                    <i class="bi bi-trash"></i> 删除
            </button>
        </div>
    `).join('');
}

// 渲染广播用户列表
function renderStatusList() {
    const statusList = document.getElementById('statusList');
    if (!statusList) return;
    
    if (statuses.length === 0) {
        statusList.innerHTML = '<div class="empty-state">没有添加任何广播用户，请添加需要监控的广播</div>';
        return;
    }
    
    statusList.innerHTML = statuses.map((status, index) => `
        <div class="user-item">
            <span class="user-id">${status.id || ''}</span>
            <div class="user-content">
                <input type="text" 
                       class="user-note-input" 
                       value="${status.note || ''}" 
                       placeholder="添加备注" 
                       onchange="updateStatusNote(${index}, this.value)">
                <div class="input-with-label">
                    <input type="number" 
                           class="user-pages-input" 
                           value="${status.pages || 1}" 
                           min="1" 
                           max="10"
                           onchange="updateStatusPages(${index}, this.value)">
                    <span class="input-label">页</span>
                </div>
                <a href="https://www.douban.com/people/${status.id}/statuses" target="_blank" class="btn-view" title="查看广播">
                    <i class="bi bi-box-arrow-up-right"></i>
                </a>
            </div>
            <button type="button" 
                    class="btn-delete" 
                    onclick="removeStatus(${index})">
                    <i class="bi bi-trash"></i> 删除
            </button>
        </div>
    `).join('');
}

// 添加新用户
function addUser() {
    const idInput = document.getElementById('newUserId');
    const noteInput = document.getElementById('newUserNote');
    const pagesInput = document.getElementById('newUserPages');
    const wishInput = document.getElementById('newUserWish');
    const doInput = document.getElementById('newUserDo');
    const collectInput = document.getElementById('newUserCollect');
    
    const id = idInput.value.trim();
    const note = noteInput.value.trim();
    const pages = parseInt(pagesInput.value) || 1;
    const monitor_wish = wishInput.checked;
    const monitor_do = doInput.checked;
    const monitor_collect = collectInput.checked;
    
    if (id) {
        if (!users.some(u => u.id === id)) {
            if (!monitor_wish && !monitor_do && !monitor_collect) {
                showToast('请至少选择一种监控类型', 'error');
                return;
            }
            
            users.push({ 
                id, 
                note, 
                pages: Math.min(Math.max(pages, 1), 10),  // 1-10页范围
                monitor_wish, 
                monitor_do, 
                monitor_collect 
            });
            
            renderUserList();
            idInput.value = '';
            noteInput.value = '';
            pagesInput.value = '1';
            wishInput.checked = true;
            doInput.checked = false;
            collectInput.checked = false;
            
            saveConfig(() => {
                showToast('用户添加成功');
            });
        } else {
            showToast('该用户ID已存在', 'error');
        }
    } else {
        showToast('请输入用户ID', 'error');
    }
}

// 删除用户
function removeUser(index) {
    if (confirm('确定要删除这个用户吗？')) {
        users.splice(index, 1);
        renderUserList();
        saveConfig(() => {
            showToast('用户已删除');
        });
    }
}

// 更新备注
function updateUserNote(index, note) {
    users[index].note = note;
    saveConfig(() => {
        showToast('备注已更新');
    });
}

// 更新用户监控类型
function updateUserMonitorType(index, type, checked) {
    if (type === 'wish') {
        users[index].monitor_wish = checked;
    } else if (type === 'do') {
        users[index].monitor_do = checked;
    } else if (type === 'collect') {
        users[index].monitor_collect = checked;
    }
    
    // 确保至少有一个监控类型被选中
    const user = users[index];
    if (!user.monitor_wish && !user.monitor_do && !user.monitor_collect) {
        showToast('至少需要选择一种监控类型', 'error');
        // 恢复之前的状态
        if (type === 'wish') {
            user.monitor_wish = true;
            renderUserList(); // 重新渲染以更新UI
        } else if (type === 'do') {
            user.monitor_do = true;
            renderUserList();
        } else if (type === 'collect') {
            user.monitor_collect = true;
            renderUserList();
        }
        return;
    }
    
    saveConfig(() => {
        showToast('监控类型已更新');
    });
}

// 更新用户抓取页数
function updateUserPages(index, pages) {
    const pagesNum = parseInt(pages) || 1;
    if (pagesNum >= 1 && pagesNum <= 10) {
        users[index].pages = pagesNum;
        saveConfig(() => {
            showToast('用户抓取页数已更新');
        });
    } else {
        showToast('用户抓取页数必须在1-10之间', 'error');
        renderUserList(); // 恢复原值
    }
}

// 添加新广播用户
function addStatus() {
    const idInput = document.getElementById('newStatusId');
    const noteInput = document.getElementById('newStatusNote');
    const pagesInput = document.getElementById('newStatusPages');
    const id = idInput.value.trim();
    const note = noteInput.value.trim();
    const pages = parseInt(pagesInput.value) || 1;
    
    if (id) {
        if (!statuses.some(s => s.id === id)) {
            statuses.push({ id, note, pages });
            renderStatusList();
            idInput.value = '';
            noteInput.value = '';
            pagesInput.value = '1';
            saveConfig(() => {
                showToast('广播用户添加成功');
            });
        } else {
            showToast('该广播用户ID已存在', 'error');
        }
    } else {
        showToast('请输入广播用户ID', 'error');
    }
}

// 删除广播用户
function removeStatus(index) {
    if (confirm('确定要删除这个广播用户吗？')) {
        statuses.splice(index, 1);
        renderStatusList();
        saveConfig(() => {
            showToast('广播用户已删除');
        });
    }
}

// 更新广播用户备注
function updateStatusNote(index, note) {
    statuses[index].note = note.trim();
    saveConfig(() => {
        showToast('广播用户备注已更新');
    });
}

// 更新广播抓取页数
function updateStatusPages(index, pages) {
    const pagesNum = parseInt(pages) || 1;
    if (pagesNum >= 1 && pagesNum <= 10) {
        statuses[index].pages = pagesNum;
        saveConfig(() => {
            showToast('广播抓取页数已更新');
        });
    } else {
        showToast('广播抓取页数必须在1-10之间', 'error');
        renderStatusList(); // 恢复原值
    }
}

// 保存配置
function saveConfig(successCallback) {
    // 禁用保存按钮，显示加载中状态
    const saveButtons = document.querySelectorAll('.btn-save');
    saveButtons.forEach(btn => {
        btn.disabled = true;
        btn.innerHTML = '<i class="bi bi-arrow-repeat spin"></i> 保存中...';
    });
    
    // 获取用户监控配置
    const monitor_user_wish = document.getElementById('monitor_user_wish').checked;
    const monitor_status = document.getElementById('monitor_status').checked;
    const monitor_latest = document.getElementById('monitor_latest').checked;
    const monitor_popular = document.getElementById('monitor_popular').checked;
    const monitor_hidden_gems = document.getElementById('monitor_hidden_gems').checked;
    const monitor_doulist = document.getElementById('monitor_doulist').checked;
    
    // 获取基本配置
    const cookie = document.getElementById('cookie').value;
    const update_interval = parseInt(document.getElementById('update_interval').value);
    
    // 获取Telegram配置
    const telegram_enabled = document.getElementById('telegram_enabled').checked;
    const telegram_bot_token = document.getElementById('telegram_bot_token').value;
    const telegram_chat_id = document.getElementById('telegram_chat_id').value;
    const telegram_notify_mode = document.querySelector('input[name="telegram_notify_mode"]:checked')?.value || 'always';
    
    // 添加Telegram代理配置
    const telegram_proxy_enabled = document.getElementById('telegram_proxy_enabled')?.checked || false;
    const telegram_proxy_type = document.getElementById('telegram_proxy_type')?.value || 'http';
    const telegram_proxy_url = document.getElementById('telegram_proxy_url')?.value || '';
    
    // 获取企业微信配置
    const wecom_enabled = document.getElementById('wecom_enabled').checked;
    const wecom_corpid = document.getElementById('wecom_corpid').value;
    const wecom_corpsecret = document.getElementById('wecom_corpsecret').value;
    const wecom_agentid = document.getElementById('wecom_agentid').value;
    const wecom_touser = document.getElementById('wecom_touser').value || '@all';
    const wecom_notify_mode = document.querySelector('input[name="wecom_notify_mode"]:checked')?.value || 'always';
    
    // 构建详细的用户数据
    const usersData = JSON.stringify(users);
    
    // 构建广播用户列表
    const statusesData = JSON.stringify(statuses);
    
    // 添加片单监控
    const doulistsData = JSON.stringify(doulists);
    
    // 创建表单数据
    const formData = new FormData();
    formData.append('cookie', cookie);
    formData.append('update_interval', update_interval);
    formData.append('users_data', usersData);
    formData.append('statuses_data', statusesData);
    formData.append('doulists_data', doulistsData);
    
    // 添加监控设置
    formData.append('monitor_user_wish', monitor_user_wish);
    formData.append('monitor_status', monitor_status);
    formData.append('monitor_latest', monitor_latest);
    formData.append('monitor_popular', monitor_popular);
    formData.append('monitor_hidden_gems', monitor_hidden_gems);
    formData.append('monitor_doulist', monitor_doulist);
    
    // 添加Telegram设置
    formData.append('telegram_enabled', telegram_enabled);
    formData.append('telegram_bot_token', telegram_bot_token);
    formData.append('telegram_chat_id', telegram_chat_id);
    formData.append('telegram_notify_mode', telegram_notify_mode);
    
    // 添加Telegram代理配置
    formData.append('telegram_proxy_enabled', telegram_proxy_enabled);
    formData.append('telegram_proxy_type', telegram_proxy_type);
    formData.append('telegram_proxy_url', telegram_proxy_url);
    
    // 添加企业微信配置
    formData.append('wecom_enabled', wecom_enabled);
    formData.append('wecom_corpid', wecom_corpid);
    formData.append('wecom_corpsecret', wecom_corpsecret);
    formData.append('wecom_agentid', wecom_agentid);
    formData.append('wecom_touser', wecom_touser);
    formData.append('wecom_notify_mode', wecom_notify_mode);
    
    // 发送请求
    fetch('/save_config', {
        method: 'POST',
        body: formData,
    })
    .then(response => response.json())
    .then(data => {
        // 恢复保存按钮
        saveButtons.forEach(btn => {
            btn.disabled = false;
            btn.innerHTML = '<i class="bi bi-check-lg"></i> 保存';
        });
        
        if (data.status === 'success') {
            if (successCallback) {
                successCallback();
            } else {
                showToast('配置已保存');
            }
            
            // 检查是否需要重启定时器
            restartScheduler();
        } else {
            showToast('保存失败：' + data.message, 'error');
        }
    })
    .catch(error => {
        // 恢复保存按钮
        saveButtons.forEach(btn => {
            btn.disabled = false;
            btn.innerHTML = '<i class="bi bi-check-lg"></i> 保存';
        });
        
        showToast('保存失败：' + error, 'error');
    });
}

// 防抖函数 - 避免频繁保存
function debounce(func, wait) {
    let timeout;
    return function() {
        const context = this;
        const args = arguments;
        clearTimeout(timeout);
        timeout = setTimeout(() => {
            func.apply(context, args);
        }, wait);
    };
}

// 更新解析器状态
function updateParserStatus() {
    fetch('/parser_status')
        .then(response => response.json())
        .then(data => {
            const statusDiv = document.getElementById('parserStatus');
            const runButton = document.getElementById('runButton');
            const statusIcon = statusDiv.querySelector('.status-icon i');
            const statusText = statusDiv.querySelector('.status-text');
            
            if (data.is_running) {
                statusDiv.className = 'status-info status-running';
                if (statusIcon) {
                    statusIcon.className = 'bi bi-arrow-clockwise';
                }
                
                runButton.disabled = true;
                
                let statusHtml = '状态: 正在运行';
                if (data.current_user && data.total_users) {
                    // 计算进度百分比
                    const progress = data.current_user / data.total_users * 100;
                    statusHtml += ` (${data.current_user}/${data.total_users})... ${progress.toFixed(1)}%`;
                }
                
                statusHtml += '<br>';
                
                if (data.current_user_name) {
                    statusHtml += `当前用户: ${data.current_user_name}`;
                } else {
                    statusHtml += '准备中...';
                }
                
                if (statusText) {
                    statusText.innerHTML = statusHtml;
                } else {
                    statusDiv.innerHTML = `
                        <div class="status-icon"><i class="bi bi-arrow-clockwise"></i></div>
                        <div class="status-text">${statusHtml}</div>
                    `;
                }
            } else {
                statusDiv.className = 'status-info status-idle';
                if (statusIcon) {
                    statusIcon.className = 'bi bi-check-circle';
                }
                
                runButton.disabled = false;
                // 确保按钮文本恢复到初始状态
                runButton.innerHTML = '<i class="bi bi-arrow-clockwise"></i> 立即更新数据';
                
                let statusHtml = '状态: 空闲<br>';
                statusHtml += `上次更新: ${data.last_run || '从未运行'}<br>`;
                statusHtml += `下次更新: ${data.next_run || '未设置'}`;
                
                if (statusText) {
                    statusText.innerHTML = statusHtml;
                } else {
                    statusDiv.innerHTML = `
                        <div class="status-icon"><i class="bi bi-check-circle"></i></div>
                        <div class="status-text">${statusHtml}</div>
                    `;
                }
            }
        })
        .catch(error => {
            console.error('获取状态失败:', error);
        });
}

// 检查是否需要重启定时器
function restartScheduler() {
    // 发送请求重启定时器
    fetch('/restart_scheduler', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            console.log('定时器已重启');
        } else {
            console.error('定时器重启失败:', data.message);
        }
    })
    .catch(error => {
        console.error('定时器重启出错:', error);
    });
}

// 运行解析器
function runParser() {
    const runButton = document.getElementById('runButton');
    const originalText = runButton.innerHTML;
    runButton.disabled = true;
    runButton.innerHTML = '<i class="bi bi-hourglass-split"></i> 启动中...';
    
    fetch('/run_parser', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'error') {
            showToast(data.message, 'error');
            runButton.disabled = false;
            runButton.innerHTML = originalText;
        } else {
            showToast('开始更新数据', 'info');
        }
        updateParserStatus();
    })
    .catch(error => {
        showToast('启动失败: ' + error, 'error');
        runButton.disabled = false;
        runButton.innerHTML = originalText;
    });
}

// 处理 Telegram 设置的显示/隐藏
function updateTelegramSettings() {
    const enabled = document.getElementById('telegram_enabled').checked;
    const settingsDiv = document.getElementById('telegramSettings');
    
    if (settingsDiv) {
        if (enabled) {
            settingsDiv.classList.add('show');
        } else {
            settingsDiv.classList.remove('show');
        }
    }
    
    // 更新代理设置显示状态
    updateTelegramProxySettings();
}

// 添加更新代理设置的函数
function updateTelegramProxySettings() {
    const proxyEnabled = document.getElementById('telegram_proxy_enabled')?.checked;
    const proxySettingsDiv = document.getElementById('telegramProxySettings');
    
    if (proxySettingsDiv) {
        if (proxyEnabled) {
            proxySettingsDiv.classList.add('show');
        } else {
            proxySettingsDiv.classList.remove('show');
        }
    }
}

// Tab 切换功能
function switchTab(tabName) {
    // 隐藏所有 tab 内容
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // 取消所有 tab 按钮的激活状态
    document.querySelectorAll('.tab-button').forEach(button => {
        button.classList.remove('active');
    });
    
    // 显示选中的 tab
    document.getElementById(`${tabName}-tab`).classList.add('active');
    
    // 激活对应的按钮
    const activeButton = document.querySelector(`.tab-button[onclick*="switchTab('${tabName}')"]`);
    if (activeButton) {
        activeButton.classList.add('active');
    }
    
    // 保存当前tab到本地存储
    localStorage.setItem('douban_config_active_tab', tabName);
}

// 修改密码
function changePassword() {
    const current = document.getElementById('current_password').value;
    const newPassword = document.getElementById('new_password').value;
    const confirm = document.getElementById('confirm_password').value;
    
    if (!current || !newPassword || !confirm) {
        showToast('所有字段都必须填写', 'error');
        return;
    }
    
    if (newPassword !== confirm) {
        showToast('两次输入的新密码不一致', 'error');
        return;
    }
    
    const formData = new FormData();
    formData.set('current', current);
    formData.set('new_password', newPassword);
    formData.set('confirm', confirm);
    
    const button = document.querySelector('.password-form button');
    const originalText = button.innerHTML;
    button.disabled = true;
    button.innerHTML = '<i class="bi bi-hourglass-split"></i> 修改中...';
    
    fetch('/change_password', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            showToast('密码修改成功');
            // 清空输入框
            document.getElementById('current_password').value = '';
            document.getElementById('new_password').value = '';
            document.getElementById('confirm_password').value = '';
        } else {
            showToast(data.message || '修改失败', 'error');
        }
    })
    .catch(error => {
        showToast('修改失败: ' + error, 'error');
    })
    .finally(() => {
        button.disabled = false;
        button.innerHTML = originalText;
    });
}

// 退出登录
function logout() {
    if (confirm('确定要退出登录吗？')) {
        window.location.href = '/logout';
    }
}

// 检测Cookie有效性
function checkCookie() {
    const cookie = document.getElementById('cookie').value.trim();
    if (!cookie) {
        showToast('请先输入 Cookie', 'error');
        return;
    }
    
    const button = document.getElementById('checkCookieBtn');
    const originalText = button.innerHTML;
    button.disabled = true;
    button.innerHTML = '<i class="bi bi-hourglass-split"></i> 检测中...';
    
    fetch('/check_cookie', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ cookie })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            showToast('✅ Cookie 有效', 'success');
        } else {
            showToast('❌ ' + (data.message || 'Cookie 无效'), 'error');
        }
    })
    .catch(error => {
        showToast('❌ 检测失败: ' + error, 'error');
    })
    .finally(() => {
        button.disabled = false;
        button.innerHTML = originalText;
    });
}

// 主题切换功能
function toggleTheme() {
    const body = document.body;
    const themeSwitch = document.getElementById('themeSwitch');
    const moonIcon = '<i class="bi bi-moon-fill"></i>';
    const sunIcon = '<i class="bi bi-sun-fill"></i>';
    
    // 检查当前主题
    if (body.classList.contains('dark-mode')) {
        // 从深色切换到浅色
        body.classList.remove('dark-mode');
        body.classList.add('light-mode');
        themeSwitch.innerHTML = moonIcon;
        localStorage.setItem('theme', 'light');
    } else if (body.classList.contains('light-mode')) {
        // 从浅色切换到深色
        body.classList.remove('light-mode');
        body.classList.add('dark-mode');
        themeSwitch.innerHTML = sunIcon;
        localStorage.setItem('theme', 'dark');
    } else {
        // 如果没有类，则检查系统首选项
        const prefersDarkMode = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
        
        if (prefersDarkMode) {
            // 系统是深色，切换到浅色
            body.classList.remove('dark-mode');
            body.classList.add('light-mode');
            themeSwitch.innerHTML = moonIcon;
            localStorage.setItem('theme', 'light');
        } else {
            // 系统是浅色，切换到深色
            body.classList.remove('light-mode');
            body.classList.add('dark-mode');
            themeSwitch.innerHTML = sunIcon;
            localStorage.setItem('theme', 'dark');
        }
    }
}

// 初始化主题
function initTheme() {
    const body = document.body;
    const themeSwitch = document.getElementById('themeSwitch');
    const savedTheme = localStorage.getItem('theme');
    const prefersDarkMode = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    const moonIcon = '<i class="bi bi-moon-fill"></i>';
    const sunIcon = '<i class="bi bi-sun-fill"></i>';
    
    if (savedTheme === 'dark') {
        body.classList.add('dark-mode');
        if (body.classList.contains('light-mode')) {
            body.classList.remove('light-mode');
        }
        themeSwitch.innerHTML = sunIcon;
    } else if (savedTheme === 'light') {
        body.classList.add('light-mode');
        if (body.classList.contains('dark-mode')) {
            body.classList.remove('dark-mode');
        }
        themeSwitch.innerHTML = moonIcon;
    } else if (prefersDarkMode) {
        // 如果系统是深色模式并且用户没有保存首选项，应用深色主题
        body.classList.add('dark-mode');
        themeSwitch.innerHTML = sunIcon;
    } else {
        // 默认使用浅色主题
        body.classList.add('light-mode');
        themeSwitch.innerHTML = moonIcon;
    }
    
    // 添加切换事件监听器
    themeSwitch.addEventListener('click', toggleTheme);
    
    // 监听系统主题变化
    if (window.matchMedia) {
        const colorSchemeQuery = window.matchMedia('(prefers-color-scheme: dark)');
        if (colorSchemeQuery.addEventListener) {
            colorSchemeQuery.addEventListener('change', (event) => {
                if (!localStorage.getItem('theme')) {
                    if (event.matches) {
                        body.classList.remove('light-mode');
                        body.classList.add('dark-mode');
                        themeSwitch.innerHTML = sunIcon;
                    } else {
                        body.classList.remove('dark-mode');
                        body.classList.add('light-mode');
                        themeSwitch.innerHTML = moonIcon;
                    }
                }
            });
        }
    }
}

/**
 * 显示用户ID教程指南
 */
function showUserIdGuide() {
    const modalId = 'userIdGuideModal';
    
    // 如果模态框已存在则直接显示
    let modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'block';
        return;
    }
    
    // 创建模态框
    modal = document.createElement('div');
    modal.id = modalId;
    modal.className = 'modal';
    
    // 模态框内容
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h3>如何获取豆瓣用户ID</h3>
                <span class="close">&times;</span>
            </div>
            <div class="modal-body">
                <div class="guide-step">
                    <div class="step-number">1</div>
                    <div class="step-content">
                        <p>登录您的豆瓣账号</p>
                    </div>
                </div>
                <div class="guide-step">
                    <div class="step-number">2</div>
                    <div class="step-content">
                        <p>点击页面右上角的头像，进入"个人主页"</p>
                    </div>
                </div>
                <div class="guide-step">
                    <div class="step-number">3</div>
                    <div class="step-content">
                        <p>查看浏览器地址栏，URL格式为：</p>
                        <div class="url-example">
                            <p>https://www.douban.com/people/<span class="highlight">user_id</span>/</p>
                        </div>
                        <p>其中 <span class="highlight">user_id</span> 部分即为您的豆瓣用户ID</p>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // 添加到页面
    document.body.appendChild(modal);
    
    // 获取关闭按钮并添加事件
    const closeBtn = modal.querySelector('.close');
    closeBtn.onclick = function() {
        modal.style.display = 'none';
    }
    
    // 点击模态框外部也可关闭
    window.onclick = function(event) {
        if (event.target == modal) {
            modal.style.display = 'none';
        }
    }
    
    // 显示模态框
    modal.style.display = 'block';
}

// 初始化工具提示
function initTooltips() {
    document.querySelectorAll('[title]').forEach(element => {
        const title = element.getAttribute('title');
        if (!title) return;
        
        // 创建工具提示元素
        element.addEventListener('mouseenter', function(e) {
            // 移除任何现有工具提示
            const existingTooltip = document.querySelector('.tooltip');
            if (existingTooltip) {
                existingTooltip.remove();
            }
            
            const tooltip = document.createElement('div');
            tooltip.className = 'tooltip';
            tooltip.textContent = title;
            document.body.appendChild(tooltip);
            
            // 定位工具提示
            const rect = element.getBoundingClientRect();
            tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
            tooltip.style.top = rect.top - tooltip.offsetHeight - 10 + window.scrollY + 'px';
            
            // 处理边界检查，确保提示不会超出屏幕
            const tooltipRect = tooltip.getBoundingClientRect();
            if (tooltipRect.left < 0) {
                tooltip.style.left = '5px';
            } else if (tooltipRect.right > window.innerWidth) {
                tooltip.style.left = (window.innerWidth - tooltipRect.width - 5) + 'px';
            }
            
            // 显示工具提示
            setTimeout(() => {
                tooltip.classList.add('show');
            }, 10);
        });
        
        // 移除工具提示
        element.addEventListener('mouseleave', function() {
            const tooltip = document.querySelector('.tooltip');
            if (tooltip) {
                tooltip.classList.remove('show');
                setTimeout(() => {
                    if (tooltip.parentNode) {
                        tooltip.parentNode.removeChild(tooltip);
                    }
                }, 300);
            }
        });
        
        // 清除title属性，防止原生工具提示
        element.setAttribute('data-original-title', title);
        element.removeAttribute('title');
    });
}

// 初始化广播用户列表
function initStatusList() {
    statuses = JSON.parse(document.getElementById('config-statuses-data').textContent || '[]');
    renderStatusList();
}

// 初始化片单列表
function initDoulistList() {
    doulists = JSON.parse(document.getElementById('config-doulist-data')?.textContent || '[]');
    renderDoulistList();
}

// 渲染片单列表
function renderDoulistList() {
    const doulistList = document.getElementById('doulistList');
    if (!doulistList) return;
    
    if (doulists.length === 0) {
        doulistList.innerHTML = '<div class="empty-state">没有添加任何片单，请添加需要监控的片单</div>';
        return;
    }
    
    doulistList.innerHTML = doulists.map((doulist, index) => `
        <div class="user-item">
            <span class="user-id">${doulist.id}</span>
            <div class="user-content">
                <input type="text" 
                       class="user-note-input" 
                       value="${doulist.note || ''}" 
                       placeholder="片单备注" 
                       onchange="updateDoulistNote(${index}, this.value)">
                <div class="input-with-label">
                    <input type="number" 
                           class="user-pages-input" 
                           value="${doulist.pages || 5}" 
                           min="1" 
                           max="20"
                           onchange="updateDoulistPages(${index}, this.value)">
                    <span class="input-label">页</span>
                </div>
            </div>
            <button type="button" 
                    class="btn-delete" 
                    onclick="removeDoulist(${index})">
                    <i class="bi bi-trash"></i> 删除
            </button>
        </div>
    `).join('');
}

// 添加片单
function addDoulist() {
    const id = document.getElementById('newDoulistId').value.trim();
    if (!id) {
        showToast('请输入片单ID', 'error');
        return;
    }
    
    // 检查是否已存在
    for (const doulist of doulists) {
        if (doulist.id === id) {
            showToast('该片单已添加', 'error');
            return;
        }
    }
    
    const note = document.getElementById('newDoulistNote').value.trim();
    const pages = parseInt(document.getElementById('newDoulistPages').value, 10) || 5;
    
    doulists.push({
        id: id,
        note: note,
        pages: Math.min(Math.max(pages, 1), 20)  // 1-20页范围
    });
    
    renderDoulistList();
    
    // 清空输入框
    document.getElementById('newDoulistId').value = '';
    document.getElementById('newDoulistNote').value = '';
    document.getElementById('newDoulistPages').value = '5';
    
    // 保存配置
    saveConfig();
}

// 移除片单
function removeDoulist(index) {
    if (confirm('确定要移除该片单吗？')) {
        doulists.splice(index, 1);
        renderDoulistList();
        saveConfig();
    }
}

// 更新片单备注
function updateDoulistNote(index, note) {
    doulists[index].note = note;
    saveConfig();
}

// 更新片单页数
function updateDoulistPages(index, pages) {
    const pagesNum = parseInt(pages, 10);
    doulists[index].pages = Math.min(Math.max(pagesNum, 1), 20);  // 1-20页范围
    saveConfig();
}

// 显示片单ID教程
function showDoulistIdGuide() {
    const modalId = 'doulistIdGuideModal';
    
    // 如果模态框已存在则直接显示
    let modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'block';
        return;
    }
    
    // 创建模态框
    modal = document.createElement('div');
    modal.id = modalId;
    modal.className = 'modal';
    
    // 模态框内容
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h3>如何获取豆瓣片单ID</h3>
                <span class="close">&times;</span>
            </div>
            <div class="modal-body">
                <div class="guide-step">
                    <div class="step-number">1</div>
                    <div class="step-content">
                        <p>访问您想要添加的豆瓣片单页面</p>
                    </div>
                </div>
                <div class="guide-step">
                    <div class="step-number">2</div>
                    <div class="step-content">
                        <p>查看浏览器地址栏，URL格式为：</p>
                        <div class="url-example">
                            <p>https://www.douban.com/doulist/<span class="highlight">1907705</span>/</p>
                        </div>
                        <p>其中 <span class="highlight">1907705</span> 部分即为片单ID</p>
                    </div>
                </div>
                <div class="guide-step">
                    <div class="step-number">3</div>
                    <div class="step-content">
                        <p>提示：</p>
                        <ul>
                            <li>您可以添加任何公开的豆瓣片单</li>
                            <li>系统会自动只抓取片单中的电影和剧集内容</li>
                            <li>片单越长，抓取的时间越长</li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // 添加到页面
    document.body.appendChild(modal);
    
    // 获取关闭按钮并添加事件
    const closeBtn = modal.querySelector('.close');
    closeBtn.onclick = function() {
        modal.style.display = 'none';
    }
    
    // 点击模态框外部也可关闭
    window.onclick = function(event) {
        if (event.target == modal) {
            modal.style.display = 'none';
        }
    }
    
    // 显示模态框
    modal.style.display = 'block';
}

// 切换通知方式
function switchNotifyMethod(method) {
    // 切换按钮状态
    const buttons = document.querySelectorAll('.method-button');
    buttons.forEach(btn => {
        btn.classList.remove('active');
    });
    
    const activeButton = document.querySelector(`.method-button[onclick*="${method}"]`);
    if (activeButton) {
        activeButton.classList.add('active');
    }
    
    // 切换显示区域
    const sections = document.querySelectorAll('.notify-section');
    sections.forEach(section => {
        section.classList.remove('active');
    });
    
    const activeSection = document.getElementById(`${method}-notify-config`);
    if (activeSection) {
        activeSection.classList.add('active');
    }
    
    // 更新通知方式启用状态
    if (method === 'telegram') {
        // 启用Telegram，禁用企业微信
        document.getElementById('wecom_enabled').checked = false;
        updateWecomSettings();
        saveConfig();
    } else if (method === 'wecom') {
        // 启用企业微信，禁用Telegram
        document.getElementById('telegram_enabled').checked = false;
        updateTelegramSettings();
        saveConfig();
    }
}

// 处理企业微信设置的显示/隐藏
function updateWecomSettings() {
    const enabled = document.getElementById('wecom_enabled').checked;
    const settingsDiv = document.getElementById('wecomSettings');
    
    if (settingsDiv) {
        if (enabled) {
            settingsDiv.classList.add('show');
        } else {
            settingsDiv.classList.remove('show');
        }
    }
}

// 初始化页面
document.addEventListener('DOMContentLoaded', function() {
    // 初始化主题
    initTheme();
    
    // 初始化用户列表
    initUserList();
    
    // 初始化广播用户列表
    initStatusList();
    
    // 初始化片单列表
    initDoulistList();
    
    // 立即更新一次状态
    updateParserStatus();
    
    // 每2秒更新一次状态
    setInterval(updateParserStatus, 2000);
    
    // 添加监控选项的变更监听
    document.querySelectorAll('.monitors-config input[type="checkbox"]').forEach(checkbox => {
        checkbox.addEventListener('change', () => {
            saveConfig(() => {
                showToast('监控配置已更新');
            });
        });
    });
    
    // 添加广播用户按钮点击事件
    const addStatusBtn = document.querySelector('.add-status-btn');
    if (addStatusBtn) {
        addStatusBtn.addEventListener('click', addStatus);
    }
    
    // 修改 cookie 输入框监听，改用 input 事件实现实时保存
    const cookieInput = document.getElementById('cookie');
    if (cookieInput) {
        cookieInput.addEventListener('input', debounce(function() {
            saveConfig(() => {
                showToast('Cookie已更新');
            });
        }, 1000));  // 1秒延迟，避免频繁保存
    }
    
    // 修改更新间隔输入框监听
    const intervalInput = document.getElementById('update_interval');
    if (intervalInput) {
        intervalInput.addEventListener('input', debounce(function() {
            if (parseInt(intervalInput.value) < 300) {
                showToast('更新间隔不能小于300秒', 'error');
                intervalInput.value = 300;
                return;
            }
            
            saveConfig(() => {
                // 发送请求重启定时器
                fetch('/restart_scheduler', {
                    method: 'POST'
                })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        showToast('更新间隔已更新');
                    } else {
                        showToast(data.message || '更新间隔设置失败', 'error');
                    }
                })
                .catch(error => {
                    showToast('更新间隔设置失败: ' + error, 'error');
                });
            });
        }, 1000));
    }
    
    // 处理 Telegram 设置的显示/隐藏
    const telegramEnabled = document.getElementById('telegram_enabled');
    if (telegramEnabled) {
        updateTelegramSettings();
        
        telegramEnabled.addEventListener('change', function() {
            updateTelegramSettings();
            
            // 如果启用Telegram，切换到Telegram界面并禁用企业微信
            if (this.checked) {
                document.getElementById('wecom_enabled').checked = false;
                updateWecomSettings();
                switchNotifyMethod('telegram');
            }
            
            saveConfig(function() {
                showToast('Telegram 配置已更新');
            });
        });
    }
    
    // 处理 Telegram Bot Token 输入
    const telegramBotToken = document.getElementById('telegram_bot_token');
    if (telegramBotToken) {
        telegramBotToken.addEventListener('input', debounce(function() {
            saveConfig();
        }, 1000));
    }
    
    // 处理 Telegram Chat ID 输入
    const telegramChatId = document.getElementById('telegram_chat_id');
    if (telegramChatId) {
        telegramChatId.addEventListener('input', debounce(function() {
            saveConfig();
        }, 1000));
    }
    
    // 处理 Telegram 通知模式选择
    document.querySelectorAll('input[name="telegram_notify_mode"]').forEach(radio => {
        radio.addEventListener('change', function() {
            saveConfig(function() {
                showToast('通知模式已更新');
            });
        });
    });
    
    // 处理 Telegram 代理设置
    const telegramProxyCheckbox = document.getElementById('telegram_proxy_enabled');
    if (telegramProxyCheckbox) {
        telegramProxyCheckbox.addEventListener('change', function() {
            updateTelegramProxySettings();
            saveConfig(function() {
                showToast('代理设置已更新');
            });
        });
    }
    
    // 处理 Telegram 代理类型选择
    const telegramProxyType = document.getElementById('telegram_proxy_type');
    if (telegramProxyType) {
        telegramProxyType.addEventListener('change', function() {
            saveConfig(function() {
                showToast('代理类型已更新');
            });
        });
    }
    
    // 处理 Telegram 代理地址输入
    const telegramProxyUrl = document.getElementById('telegram_proxy_url');
    if (telegramProxyUrl) {
        telegramProxyUrl.addEventListener('input', debounce(function() {
            saveConfig();
        }, 1000));
    }
    
    // 从本地存储恢复上次打开的tab
    const lastTab = localStorage.getItem('douban_config_active_tab');
    if (lastTab && document.getElementById(`${lastTab}-tab`)) {
        switchTab(lastTab);
    }
    
    // 添加动态表单验证
    const passwordInputs = document.querySelectorAll('.password-form input[type="password"]');
    if (passwordInputs.length > 0) {
        passwordInputs.forEach(input => {
            input.addEventListener('input', function() {
                // 检查新密码和确认密码是否匹配
                const newPassword = document.getElementById('new_password');
                const confirmPassword = document.getElementById('confirm_password');
                
                if (newPassword && confirmPassword && 
                    newPassword.value && confirmPassword.value && 
                    newPassword.value !== confirmPassword.value) {
                    confirmPassword.setCustomValidity('两次输入的密码不匹配');
                } else if (confirmPassword) {
                    confirmPassword.setCustomValidity('');
                }
            });
        });
    }
    
    // 添加页面淡入效果
    document.body.classList.add('loaded');
    
    // 获取服务器地址
    const serverAddressEl = document.getElementById('server-address');
    if (serverAddressEl) {
        const protocol = window.location.protocol;
        const hostname = window.location.hostname;
        const port = window.location.port;
        const serverAddress = `${protocol}//${hostname}${port ? ':' + port : ''}`;
        serverAddressEl.textContent = serverAddress;
    }
    
    // 为所有复制按钮添加事件
    const copyButtons = document.querySelectorAll('.copy-btn');
    copyButtons.forEach(button => {
        button.addEventListener('click', function() {
            const path = this.getAttribute('data-path');
            const protocol = window.location.protocol;
            const hostname = window.location.hostname;
            const port = window.location.port;
            let textToCopy;
            
            if (this.id === 'copy-address-btn') {
                textToCopy = serverAddressEl.textContent;
            } else {
                textToCopy = `${protocol}//${hostname}${port ? ':' + port : ''}${path}`;
            }
            
            // 提供兼容性更好的复制功能实现
            function copyTextToClipboard(text) {
                // 首先尝试使用现代Clipboard API
                if (navigator.clipboard && navigator.clipboard.writeText) {
                    return navigator.clipboard.writeText(text)
                        .then(() => true)
                        .catch(() => {
                            // 如果Clipboard API失败，使用fallback方法
                            return fallbackCopyTextToClipboard(text);
                        });
                } else {
                    // 浏览器不支持Clipboard API，使用fallback方法
                    return Promise.resolve(fallbackCopyTextToClipboard(text));
                }
            }
            
            // 兼容性方法：使用textarea元素复制
            function fallbackCopyTextToClipboard(text) {
                const textArea = document.createElement("textarea");
                textArea.value = text;
                
                // 将textarea设置为不可见
                textArea.style.position = "fixed";
                textArea.style.top = "-999999px";
                textArea.style.left = "-999999px";
                document.body.appendChild(textArea);
                
                // 保存当前选中内容
                const selected = document.getSelection().rangeCount > 0 
                    ? document.getSelection().getRangeAt(0) 
                    : false;
                
                // 选中文本并复制
                textArea.select();
                let success = false;
                try {
                    success = document.execCommand('copy');
                } catch (err) {
                    console.error('Fallback: 复制到剪贴板失败', err);
                }
                
                // 清理
                document.body.removeChild(textArea);
                
                // 恢复原始选择
                if (selected) {
                    document.getSelection().removeAllRanges();
                    document.getSelection().addRange(selected);
                }
                
                return success;
            }
            
            copyTextToClipboard(textToCopy)
                .then((success) => {
                    // 复制成功，修改按钮图标为成功状态
                    const originalIcon = this.innerHTML;
                    this.innerHTML = '<i class="bi bi-check"></i>';
                    this.style.color = '#28a745';
                    
                    // 显示Toast提示
                    showToast('复制成功！', 'success');
                    
                    // 1秒后恢复原始图标
                    setTimeout(() => {
                        this.innerHTML = originalIcon;
                        this.style.color = '';
                    }, 1000);
                })
                .catch(err => {
                    console.error('复制失败: ', err);
                    showToast('复制失败', 'error');
                });
        });
    });
    
    // 初始化工具提示
    initTooltips();
    
    // 处理企业微信设置
    const wecomEnabled = document.getElementById('wecom_enabled');
    if (wecomEnabled) {
        updateWecomSettings();
        
        wecomEnabled.addEventListener('change', function() {
            updateWecomSettings();
            
            // 如果启用企业微信，切换到企业微信界面并禁用Telegram
            if (this.checked) {
                document.getElementById('telegram_enabled').checked = false;
                updateTelegramSettings();
                switchNotifyMethod('wecom');
            }
            
            saveConfig(function() {
                showToast('企业微信配置已更新');
            });
        });
    }
    
    // 企业微信配置字段自动保存
    const wecomFields = [
        'wecom_corpid', 
        'wecom_corpsecret', 
        'wecom_agentid',
        'wecom_touser'
    ];
    
    wecomFields.forEach(field => {
        const element = document.getElementById(field);
        if (element) {
            element.addEventListener('input', debounce(function() {
                saveConfig();
            }, 1000));
        }
    });
    
    // 处理企业微信通知模式选择
    document.querySelectorAll('input[name="wecom_notify_mode"]').forEach(radio => {
        radio.addEventListener('change', function() {
            saveConfig(function() {
                showToast('通知模式已更新');
            });
        });
    });
}); 