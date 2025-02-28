# Toggl Tools

A collection of utilities for Toggl time tracking to help you analyze and clean up your time entries.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.6+](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/downloads/)

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
   git clone https://github.com/yourusername/toggl-tools.git
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
python overlap_detector.py --days 30 --min-overlap 300
```

### Overnight Entry Splitter

```bash
python overnight_splitter.py --days 30 --interactive
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