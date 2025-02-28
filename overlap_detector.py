#!/usr/bin/env python3
"""
Toggl Overlap Detector

This script identifies overlapping time entries in Toggl, which indicates
time tracking errors or concurrent activities.
"""

import argparse
import logging
import os
import sys
from datetime import datetime, timedelta
import pytz
from tabulate import tabulate
from collections import defaultdict

from api_client import TogglApiClient
from entry_processor import EntryProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Toggl Overlap Detector")
    parser.add_argument(
        "--api-key",
        help="Toggl API key (overrides environment variable and .env file)"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of days to look back (default: 7)"
    )
    parser.add_argument(
        "--timezone",
        default="Asia/Shanghai",
        help="Timezone for day boundaries (default: Asia/Shanghai)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--min-overlap",
        type=int,
        default=60,
        help="Minimum overlap in seconds to report (default: 60)"
    )
    return parser.parse_args()

def format_duration(seconds):
    """Format duration in seconds to a human-readable string."""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return f"{hours}h {minutes}m"

def find_overlapping_entries(entries, min_overlap_seconds=60):
    """
    Find overlapping time entries.

    Args:
        entries: List of time entries with start and end times
        min_overlap_seconds: Minimum overlap duration in seconds to report

    Returns:
        List of tuples (entry1, entry2, overlap_duration) for overlapping entries
    """
    # Sort entries by start time
    sorted_entries = sorted(entries, key=lambda e: e["start_time"])
    overlaps = []

    # Compare each entry with subsequent entries to find overlaps
    for i, entry1 in enumerate(sorted_entries):
        for entry2 in sorted_entries[i+1:]:
            # If entry2 starts after entry1 ends, no need to check further entries
            if entry2["start_time"] >= entry1["end_time"]:
                break

            # Calculate overlap duration
            overlap_start = max(entry1["start_time"], entry2["start_time"])
            overlap_end = min(entry1["end_time"], entry2["end_time"])
            overlap_duration = int((overlap_end - overlap_start).total_seconds())

            # Only report overlaps above the minimum threshold
            if overlap_duration >= min_overlap_seconds:
                overlaps.append((entry1, entry2, overlap_duration))

    return overlaps

def main():
    """Main function."""
    args = parse_args()

    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")

    # Initialize API client
    try:
        api_client = TogglApiClient(api_key=args.api_key)
        logger.debug("API client initialized")
    except ValueError as e:
        logger.error(f"Error initializing API client: {e}")
        sys.exit(1)

    # Initialize entry processor
    timezone = args.timezone
    try:
        entry_processor = EntryProcessor(api_client, timezone=timezone)
        logger.debug(f"Entry processor initialized with timezone {timezone}")
    except Exception as e:
        logger.error(f"Error initializing entry processor: {e}")
        sys.exit(1)

    # Calculate date range
    end_date = datetime.now(pytz.UTC)
    start_date = end_date - timedelta(days=args.days)

    # Fetch time entries
    logger.info(f"Fetching time entries for the last {args.days} days...")
    try:
        entries = api_client.get_time_entries(start_date, end_date)
        logger.info(f"Retrieved {len(entries)} time entries")
    except Exception as e:
        logger.error(f"Error fetching time entries: {e}")
        sys.exit(1)

    # Process entries to add metadata
    processed_entries = []
    running_entries = 0
    tz = pytz.timezone(timezone)

    for entry in entries:
        # Skip entries without a stop time (currently running)
        if entry.get("stop") is None:
            running_entries += 1
            logger.debug(f"Skipping running entry: {entry.get('description', 'No description')} (no stop time)")
            continue

        processed_entry = entry_processor.process_entry(entry)

        # Add datetime objects for easier comparison
        start_time = datetime.fromisoformat(entry["start"].replace('Z', '+00:00')).astimezone(tz)
        end_time = datetime.fromisoformat(entry["stop"].replace('Z', '+00:00')).astimezone(tz)

        processed_entry["start_time"] = start_time
        processed_entry["end_time"] = end_time
        processed_entry["day"] = start_time.strftime("%Y-%m-%d")

        processed_entries.append(processed_entry)

    # After processing all entries, log how many running entries were skipped
    if running_entries > 0:
        logger.info(f"Skipped {running_entries} running entries (no stop time)")

    # Find overlapping entries
    overlaps = find_overlapping_entries(processed_entries, args.min_overlap)

    if overlaps:
        logger.info(f"Found {len(overlaps)} overlapping time entries:")

        # Group overlaps by day for better readability
        overlaps_by_day = defaultdict(list)
        for entry1, entry2, duration in overlaps:
            day = entry1["day"]
            overlaps_by_day[day].append((entry1, entry2, duration))

        # Prepare table data
        table_data = []
        for day, day_overlaps in sorted(overlaps_by_day.items()):
            # Add row for the day summary
            table_data.append([
                day,
                f"TOTAL: {len(day_overlaps)} overlaps",
                "",
                "",
                "",
                "",
                ""
            ])

            # Add rows for each overlap on this day
            for entry1, entry2, duration in day_overlaps:
                # Format times
                entry1_time = f"{entry1['start_time'].strftime('%H:%M')} - {entry1['end_time'].strftime('%H:%M')}"
                entry2_time = f"{entry2['start_time'].strftime('%H:%M')} - {entry2['end_time'].strftime('%H:%M')}"

                # Add row for the first entry
                table_data.append([
                    "",
                    entry1.get("id", ""),
                    entry1.get("description", "No description"),
                    entry1_time,
                    entry1.get("project_name", "No project"),
                    format_duration(duration),
                    "↓ overlaps with ↓"
                ])

                # Add row for the second entry
                table_data.append([
                    "",
                    entry2.get("id", ""),
                    entry2.get("description", "No description"),
                    entry2_time,
                    entry2.get("project_name", "No project"),
                    "",
                    ""
                ])

                # Add empty row for better readability
                table_data.append(["", "", "", "", "", "", ""])

        # Print table
        headers = ["Date", "ID", "Description", "Time", "Project", "Overlap", ""]
        print(tabulate(table_data, headers=headers, tablefmt="grid"))
    else:
        logger.info(f"No overlapping time entries found with minimum overlap of {args.min_overlap} seconds.")

    logger.info("Done!")

if __name__ == "__main__":
    main()