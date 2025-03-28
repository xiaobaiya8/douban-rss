# Douban Movies/TV API

A tool for monitoring Douban movie and TV series information and providing API interfaces. It supports automatic synchronization of user wishlists, latest movies/TV shows, popular content, and hidden gems.

## Features

- **User Wishlist Monitoring**: Automatically synchronize movies and TV shows from Douban user wishlists
- **Popular List Monitoring**: Provides Douban's latest, most popular, and hidden gem lists
- **Radarr/Sonarr Compatible**: API interface format compatible with Radarr and Sonarr import
- **RSS Feed Support**: Provides standard RSS subscription interfaces for RSS readers and MoviePilot
- **Custom Update Frequency**: Configurable automatic update intervals
- **Multi-user Support**: Monitor wishlists from multiple Douban users simultaneously
- **Telegram Notifications**: Support for sending update notifications via Telegram
- **User-friendly Web Configuration Interface**: Easy-to-use configuration management page
- **Dark/Light Theme**: Support for automatic and manual dark/light theme switching

## Quick Start

### Using Docker Compose (Recommended)

1. Create a project directory and download the source code

```bash
git clone https://github.com/xiaobaiya8/xiaobai-douban.git
cd xiaobai-douban
```

2. Start the service

```bash
docker-compose up -d
```

3. Access the Web interface for configuration

```
http://your-ip:9150
```

## Configuration Guide

When accessing the Web interface for the first time, you need to set an access password. After logging in, you can configure the following:

### Basic Configuration

- **Cookie**: Douban website Cookie, used for accessing user data (required)
- **Monitoring Items**: Select the types of data to monitor (user wishlist, latest, most popular, hidden gems)

### User List

- Add Douban user IDs to monitor (can be found in the user's profile URL)
- Add notes for users for easier management

### Update Interval

- Set the time interval for automatic updates (minimum 5 minutes)

### Telegram Notifications

- Configure Telegram Bot Token and Chat ID to enable update notifications

## API Interfaces

Once successfully configured, the system provides the following API interfaces:

### For Radarr/Sonarr and Similar Automatic Download Software

| Content | API Endpoint | Description |
| ---- | ---- | ---- |
| User Movie Wishlist | `/rss/movies` | All movies in users' wishlists |
| User TV Wishlist | `/rss/tv` | All TV shows in users' wishlists |
| Latest Movies | `/rss/new_movies` | Douban latest movies |
| Popular Movies | `/rss/hot_movies` | Douban popular movies |
| Popular TV Shows | `/rss/hot_tv` | Douban popular TV shows |
| Hidden Gem Movies | `/rss/hidden_gems_movies` | Douban hidden but highly rated movies |

### For RSSHub/MoviePilot and Similar RSS Software

| Content | API Endpoint | Description |
| ---- | ---- | ---- |
| User Wishlist (All) | `/rsshub/wish` | All movies and TV shows in users' wishlists |
| User Movie Wishlist | `/rsshub/movies` | All movies in users' wishlists |
| User TV Wishlist | `/rsshub/tv` | All TV shows in users' wishlists |
| Latest Movies | `/rsshub/new_movies` | Douban latest movies |
| Popular Movies | `/rsshub/hot_movies` | Douban popular movies |
| Popular TV Shows | `/rsshub/hot_tv` | Douban popular TV shows |
| Hidden Gem Movies | `/rsshub/hidden_gems_movies` | Douban hidden but highly rated movies |

### Usage Notes

- The `/rsshub/` path returns XML format, suitable for RSS readers
- The `/rss/` path returns JSON format, suitable for Radarr/Sonarr import
- RSS data uses standard XML format, including channel and item elements that comply with specifications
- Each entry provides a link to the original Douban page URL and cover image

## Environment Variables

- `CONFIG_DIR`: Configuration file directory (default is `./config`)
- `TZ`: Timezone setting (default is `Asia/Shanghai`)

## FAQ

### How to Get Cookie

1. Log in to the Douban website
2. Press F12 in your browser to open developer tools
3. Switch to the Network tab
4. Refresh the page, select any request
5. Find Cookie in the request headers and copy the complete content

### Cookie Expiration Issues

Douban Cookies usually have a relatively long validity period. If prompted as invalid, please obtain a new one and update the configuration.

## Disclaimer

This project is for personal learning and research purposes only. Do not use it for commercial purposes. When using this tool, please comply with Douban's terms of use and relevant laws and regulations. 