#!/usr/bin/env python3
"""
每日任务包装脚本 — 按顺序执行所有数据采集任务
用法: python scripts/daily_tasks.py
"""
import os
import sys
import subprocess

# ─── 配置 ─────────────────────────────────────────────────

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))

TASKS = [
    {"name": "美股市场观察", "script": "fetch_watchlist.py", "optional": False},
    {"name": "A股市场观察(沪深300)", "script": "fetch_cn_watchlist.py", "optional": False},
    {"name": "A股市场观察(中证500)", "script": "fetch_cn_watchlist.py --benchmark zz500", "optional": True},
    {"name": "隔夜雷达", "script": "run_daily.py", "optional": False},
]

# ─── 执行逻辑 ─────────────────────────────────────────────

def run_task(script_name: str) -> bool:
    """运行单个脚本，返回是否成功"""
    # 支持带参数的脚本，如 "fetch_cn_watchlist.py --benchmark zz500"
    parts = script_name.split()
    script_file = parts[0]
    script_args = parts[1:]
    script_path = os.path.join(SCRIPTS_DIR, script_file)
    if not os.path.exists(script_path):
        print(f"ERROR: 脚本不存在: {script_path}")
        return False

    print(f"\n{'=' * 50}")
    print(f"执行: {script_name}")
    print(f"{'=' * 50}")

    result = subprocess.run(
        [sys.executable, script_path] + script_args,
        cwd=SCRIPTS_DIR,
        capture_output=False,
    )

    return result.returncode == 0


def main():
    """主入口：按顺序执行所有任务"""
    print("=" * 50)
    print("每日数据采集任务开始")
    print("=" * 50)

    results = {}
    for task in TASKS:
        name = task["name"]
        script = task["script"]

        success = run_task(script)
        results[name] = success

        if not success and not task.get("optional", False):
            print(f"\nERROR: {name} 失败，终止后续任务")
            break

    # ─── 总结 ────────────────────────────────────────────────
    print("\n" + "=" * 50)
    print("任务执行总结")
    print("=" * 50)

    for name, success in results.items():
        status = "✓ 成功" if success else "✗ 失败"
        print(f"  {name}: {status}")

    all_success = all(results.values())
    if all_success:
        print("\n✓ 所有任务执行成功")
    else:
        print("\n✗ 部分任务执行失败")

    return all_success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
