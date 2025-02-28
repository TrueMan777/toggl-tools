# Toggl Overlap Detector

The Toggl Overlap Detector is a tool that helps you identify overlapping time entries in your Toggl time tracking data. This can be useful for detecting time tracking errors, identifying concurrent activities, or analyzing your multitasking patterns.

## How It Works

The Overlap Detector works by:

1. Fetching your time entries from the Toggl API for a specified time period
2. Processing these entries to identify pairs that overlap in time
3. Grouping overlapping entries by day for easier analysis
4. Displaying detailed information about each overlap, including the duration of the overlap

## Usage

### Command Line

```bash
toggl-overlap-detector [options]
```

### Options

- `--api-key KEY`: Toggl API key (overrides environment variable and .env file)
- `--days DAYS`: Number of days to look back (default: 7)
- `--timezone TIMEZONE`: Timezone for time calculations (default: Asia/Shanghai)
- `--verbose`: Enable verbose logging
- `--min-overlap SECONDS`: Minimum overlap in seconds to report (default: 60)

### Examples

**Basic usage (last 7 days):**
```bash
toggl-overlap-detector
```

**Check the last 30 days:**
```bash
toggl-overlap-detector --days 30
```

**Only show overlaps of at least 5 minutes:**
```bash
toggl-overlap-detector --min-overlap 300
```

**Use a specific timezone:**
```bash
toggl-overlap-detector --timezone America/New_York
```

## Understanding the Output

The output is organized by day and shows each pair of overlapping entries in a table format:

```
=== 2023-01-15 ===
+-------+---------------+-------------+------------+-------+---------------+-------------+------------+----------+
| ID 1  | Description 1 | Time 1      | Project 1  | ID 2  | Description 2 | Time 2      | Project 2  | Overlap  |
+-------+---------------+-------------+------------+-------+---------------+-------------+------------+----------+
| 12345 | Meeting       | 10:00-11:30 | Work       | 12346 | Email         | 11:00-12:00 | Work       | 30m 0s   |
+-------+---------------+-------------+------------+-------+---------------+-------------+------------+----------+
```

This shows that on January 15, 2023, you had two overlapping entries:
1. "Meeting" from 10:00 to 11:30
2. "Email" from 11:00 to 12:00

These entries overlap by 30 minutes.

## Common Use Cases

### Finding Time Tracking Errors

The most common use case is to identify errors in your time tracking. For example, you might have forgotten to stop a timer before starting a new one.

### Analyzing Multitasking

If you intentionally track multiple activities at once, the Overlap Detector can help you analyze your multitasking patterns.

### Improving Time Tracking Accuracy

By regularly checking for overlaps, you can improve the accuracy of your time tracking data, which is especially important for billing or reporting purposes.

## Troubleshooting

### No Overlaps Found

If no overlaps are found, it could mean:
- You have no overlapping time entries in the specified time period
- The minimum overlap threshold is too high
- There's an issue with the timezone setting

### API Key Issues

If you get an error about the API key:
- Make sure your `.env` file contains the correct API key
- Try passing the API key directly with the `--api-key` option

## Advanced Usage

### Integration with Other Tools

You can pipe the output to other tools for further processing:

```bash
toggl-overlap-detector --days 30 > overlaps.txt
```

### Scripting

You can use the Overlap Detector in scripts by checking its exit code:

```bash
toggl-overlap-detector --days 1
if [ $? -eq 0 ]; then
    echo "No issues found"
else
    echo "Overlaps detected"
fi
``` 