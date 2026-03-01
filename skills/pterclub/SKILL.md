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
- `alive_time`: Torrent age/survival time (e.g., "3天 5时", "2时 30分")
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
    └─ 大小: 5.33 GB | 存活: 3天 5时 | 标签: Free, 禁转

**2.** Xiao he tian jiu - Photo Set Collection-LikeArt
    └─ 副标题: Xiao he tian jiu 精选图集
    └─ 大小: 10.31 GB | 存活: 2时 30分 | 标签: Free, 禁转
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

**Preset handling (integration with qbittorrent skill):**

If the user's selection message includes a preset reference (e.g., `normal预设`, `使用 yellow 预设`), the agent should interpret this as a request to add the torrent to qBittorrent with that preset. The agent must:

1. Extract the torrent numbers and the preset name (e.g., `normal`, `yellow`).
2. For each selected torrent, call `pterclub.py download <torrent_id>` (without `--preset`).
3. After downloading the torrent file, invoke the qbittorrent skill's `add_torrent_file` tool, passing:
   - `file_path`: downloaded torrent path
   - `preset`: the preset name (e.g., `normal`, `yellow`)
4. If qBittorrent add succeeds, delete the local torrent file.
5. Return a combined success message from both steps.

**Do not modify pterclub.py to accept `--preset`.** The preset logic belongs to the agent orchestrating both skills. The pterclub skill only downloads torrents; the agent handles qBittorrent integration.

### 5. Download Torrents

For each selected torrent without a preset:
```bash
python3 ~/.openclaw/workspace/skills/pterclub/scripts/pterclub.py download <torrent_id>
```

The torrent file is saved to `~/.openclaw/workspace/torrents/`.

### 6. qBittorrent Integration (Agent-Orchestrated)

If the user specified a preset in their selection, the agent must **after downloading** invoke the qbittorrent skill's `add_torrent_file` tool, passing the `preset` name as a parameter. The qbittorrent skill knows how to map that preset to its own configuration (e.g., save_path and category).

On success, delete the local torrent file to avoid clutter. Return the qbittorrent skill's confirmation.

Ensure the qbittorrent skill is configured and reachable.

### 7. Return Results

Report to user:
- If preset was used: qBittorrent add confirmation + torrent name.
- If no preset: downloaded file paths and basic torrent info.

Example (with preset):
```
已添加到 qBittorrent (preset: normal)
- [PTer][453737].飞驰人生.Pegasus.2019.2160p.WEB-DL.H265.AAC-PTerWEB.mkv.torrent
qBittorrent: Ok.
```

Example (without preset):
```
已下载：
- Xing dai lu lu - Photo Set Collection-LikeArt.torrent (5.33 GB)
  路径: ~/.openclaw/workspace/torrents/Xing dai lu lu.torrent
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
