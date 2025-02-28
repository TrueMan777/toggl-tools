#!/usr/bin/env python3
"""
Test script for verifying the splitting functionality of the Toggl Overnight Entry Splitter.

This script creates mock entries and tests the splitting functionality.
"""

import logging
import pytz
from datetime import datetime, timedelta
from api_client import TogglApiClient
from entry_processor import EntryProcessor

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MockTogglApiClient:
    """Mock Toggl API client for testing."""

    def __init__(self):
        self.entries = []
        self.created_entries = []
        self.deleted_entries = []

    def create_time_entry(self, description, start_time, end_time, tags=None, project_id=None, billable=False):
        """Mock creating a time entry."""
        entry_id = len(self.created_entries) + 1000
        entry = {
            "id": entry_id,
            "description": description,
            "start": start_time.isoformat(),
            "stop": end_time.isoformat(),
            "tags": tags or [],
            "project_id": project_id,
            "billable": billable
        }
        self.created_entries.append(entry)
        logger.debug(f"Created mock entry: {entry_id}")
        return entry

    def delete_time_entry(self, entry_id):
        """Mock deleting a time entry."""
        self.deleted_entries.append(entry_id)
        logger.debug(f"Deleted mock entry: {entry_id}")
        return True

def create_mock_entry(start_time, duration_hours, description="Test Entry", project_id=12345):
    """Create a mock time entry."""
    start_time_utc = start_time.astimezone(pytz.UTC)
    stop_time_utc = start_time_utc + timedelta(hours=duration_hours)

    return {
        "id": len(mock_api.entries) + 1,
        "description": description,
        "start": start_time_utc.isoformat().replace('+00:00', 'Z'),
        "stop": stop_time_utc.isoformat().replace('+00:00', 'Z'),
        "duration": int(duration_hours * 3600),
        "project_id": project_id,
        "workspace_id": 67890,
        "tags": ["test"],
        "billable": False
    }

def test_overnight_splitting():
    """Test splitting overnight entries."""
    logger.info("Testing overnight entry splitting...")

    # Create a timezone for testing
    timezone = pytz.timezone("Asia/Shanghai")

    # Create an entry processor
    processor = EntryProcessor(mock_api, timezone=timezone.zone)

    # Create a mock overnight entry (starts at 10 PM, ends at 2 AM the next day)
    today = datetime.now(timezone).replace(hour=0, minute=0, second=0, microsecond=0)
    start_time = today.replace(hour=22)  # 10 PM
    overnight_entry = create_mock_entry(start_time, 4, "Overnight Entry")
    mock_api.entries.append(overnight_entry)

    # Process the entry
    processed_entry = processor.process_entry(overnight_entry)

    # Verify it's identified as an overnight entry
    assert processed_entry["is_overnight"], "Entry should be identified as overnight"

    # Split the entry
    split_entries = processor.split_overnight_entry(processed_entry)

    # Verify we have two split entries
    assert len(split_entries) == 2, f"Expected 2 split entries, got {len(split_entries)}"

    # Verify the split entries have the correct times
    first_entry = split_entries[0]
    second_entry = split_entries[1]

    first_start = datetime.fromisoformat(first_entry["start"].replace('Z', '+00:00')).astimezone(timezone)
    first_stop = datetime.fromisoformat(first_entry["stop"].replace('Z', '+00:00')).astimezone(timezone)

    second_start = datetime.fromisoformat(second_entry["start"].replace('Z', '+00:00')).astimezone(timezone)
    second_stop = datetime.fromisoformat(second_entry["stop"].replace('Z', '+00:00')).astimezone(timezone)

    # First entry should start at 10 PM and end at midnight
    assert first_start.hour == 22, f"First entry should start at 10 PM, got {first_start.hour}"
    assert first_stop.hour == 0, f"First entry should end at midnight, got {first_stop.hour}"

    # Second entry should start at midnight and end at 2 AM
    assert second_start.hour == 0, f"Second entry should start at midnight, got {second_start.hour}"
    assert second_stop.hour == 2, f"Second entry should end at 2 AM, got {second_stop.hour}"

    # Verify the descriptions include the split information
    assert "(split 1/2)" in first_entry["description"], f"First entry description should indicate split: {first_entry['description']}"
    assert "(split 2/2)" in second_entry["description"], f"Second entry description should indicate split: {second_entry['description']}"

    logger.info("Overnight entry splitting test passed!")

def test_multi_day_splitting():
    """Test splitting entries that span multiple days."""
    logger.info("Testing multi-day entry splitting...")

    # Create a timezone for testing
    timezone = pytz.timezone("Asia/Shanghai")

    # Create an entry processor
    processor = EntryProcessor(mock_api, timezone=timezone.zone)

    # Create a mock multi-day entry (starts at 10 PM, ends at 2 AM two days later)
    today = datetime.now(timezone).replace(hour=0, minute=0, second=0, microsecond=0)
    start_time = today.replace(hour=22)  # 10 PM
    multi_day_entry = create_mock_entry(start_time, 28, "Multi-day Entry")  # 28 hours = spans 3 days
    mock_api.entries.append(multi_day_entry)

    # Process the entry
    processed_entry = processor.process_entry(multi_day_entry)

    # Verify it's identified as an overnight entry
    assert processed_entry["is_overnight"], "Entry should be identified as overnight"

    # Split the entry
    split_entries = processor.split_overnight_entry(processed_entry)

    # Verify we have three split entries (one for each day)
    assert len(split_entries) == 3, f"Expected 3 split entries, got {len(split_entries)}"

    # Verify the descriptions include the split information
    assert "(split 1/3)" in split_entries[0]["description"], f"First entry description should indicate split: {split_entries[0]['description']}"
    assert "(split 2/3)" in split_entries[1]["description"], f"Second entry description should indicate split: {split_entries[1]['description']}"
    assert "(split 3/3)" in split_entries[2]["description"], f"Third entry description should indicate split: {split_entries[2]['description']}"

    logger.info("Multi-day entry splitting test passed!")

def test_long_entry_splitting():
    """Test splitting long entries."""
    logger.info("Testing long entry splitting...")

    # Create a timezone for testing
    timezone = pytz.timezone("Asia/Shanghai")

    # Create an entry processor with a lower threshold for testing
    processor = EntryProcessor(mock_api, timezone=timezone.zone, long_entry_threshold=8)

    # Create a mock long entry (10 hours, not overnight)
    today = datetime.now(timezone).replace(hour=0, minute=0, second=0, microsecond=0)
    start_time = today.replace(hour=8)  # 8 AM
    long_entry = create_mock_entry(start_time, 10, "Long Entry")  # 10 hours
    mock_api.entries.append(long_entry)

    # Process the entry
    processed_entry = processor.process_entry(long_entry)

    # Verify it's identified as a long entry
    assert processed_entry["duration_hours"] >= processor.long_entry_threshold, "Entry should be identified as long"

    # Split the entry
    split_entries = processor.split_long_entry(processed_entry, processor.long_entry_threshold)

    # Verify we have two split entries
    assert len(split_entries) == 2, f"Expected 2 split entries, got {len(split_entries)}"

    # Verify the descriptions include the split information
    assert "(long split 1/2)" in split_entries[0]["description"], f"First entry description should indicate long split: {split_entries[0]['description']}"
    assert "(long split 2/2)" in split_entries[1]["description"], f"Second entry description should indicate long split: {split_entries[1]['description']}"

    logger.info("Long entry splitting test passed!")

def test_batch_processing():
    """Test batch processing of entries."""
    logger.info("Testing batch processing...")

    # Create a timezone for testing
    timezone = pytz.timezone("Asia/Shanghai")

    # Create an entry processor
    processor = EntryProcessor(mock_api, timezone=timezone.zone, long_entry_threshold=8)

    # Create various mock entries
    today = datetime.now(timezone).replace(hour=0, minute=0, second=0, microsecond=0)

    # Regular entry (not overnight, not long)
    regular_entry = create_mock_entry(today.replace(hour=9), 4, "Regular Entry")

    # Overnight entry
    overnight_entry = create_mock_entry(today.replace(hour=22), 4, "Overnight Entry")

    # Long entry (not overnight)
    long_entry = create_mock_entry(today.replace(hour=8), 10, "Long Entry")

    # Long overnight entry
    long_overnight_entry = create_mock_entry(today.replace(hour=20), 12, "Long Overnight Entry")

    # Add entries to the mock API
    mock_api.entries = []  # Clear existing entries
    mock_api.entries.extend([regular_entry, overnight_entry, long_entry, long_overnight_entry])

    # Reset the created and deleted entries for this test
    mock_api.created_entries = []
    mock_api.deleted_entries = []

    # Process all entries
    summary = processor.process_entries(
        [regular_entry, overnight_entry, long_entry, long_overnight_entry],
        dry_run=False,
        interactive=False,
        no_delete=False
    )

    # Print debug information
    logger.debug(f"Created entries: {len(mock_api.created_entries)}")
    for i, entry in enumerate(mock_api.created_entries):
        logger.debug(f"  Entry {i+1}: {entry.get('description')}")

    logger.debug(f"Deleted entries: {len(mock_api.deleted_entries)}")
    for i, entry_id in enumerate(mock_api.deleted_entries):
        logger.debug(f"  Entry {i+1}: {entry_id}")

    # Verify the summary
    assert summary["total_entries"] == 4, f"Expected 4 total entries, got {summary['total_entries']}"
    assert summary["overnight_entries"] == 2, f"Expected 2 overnight entries, got {summary['overnight_entries']}"
    assert summary["long_entries"] == 2, f"Expected 2 long entries, got {summary['long_entries']}"

    # Verify the number of created and deleted entries
    # We should have:
    # - 2 entries for the overnight entry
    # - 2 entries for the long entry (but it might be skipped if it's processed after the long overnight entry)
    # - 2 entries for the long overnight entry
    # Total: 4-6 new entries
    assert len(mock_api.created_entries) >= 4, f"Expected at least 4 created entries, got {len(mock_api.created_entries)}"

    # We should have deleted at least 2 original entries (overnight and long overnight)
    assert len(mock_api.deleted_entries) >= 2, f"Expected at least 2 deleted entries, got {len(mock_api.deleted_entries)}"

    logger.info("Batch processing test passed!")

if __name__ == "__main__":
    # Create a mock API client
    mock_api = MockTogglApiClient()

    # Run the tests
    test_overnight_splitting()
    test_multi_day_splitting()
    test_long_entry_splitting()
    test_batch_processing()

    logger.info("All tests passed!")