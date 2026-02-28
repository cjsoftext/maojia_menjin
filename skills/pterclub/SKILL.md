---
name: pterclub
description: Search and download torrents from PTerClub (PT之友俱乐部). Use when the user wants to find and download torrents from PTerClub, search for specific content, or manage torrent downloads. Triggers on requests like "search PTerClub for...", "download torrent...", "find movie on PTerClub", or any PTerClub-related torrent queries.
---

# PTerClub Skill

Search and download torrents from PTerClub (PT之友俱乐部) private tracker.

## Prerequisites

- Python 3 with `requests` and `beautifulsoup4` packages
- Valid PTerClub account cookies

## Authentication

Cookies are stored in `~/.openclaw/workspace/pterclub_cookies.json`. If cookies are missing or expired, ask the user to provide their PTerClub cookies.

To get cookies:
1. Login to https://pterclub.net in browser
2. Open Developer Tools → Application/Storage → Cookies
3. Copy the cookie string (including c_secure_login, c_secure_pass, c_secure_uid, PHPSESSID)

## Workflow

### 1. Check Authentication

```bash
python3 ~/.openclaw/workspace/skills/pterclub/scripts/pterclub.py check-login
```

If this fails, ask the user for cookies:
> "Please provide your PTerClub cookies. You can find them in your browser's developer tools after logging in."

Then save them:
```bash
python3 ~/.openclaw/workspace/skills/pterclub/scripts/pterclub.py save-cookies "c_secure_login=...; c_secure_pass=...; ..."
```

### 2. Search Torrents

User provides search query in natural language. Construct appropriate keywords and search:

```bash
python3 ~/.openclaw/workspace/skills/pterclub/scripts/pterclub.py search "<keywords>"
```

The script returns JSON array of results with fields:
- `id`: Torrent ID
- `title`: Main torrent title
- `subtitle`: Subtitle/description (e.g., "XIUREN秀人网 No.10751-10800 模特写真")
- `size`: File size
- `seeders`: Number of seeders
- `leechers`: Number of leechers
- `snatched`: Download count
- `tags`: Array of tags (e.g., "Free", "国语", "中字", "禁转", "2X Free")
- `details_url`: URL to torrent details page

### 3. Present Results

Display results in a **clean list format** (NOT tables, as tables render poorly on mobile Slack).

Use this format:
```
找到以下种子：

**1.** Xing dai lu lu - Photo Set Collection-LikeArt
    └─ 副标题: Xing dai lu lu 模特写真合集
    └─ 大小: 5.33 GB | 标签: Free, 禁转

**2.** Xiao he tian jiu - Photo Set Collection-LikeArt
    └─ 副标题: Xiao he tian jiu 精选图集
    └─ 大小: 10.31 GB | 标签: Free, 禁转
```

**Formatting rules:**
- Use **bold** for the number (e.g., **1.**)
- Main title on the first line
- Subtitle indented with `└─ 副标题:`
- Size and tags on the next line indented with `└─`
- Use `|` to separate size and tags
- Show up to 10 results maximum
- Filter out duplicates and unwanted results as requested by user

### 4. Handle User Selection

User can respond in multiple ways:
- "下载 1" or just "1" → Download torrent #1
- "下载 1,3" or "1, 3" → Download torrents #1 and #3
- "全部下载" → Download all shown torrents
- "再看看" or "取消" → Cancel operation

Parse the response and extract numbers.

### 5. Download Torrents

For each selected torrent:
```bash
python3 ~/.openclaw/workspace/skills/pterclub/scripts/pterclub.py download <torrent_id>
```

The torrent file is saved to `~/.openclaw/workspace/torrents/`.

### 6. Return Results

Report to user:
- Downloaded file paths
- Basic torrent info (title, size)

Example:
```
已下载：
- Xing dai lu lu - Photo Set Collection-LikeArt.torrent (5.33 GB)
  路径: ~/.openclaw/workspace/torrents/Xing dai lu lu.torrent
```

### 7. Optional: Push to qBittorrent

If user has configured qBittorrent integration and wants to add to download queue, invoke the qbittorrent skill:

```
Use qbittorrent skill to add torrent file: <filepath>
```

## Error Handling

- **Login expired**: Ask for new cookies
- **No results**: Inform user and suggest alternative keywords
- **Download failed**: Report error, may retry once
- **Network error**: Wait 2 seconds and retry

## Rate Limiting

Be respectful to the server:
- Add 1-2 second delay between requests
- Don't make more than 5 searches per minute

## Example Interactions

**Example 1: Simple search and download**
```
User: 找一下流浪地球2的种子
Agent: [searches "流浪地球2", shows list results]
User: 下载第一个
Agent: [downloads torrent #1, returns path]
```

**Example 2: Multiple downloads**
```
User: 搜索复仇者联盟
Agent: [shows list with 5 results]
User: 下载 1,3,5
Agent: [downloads 3 torrents, returns paths]
```

**Example 3: No results**
```
User: 找某某某电影
Agent: [searches, no results]
Agent: 未找到相关种子，建议尝试英文名称或简化关键词
```

**Example 4: Filtered search**
```
User: 提取非XIUREN的最新十个LikeArt种子
Agent: [searches "LikeArt", filters out XIUREN, shows 10 results]
```

## Cookie Storage Location

- File: `~/.openclaw/workspace/pterclub_cookies.json`
- Format: JSON with `cookies` object and `saved_at` timestamp
- Torrent download directory: `~/.openclaw/workspace/torrents/`
