# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2025-03-02

### Added
- Auto-tagging tool for automatically assigning tags to time entries based on their descriptions
- Command-line options for the auto-tagging tool:
  - `--untagged-only`: Only process entries without tags (default behavior)
  - `--all-entries`: Process all entries, including those that already have tags
  - `--min-duration`: Minimum duration in minutes to include

### Changed
- Improved pattern matching in auto-tagging tool to use whole word matching
  - Patterns now match only complete words, preventing false matches
  - For example, "eat" will match "Let's eat lunch" but not "eating lunch"
- Fixed API endpoint for updating time entries


## [0.1.0] - 2025-02-27

### Added
- Initial release
- Toggl Overlap Detector for identifying overlapping time entries
- Toggl Overnight Entry Splitter for splitting entries that span across midnight
- API client for interacting with the Toggl API
- Entry processor for manipulating time entries
- Command-line interfaces for both tools
- Basic documentation and examples