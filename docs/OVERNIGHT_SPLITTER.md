# Toggl Overnight Entry Splitter

The Toggl Overnight Entry Splitter is a tool that helps you split time entries that span across midnight or exceed a maximum duration. This makes it easier to analyze your time spent per day and maintain accurate daily records.

## How It Works

The Overnight Splitter works by:

1. Fetching your time entries from the Toggl API for a specified time period
2. Identifying entries that span across midnight or exceed a maximum duration
3. Splitting these entries into multiple entries, one for each day
4. Creating the new entries in your Toggl account and optionally deleting the original entries

## Usage

### Command Line

```bash
toggl-overnight-splitter [options]
```

### Options

- `--api-key KEY`: Toggl API key (overrides environment variable and .env file)
- `--days DAYS`: Number of days to look back (default: 7)
- `--timezone TIMEZONE`: Timezone for day boundaries (default: Asia/Shanghai)
- `--dry-run`: Identify entries without splitting them
- `--verbose`: Enable verbose logging
- `--interactive`: Confirm each split before applying
- `--no-delete`: Keep original entries after splitting

### Examples

**Basic usage (last 7 days):**
```bash
toggl-overnight-splitter
```

**Check the last 30 days:**
```bash
toggl-overnight-splitter --days 30
```

**Dry run (identify entries without splitting them):**
```bash
toggl-overnight-splitter --dry-run
```

**Interactive mode (confirm each split):**
```bash
toggl-overnight-splitter --interactive
```

**Keep original entries:**
```bash
toggl-overnight-splitter --no-delete
```

## Understanding the Output

The tool first displays a table of entries that need to be split:

```
Found 3 entries to split:

+-------+---------------+---------------------+---------------------+----------+------------+-------------+
| ID    | Description   | Start               | Stop                | Duration | Project    | Split Type  |
+-------+---------------+---------------------+---------------------+----------+------------+-------------+
| 12345 | Sleep         | 2023-01-15 22:00:00 | 2023-01-16 06:00:00 | 8h 0m    | Personal   | Overnight   |
| 12346 | Work marathon | 2023-01-17 09:00:00 | 2023-01-18 15:00:00 | 30h 0m   | Work       | Overnight,  |
|       |               |                     |                     |          |            | Long        |
+-------+---------------+---------------------+---------------------+----------+------------+-------------+
```

If you're in interactive mode, for each entry it will show how it will be split and ask for confirmation:

```
Original entry: Sleep (2023-01-15 22:00:00 - 2023-01-16 06:00:00)
+---------------------------+---------------------+---------------------+----------+
| Description               | Start               | Stop                | Duration |
+---------------------------+---------------------+---------------------+----------+
| Sleep (split 1/2)         | 2023-01-15 22:00:00 | 2023-01-15 23:59:59 | 2h 0m    |
| Sleep (split 2/2)         | 2023-01-16 00:00:00 | 2023-01-16 06:00:00 | 6h 0m    |
+---------------------------+---------------------+---------------------+----------+

Apply this split? (y/n):
```

## Common Use Cases

### Daily Time Analysis

If you track activities that span across midnight (like sleep), splitting them makes it easier to analyze how much time you spent on each activity per day.

### Accurate Daily Reports

For work or billing purposes, having entries split by day can make reporting more accurate and easier to understand.

### Long Activities

Some activities might span multiple days (like a work marathon or travel). Splitting these makes your time tracking more granular and easier to analyze.

## Troubleshooting

### No Entries to Split Found

If no entries to split are found, it could mean:
- You have no entries that span across midnight or exceed the maximum duration
- There's an issue with the timezone setting

### API Key Issues

If you get an error about the API key:
- Make sure your `.env` file contains the correct API key
- Try passing the API key directly with the `--api-key` option

### Split Entries Not Appearing

If split entries don't appear in your Toggl account:
- Check if there were any error messages during the split
- Make sure your API key has write access to your Toggl account
- Try running with the `--verbose` option to see more detailed logs

## Advanced Usage

### Custom Splitting Logic

The default behavior is to split entries at midnight in the specified timezone. If you need different splitting logic, you can modify the `split_overnight_entry` and `split_long_entry` methods in the `EntryProcessor` class.

### Batch Processing

You can use the Overnight Splitter in batch scripts to regularly clean up your time entries:

```bash
# Split entries from the last 30 days without confirmation
toggl-overnight-splitter --days 30

# Output a summary
echo "Overnight entry splitting completed at $(date)"
``` 