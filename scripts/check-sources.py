#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

"""
Regists 出海指南 - 官方来源更新检测脚本
每月自动运行，检查所有来源页面是否有变化，生成更新报告。

Usage:
    python scripts/check-sources.py [--run]
    
    --run: 实际执行检测并更新配置
    (不传参): 仅输出状态摘要
"""

import os
import json
import hashlib
import sys
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BASE_DIR, "data", "update-config.json")
RUNTIME_DIR = os.path.join(BASE_DIR, "data", "runtime")
REPORT_DIR = os.path.join(BASE_DIR, "data", "reports")
os.makedirs(RUNTIME_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)

RESULTS_PATH = os.path.join(RUNTIME_DIR, "last-check-results.json")

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Regists-Updater/1.0"


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(config):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def fetch_url(url, timeout=30):
    """Fetch URL content, return (status_code, content_bytes, error_msg)"""
    req = Request(url, headers={"User-Agent": USER_AGENT})
    try:
        resp = urlopen(req, timeout=timeout)
        content = resp.read()
        return resp.status, content, None
    except HTTPError as e:
        return e.code, b"", str(e)
    except URLError as e:
        return 0, b"", str(e)
    except Exception as e:
        return 0, b"", str(e)


def compute_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()[:16]


def check_source(source):
    """Check a single source URL for changes.
    Returns dict with status info.
    """
    url = source["url"]
    name = source["name"]
    last_hash = source.get("lastHash")

    status_code, content, error = fetch_url(url)

    result = {
        "name": name,
        "url": url,
        "status_code": status_code,
        "error": error,
        "changed": None,  # True/False/None (unknown)
        "new_hash": None,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }

    if status_code == 200 and content:
        new_hash = compute_hash(content)
        result["new_hash"] = new_hash

        if last_hash and last_hash != new_hash:
            result["changed"] = True
        elif last_hash and last_hash == new_hash:
            result["changed"] = False
        else:
            result["changed"] = None  # First check, no baseline
    else:
        result["changed"] = None
        result["error"] = result["error"] or f"HTTP {status_code}"

    return result


def run_check(config):
    """Run full check on all sources."""
    results = {
        "check_time": datetime.now(timezone.utc).isoformat(),
        "total_sources": 0,
        "changed": 0,
        "unchanged": 0,
        "failed": 0,
        "first_check": 0,
        "details": [],
    }

    for region in config["regions"]:
        for source in region.get("sources", []):
            results["total_sources"] += 1
            print(f"  Checking [{region['id']}] {source['name']}...", end=" ")
            sys.stdout.flush()

            check = check_source(source)
            check["region_id"] = region["id"]

            if check["error"]:
                results["failed"] += 1
                print(f"❌ FAILED: {check['error']}")
            elif check["changed"] is True:
                results["changed"] += 1
                print("🔴 CHANGED")
            elif check["changed"] is False:
                results["unchanged"] += 1
                print("✅ unchanged")
            else:
                results["first_check"] += 1
                print("📝 first check (baseline set)")

            # Update source config
            if check["new_hash"]:
                source["lastHash"] = check["new_hash"]
            source["lastChecked"] = check["checked_at"]

            results["details"].append(check)

    # Update global check timestamp
    config["lastCheck"] = results["check_time"]
    save_config(config)
    save_results(results)

    return results


def save_results(results):
    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # Generate human-readable report
    report_path = os.path.join(REPORT_DIR, f"update-{datetime.now().strftime('%Y%m%d')}.md")
    lines = [
        f"# Regists 月度来源更新报告",
        f"",
        f"**检查时间**: {results['check_time']}",
        f"**统计**:",
        f"- 总来源数: {results['total_sources']}",
        f"- 已变更: {results['changed']}",
        f"- 未变更: {results['unchanged']}",
        f"- 首次检测: {results['first_check']}",
        f"- 失败: {results['failed']}",
        f"",
    ]

    if results["changed"] > 0:
        lines.append("## ⚠️ 需要关注的变更")
        lines.append("")
        for d in results["details"]:
            if d["changed"]:
                lines.append(f"- **[{d['region_id']}]** {d['name']}: 内容已变更")
                lines.append(f"  - URL: {d['url']}")
                lines.append("")

    if results["failed"] > 0:
        lines.append("## ❌ 检查失败的来源")
        lines.append("")
        for d in results["details"]:
            if d["error"]:
                lines.append(f"- **[{d['region_id']}]** {d['name']}: {d['error']}")
                lines.append(f"  - URL: {d['url']}")
                lines.append("")

    lines.extend([
        "## ✅ 更新摘要",
        "",
        f"本次检查完成。共 {results['total_sources']} 个来源，",
        f"{results['unchanged']} 个未变更，{results['changed']} 个已变更，{results['failed']} 个检查失败。",
        "",
        "---",
        f"_自动生成于 {results['check_time']}_",
    ])

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return report_path


def print_status(config, results=None):
    """Print current status summary."""
    print(f"\n{'='*60}")
    print(f"  Regists 出海指南 - 来源状态")
    print(f"{'='*60}")

    if config.get("lastCheck"):
        print(f"  上次检查: {config['lastCheck']}")
    else:
        print(f"  上次检查: 从未")

    print(f"\n  地区       来源数  状态")
    print(f"  {'-'*40}")
    for region in config["regions"]:
        sources = region.get("sources", [])
        checked = sum(1 for s in sources if s.get("lastChecked"))
        print(f"  {region['id']:<12} {len(sources):<8} {'✅' if checked == len(sources) else '⏳'} ({checked}/{len(sources)})")

    if results:
        print(f"\n  上次运行结果:")
        print(f"    总来源: {results['total_sources']}")
        print(f"    变更:   {results['changed']}")
        print(f"    未变:   {results['unchanged']}")
        print(f"    失败:   {results['failed']}")
        print(f"    首次:   {results['first_check']}")

    print(f"{'='*60}\n")


def main():
    config = load_config()

    if "--run" in sys.argv:
        print("=" * 60)
        print("  Regists 来源更新检测 - 运行中...")
        print("=" * 60)

        results = run_check(config)
        report_path = os.path.join(REPORT_DIR, f"update-{datetime.now().strftime('%Y%m%d')}.md")

        print(f"\n{'='*60}")
        print(f"  检查完成!")
        print(f"  报告已保存: {report_path}")
        print(f"  {'='*60}")
        print_results_summary(results)

        # Return non-zero if changes detected
        if results["changed"] > 0:
            print("\n⚠️  检测到内容变更，请手动审核并更新网站数据文件。")
            return 1
        return 0
    else:
        # Try to load last results
        results = None
        if os.path.exists(RESULTS_PATH):
            with open(RESULTS_PATH, "r", encoding="utf-8") as f:
                results = json.load(f)
        print_status(config, results)
        return 0


def print_results_summary(results):
    print(f"\n  总来源: {results['total_sources']}")
    print(f"  ✅ 未变更: {results['unchanged']}")
    print(f"  🔴 已变更: {results['changed']}")
    print(f"  ❌ 失败:   {results['failed']}")
    print(f"  📝 首次:   {results['first_check']}")

    if results["changed"] > 0:
        print(f"\n  需要关注的变更:")
        for d in results["details"]:
            if d["changed"]:
                print(f"    - [{d['region_id']}] {d['name']}")

    if results["failed"] > 0:
        print(f"\n  检查失败的来源:")
        for d in results["details"]:
            if d["error"]:
                print(f"    - [{d['region_id']}] {d['name']}: {d['error']}")


if __name__ == "__main__":
    sys.exit(main())
