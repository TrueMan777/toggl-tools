#!/usr/bin/env python3
"""
Toggl Auto Tagger

This script automatically assigns tags to Toggl time entries based on their descriptions.
It uses a mapping file to match descriptions to tags and applies them to entries.
"""

import argparse
import logging
import os
import sys
import json
import re
from datetime import datetime, timedelta
import pytz
from tabulate import tabulate
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
    parser = argparse.ArgumentParser(description="Automatically tag Toggl time entries based on descriptions.")
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
        "--dry-run",
        action="store_true",
        help="Show what would be tagged without making changes"
    )
    parser.add_argument(
        "--mapping-file",
        default="tag_mappings.json",
        help="JSON file containing description to tag mappings (default: tag_mappings.json)"
    )
    parser.add_argument(
        "--create-mapping",
        action="store_true",
        help="Create a new mapping file with available tags"
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Confirm each tag assignment before applying"
    )
    parser.add_argument(
        "--untagged-only",
        action="store_true",
        help="Only process entries without tags (default behavior)"
    )
    parser.add_argument(
        "--all-entries",
        action="store_true",
        help="Process all entries, including those that already have tags"
    )
    parser.add_argument(
        "--min-duration",
        type=int,
        default=0,
        help="Minimum duration in minutes to include (default: 0)"
    )
    return parser.parse_args()


def load_tag_mappings(mapping_file):
    """
    Load tag mappings from a JSON file.

    Args:
        mapping_file (str): Path to the mapping file

    Returns:
        dict: Mapping of description patterns to tags
    """
    if not os.path.exists(mapping_file):
        logger.warning(f"Mapping file {mapping_file} not found")
        return {}

    try:
        with open(mapping_file, 'r') as f:
            mappings = json.load(f)
            logger.info(f"Loaded {len(mappings)} tag mappings from {mapping_file}")
            return mappings
    except json.JSONDecodeError:
        logger.error(f"Error parsing mapping file {mapping_file}")
        return {}
    except Exception as e:
        logger.error(f"Error loading mapping file: {e}")
        return {}


def create_mapping_file(api_client, mapping_file):
    """
    Create a new mapping file with available tags.

    Args:
        api_client (TogglApiClient): Toggl API client
        mapping_file (str): Path to the mapping file

    Returns:
        bool: True if successful, False otherwise
    """
    # Get all available tags
    tags = api_client.get_workspace_tags()

    if not tags:
        logger.error("No tags found in workspace")
        return False

    # Create a template mapping structure
    mappings = {}
    for tag in tags:
        tag_name = tag.get('name')
        if tag_name:
            # Create an empty list for each tag
            mappings[tag_name] = []

    # Write the template to file
    try:
        with open(mapping_file, 'w') as f:
            json.dump(mappings, f, indent=2)
            logger.info(f"Created mapping template with {len(mappings)} tags in {mapping_file}")
            print(f"{Fore.GREEN}Created mapping template in {mapping_file}{Style.RESET_ALL}")
            print("Edit this file to add description patterns for each tag.")
            print("Example format:")
            print('''{
  "Work": [
    "client meeting",
    "project planning",
    "coding"
  ],
  "Personal": [
    "gym",
    "reading",
    "meditation"
  ]
}''')
            return True
    except Exception as e:
        logger.error(f"Error creating mapping file: {e}")
        return False


def find_matching_tag(description, tag_mappings):
    """
    Find a matching tag for a description.

    Args:
        description (str): Time entry description
        tag_mappings (dict): Mapping of tags to description patterns

    Returns:
        list: List of matching tags

    Note:
        Patterns are matched as whole words only, using word boundaries.
        For example, the pattern "eat" will match "Let's eat lunch" but not "eating lunch".
        Regex patterns are supported for more complex matching.
    """
    if not description:
        return []

    matching_tags = []
    description_lower = description.lower()

    logger.debug(f"Finding tags for description: '{description_lower}'")

    # Check each tag's patterns
    for tag, patterns in tag_mappings.items():
        for pattern in patterns:
            pattern_lower = pattern.lower()

            logger.debug(f"Checking pattern '{pattern_lower}' for tag '{tag}'")

            # Check if the pattern is a whole word in the description
            # Create a regex pattern that matches the word with word boundaries
            word_pattern = r'\b' + re.escape(pattern_lower) + r'\b'
            is_whole_word_match = bool(re.search(word_pattern, description_lower))

            # Try exact whole word match first
            if is_whole_word_match:
                logger.debug(f"✓ Found whole word match: '{pattern_lower}' in '{description_lower}' for tag '{tag}'")
                matching_tags.append(tag)
                break  # Only add each tag once
            # Then try regex match if pattern contains special characters
            elif any(c in pattern for c in ".*+?^$()[]{}|\\"):
                try:
                    regex_match = re.search(pattern_lower, description_lower)
                    if regex_match:
                        logger.debug(f"✓ Found regex match: '{pattern_lower}' in '{description_lower}' for tag '{tag}'")
                        matching_tags.append(tag)
                        break  # Only add each tag once
                    else:
                        logger.debug(f"✗ No regex match: '{pattern_lower}' not in '{description_lower}'")
                except re.error:
                    # If the pattern is not a valid regex, skip it
                    logger.warning(f"Invalid regex pattern: {pattern}")
                    continue
            else:
                # For non-regex patterns, we already checked for whole word match above
                logger.debug(f"✗ No whole word match: '{pattern_lower}' is not a whole word in '{description_lower}'")

    return matching_tags


def process_entries(api_client, entries, tag_mappings, dry_run=False, interactive=False, untagged_only=True, min_duration_minutes=0):
    """
    Process entries and apply tags based on mappings.

    Args:
        api_client (TogglApiClient): Toggl API client
        entries (list): List of time entries
        tag_mappings (dict): Mapping of tags to description patterns
        dry_run (bool): If True, don't actually apply tags
        interactive (bool): If True, confirm each tag assignment
        untagged_only (bool): If True, only process entries without tags
        min_duration_minutes (int): Minimum duration in minutes to include

    Returns:
        dict: Statistics about the tagging process
    """
    stats = {
        "processed": 0,
        "tagged": 0,
        "skipped": 0,
        "errors": 0,
        "tags_applied": {}
    }

    min_duration_seconds = min_duration_minutes * 60

    for entry in entries:
        stats["processed"] += 1
        entry_id = entry.get('id')
        description = entry.get('description', '')
        duration = entry.get('duration', 0)

        logger.debug(f"Processing entry {entry_id}: '{description}' (duration: {duration}s)")

        # Skip entries shorter than minimum duration
        if duration < min_duration_seconds:
            logger.debug(f"Skipping entry {entry_id} as it's shorter than minimum duration")
            stats["skipped"] += 1
            continue

        # Skip entries that already have tags if untagged_only is True
        if untagged_only and entry.get('tags') and len(entry.get('tags', [])) > 0:
            logger.debug(f"Skipping entry {entry_id} as it already has tags: {entry.get('tags')}")
            stats["skipped"] += 1
            continue

        # Find matching tags
        logger.debug(f"Finding matching tags for entry {entry_id}: '{description}'")
        matching_tags = find_matching_tag(description, tag_mappings)

        if not matching_tags:
            logger.debug(f"No matching tags found for entry {entry_id}: '{description}'")
            stats["skipped"] += 1
            continue

        logger.debug(f"Found matching tags for entry {entry_id}: {matching_tags}")

        # Format entry information for display
        start_time = datetime.fromisoformat(entry['start'].replace('Z', '+00:00'))
        duration_str = f"{int(duration / 3600)}h {int((duration % 3600) / 60)}m" if duration >= 3600 else f"{int(duration / 60)}m"

        # Display the entry and proposed tags
        print(f"\n{Fore.CYAN}Entry:{Style.RESET_ALL} {start_time.strftime('%Y-%m-%d %H:%M')} - {description} ({duration_str})")

        # Show existing tags if any
        existing_tags = entry.get('tags', [])
        if existing_tags:
            print(f"{Fore.CYAN}Existing tags:{Style.RESET_ALL} {', '.join(existing_tags)}")

        print(f"{Fore.CYAN}Tags to apply:{Style.RESET_ALL} {', '.join(matching_tags)}")

        # If interactive, ask for confirmation
        proceed = True
        if interactive:
            response = input(f"{Fore.YELLOW}Apply these tags? (y/n/edit):{Style.RESET_ALL} ").lower()
            if response == 'n':
                proceed = False
                stats["skipped"] += 1
            elif response == 'edit':
                # Allow editing the tags
                edited_tags = input(f"{Fore.YELLOW}Enter comma-separated tags:{Style.RESET_ALL} ")
                matching_tags = [tag.strip() for tag in edited_tags.split(',') if tag.strip()]

        if proceed and not dry_run:
            try:
                # Apply the tags
                api_client.add_tags_to_time_entry(entry_id, matching_tags)
                stats["tagged"] += 1

                # Update tag statistics
                for tag in matching_tags:
                    stats["tags_applied"][tag] = stats["tags_applied"].get(tag, 0) + 1

                print(f"{Fore.GREEN}✓ Tags applied successfully{Style.RESET_ALL}")
            except Exception as e:
                logger.error(f"Error applying tags to entry {entry_id}: {e}")
                print(f"{Fore.RED}✗ Error applying tags: {e}{Style.RESET_ALL}")
                stats["errors"] += 1
        elif dry_run:
            # In dry run mode, just count as tagged
            stats["tagged"] += 1
            for tag in matching_tags:
                stats["tags_applied"][tag] = stats["tags_applied"].get(tag, 0) + 1
            print(f"{Fore.YELLOW}Would apply tags (dry run){Style.RESET_ALL}")

    return stats


def display_stats(stats):
    """
    Display statistics about the tagging process.

    Args:
        stats (dict): Statistics about the tagging process
    """
    print(f"\n{Fore.CYAN}=== Tagging Statistics ==={Style.RESET_ALL}")
    print(f"Entries processed: {stats['processed']}")
    print(f"Entries tagged: {stats['tagged']}")
    print(f"Entries skipped: {stats['skipped']}")
    print(f"Errors: {stats['errors']}")

    if stats["tags_applied"]:
        print(f"\n{Fore.CYAN}Tags Applied:{Style.RESET_ALL}")
        for tag, count in sorted(stats["tags_applied"].items(), key=lambda x: x[1], reverse=True):
            print(f"  {tag}: {count}")


def main():
    """Main function."""
    # Parse command line arguments
    args = parse_args()

    # Set up logging
    setup_logging(args.verbose)

    try:
        # Initialize API client
        api_client = TogglApiClient(api_key=args.api_key)

        # If creating a mapping file, do that and exit
        if args.create_mapping:
            create_mapping_file(api_client, args.mapping_file)
            return

        # Load tag mappings
        tag_mappings = load_tag_mappings(args.mapping_file)
        if not tag_mappings:
            print(f"{Fore.RED}No tag mappings found. Use --create-mapping to create a template.{Style.RESET_ALL}")
            return

        # Get date range
        start_date, end_date = get_date_range(args.days, args.timezone)

        # Get all time entries for the date range
        entries = api_client.get_time_entries(start_date, end_date)

        if not entries:
            print(f"{Fore.YELLOW}No time entries found in the specified date range.{Style.RESET_ALL}")
            return

        # Determine whether to process only untagged entries
        untagged_only = not args.all_entries

        # Process entries and apply tags
        print(f"{Fore.CYAN}Processing {len(entries)} time entries from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}{Style.RESET_ALL}")
        if untagged_only:
            print(f"{Fore.CYAN}Only processing entries without tags{Style.RESET_ALL}")
        if args.dry_run:
            print(f"{Fore.YELLOW}DRY RUN: No changes will be made{Style.RESET_ALL}")

        stats = process_entries(
            api_client,
            entries,
            tag_mappings,
            dry_run=args.dry_run,
            interactive=args.interactive,
            untagged_only=untagged_only,
            min_duration_minutes=args.min_duration
        )

        # Display statistics
        display_stats(stats)

    except Exception as e:
        logger.error(f"Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()