#!/usr/bin/env python3
"""
Weekly Meeting Update Runner

Runs both monitors and generates the weekly digest.

Usage:
    python run_weekly_update.py               # Run everything
    python run_weekly_update.py --skip-rco    # Skip RCO monitor
    python run_weekly_update.py --skip-official  # Skip official meetings
"""

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\n{'='*60}")
    print(f"{description}")
    print(f"{'='*60}\n")

    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=False,
            text=True
        )
        print(f"\n✓ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n✗ {description} failed with error code {e.returncode}")
        return False
    except Exception as e:
        print(f"\n✗ {description} failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Run weekly meeting update")
    parser.add_argument(
        "--skip-rco",
        action="store_true",
        help="Skip RCO monitor"
    )
    parser.add_argument(
        "--skip-official",
        action="store_true",
        help="Skip official meetings monitor"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of days to check (default: 7)"
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output file for digest (default: weekly_digest_YYYYMMDD.md)"
    )

    args = parser.parse_args()

    print("🚀 Starting weekly meeting update...")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    success_count = 0
    total_tasks = 0

    # Run RCO Monitor
    if not args.skip_rco:
        total_tasks += 1
        if run_command(
            ["python3", "rco_monitor.py", "--check", "--days", str(args.days)],
            "Running RCO Monitor"
        ):
            success_count += 1

    # Run Official Meetings Monitor
    if not args.skip_official:
        total_tasks += 1
        if run_command(
            ["python3", "official_meetings_monitor.py", "--check"],
            "Running Official Meetings Monitor"
        ):
            success_count += 1

    # Generate digest
    total_tasks += 1
    output_file = args.output or f"weekly_digest_{datetime.now().strftime('%Y%m%d')}.md"

    if run_command(
        ["python3", "weekly_digest.py", "--days", str(args.days), "--output", output_file],
        "Generating Weekly Digest"
    ):
        success_count += 1

    # Summary
    print(f"\n{'='*60}")
    print(f"Summary")
    print(f"{'='*60}")
    print(f"✓ Completed: {success_count}/{total_tasks} tasks")

    if success_count == total_tasks:
        print(f"\n🎉 All done! Digest saved to: {output_file}")
        return 0
    else:
        print(f"\n⚠️  Some tasks failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
