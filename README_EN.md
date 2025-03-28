# Douban Movies/TV API

A tool for monitoring Douban movie and TV series information and providing API interfaces. It supports automatic synchronization of user wishlists, latest movies/TV shows, popular content, and hidden gems.

[中文文档](https://github.com/xiaobaiya8/douban-rss/blob/main/README.md)

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

### Method 1: Direct Docker Installation (Simplest)

```bash
# Create configuration directory
mkdir -p douban-rss/config

# Start container
docker run -d \
  --name douban-rss \
  -p 9150:9150 \
  -v $(pwd)/douban-rss/config:/config \
  -e TZ=Asia/Shanghai \
  -e CONFIG_DIR=/config \
  --restart unless-stopped \
  xiaobaiya000/douban-rss:latest
```

### Method 2: Using Docker Compose

1. Create project directory

```bash
mkdir -p douban-rss && cd douban-rss
```

2. Create docker-compose.yml file

```bash
cat > docker-compose.yml << EOF
version: '3'

services:
  douban-rss:
    image: xiaobaiya000/douban-rss:latest
    container_name: douban-rss
    ports:
      - "9150:9150"
    volumes:
      - ./config:/config
    restart: unless-stopped
    environment:
      - TZ=Asia/Shanghai
      - CONFIG_DIR=/config
      - PYTHONUNBUFFERED=1
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
EOF
```

3. Start service

```bash
docker-compose up -d
```

### Method 3: Build from Source (For Developers)

1. Clone repository and enter directory

```bash
git clone https://github.com/xiaobaiya8/xiaobai-douban.git
cd xiaobai-douban
```

2. Build and start with Docker Compose

```bash
docker-compose up -d
```

4. Access the Web interface for configuration

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

| Content | API Endpoint |
| ---- | ---- |
| User Movie Wishlist | `/rss/movies` |
| User TV Wishlist | `/rss/tv` |
| Latest Movies | `/rss/new_movies` |
| Popular Movies | `/rss/hot_movies` |
| Popular TV Shows | `/rss/hot_tv` |
| Hidden Gem Movies | `/rss/hidden_gems_movies` |

### For RSSHub/MoviePilot and Similar RSS Software

| Content | API Endpoint |
| ---- | ---- |
| User Wishlist (All) | `/rsshub/wish` |
| User Movie Wishlist | `/rsshub/movies` |
| User TV Wishlist | `/rsshub/tv` |
| Latest Movies | `/rsshub/new_movies` |
| Popular Movies | `/rsshub/hot_movies` |
| Popular TV Shows | `/rsshub/hot_tv` |
| Hidden Gem Movies | `/rsshub/hidden_gems_movies` |

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