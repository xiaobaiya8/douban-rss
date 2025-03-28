# 豆瓣电影/剧集 API

一个用于监控豆瓣电影和剧集信息并提供 API 接口的工具，支持自动同步用户想看列表、最新电影/剧集、热门电影/剧集以及冷门佳片。

## 功能特点

- **用户想看列表监控**：自动同步豆瓣用户想看的电影和剧集
- **热门榜单监控**：提供豆瓣最新、最热和冷门佳片榜单
- **Radarr/Sonarr 兼容**：API 接口格式兼容 Radarr 和 Sonarr 导入
- **RSS订阅支持**：提供标准RSS订阅接口，适配各类RSS阅读器及MoviePilot
- **自定义更新频率**：可配置的自动更新时间间隔
- **多用户支持**：可同时监控多个豆瓣用户的想看列表
- **Telegram 通知**：支持通过 Telegram 发送更新通知
- **简洁易用的 Web 配置界面**：提供用户友好的配置管理页面
- **深色/浅色主题**：支持自动和手动深色/浅色主题切换

## 快速开始

### 使用 Docker Compose（推荐）

1. 创建项目目录并下载源码

```bash
git clone https://github.com/xiaobaiya8/xiaobai-douban.git
cd xiaobai-douban
```

2. 启动服务

```bash
docker-compose up -d
```

3. 访问 Web 界面进行配置

```bash
http://your-ip:9150
```

## 配置说明

首次访问 Web 界面时，需要设置访问密码。登录后，可以配置以下内容：

### 基本配置

- **Cookie**：豆瓣网站的 Cookie，用于获取用户数据（必填）
- **监控项目**：选择要监控的数据类型（用户想看、最新、最热、冷门佳片）

### 用户列表

- 添加要监控的豆瓣用户 ID（可在用户个人主页 URL 中找到）
- 可为用户添加备注，方便管理

### 更新间隔

- 设置自动更新的时间间隔（最短 5 分钟）

### Telegram 通知

- 配置 Telegram Bot Token 和 Chat ID，启用更新通知功能

## API 接口

成功配置后，系统提供以下 API 接口：

### 适用于Radarr/Sonarr等自动下载软件

| 内容 | 接口地址 |
| ---- | ---- |
| 用户想看电影 | `/rss/movies` |
| 用户想看剧集 | `/rss/tv` |
| 最新电影 | `/rss/new_movies` |
| 热门电影 | `/rss/hot_movies` |
| 热门剧集 | `/rss/hot_tv` |
| 冷门佳片电影 | `/rss/hidden_gems_movies` |

### 适用于RSSHub/MoviePilot等RSS软件

| 内容 | 接口地址 |
| ---- | ---- |
| 用户想看(全部) | `/rsshub/wish` |
| 用户想看电影 | `/rsshub/movies` |
| 用户想看剧集 | `/rsshub/tv` |
| 最新电影 | `/rsshub/new_movies` |
| 热门电影 | `/rsshub/hot_movies` |
| 热门剧集 | `/rsshub/hot_tv` |
| 冷门佳片电影 | `/rsshub/hidden_gems_movies` |

### 使用说明

- `/rsshub/` 路径返回XML格式，适合RSS阅读器订阅
- `/rss/` 路径返回JSON格式，适合Radarr/Sonarr导入
- RSS数据使用标准的XML格式，包含符合规范的channel和item元素
- 每个条目都提供了链接到豆瓣原始页面的URL和封面图片

## 环境变量

- `CONFIG_DIR`：配置文件目录（默认为 `./config`）
- `TZ`：时区设置（默认为 `Asia/Shanghai`）

## 常见问题

### Cookie 获取方法

1. 登录豆瓣网站
2. 在浏览器中按 F12 打开开发者工具
3. 切换到 Network 标签
4. 刷新页面，选择任意请求
5. 在请求头中找到 Cookie，复制完整内容

### Cookie 失效问题

豆瓣 Cookie 通常有效期较长，如果提示失效，请重新获取并更新配置。

## 声明

本项目仅用于个人学习和研究，请勿用于商业用途。使用本工具时，请遵守豆瓣网站的使用条款和相关法律法规。 