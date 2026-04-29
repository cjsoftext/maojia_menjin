#!/usr/bin/env python3
"""
Commit generated GKD rule to GitHub repository.

Usage:
    python3 commit_rule.py \
        --repo cjsoftext/gkd-rule \
        --rule-file /path/to/rule.json \
        --message "Add rule: xxx for yyy" \
        [--token GITHUB_TOKEN]

Environment:
    GH_TOKEN - GitHub token (optional, falls back to env var)
"""

import json
import os
import sys
import argparse
import subprocess
import tempfile
import shutil
from typing import Dict, Any


def clone_repo(repo: str, token: str = None) -> str:
    """Clone repository to temp directory."""
    temp_dir = tempfile.mkdtemp(prefix="gkd-repo-")
    
    if token:
        url = f"https://{token}@github.com/{repo}.git"
    else:
        url = f"https://github.com/{repo}.git"
    
    result = subprocess.run(
        ["git", "clone", "--depth", "1", url, temp_dir],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        raise RuntimeError(f"Failed to clone repo: {result.stderr}")
    
    return temp_dir


def load_subscription(repo_path: str) -> Dict:
    """Load subscription.json from repo."""
    sub_path = os.path.join(repo_path, "subscription.json")
    if os.path.exists(sub_path):
        with open(sub_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "id": -2,
        "name": "本地订阅",
        "version": 7,
        "globalGroups": [],
        "categories": [],
        "apps": []
    }


def save_subscription(repo_path: str, subscription: Dict):
    """Save subscription.json to repo."""
    sub_path = os.path.join(repo_path, "subscription.json")
    with open(sub_path, 'w', encoding='utf-8') as f:
        json.dump(subscription, f, ensure_ascii=False, indent=2)


def merge_rule(subscription: Dict, new_rule: Dict) -> Dict:
    """Merge new rule into subscription."""
    new_app = new_rule.get("app", {})
    new_group = new_rule.get("group", {})
    
    app_id = new_app.get("id")
    
    # Find existing app
    existing_app = None
    for app in subscription.get("apps", []):
        if app.get("id") == app_id:
            existing_app = app
            break
    
    if existing_app:
        # Check for existing group with same name
        existing_group = None
        for group in existing_app.get("groups", []):
            if group.get("name") == new_group.get("name"):
                existing_group = group
                break
        
        if existing_group:
            # Update existing group
            existing_group.update(new_group)
        else:
            # Add new group with auto-incremented key
            existing_keys = [g.get("key", 0) for g in existing_app.get("groups", [])]
            new_key = max(existing_keys) + 1 if existing_keys else 1
            new_group["key"] = new_key
            existing_app.setdefault("groups", []).append(new_group)
    else:
        # Add new app
        subscription.setdefault("apps", []).append(new_app)
    
    # Increment version
    subscription["version"] = subscription.get("version", 0) + 1
    
    return subscription


def commit_and_push(repo_path: str, message: str, token: str = None):
    """Commit changes and push to GitHub."""
    # Configure git
    subprocess.run(["git", "config", "user.name", "GKD Rule Generator"], cwd=repo_path, check=True)
    subprocess.run(["git", "config", "user.email", "gkd@openclaw.local"], cwd=repo_path, check=True)
    
    # Add changes
    subprocess.run(["git", "add", "subscription.json"], cwd=repo_path, check=True)
    
    # Commit
    result = subprocess.run(
        ["git", "commit", "-m", message],
        cwd=repo_path,
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0 and "nothing to commit" not in result.stderr.lower():
        raise RuntimeError(f"Failed to commit: {result.stderr}")
    
    # Push
    result = subprocess.run(
        ["git", "push"],
        cwd=repo_path,
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        raise RuntimeError(f"Failed to push: {result.stderr}")


def main():
    parser = argparse.ArgumentParser(description="Commit GKD rule to GitHub")
    parser.add_argument("--repo", default="cjsoftext/gkd-rule", help="GitHub repo")
    parser.add_argument("--rule-file", required=True, help="Path to generated rule JSON")
    parser.add_argument("--message", required=True, help="Commit message")
    parser.add_argument("--token", default=os.environ.get("GH_TOKEN"), help="GitHub token")
    
    args = parser.parse_args()
    
    if not args.token:
        print(json.dumps({"error": "GitHub token required"}), file=sys.stderr)
        sys.exit(1)
    
    repo_path = None
    try:
        # Load rule
        with open(args.rule_file, 'r', encoding='utf-8') as f:
            rule = json.load(f)
        
        # Clone repo
        print(f"Cloning {args.repo}...", file=sys.stderr)
        repo_path = clone_repo(args.repo, args.token)
        
        # Load subscription
        subscription = load_subscription(repo_path)
        
        # Merge rule
        print("Merging rule...", file=sys.stderr)
        subscription = merge_rule(subscription, rule)
        
        # Save subscription
        save_subscription(repo_path, subscription)
        
        # Commit and push
        print("Committing...", file=sys.stderr)
        commit_and_push(repo_path, args.message, args.token)
        
        result = {
            "success": True,
            "repo": args.repo,
            "app": rule.get("app", {}).get("name"),
            "groupKey": rule.get("groupKey"),
            "subscriptionUrl": f"https://gkd-rule-cjsoftexts-projects.vercel.app/subscription.json"
        }
        
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)
    finally:
        if repo_path:
            shutil.rmtree(repo_path, ignore_errors=True)


if __name__ == "__main__":
    main()
