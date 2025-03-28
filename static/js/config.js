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
            <input type="text" 
                   class="user-note-input" 
                   value="${user.note || ''}" 
                   placeholder="添加备注" 
                   onchange="updateUserNote(${index}, this.value)">
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
            <div class="user-actions">
                <input type="text" 
                       class="user-note-input" 
                       value="${status.note || ''}" 
                       placeholder="添加备注" 
                       onchange="updateStatusNote(${index}, this.value)">
                <div class="input-with-label">
                    <input type="number" 
                           class="status-pages-input" 
                           value="${status.pages || 1}" 
                           min="1" 
                           max="10"
                           onchange="updateStatusPages(${index}, this.value)">
                    <span class="input-label">页</span>
                </div>
                <a href="https://www.douban.com/people/${status.id}/statuses" target="_blank" class="btn-view" title="查看广播">
                    <i class="bi bi-box-arrow-up-right"></i>
                </a>
                <button type="button" 
                        class="btn-delete" 
                        onclick="removeStatus(${index})">
                        <i class="bi bi-trash"></i> 删除
                </button>
            </div>
        </div>
    `).join('');
}

// 添加新用户
function addUser() {
    const idInput = document.getElementById('newUserId');
    const noteInput = document.getElementById('newUserNote');
    const id = idInput.value.trim();
    const note = noteInput.value.trim();
    
    if (id) {
        if (!users.some(u => u.id === id)) {
            users.push({ id, note });
            renderUserList();
            idInput.value = '';
            noteInput.value = '';
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
    
    // 获取基本配置
    const cookie = document.getElementById('cookie').value;
    const update_interval = parseInt(document.getElementById('update_interval').value);
    
    // 获取Telegram配置
    const telegram_enabled = document.getElementById('telegram_enabled').checked;
    const telegram_bot_token = document.getElementById('telegram_bot_token').value;
    const telegram_chat_id = document.getElementById('telegram_chat_id').value;
    const telegram_notify_mode = document.querySelector('input[name="telegram_notify_mode"]:checked').value;
    
    // 构建用户ID和备注列表
    const user_ids = users.map(u => u.id).join(',');
    const user_notes = users.map(u => u.note || '').join(',');
    
    // 构建广播用户列表
    const status_ids = statuses.map(s => s.id).join(',');
    const status_notes = statuses.map(s => s.note || '').join(',');
    const status_pages = statuses.map(s => s.pages || 1).join(',');
    
    // 创建表单数据
    const formData = new FormData();
    formData.append('cookie', cookie);
    formData.append('update_interval', update_interval);
    formData.append('user_ids', user_ids);
    formData.append('user_notes', user_notes);
    
    // 添加广播用户数据
    formData.append('status_ids', status_ids);
    formData.append('status_notes', status_notes);
    formData.append('status_pages', status_pages);
    
    // 添加监控设置
    formData.append('monitor_user_wish', monitor_user_wish);
    formData.append('monitor_status', monitor_status);
    formData.append('monitor_latest', monitor_latest);
    formData.append('monitor_popular', monitor_popular);
    formData.append('monitor_hidden_gems', monitor_hidden_gems);
    
    // 添加Telegram设置
    formData.append('telegram_enabled', telegram_enabled);
    formData.append('telegram_bot_token', telegram_bot_token);
    formData.append('telegram_chat_id', telegram_chat_id);
    formData.append('telegram_notify_mode', telegram_notify_mode);
    
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
    const telegramEnabled = document.getElementById('telegram_enabled');
    const telegramSettings = document.getElementById('telegramSettings');
    
    if (!telegramEnabled || !telegramSettings) return;
    
    if (telegramEnabled.checked) {
        telegramSettings.classList.add('show');
    } else {
        telegramSettings.classList.remove('show');
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

// 初始化页面
document.addEventListener('DOMContentLoaded', function() {
    // 初始化主题
    initTheme();
    
    // 初始化用户列表
    initUserList();
    
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
        
        // 只在用户手动改变时保存配置
        telegramEnabled.addEventListener('change', function() {
            updateTelegramSettings();
            saveConfig(() => {
                showToast('Telegram 配置已更新');
            });
        });
    }
    
    // 添加 Bot Token 和 Chat ID 的实时保存
    const telegramBotToken = document.getElementById('telegram_bot_token');
    if (telegramBotToken) {
        telegramBotToken.addEventListener('input', debounce(function() {
            saveConfig(() => {
                showToast('Bot Token 已更新');
            });
        }, 1000));
    }
    
    const telegramChatId = document.getElementById('telegram_chat_id');
    if (telegramChatId) {
        telegramChatId.addEventListener('input', debounce(function() {
            saveConfig(() => {
                showToast('Chat ID 已更新');
            });
        }, 1000));
    }
    
    // 添加通知模式单选按钮的事件监听
    document.querySelectorAll('input[name="telegram_notify_mode"]').forEach(radio => {
        radio.addEventListener('change', function() {
            saveConfig(() => {
                showToast('通知模式已更新');
            });
        });
    });
    
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
}); 