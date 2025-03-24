# Toggl Tools

A collection of utilities for Toggl time tracking to help you analyze and clean up your time entries.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)


## 🛠️ Tools Included

### 🔍 Toggl Overlap Detector

Identifies overlapping time entries in Toggl, helping you detect time tracking errors or concurrent activities.

**Key Features:**
- Identifies time entries that overlap with each other
- Configurable minimum overlap threshold
- Groups overlapping entries by day for easy analysis
- Detailed output with overlap duration

### ✂️ Toggl Overnight Entry Splitter

Splits Toggl time entries that span across midnight or exceed a maximum duration, making it easier to analyze time spent per day.

**Key Features:**
- Splits overnight entries into separate entries for each day
- Handles entries that span multiple days
- Interactive mode to confirm each split
- Option to keep original entries after splitting

### 🏷️ Toggl Untagged Entries Finder

Identifies and lists all Toggl time entries that don't have any tags, helping you find entries that might need categorization.

**Key Features:**
- Lists all time entries without tags
- Configurable date range and minimum duration
- Multiple output formats (table, CSV, JSON)
- Sorting options by date, duration, or description
- Summary statistics of total untagged time

### 🤖 Toggl Auto Tagger

Automatically assigns tags to Toggl time entries based on their descriptions using customizable mapping rules.

**Key Features:**
- Automatically tags entries based on description patterns
- Creates a template mapping file with all available tags
- Interactive mode to confirm each tag assignment
- Dry run mode to preview changes without applying them
- Detailed statistics on applied tags

### 💾 Toggl Entries Exporter

Exports all Toggl time entries to a JSON file for backup, analysis, or data processing.

**Key Features:**
- Exports all time entries within a specified date range to JSON
- Handles Toggl API limitations by fetching data in batches
- Sorts entries by start date for easy analysis
- Preserves non-ASCII characters (like Cyrillic)
- Configurable minimum duration and inclusion of running entries
- Option for pretty-printed JSON output

## 📋 Why These Tools Are Useful

### For Freelancers and Consultants
- Ensure accurate billing by identifying and fixing time tracking errors
- Split overnight work sessions for proper daily reporting
- Improve client reporting with clean, day-based time entries

### For Teams and Managers
- Identify potential time tracking issues across team members
- Get more accurate insights into daily work patterns
- Improve time tracking habits across your organization

### For Personal Productivity
- Get more accurate data about your daily work habits
- Identify when you're trying to multitask (overlapping entries)
- Better understand your work patterns across days

## 🚀 Quick Start

### Installation

1. Clone this repository
   ```
   git clone https://github.com/TrueMan777/toggl-tools.git
   cd toggl-tools
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up your Toggl API key in a `.env` file:
   ```
   TOGGL_API_KEY=your_api_key_here
   ```

### Overlap Detector

```bash
python overlap_detector.py --days 30 --min-overlap 60
```

### Overnight Entry Splitter

```bash
python overnight_splitter.py --days 30 --interactive
```

### Untagged Entries Finder

```bash
python untagged_entries.py --days 30 --output table --sort-by date --min-duration 1
```

### Auto Tagger

```bash
python auto_tagger.py --days 30 --interactive
```

### Entries Exporter

```bash
python export_entries.py --days 90 --pretty --output-file my_toggl_data.json
```

## 📖 Documentation

### Overlap Detector

```
python overlap_detector.py [options]
```

#### Options

- `--api-key KEY`: Toggl API key (overrides environment variable and .env file)
- `--days DAYS`: Number of days to look back (default: 7)
- `--timezone TIMEZONE`: Timezone for time calculations (default: Asia/Shanghai)
- `--verbose`: Enable verbose logging
- `--min-overlap SECONDS`: Minimum overlap in seconds to report (default: 60)

### Overnight Entry Splitter

```
python overnight_splitter.py [options]
```

#### Options

- `--api-key KEY`: Toggl API key (overrides environment variable and .env file)
- `--days DAYS`: Number of days to look back (default: 7)
- `--timezone TIMEZONE`: Timezone for day boundaries (default: Asia/Shanghai)
- `--dry-run`: Identify entries without splitting them
- `--verbose`: Enable verbose logging
- `--interactive`: Confirm each split before applying
- `--no-delete`: Keep original entries after splitting

### Untagged Entries Finder

```
python untagged_entries.py [options]
```

#### Options

- `--api-key KEY`: Toggl API key (overrides environment variable and .env file)
- `--days DAYS`: Number of days to look back (default: 7)
- `--timezone TIMEZONE`: Timezone for time calculations (default: Asia/Shanghai)
- `--verbose`: Enable verbose logging
- `--output FORMAT`: Output format: table, csv, or json (default: table)
- `--sort-by FIELD`: Sort results by: date, duration, or description (default: date)
- `--min-duration MINUTES`: Minimum duration in minutes to include (default: 0)

### Auto Tagger

Automatically tag Toggl time entries based on their descriptions.

```
python auto_tagger.py [options]
```

Options:
- `--api-key API_KEY`: Toggl API key (overrides environment variable and .env file)
- `--days DAYS`: Number of days to look back (default: 7)
- `--timezone TIMEZONE`: Timezone for time calculations (default: Asia/Shanghai)
- `--verbose`: Enable verbose logging
- `--dry-run`: Show what would be tagged without making changes
- `--mapping-file MAPPING_FILE`: JSON file containing description to tag mappings (default: tag_mappings.json)
- `--create-mapping`: Create a new mapping file with available tags
- `--interactive`: Confirm each tag assignment before applying
- `--untagged-only`: Only process entries without tags (default behavior)
- `--all-entries`: Process all entries, including those that already have tags
- `--min-duration MINUTES`: Minimum duration in minutes to include (default: 0)

#### Tag Mapping File

The tag mapping file is a JSON file that maps tags to description patterns. The format is:

```json
{
  "Tag1": [
    "pattern1",
    "pattern2"
  ],
  "Tag2": [
    "pattern3",
    "pattern4"
  ]
}
```

**Note on pattern matching:**
- Patterns are matched as whole words only, using word boundaries.
- For example, the pattern "eat" will match "Let's eat lunch" but not "eating lunch".
- Regex patterns are supported for more complex matching.
- If a description matches patterns for multiple tags, all matching tags will be applied.

You can create a template mapping file with all available tags using the `--create-mapping` option.

### Entries Exporter

```
python export_entries.py [options]
```

#### Options
- `--api-key KEY`: Toggl API key (overrides environment variable and .env file)
- `--days DAYS`: Number of days to look back (default: 30)
- `--timezone TIMEZONE`: Timezone for time calculations (default: Asia/Shanghai)
- `--verbose`: Enable verbose logging
- `--output-file FILE`: Output JSON file path (default: toggl_entries.json)
- `--pretty`: Pretty-print the JSON output
- `--include-running`: Include currently running time entries
- `--min-duration MINUTES`: Minimum duration in minutes to include (default: 0)

#### JSON Output Format

The output JSON file has the following structure:

```json
{
  "metadata": {
    "exported_at": "2023-08-01T12:34:56.789012",
    "entry_count": 123
  },
  "entries": [
    {
      "id": 1234567890,
      "description": "Working on project",
      "start": "2023-07-31T10:00:00+00:00",
      "stop": "2023-07-31T12:30:00+00:00",
      "duration": 9000,
      "duration_formatted": "2h 30m",
      "tags": ["Work", "Project"],
      ...
    },
    ...
  ]
}
```

Entries are sorted by start date in ascending order, and non-ASCII characters (like Cyrillic) are preserved in their original form.

## 🧰 Requirements

- Python 3.10+
- Toggl account with API access
- Required Python packages (see requirements.txt)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

See [CONTRIBUTING.md](CONTRIBUTING.md) for more details.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Toggl API](https://github.com/toggl/toggl_api_docs) for providing the API that makes these tools possible
- All contributors who help improve these tools