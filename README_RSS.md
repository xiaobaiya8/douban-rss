# 豆瓣电影/剧集 RSS 功能说明

本模块提供了豆瓣电影和剧集的RSS订阅功能，可以方便地在RSS阅读器中订阅最新的电影和剧集信息。

## 功能特点

1. 完全独立的模块化设计，不影响主程序逻辑
2. 提供丰富的RSS订阅接口，覆盖所有数据类型
3. 符合标准的RSS格式，兼容大多数RSS阅读器
4. 包含电影/剧集详细信息和封面图片

## 可用的RSS接口

### 适用于RSSHub/MicroPub等RSS软件

| 内容 | 接口地址 | 说明 |
| ---- | ---- | ---- |
| 用户想看(全部) | `/rsshub/wish` | 所有用户想看的电影和剧集 |
| 用户想看电影 | `/rsshub/movies` | 所有用户想看的电影 |
| 用户想看剧集 | `/rsshub/tv` | 所有用户想看的电视剧 |
| 最新电影 | `/rsshub/new_movies` | 豆瓣最新电影 |
| 热门电影 | `/rsshub/hot_movies` | 豆瓣热门电影 |
| 热门剧集 | `/rsshub/hot_tv` | 豆瓣热门电视剧 |
| 冷门佳片电影 | `/rsshub/hidden_gems_movies` | 豆瓣冷门但高分的电影 |

### 适用于Radarr/Sonarr等自动下载软件

| 内容 | 接口地址 | 说明 |
| ---- | ---- | ---- |
| 用户想看电影 | `/rss/movies` | 所有用户想看的电影 |
| 用户想看剧集 | `/rss/tv` | 所有用户想看的电视剧 |
| 最新电影 | `/rss/new_movies` | 豆瓣最新电影 |
| 热门电影 | `/rss/hot_movies` | 豆瓣热门电影 |
| 热门剧集 | `/rss/hot_tv` | 豆瓣热门电视剧 |
| 冷门佳片电影 | `/rss/hidden_gems_movies` | 豆瓣冷门但高分的电影 |

## 使用方法

1. 启动豆瓣API服务后，RSS功能会自动启用

2. 在RSS阅读器中使用：
   - 添加订阅源：`http://您的服务器IP:9150/rsshub/路径`
   - 例如：`http://192.168.1.100:9150/rsshub/movies`

3. 在Radarr/Sonarr中使用：
   - 添加列表：`http://您的服务器IP:9150/rss/路径`
   - 例如：`http://192.168.1.100:9150/rss/movies`

## 技术说明

- `/rsshub/` 路径返回XML格式，适合RSS阅读器订阅
- `/rss/` 路径返回JSON格式，适合Radarr/Sonarr导入
- RSS数据使用标准的XML格式，包含符合规范的channel和item元素
- 支持atom:link和content:encoded扩展，提供更丰富的内容展示
- 每个条目都提供了链接到豆瓣原始页面的URL
- 图片和评分信息包含在description和content:encoded中

## 更新频率

RSS内容会随着豆瓣数据的更新而更新，更新频率取决于您在系统中设置的更新间隔。
