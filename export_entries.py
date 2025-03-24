#!/usr/bin/env python3
"""
Toggl Entries Exporter

This script exports all Toggl time entries within a specified date range to a JSON file.
It can be used for backup, analysis, or data processing purposes.
"""

import argparse
import logging
import os
import sys
import json
from datetime import datetime, timedelta
import pytz
from colorama import init, Fore, Style
from dotenv import load_dotenv

# Import local modules
from api_client import TogglApiClient
from untagged_entries import get_date_range, setup_logging

# Initialize colorama
init()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Export Toggl time entries to a JSON file.")
    parser.add_argument(
        "--api-key",
        help="Toggl API key (overrides environment variable and .env file)"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Number of days to look back (default: 30)"
    )
    parser.add_argument(
        "--timezone",
        default="Asia/Shanghai",
        help="Timezone for time calculations (default: Asia/Shanghai)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--output-file",
        default="toggl_entries.json",
        help="Output JSON file path (default: toggl_entries.json)"
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print the JSON output"
    )
    parser.add_argument(
        "--include-running",
        action="store_true",
        help="Include currently running time entries"
    )
    parser.add_argument(
        "--min-duration",
        type=int,
        default=0,
        help="Minimum duration in minutes to include (default: 0)"
    )
    return parser.parse_args()


def process_entries(entries, min_duration_minutes=0, include_running=False):
    """
    Process time entries for export.

    Args:
        entries (list): List of time entries from the API
        min_duration_minutes (int): Minimum duration in minutes to include
        include_running (bool): Whether to include currently running entries

    Returns:
        list: Processed entries ready for export
    """
    processed_entries = []
    min_duration_seconds = min_duration_minutes * 60

    for entry in entries:
        # Skip entries without a stop time (currently running) if not including running entries
        if not entry.get('stop') and not include_running:
            logger.debug(f"Skipping running entry: {entry.get('description', 'No description')}")
            continue

        # Calculate duration in seconds
        duration = entry.get('duration', 0)

        # Skip entries shorter than minimum duration
        if duration < min_duration_seconds:
            logger.debug(f"Skipping entry shorter than minimum duration: {duration/60:.1f}m")
            continue

        # Process timestamps
        if entry.get('start'):
            entry['start_iso'] = entry['start']
            entry['start'] = datetime.fromisoformat(entry['start'].replace('Z', '+00:00')).isoformat()

        if entry.get('stop'):
            entry['stop_iso'] = entry['stop']
            entry['stop'] = datetime.fromisoformat(entry['stop'].replace('Z', '+00:00')).isoformat()

        # Add formatted duration
        entry['duration_formatted'] = format_duration(duration)

        # Add to processed entries
        processed_entries.append(entry)

    return processed_entries


def format_duration(seconds):
    """
    Format duration in seconds to a human-readable string.

    Args:
        seconds (int): Duration in seconds

    Returns:
        str: Formatted duration string (e.g., "2h 30m")
    """
    hours = int(seconds / 3600)
    minutes = int((seconds % 3600) / 60)

    if hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m"


def export_to_json(entries, output_file, pretty=False):
    """
    Export entries to a JSON file.

    Args:
        entries (list): Processed time entries
        output_file (str): Path to the output file
        pretty (bool): Whether to pretty-print the JSON

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Sort entries by start date
        sorted_entries = sorted(entries, key=lambda x: x.get('start', ''))
        logger.info(f"Sorted {len(entries)} entries by start date")

        # Add metadata
        export_data = {
            "metadata": {
                "exported_at": datetime.now().isoformat(),
                "entry_count": len(sorted_entries)
            },
            "entries": sorted_entries
        }

        # Write to file, ensuring Cyrillic characters are kept as is
        with open(output_file, 'w', encoding='utf-8') as f:
            if pretty:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            else:
                json.dump(export_data, f, ensure_ascii=False)

        logger.info(f"Exported {len(sorted_entries)} entries to {output_file}")
        return True
    except Exception as e:
        logger.error(f"Error exporting to JSON: {e}")
        return False


def get_entries_in_batches(api_client, start_date, end_date, batch_size_days=30):
    """
    Get time entries in batches to avoid API limitations.

    Args:
        api_client (TogglApiClient): Toggl API client
        start_date (datetime): Start date for the query
        end_date (datetime): End date for the query
        batch_size_days (int): Maximum days per batch

    Returns:
        list: Combined time entries from all batches
    """
    all_entries = []
    current_start = start_date

    # Ensure we don't request future dates
    now = datetime.now(end_date.tzinfo)
    if end_date > now:
        logger.warning(f"End date {end_date.strftime('%Y-%m-%d')} is in the future. Using current date instead.")
        end_date = now

    # Check if start date is also in the future
    if start_date > now:
        logger.warning(f"Start date {start_date.strftime('%Y-%m-%d')} is in the future. No data will be fetched.")
        return []

    while current_start < end_date:
        # Calculate batch end date (either batch_size_days from current_start or end_date)
        batch_end = min(current_start + timedelta(days=batch_size_days), end_date)

        logger.info(f"Fetching batch from {current_start.strftime('%Y-%m-%d')} to {batch_end.strftime('%Y-%m-%d')}")
        try:
            batch_entries = api_client.get_time_entries(current_start, batch_end)
            all_entries.extend(batch_entries)
            logger.info(f"Retrieved {len(batch_entries)} entries in this batch")
        except Exception as e:
            logger.error(f"Error retrieving batch: {e}")

        # Move to next batch
        current_start = batch_end

    return all_entries


def main():
    """Main function."""
    # Parse command line arguments
    args = parse_args()

    # Set up logging
    setup_logging(args.verbose)

    try:
        # Initialize API client
        api_client = TogglApiClient(api_key=args.api_key)

        # Get date range
        start_date, end_date = get_date_range(args.days, args.timezone)

        # Get all time entries for the date range in batches
        print(f"{Fore.CYAN}Retrieving time entries from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}{Style.RESET_ALL}")
        entries = get_entries_in_batches(api_client, start_date, end_date)

        if not entries:
            print(f"{Fore.YELLOW}No time entries found in the specified date range.{Style.RESET_ALL}")
            return
        else:
            print(f"{Fore.GREEN}Successfully retrieved {len(entries)} time entries{Style.RESET_ALL}")

        # Process entries
        print(f"{Fore.CYAN}Processing {len(entries)} time entries{Style.RESET_ALL}")

        processed_entries = process_entries(
            entries,
            min_duration_minutes=args.min_duration,
            include_running=args.include_running
        )

        # Export to JSON
        if export_to_json(processed_entries, args.output_file, args.pretty):
            print(f"{Fore.GREEN}Successfully exported {len(processed_entries)} entries to {args.output_file}{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}Failed to export entries to {args.output_file}{Style.RESET_ALL}")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()