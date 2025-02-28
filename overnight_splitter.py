#!/usr/bin/env python3
"""
Toggl Overnight Entry Splitter

This script identifies and splits Toggl time entries that span across midnight,
making it easier to analyze time spent per day.

Usage:
    python toggl_overnight_splitter.py [options]

Options:
    --api-key KEY         Toggl API key (overrides environment variable and .env file)
    --days DAYS           Number of days to look back (default: 7)
    --timezone TIMEZONE   Timezone for day boundaries (default: Asia/Shanghai)
    --dry-run             Identify entries without splitting them
    --verbose             Enable verbose logging
    --interactive         Confirm each split before applying
    --no-delete           Keep original entries after splitting
"""

import os
import sys
import argparse
import logging
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv
from tabulate import tabulate

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
    parser = argparse.ArgumentParser(description="Toggl Overnight Entry Splitter")

    parser.add_argument("--api-key", help="Toggl API key (overrides environment variable and .env file)")
    parser.add_argument("--days", type=int, default=7, help="Number of days to look back (default: 7)")
    parser.add_argument("--timezone", default="Asia/Shanghai", help="Timezone for day boundaries (default: Asia/Shanghai)")
    parser.add_argument("--dry-run", action="store_true", help="Identify entries without splitting them")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("--interactive", action="store_true", help="Confirm each split before applying")
    parser.add_argument("--no-delete", action="store_true", help="Keep original entries after splitting")

    return parser.parse_args()

def format_duration(seconds):
    """Format duration in seconds to a human-readable string."""
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{int(hours)}h {int(minutes)}m"

def display_entries(entries, timezone_str):
    """Display entries in a tabular format."""
    if not entries:
        logger.info("No entries to display.")
        return

    timezone = pytz.timezone(timezone_str)
    table_data = []

    for entry in entries:
        start_time = datetime.fromisoformat(entry["start"].replace("Z", "+00:00")).astimezone(timezone)
        stop_time = datetime.fromisoformat(entry["stop"].replace("Z", "+00:00")).astimezone(timezone)

        table_data.append([
            entry.get("id", "No ID"),
            entry.get("description", "No description"),
            start_time.strftime("%Y-%m-%d %H:%M"),
            stop_time.strftime("%Y-%m-%d %H:%M"),
            format_duration(entry.get("duration", 0)),
            entry.get("project", "No project")
        ])

    headers = ["ID", "Description", "Start Time", "End Time", "Duration", "Project"]
    print(tabulate(table_data, headers=headers, tablefmt="grid"))

def confirm_action(prompt):
    """Ask for user confirmation."""
    while True:
        response = input(f"{prompt} (y/n): ").lower().strip()
        if response in ["y", "yes"]:
            return True
        elif response in ["n", "no"]:
            return False
        else:
            print("Please enter 'y' or 'n'.")

def display_split_preview(original_entry, split_entries, timezone_str):
    """Display a preview of how an entry will be split."""
    timezone = pytz.timezone(timezone_str)

    # Display original entry
    print("\nOriginal entry:")
    original_start = datetime.fromisoformat(original_entry["start"].replace("Z", "+00:00")).astimezone(timezone)
    original_stop = datetime.fromisoformat(original_entry["stop"].replace("Z", "+00:00")).astimezone(timezone)
    original_duration = original_entry.get("duration_seconds", 0)

    print(f"Description: {original_entry.get('description', 'No description')}")
    print(f"Start: {original_start.strftime('%Y-%m-%d %H:%M')}")
    print(f"End: {original_stop.strftime('%Y-%m-%d %H:%M')}")
    print(f"Duration: {format_duration(original_duration)}")
    print(f"Project: {original_entry.get('project', 'No project')}")

    # Display split entries
    print("\nWill be split into:")
    for i, entry in enumerate(split_entries, 1):
        start_time = datetime.fromisoformat(entry["start"].replace("Z", "+00:00")).astimezone(timezone)
        stop_time = datetime.fromisoformat(entry["stop"].replace("Z", "+00:00")).astimezone(timezone)
        duration = entry.get("duration", 0)

        print(f"\nPart {i}:")
        print(f"Description: {entry.get('description', 'No description')}")
        print(f"Start: {start_time.strftime('%Y-%m-%d %H:%M')}")
        print(f"End: {stop_time.strftime('%Y-%m-%d %H:%M')}")
        print(f"Duration: {format_duration(duration)}")
        print(f"Project: {entry.get('project', 'No project')}")

def main():
    """Main function."""
    args = parse_args()

    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")

    # Initialize API client
    # Note: The TogglApiClient will handle loading from .env with override=True
    try:
        api_client = TogglApiClient(api_key=args.api_key)
        logger.debug("API client initialized")
    except ValueError as e:
        logger.error(f"Error initializing API client: {e}")
        sys.exit(1)

    # Initialize entry processor
    processor = EntryProcessor(api_client, timezone=args.timezone)
    logger.debug(f"Entry processor initialized with timezone {args.timezone}")

    # Calculate date range
    end_date = datetime.now(pytz.UTC)
    start_date = end_date - timedelta(days=args.days)

    logger.info(f"Fetching time entries for the last {args.days} days...")

    # Fetch time entries
    try:
        entries = api_client.get_time_entries(start_date, end_date)
        logger.info(f"Retrieved {len(entries)} time entries")
    except Exception as e:
        logger.error(f"Error fetching time entries: {e}")
        sys.exit(1)

    # Process entries
    logger.info("Processing time entries...")

    # First, just identify entries that need splitting
    summary = processor.process_entries(entries, dry_run=True)

    # Display summary
    logger.info(f"Total entries: {summary['total_entries']}")
    logger.info(f"Overnight entries: {summary['overnight_entries']}")
    logger.info(f"Long entries: {summary['long_entries']}")

    # Display overnight entries
    if summary['overnight_entries'] > 0:
        logger.info("\nOvernight entries:")
        display_entries(summary['overnight_entry_details'], args.timezone)

    # Display long entries
    if summary['long_entries'] > 0:
        logger.info("\nLong entries:")
        display_entries(summary['long_entry_details'], args.timezone)

    # Split entries if not in dry run mode
    if not args.dry_run and (summary['overnight_entries'] > 0 or summary['long_entries'] > 0):
        logger.info("\nSplitting entries...")

        # If interactive mode is enabled, we'll handle each entry individually
        if args.interactive:
            # Process overnight entries
            for entry in summary['overnight_entry_details']:
                # Split the entry
                split_entries = processor.split_overnight_entry(entry)

                # Skip if no splitting needed
                if len(split_entries) <= 1:
                    logger.info(f"Entry {entry.get('id')} does not need splitting.")
                    continue

                # Display preview and ask for confirmation
                display_split_preview(entry, split_entries, args.timezone)
                if not confirm_action("Apply this split?"):
                    logger.info(f"Skipping entry {entry.get('id')} as per user request.")
                    continue

                # Apply the split
                try:
                    # Create new entries
                    for split_entry in split_entries:
                        # Parse the start and end times
                        start_time = datetime.fromisoformat(split_entry['start'].replace('Z', '+00:00'))
                        end_time = datetime.fromisoformat(split_entry['stop'].replace('Z', '+00:00'))

                        # Create the entry with the new method signature
                        new_entry = api_client.create_time_entry(
                            description=split_entry['description'],
                            start_time=start_time,
                            end_time=end_time,
                            tags=split_entry.get('tags'),
                            project_id=split_entry.get('project_id'),
                            billable=split_entry.get('billable', False)
                        )
                        logger.info(f"Created new entry: {new_entry.get('id')}")

                    # Delete the original entry if not keeping it
                    if not args.no_delete:
                        api_client.delete_time_entry(entry.get('id'))
                        logger.info(f"Deleted original entry {entry.get('id')}")

                    logger.info(f"Successfully split entry {entry.get('id')} into {len(split_entries)} entries.")

                except Exception as e:
                    logger.error(f"Error splitting entry {entry.get('id')}: {e}")

            # Process long entries (that aren't also overnight entries)
            overnight_ids = [entry.get('id') for entry in summary['overnight_entry_details']]
            long_entries_to_process = [entry for entry in summary['long_entry_details'] if entry.get('id') not in overnight_ids]

            for entry in long_entries_to_process:
                # Split the entry
                split_entries = processor.split_long_entry(entry, processor.long_entry_threshold)

                # Skip if no splitting needed
                if len(split_entries) <= 1:
                    logger.info(f"Entry {entry.get('id')} does not need splitting.")
                    continue

                # Display preview and ask for confirmation
                display_split_preview(entry, split_entries, args.timezone)
                if not confirm_action("Apply this split?"):
                    logger.info(f"Skipping entry {entry.get('id')} as per user request.")
                    continue

                # Apply the split
                try:
                    # Create new entries
                    for split_entry in split_entries:
                        # Parse the start and end times
                        start_time = datetime.fromisoformat(split_entry['start'].replace('Z', '+00:00'))
                        end_time = datetime.fromisoformat(split_entry['stop'].replace('Z', '+00:00'))

                        # Create the entry with the new method signature
                        new_entry = api_client.create_time_entry(
                            description=split_entry['description'],
                            start_time=start_time,
                            end_time=end_time,
                            tags=split_entry.get('tags'),
                            project_id=split_entry.get('project_id'),
                            billable=split_entry.get('billable', False)
                        )
                        logger.info(f"Created new entry: {new_entry.get('id')}")

                    # Delete the original entry if not keeping it
                    if not args.no_delete:
                        api_client.delete_time_entry(entry.get('id'))
                        logger.info(f"Deleted original entry {entry.get('id')}")

                    logger.info(f"Successfully split entry {entry.get('id')} into {len(split_entries)} entries.")

                except Exception as e:
                    logger.error(f"Error splitting entry {entry.get('id')}: {e}")

        # If not in interactive mode, process all entries at once
        else:
            # Process all entries
            batch_summary = processor.process_entries(
                entries,
                dry_run=False,
                interactive=False,
                no_delete=args.no_delete
            )

            # Display summary of operations
            logger.info("\nSplit operation summary:")
            logger.info(f"Entries processed: {batch_summary['entries_processed']}")
            logger.info(f"Entries successfully split: {batch_summary['entries_split']}")
            logger.info(f"Entries skipped: {batch_summary['entries_skipped']}")
            logger.info(f"New entries created: {batch_summary['new_entries_created']}")

    logger.info("Done!")

if __name__ == "__main__":
    main()