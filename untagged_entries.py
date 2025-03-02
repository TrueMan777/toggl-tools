#!/usr/bin/env python3
"""
Toggl Untagged Entries Finder

This script identifies and lists all Toggl time entries that don't have any tags.
It helps users find entries that might need categorization or organization.
"""

import argparse
import logging
import os
import sys
from datetime import datetime, timedelta
import pytz
from tabulate import tabulate
from colorama import init, Fore, Style
from dotenv import load_dotenv

# Import local modules
from api_client import TogglApiClient

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
    parser = argparse.ArgumentParser(description="Find Toggl time entries without tags.")
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
        help="Timezone for time calculations (default: Asia/Shanghai)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--output",
        choices=["table", "csv", "json"],
        default="table",
        help="Output format (default: table)"
    )
    parser.add_argument(
        "--sort-by",
        choices=["date", "duration", "description"],
        default="date",
        help="Sort results by field (default: date)"
    )
    parser.add_argument(
        "--min-duration",
        type=int,
        default=0,
        help="Minimum duration in minutes to include (default: 0)"
    )
    return parser.parse_args()


def setup_logging(verbose):
    """Set up logging level based on verbosity."""
    if verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")
    else:
        logger.setLevel(logging.INFO)


def get_date_range(days, timezone):
    """
    Calculate the date range for the query.

    Args:
        days (int): Number of days to look back
        timezone (str): Timezone to use for calculations

    Returns:
        tuple: (start_date, end_date) as datetime objects
    """
    tz = pytz.timezone(timezone)
    end_date = datetime.now(tz)
    start_date = end_date - timedelta(days=days)

    # Set start date to beginning of day
    start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)

    logger.debug(f"Date range: {start_date.isoformat()} to {end_date.isoformat()}")
    return start_date, end_date


def find_untagged_entries(api_client, start_date, end_date, min_duration_minutes=0):
    """
    Find all time entries without tags.

    Args:
        api_client (TogglApiClient): Toggl API client
        start_date (datetime): Start date for the query
        end_date (datetime): End date for the query
        min_duration_minutes (int): Minimum duration in minutes to include

    Returns:
        list: List of untagged time entries
    """
    # Get all time entries for the date range
    entries = api_client.get_time_entries(start_date, end_date)

    # Filter entries without tags
    untagged_entries = []
    min_duration_seconds = min_duration_minutes * 60

    for entry in entries:
        # Skip entries without a stop time (currently running)
        if not entry.get('stop'):
            continue

        # Calculate duration in seconds
        duration = entry.get('duration', 0)

        # Skip entries shorter than minimum duration
        if duration < min_duration_seconds:
            continue

        # Check if entry has no tags or empty tags list
        if not entry.get('tags') or len(entry.get('tags', [])) == 0:
            # Add local timezone information
            start_time = datetime.fromisoformat(entry['start'].replace('Z', '+00:00'))
            stop_time = datetime.fromisoformat(entry['stop'].replace('Z', '+00:00'))

            # Add processed information to the entry
            processed_entry = {
                **entry,
                'start_time': start_time,
                'stop_time': stop_time,
                'duration_hours': duration / 3600,
                'duration_minutes': duration / 60
            }

            untagged_entries.append(processed_entry)

    logger.info(f"Found {len(untagged_entries)} untagged entries")
    return untagged_entries


def sort_entries(entries, sort_by):
    """
    Sort entries by the specified field.

    Args:
        entries (list): List of time entries
        sort_by (str): Field to sort by ('date', 'duration', or 'description')

    Returns:
        list: Sorted list of time entries
    """
    if sort_by == 'date':
        return sorted(entries, key=lambda x: x['start_time'])
    elif sort_by == 'duration':
        return sorted(entries, key=lambda x: x['duration_hours'], reverse=True)
    elif sort_by == 'description':
        return sorted(entries, key=lambda x: x.get('description', '').lower())
    return entries


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


def output_results(entries, format_type, timezone):
    """
    Output the results in the specified format.

    Args:
        entries (list): List of time entries
        format_type (str): Output format ('table', 'csv', or 'json')
        timezone (str): Timezone for displaying times
    """
    if not entries:
        print(f"{Fore.YELLOW}No untagged entries found.{Style.RESET_ALL}")
        return

    tz = pytz.timezone(timezone)

    if format_type == 'table':
        # Prepare table data
        table_data = []
        total_duration = 0

        for entry in entries:
            start_time_local = entry['start_time'].astimezone(tz)
            description = entry.get('description', 'No description')
            duration = entry.get('duration', 0)
            project_name = entry.get('project', {}).get('name', 'No project')

            table_data.append([
                start_time_local.strftime('%Y-%m-%d %H:%M'),
                description,
                format_duration(duration),
                project_name
            ])

            total_duration += duration

        # Print the table
        print(tabulate(
            table_data,
            headers=['Date', 'Description', 'Duration', 'Project'],
            tablefmt='grid'
        ))

        # Print summary
        print(f"\n{Fore.GREEN}Total: {len(entries)} entries, {format_duration(total_duration)}{Style.RESET_ALL}")

    elif format_type == 'csv':
        # Output CSV format
        print("Date,Description,Duration,Project")
        for entry in entries:
            start_time_local = entry['start_time'].astimezone(tz)
            description = entry.get('description', 'No description').replace(',', ' ')
            duration = format_duration(entry.get('duration', 0))
            project_name = entry.get('project', {}).get('name', 'No project').replace(',', ' ')

            print(f"{start_time_local.strftime('%Y-%m-%d %H:%M')},{description},{duration},{project_name}")

    elif format_type == 'json':
        # Output JSON format
        import json

        # Convert datetime objects to strings for JSON serialization
        json_entries = []
        for entry in entries:
            json_entry = {
                'id': entry.get('id'),
                'description': entry.get('description', 'No description'),
                'start': entry['start_time'].astimezone(tz).isoformat(),
                'stop': entry['stop_time'].astimezone(tz).isoformat(),
                'duration': entry.get('duration', 0),
                'duration_formatted': format_duration(entry.get('duration', 0)),
                'project': entry.get('project', {}).get('name', 'No project')
            }
            json_entries.append(json_entry)

        print(json.dumps(json_entries, indent=2))


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

        # Find untagged entries
        untagged_entries = find_untagged_entries(
            api_client,
            start_date,
            end_date,
            args.min_duration
        )

        # Sort entries
        sorted_entries = sort_entries(untagged_entries, args.sort_by)

        # Output results
        output_results(sorted_entries, args.output, args.timezone)

    except Exception as e:
        logger.error(f"Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()