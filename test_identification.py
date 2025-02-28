#!/usr/bin/env python3
"""
Test script for Toggl entry identification.

This script creates mock time entries and tests the identification functionality.
"""

import pytz
from datetime import datetime, timedelta
import logging
from entry_processor import EntryProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_mock_entry(start_time, duration_hours, description="Test Entry", project_name="Test Project"):
    """
    Create a mock time entry for testing.
    
    Args:
        start_time (datetime): Start time of the entry
        duration_hours (float): Duration in hours
        description (str): Entry description
        project_name (str): Project name
        
    Returns:
        dict: Mock time entry
    """
    # Convert to UTC for API compatibility
    start_time_utc = start_time.astimezone(pytz.UTC)
    stop_time_utc = start_time_utc + timedelta(hours=duration_hours)
    
    return {
        "id": 12345,
        "description": description,
        "start": start_time_utc.isoformat().replace("+00:00", "Z"),
        "stop": stop_time_utc.isoformat().replace("+00:00", "Z"),
        "duration": int(duration_hours * 3600),
        "project_id": 67890,
        "project": project_name,
        "workspace_id": 9876,
        "tags": [],
        "billable": False
    }

def test_overnight_identification():
    """
    Test the identification of overnight and long entries.
    """
    # Create test entries
    # 1. Regular entry (8 hours, not overnight)
    regular_entry = create_mock_entry(
        datetime(2023, 5, 1, 9, 0, 0, tzinfo=pytz.timezone("Asia/Shanghai")),
        8.0,
        "Regular Entry",
        "Regular Project"
    )
    
    # 2. Overnight entry (4 hours, crosses midnight)
    overnight_entry = create_mock_entry(
        datetime(2023, 5, 1, 22, 0, 0, tzinfo=pytz.timezone("Asia/Shanghai")),
        4.0,
        "Overnight Entry",
        "Overnight Project"
    )
    
    # 3. Long entry (25 hours, crosses midnight)
    long_entry = create_mock_entry(
        datetime(2023, 5, 1, 10, 0, 0, tzinfo=pytz.timezone("Asia/Shanghai")),
        25.0,
        "Long Entry",
        "Long Project"
    )
    
    # 4. Long overnight entry (26 hours, crosses midnight)
    long_overnight_entry = create_mock_entry(
        datetime(2023, 5, 1, 22, 0, 0, tzinfo=pytz.timezone("Asia/Shanghai")),
        26.0,
        "Long Overnight Entry",
        "Long Overnight Project"
    )
    
    # Combine all test entries
    test_entries = [regular_entry, overnight_entry, long_entry, long_overnight_entry]
    
    # Process entries
    processor = EntryProcessor(None, timezone="Asia/Shanghai")
    
    # Process each entry individually for debugging
    logger.info("Processing test entries:")
    for i, entry in enumerate(test_entries, 1):
        processed = processor.process_entry(entry)
        logger.info(f"Entry {i}: {processed['description']} - " +
                   f"Start: {processed['start_time_local'].strftime('%Y-%m-%d %H:%M')}, " +
                   f"Stop: {processed['stop_time_local'].strftime('%Y-%m-%d %H:%M')}, " +
                   f"Duration: {processed['duration_hours']:.1f} hours, " +
                   f"Overnight: {processed['is_overnight']}")
    
    # Process all entries
    all_entries, overnight_entries, long_entries = [], [], []
    
    for entry in test_entries:
        processed_entry = processor.process_entry(entry)
        all_entries.append(processed_entry)
        
        if processed_entry["is_overnight"]:
            overnight_entries.append(processed_entry)
            
        if processed_entry["duration_hours"] >= processor.long_entry_threshold:
            long_entries.append(processed_entry)
    
    # Verify results based on updated expectations
    logger.info(f"Overnight entries: {len(overnight_entries)} (expected: 3)")
    logger.info(f"Long entries: {len(long_entries)} (expected: 2)")
    
    assert len(overnight_entries) == 3, f"Expected 3 overnight entries, got {len(overnight_entries)}"
    assert len(long_entries) == 2, f"Expected 2 long entries, got {len(long_entries)}"
    
    logger.info("All tests passed!")
    
    # Return a summary
    return {
        "total_entries": len(all_entries),
        "overnight_entries": len(overnight_entries),
        "long_entries": len(long_entries)
    }

if __name__ == "__main__":
    summary = test_overnight_identification()
    logger.info(f"Processing summary: {summary}")