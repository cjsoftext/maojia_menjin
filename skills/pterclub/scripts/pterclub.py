#!/usr/bin/env python3
"""
PTerClub skill core module for searching and downloading torrents.
"""

import os
import json
import re
import time
from pathlib import Path
from typing import Optional, List, Dict, Any
from urllib.parse import urljoin, quote
import requests
from bs4 import BeautifulSoup

# Constants
BASE_URL = "https://pterclub.net"
COOKIE_FILE = Path.home() / ".openclaw" / "workspace" / "pterclub_cookies.json"
TORRENTS_DIR = Path.home() / ".openclaw" / "workspace" / "torrents"

# Ensure torrents directory exists
TORRENTS_DIR.mkdir(parents=True, exist_ok=True)


def load_cookies() -> Optional[Dict[str, str]]:
    """Load cookies from local storage."""
    if not COOKIE_FILE.exists():
        return None
    try:
        with open(COOKIE_FILE, 'r') as f:
            data = json.load(f)
            return data.get('cookies')
    except Exception:
        return None


def save_cookies(cookie_str: str) -> bool:
    """Save cookies to local storage."""
    try:
        # Parse cookie string into dict
        cookies = {}
        for item in cookie_str.split(';'):
            item = item.strip()
            if '=' in item:
                key, value = item.split('=', 1)
                cookies[key.strip()] = value.strip()
        
        with open(COOKIE_FILE, 'w') as f:
            json.dump({'cookies': cookies, 'saved_at': time.time()}, f)
        return True
    except Exception as e:
        print(f"Error saving cookies: {e}")
        return False


def parse_cookie_string(cookie_str: str) -> Dict[str, str]:
    """Parse a cookie string into a dictionary."""
    cookies = {}
    for item in cookie_str.split(';'):
        item = item.strip()
        if '=' in item:
            key, value = item.split('=', 1)
            cookies[key.strip()] = value.strip()
    return cookies


def check_login(cookies: Dict[str, str]) -> bool:
    """Check if cookies are valid by accessing userdetails page."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        resp = requests.get(
            f"{BASE_URL}/index.php",
            cookies=cookies,
            headers=headers,
            timeout=30,
            allow_redirects=False
        )
        # If we get redirect to login, cookies are invalid
        if resp.status_code == 302 and 'login.php' in resp.headers.get('Location', ''):
            return False
        # Check if logged in by looking for username
        if '欢迎回来' in resp.text or 'userdetails.php' in resp.text:
            return True
        return False
    except Exception as e:
        print(f"Error checking login: {e}")
        return False


def search_torrents(cookies: Dict[str, str], keyword: str) -> List[Dict[str, Any]]:
    """Search torrents by keyword."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        search_url = f"{BASE_URL}/torrents.php?search={quote(keyword)}&search_area=0&search_mode=0"

        resp = requests.get(
            search_url,
            cookies=cookies,
            headers=headers,
            timeout=30
        )
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, 'html.parser')

        results = []
        # Find torrent table rows - look for rows with class containing 'sticky' or standard torrent rows
        rows = soup.find_all('tr')

        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) < 5:
                continue

            try:
                # The title is usually in the second column (index 1)
                # Find the cell that contains a link to details.php
                title_cell = None
                title_link = None

                for cell in cells:
                    link = cell.find('a', href=re.compile(r'details\.php\?id='))
                    if link:
                        title_cell = cell
                        title_link = link
                        break

                if not title_link:
                    continue

                main_title = title_link.get_text(strip=True)
                details_url = title_link.get('href', '')
                if details_url.startswith('/'):
                    details_url = f"{BASE_URL}{details_url}"
                elif not details_url.startswith('http'):
                    details_url = f"{BASE_URL}/{details_url}"

                # Extract torrent ID
                torrent_id = None
                match = re.search(r'id=(\d+)', details_url)
                if match:
                    torrent_id = match.group(1)

                if not torrent_id:
                    continue

                # Extract subtitle - look for span in the second div (after tags)
                subtitle = ""
                # Find all divs in title_cell
                divs = title_cell.find_all('div', recursive=True)
                for div in divs:
                    # Look for span that contains the subtitle text (not in a link)
                    span = div.find('span', recursive=False)
                    if span:
                        text = span.get_text(strip=True)
                        if text and text != main_title and len(text) > 5:
                            subtitle = text
                            break
                
                # Alternative: if no span found, look for text nodes after tags
                if not subtitle:
                    # Find the div containing tags
                    for div in divs:
                        tag_link = div.find('a', href=lambda x: x and 'tag_' in x)
                        if tag_link:
                            # Get text after the tag link
                            for sibling in tag_link.next_siblings:
                                if hasattr(sibling, 'get_text'):
                                    text = sibling.get_text(strip=True)
                                else:
                                    text = str(sibling).strip()
                                if text and len(text) > 5:
                                    subtitle = text
                                    break
                            if subtitle:
                                break

                # Find index of title cell to determine other column positions
                cell_index = cells.index(title_cell)

                # Extract metadata - typically:
                # comments = cells[cell_index+1]
                # size = cells[cell_index+2] or cells[cell_index+3]
                # seeders = next column
                # leechers = next column
                # snatched = next column

                size = 'N/A'
                seeders = '0'
                leechers = '0'
                snatched = '0'

                # Try to find cells with numeric values for seeders/leechers
                for i, cell in enumerate(cells):
                    text = cell.get_text(strip=True)
                    # Look for size pattern (GB, MB, TB)
                    if re.match(r'^\d+(\.\d+)?\s*[GMKT]B$', text, re.I):
                        size = text
                    # Look for seeders (usually a number, sometimes colored)
                    elif cell.find('span', class_=re.compile(r'seed|up', re.I)) or re.match(r'^\d+$', text):
                        if seeders == '0' and text.isdigit():
                            seeders = text
                    elif cell.find('span', class_=re.compile(r'leech|down', re.I)):
                        if leechers == '0':
                            leechers = text

                # Alternative: try fixed positions if we have enough cells
                if len(cells) >= cell_index + 5:
                    # Common layout: [checkbox][cat][title][comments][size][seeders][leechers][snatched][uploader]
                    size_candidates = [cells[cell_index+2], cells[cell_index+3]] if cell_index+3 < len(cells) else [cells[cell_index+2]]
                    for cand in size_candidates:
                        text = cand.get_text(strip=True)
                        if re.match(r'^\d+(\.\d+)?\s*[GMKT]B$', text, re.I):
                            size = text
                            break

                # Extract tags (Free, 国语, 中字, 禁转, etc.)
                tags = []
                # Look for img alt text which often contains tag info
                for img in title_cell.find_all('img'):
                    alt = img.get('alt', '')
                    title_attr = img.get('title', '')
                    if alt and alt not in ['', ' ']:
                        tags.append(alt)
                    if title_attr and title_attr not in ['', ' '] and title_attr not in tags:
                        tags.append(title_attr)

                # Look for tag links
                tag_links = title_cell.find_all('a', href=re.compile(r'tag_'))
                for tag_link in tag_links:
                    tag_text = tag_link.get_text(strip=True)
                    if tag_text and tag_text not in tags:
                        tags.append(tag_text)

                # Filter out non-torrent results (like userdetails pages)
                if not details_url or 'details.php' not in details_url or 'id=' not in details_url:
                    continue
                    
                # Filter tags - only keep meaningful ones
                meaningful_tags = []
                for tag in tags:
                    # Skip UI elements and common noise
                    if tag in ['Show/Hide', 'comments', '评论数', 'time', '存活时间', 
                              'size', '大小', 'seeders', '种子数', 'leechers', '下载数',
                              'snatched', '完成数', 'Other', 'CHN', 'preview', 'download',
                              '下载本种', '还没有审核', 'Unbookmarked', '收藏', 
                              'IMDb评分', '豆瓣评分', '已通过审核']:
                        continue
                    if '电影' in tag or '电视剧' in tag or '动画' in tag or '综艺' in tag:
                        continue
                    if tag and tag not in meaningful_tags:
                        meaningful_tags.append(tag)
                
                results.append({
                    'id': torrent_id,
                    'title': main_title,
                    'subtitle': subtitle,
                    'size': size,
                    'seeders': seeders,
                    'leechers': leechers,
                    'snatched': snatched,
                    'tags': meaningful_tags,
                    'details_url': details_url
                })

            except Exception as e:
                continue

        return results

    except Exception as e:
        print(f"Error searching torrents: {e}")
        return []


def download_torrent(cookies: Dict[str, str], torrent_id: str, filename: Optional[str] = None) -> Optional[Path]:
    """Download a torrent file."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # Construct download URL - use cookies only, no passkey needed
        download_url = f"{BASE_URL}/download.php?id={torrent_id}"
        
        resp = requests.get(
            download_url,
            cookies=cookies,
            headers=headers,
            timeout=30,
            allow_redirects=True
        )
        resp.raise_for_status()
        
        # Determine filename
        if not filename:
            # Try to get from Content-Disposition
            cd = resp.headers.get('Content-Disposition', '')
            match = re.search(r'filename="?([^"]+)"?', cd)
            if match:
                filename = match.group(1)
            else:
                filename = f"{torrent_id}.torrent"
        
        # Ensure .torrent extension
        if not filename.endswith('.torrent'):
            filename += '.torrent'
        
        # Save file
        filepath = TORRENTS_DIR / filename
        counter = 1
        while filepath.exists():
            stem = Path(filename).stem
            filepath = TORRENTS_DIR / f"{stem}_{counter}.torrent"
            counter += 1
        
        with open(filepath, 'wb') as f:
            f.write(resp.content)
        
        return filepath
        
    except Exception as e:
        print(f"Error downloading torrent: {e}")
        return None


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python pterclub.py <command> [args]")
        print("Commands:")
        print("  save-cookies <cookie_string>  - Save cookies to local storage")
        print("  check-login                   - Check if cookies are valid")
        print("  search <keyword>              - Search torrents")
        print("  download <torrent_id>         - Download a torrent")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'save-cookies':
        if len(sys.argv) < 3:
            print("Error: Cookie string required")
            sys.exit(1)
        cookie_str = sys.argv[2]
        if save_cookies(cookie_str):
            print("Cookies saved successfully")
        else:
            print("Failed to save cookies")
            sys.exit(1)
    
    elif command == 'check-login':
        cookies = load_cookies()
        if not cookies:
            print("No cookies found. Please save cookies first.")
            sys.exit(1)
        if check_login(cookies):
            print("Login valid")
        else:
            print("Login invalid or expired")
            sys.exit(1)
    
    elif command == 'search':
        if len(sys.argv) < 3:
            print("Error: Keyword required")
            sys.exit(1)
        keyword = sys.argv[2]
        cookies = load_cookies()
        if not cookies:
            print("No cookies found. Please save cookies first.")
            sys.exit(1)
        results = search_torrents(cookies, keyword)
        print(json.dumps(results, ensure_ascii=False, indent=2))
    
    elif command == 'download':
        if len(sys.argv) < 3:
            print("Error: Torrent ID required")
            sys.exit(1)
        torrent_id = sys.argv[2]
        cookies = load_cookies()
        if not cookies:
            print("No cookies found. Please save cookies first.")
            sys.exit(1)
        filepath = download_torrent(cookies, torrent_id)
        if filepath:
            print(f"Downloaded: {filepath}")
        else:
            print("Download failed")
            sys.exit(1)
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
