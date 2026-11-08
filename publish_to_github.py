"""把 personal-homepage/ 发布到 GitHub 仓库 main 分支（走 api.github.com）。

适用场景：网络代理只放行 api.github.com，github.com 的 git 端点不可达，
无法使用常规 `git push`。本脚本改用 GitHub Git Data API，基于远端 main
的最新提交创建一个新 commit，保留完整提交历史，不需要 force push。

用法（在 personal-homepage/ 目录下）：

    python publish_to_github.py --dry-run     # 只读预览变更，无需 token
    # 确认无误后设置 token 再发布：
    $env:GITHUB_TOKEN = "github_pat_..."     # PowerShell（CMD 用 set）
    python publish_to_github.py               # 真正发布

Token 需要对该仓库有写权限：推荐 fine-grained token，资源所有者选
kid141234、仓库只勾 kid141234.github.io、Contents 设为 Read and Write
（Git Data API 的 blob/tree/commit/ref 写端点均要求 Contents: write）。
Token 只从环境变量读取，不会写入文件或打印。

发布成功后 GitHub Actions 会自动部署 dist/ 到 https://kid141234.github.io/ 。
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OWNER = "kid141234"
REPO = "kid141234.github.io"
BRANCH = "main"
API = "https://api.github.com"

# 与项目 .gitignore 保持一致；另外排除本脚本运行产生的临时物
IGNORED_DIRS = {"qa", "node_modules", ".sites-runtime", ".sites-checkout",
                ".openai", ".git", "__pycache__"}
IGNORED_SUFFIXES = (".log", ".tar.gz", ".pyc")


def api(method: str, path: str, token: str, payload: dict | None = None):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "Content-Type": "application/json",
        "User-Agent": "personal-homepage-publisher",
    }
    if token:
        headers["Authorization"] = "Bearer " + token
    req = urllib.request.Request(
        API + path,
        data=data,
        method=method,
        headers=headers,
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")
        raise RuntimeError(f"{method} {path} -> HTTP {exc.code}: {body[:500]}") from None


def blob_sha(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def local_files() -> dict[str, bytes]:
    files: dict[str, bytes] = {}
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT)
        if any(part in IGNORED_DIRS for part in rel.parts):
            continue
        if any(str(rel).endswith(s) for s in IGNORED_SUFFIXES):
            continue
        files[rel.as_posix()] = path.read_bytes()
    return files


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish personal-homepage to GitHub Pages")
    parser.add_argument("--dry-run", action="store_true", help="只预览变更，不写入远端")
    parser.add_argument("--message", default="Add John Lee study notes topic to homepage",
                        help="提交信息")
    args = parser.parse_args()

    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if not token and not args.dry_run:
        print("缺少 GITHUB_TOKEN 环境变量。", file=sys.stderr)
        print('PowerShell: $env:GITHUB_TOKEN = "github_pat_..."', file=sys.stderr)
        return 2
    if not token:
        print("[dry-run] 未提供 token，仅做只读预览。\n")

    repo_path = f"/repos/{OWNER}/{REPO}"
    ref = api("GET", f"{repo_path}/git/ref/heads/{BRANCH}", token)
    head_sha = ref["object"]["sha"]
    commit = api("GET", f"{repo_path}/git/commits/{head_sha}", token)
    base_tree_sha = commit["tree"]["sha"]
    tree = api("GET", f"{repo_path}/git/trees/{base_tree_sha}?recursive=1", token)
    if tree.get("truncated"):
        raise RuntimeError("远端文件树被截断，无法安全计算差异")
    remote = {item["path"]: item["sha"] for item in tree["tree"] if item["type"] == "blob"}

    local = local_files()
    changed = {p: data for p, data in local.items() if remote.get(p) != blob_sha(data)}
    removed = sorted(set(remote) - set(local))

    print(f"远端 main HEAD : {head_sha[:12]}")
    print(f"本地文件       : {len(local)} 个")
    print(f"新增/修改      : {len(changed)} 个")
    for p in sorted(changed):
        print(f"  {'新增' if p not in remote else '修改'}  {p}")
    print(f"删除           : {len(removed)} 个")
    for p in removed:
        print(f"  删除  {p}")

    if not changed and not removed:
        print("\n远端已是最新，无需发布。")
        return 0
    if args.dry_run:
        print("\n[dry-run] 未写入远端。设置 GITHUB_TOKEN 后去掉 --dry-run 即可发布。")
        return 0

    entries = []
    for p, data in sorted(changed.items()):
        blob = api("POST", f"{repo_path}/git/blobs", token,
                   {"content": base64.b64encode(data).decode("ascii"), "encoding": "base64"})
        mode = "100755" if p.endswith((".sh", ".mjs")) and data.startswith(b"#!") else "100644"
        entries.append({"path": p, "mode": mode, "type": "blob", "sha": blob["sha"]})
        print(f"  已上传 blob {p}")
    for p in removed:
        entries.append({"path": p, "mode": "100644", "type": "blob", "sha": None})

    new_tree = api("POST", f"{repo_path}/git/trees", token,
                   {"base_tree": base_tree_sha, "tree": entries})
    new_commit = api("POST", f"{repo_path}/git/commits", token,
                     {"message": args.message, "tree": new_tree["sha"], "parents": [head_sha]})
    updated = api("PATCH", f"{repo_path}/git/refs/heads/{BRANCH}", token,
                  {"sha": new_commit["sha"]})

    print(f"\n发布成功：{BRANCH} -> {updated['object']['sha'][:12]}")
    print(f"提交信息：{args.message}")
    print("GitHub Actions 将自动部署 dist/，稍后访问 https://kid141234.github.io/")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"发布失败：{exc}", file=sys.stderr)
        sys.exit(1)
