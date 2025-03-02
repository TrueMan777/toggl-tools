from datetime import datetime, timedelta
import pytz
import copy
import logging
from dateutil import parser

# Set up logging
logger = logging.getLogger(__name__)

class EntryProcessor:
    """
    Processor for identifying and splitting Toggl time entries.
    """

    def __init__(self, api_client, timezone="Asia/Shanghai", long_entry_threshold=24):
        """
        Initialize the entry processor.

        Args:
            api_client (TogglApiClient): Toggl API client
            timezone (str): Timezone to use for midnight calculation
            long_entry_threshold (int): Threshold in hours for considering an entry as "long"
        """
        self.api_client = api_client
        self.timezone = pytz.timezone(timezone)
        self.long_entry_threshold = long_entry_threshold
        logger.debug(f"EntryProcessor initialized with timezone {timezone} and long entry threshold {long_entry_threshold}h")

    def identify_overnight_entries(self, entries):
        """
        Identify entries that span across midnight in the specified timezone.

        Args:
            entries (list): List of time entries

        Returns:
            list: List of overnight entries
        """
        overnight_entries = []

        for entry in entries:
            if self.is_overnight_entry(entry):
                overnight_entries.append(entry)

        return overnight_entries

    def is_overnight_entry(self, entry):
        """
        Check if an entry spans across midnight in the specified timezone.

        Args:
            entry (dict): Time entry

        Returns:
            bool: True if the entry spans across midnight
        """
        # Skip entries without a stop time (currently running)
        if not entry.get('stop'):
            return False

        # Convert entry times to the specified timezone
        start_time = datetime.fromisoformat(entry['start'].replace('Z', '+00:00')).astimezone(self.timezone)
        stop_time = datetime.fromisoformat(entry['stop'].replace('Z', '+00:00')).astimezone(self.timezone)

        # Check if the entry spans different days in the local timezone
        return start_time.date() != stop_time.date()

    def identify_long_entries(self, entries, max_hours=24):
        """
        Identify entries that exceed the maximum duration.

        Args:
            entries (list): List of time entries
            max_hours (int): Maximum allowed duration in hours

        Returns:
            list: List of entries exceeding the maximum duration
        """
        long_entries = []
        max_seconds = max_hours * 3600

        for entry in entries:
            # Skip entries without a stop time (currently running)
            if not entry.get('stop'):
                continue

            # Calculate duration in seconds
            start_time = datetime.fromisoformat(entry['start'].replace('Z', '+00:00'))
            stop_time = datetime.fromisoformat(entry['stop'].replace('Z', '+00:00'))
            duration = (stop_time - start_time).total_seconds()

            if duration > max_seconds:
                long_entries.append(entry)

        return long_entries

    def get_local_midnight(self, date):
        """
        Get the UTC timestamp for midnight in the specified timezone.

        Args:
            date (datetime.date): Date to get midnight for

        Returns:
            datetime: UTC datetime for midnight in the specified timezone
        """
        # Create a datetime for midnight in the local timezone
        local_midnight = datetime.combine(date, datetime.min.time())
        local_midnight = self.timezone.localize(local_midnight)

        # Convert to UTC
        utc_midnight = local_midnight.astimezone(pytz.UTC)

        return utc_midnight

    def split_entry_at_midnight(self, entry):
        """
        Split an entry at midnight into two entries.

        Args:
            entry (dict): Time entry to split

        Returns:
            tuple: Two entries (first_entry, second_entry)
        """
        # Convert entry times to the specified timezone
        start_time = datetime.fromisoformat(entry['start'].replace('Z', '+00:00')).astimezone(self.timezone)
        stop_time = datetime.fromisoformat(entry['stop'].replace('Z', '+00:00')).astimezone(self.timezone)

        # Calculate the next midnight after start_time
        next_day = start_time.date() + timedelta(days=1)
        midnight = datetime.combine(next_day, datetime.min.time())
        midnight = self.timezone.localize(midnight)

        # Create two entries split at midnight
        first_entry = copy.deepcopy(entry)
        first_entry['stop'] = midnight.astimezone(pytz.UTC).isoformat().replace('+00:00', 'Z')

        second_entry = copy.deepcopy(entry)
        second_entry['start'] = midnight.astimezone(pytz.UTC).isoformat().replace('+00:00', 'Z')

        # If the entry spans multiple midnights, we'll need to handle that in process_entries

        return first_entry, second_entry

    def split_long_entry(self, entry, max_hours=24):
        """
        Split an entry that exceeds the maximum duration.

        Args:
            entry (dict): Time entry to split
            max_hours (int): Maximum allowed duration in hours

        Returns:
            list: List of split entries
        """
        # Check if the entry is actually long
        if entry["duration_hours"] <= max_hours:
            logger.warning("Attempted to split non-long entry")
            return [entry]

        # Get start and end times in local timezone
        start_time = entry["start_time_local"]
        stop_time = entry["stop_time_local"]

        # Initialize list of split entries
        split_entries = []

        # Calculate how many parts we need
        total_hours = entry["duration_hours"]
        num_parts = int(total_hours / max_hours) + (1 if total_hours % max_hours > 0 else 0)

        # Current segment starts at the entry start time
        current_segment_start = start_time

        # Loop until we've covered the entire entry
        for i in range(num_parts):
            # Calculate the end of the current segment
            max_seconds = max_hours * 3600
            segment_end_time = min(
                current_segment_start + timedelta(seconds=max_seconds),
                stop_time
            )

            # Create a new entry for this segment
            segment_entry = {
                # Copy essential fields from the original entry
                "description": entry.get("description", ""),
                "project_id": entry.get("project_id"),
                "workspace_id": entry.get("workspace_id"),
                "tags": entry.get("tags", []),
                "billable": entry.get("billable", False),
                "start": current_segment_start.astimezone(pytz.UTC).isoformat().replace('+00:00', 'Z'),
                "stop": segment_end_time.astimezone(pytz.UTC).isoformat().replace('+00:00', 'Z'),
                "duration": int((segment_end_time - current_segment_start).total_seconds()),
                "created_with": "toggl_overnight_splitter",
                "split_from_id": entry.get("id", None)
            }

            # Add a note about this being a split entry
            segment_entry["description"] = f"{segment_entry['description']} (long split {i+1}/{num_parts})"

            split_entries.append(segment_entry)
            logger.debug(f"Split long entry part {i+1}: {current_segment_start.strftime('%Y-%m-%d %H:%M')} to {segment_end_time.strftime('%Y-%m-%d %H:%M')}")

            # Move to the next segment
            current_segment_start = segment_end_time

        logger.info(f"Split long entry into {len(split_entries)} parts")
        return split_entries

    def process_entries(self, entries, dry_run=True, interactive=False, no_delete=False):
        """
        Process all entries, identifying and splitting those that need it.

        Args:
            entries (list): List of time entries
            dry_run (bool): If True, don't actually modify entries
            interactive (bool): If True, ask for confirmation before each split
            no_delete (bool): If True, keep original entries after splitting

        Returns:
            dict: Summary of processed entries and operations
        """
        # Process each entry to add metadata
        processed_entries = [self.process_entry(entry) for entry in entries]

        # Identify entries that need splitting
        overnight_entries = [entry for entry in processed_entries if entry["is_overnight"]]
        long_entries = [entry for entry in processed_entries if entry["duration_hours"] >= self.long_entry_threshold]

        # Initialize counters for the summary
        entries_processed = 0
        entries_split = 0
        entries_skipped = 0
        new_entries_created = 0
        split_operations = []

        # If not in dry run mode, actually split the entries
        if not dry_run:
            # First, handle overnight entries
            for entry in overnight_entries:
                entries_processed += 1

                # Split the entry
                split_entries = self.split_overnight_entry(entry)

                # Skip if no splitting needed
                if len(split_entries) <= 1:
                    logger.info(f"Entry {entry.get('id')} does not need splitting.")
                    entries_skipped += 1
                    continue

                # If in interactive mode, ask for confirmation
                if interactive:
                    # This would be handled by the main script
                    # For now, just log it
                    logger.info(f"Would ask for confirmation to split entry {entry.get('id')} into {len(split_entries)} parts")
                    # Skip this entry in batch mode since we'll handle it in interactive mode
                    continue

                # Apply the split
                try:
                    # Create new entries
                    created_entries = []
                    for split_entry in split_entries:
                        # Actually create the entry via the API client
                        start_time = datetime.fromisoformat(split_entry['start'].replace('Z', '+00:00'))
                        end_time = datetime.fromisoformat(split_entry['stop'].replace('Z', '+00:00'))

                        new_entry = self.api_client.create_time_entry(
                            description=split_entry['description'],
                            start_time=start_time,
                            end_time=end_time,
                            tags=split_entry.get('tags'),
                            project_id=split_entry.get('project_id'),
                            billable=split_entry.get('billable', False)
                        )
                        created_entries.append(new_entry)
                        new_entries_created += 1
                        logger.debug(f"Created new entry: {new_entry.get('id')}")

                    # Delete the original entry if not keeping it
                    if not no_delete:
                        self.api_client.delete_time_entry(entry.get('id'))
                        logger.debug(f"Deleted original entry {entry.get('id')}")

                    entries_split += 1
                    logger.info(f"Successfully split entry {entry.get('id')} into {len(split_entries)} entries.")

                    # Record this split operation
                    split_operations.append({
                        "original_entry": entry,
                        "split_entries": created_entries,
                        "type": "overnight"
                    })

                except Exception as e:
                    logger.error(f"Error splitting entry {entry.get('id')}: {e}")
                    entries_skipped += 1

            # Then, handle long entries
            for entry in long_entries:
                # Skip if already processed as an overnight entry
                if any(op["original_entry"].get("id") == entry.get("id") for op in split_operations):
                    logger.info(f"Entry {entry.get('id')} already processed as an overnight entry.")
                    continue

                entries_processed += 1

                # Split the entry
                split_entries = self.split_long_entry(entry, self.long_entry_threshold)

                # Skip if no splitting needed
                if len(split_entries) <= 1:
                    logger.info(f"Entry {entry.get('id')} does not need splitting.")
                    entries_skipped += 1
                    continue

                # If in interactive mode, ask for confirmation
                if interactive:
                    # This would be handled by the main script
                    # For now, just log it
                    logger.info(f"Would ask for confirmation to split entry {entry.get('id')} into {len(split_entries)} parts")
                    # Skip this entry in batch mode since we'll handle it in interactive mode
                    continue

                # Apply the split
                try:
                    # Create new entries
                    created_entries = []
                    for split_entry in split_entries:
                        # Actually create the entry via the API client
                        start_time = datetime.fromisoformat(split_entry['start'].replace('Z', '+00:00'))
                        end_time = datetime.fromisoformat(split_entry['stop'].replace('Z', '+00:00'))

                        new_entry = self.api_client.create_time_entry(
                            description=split_entry['description'],
                            start_time=start_time,
                            end_time=end_time,
                            tags=split_entry.get('tags'),
                            project_id=split_entry.get('project_id'),
                            billable=split_entry.get('billable', False)
                        )
                        created_entries.append(new_entry)
                        new_entries_created += 1
                        logger.debug(f"Created new entry: {new_entry.get('id')}")

                    # Delete the original entry if not keeping it
                    if not no_delete:
                        self.api_client.delete_time_entry(entry.get('id'))
                        logger.debug(f"Deleted original entry {entry.get('id')}")

                    entries_split += 1
                    logger.info(f"Successfully split entry {entry.get('id')} into {len(split_entries)} entries.")

                    # Record this split operation
                    split_operations.append({
                        "original_entry": entry,
                        "split_entries": created_entries,
                        "type": "long"
                    })

                except Exception as e:
                    logger.error(f"Error splitting entry {entry.get('id')}: {e}")
                    entries_skipped += 1

        # Create a summary
        summary = {
            'total_entries': len(entries),
            'overnight_entries': len(overnight_entries),
            'long_entries': len(long_entries),
            'entries_processed': entries_processed,
            'entries_split': entries_split,
            'entries_skipped': entries_skipped,
            'new_entries_created': new_entries_created,
            'split_operations': split_operations,
            'overnight_entry_details': overnight_entries,
            'long_entry_details': long_entries
        }

        return summary

    def process_entry(self, entry):
        """
        Process a single time entry to determine if it spans across midnight.

        Args:
            entry (dict): Time entry from Toggl API

        Returns:
            dict: Processed entry with additional metadata
        """
        # Parse start and stop times
        start_time = parser.parse(entry["start"])
        stop_time = parser.parse(entry["stop"]) if "stop" in entry and entry["stop"] else datetime.now(pytz.UTC)

        # Convert to the specified timezone
        start_time_local = start_time.astimezone(self.timezone)
        stop_time_local = stop_time.astimezone(self.timezone)

        # Calculate duration in hours
        duration_seconds = (stop_time - start_time).total_seconds()
        duration_hours = duration_seconds / 3600

        # Check if the entry spans across midnight
        start_date = start_time_local.date()
        stop_date = stop_time_local.date()
        is_overnight = start_date != stop_date

        # Create processed entry with additional metadata
        processed_entry = {
            **entry,
            "start_time": start_time,
            "stop_time": stop_time,
            "start_time_local": start_time_local,
            "stop_time_local": stop_time_local,
            "duration_seconds": duration_seconds,
            "duration_hours": duration_hours,
            "is_overnight": is_overnight
        }

        logger.debug(f"Processed entry: {processed_entry['description']} - {duration_hours:.1f}h, overnight: {is_overnight}")
        return processed_entry

    def split_overnight_entry(self, entry):
        """
        Split an overnight entry into multiple entries, one for each day.

        Args:
            entry (dict): Processed time entry that spans across midnight

        Returns:
            list: List of split entries
        """
        if not entry["is_overnight"]:
            logger.warning("Attempted to split non-overnight entry")
            return [entry]

        # Get start and end times in local timezone
        start_time = entry["start_time_local"]
        stop_time = entry["stop_time_local"]

        # Initialize list of split entries
        split_entries = []

        # Current day starts at the entry start time
        current_day_start = start_time

        # Calculate the total number of days this entry spans
        days_spanned = (stop_time.date() - start_time.date()).days + 1

        # Loop until we've covered the entire entry
        day_count = 0
        while current_day_start < stop_time:
            day_count += 1
            # Calculate the end of the current day (midnight of the next day)
            next_day = current_day_start.date() + timedelta(days=1)
            next_midnight = datetime.combine(next_day, datetime.min.time())
            next_midnight = self.timezone.localize(next_midnight)

            # If next midnight is after the stop time, use the stop time instead
            current_day_end = min(next_midnight, stop_time)

            # Create a new entry for this day
            day_entry = {
                # Copy essential fields from the original entry
                "description": entry.get("description", ""),
                "project_id": entry.get("project_id"),
                "workspace_id": entry.get("workspace_id"),
                "tags": entry.get("tags", []),
                "billable": entry.get("billable", False),
                "start": current_day_start.astimezone(pytz.UTC).isoformat().replace('+00:00', 'Z'),
                "stop": current_day_end.astimezone(pytz.UTC).isoformat().replace('+00:00', 'Z'),
                "duration": int((current_day_end - current_day_start).total_seconds()),
                "created_with": "toggl_overnight_splitter",
                "split_from_id": entry.get("id", None)
            }

            # Add a note about this being a split entry
            day_entry["description"] = f"{day_entry['description']} (split {day_count}/{days_spanned})"

            split_entries.append(day_entry)
            logger.debug(f"Split entry part: {current_day_start.strftime('%Y-%m-%d %H:%M')} to {current_day_end.strftime('%Y-%m-%d %H:%M')}")

            # Move to the next day
            current_day_start = current_day_end

        logger.info(f"Split overnight entry into {len(split_entries)} parts")
        return split_entries