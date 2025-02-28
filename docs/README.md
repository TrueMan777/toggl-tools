# Toggl Tools Documentation

This directory contains detailed documentation for the Toggl Tools package.

## Contents

- [Overlap Detector](OVERLAP_DETECTOR.md) - Documentation for the Toggl Overlap Detector tool
- [Overnight Splitter](OVERNIGHT_SPLITTER.md) - Documentation for the Toggl Overnight Entry Splitter tool

## Images

The `images/` directory contains screenshots and diagrams used in the documentation:

- `overlap_detector_example.png` - Example output of the Overlap Detector
- `overnight_splitter_example.png` - Example output of the Overnight Splitter

## Additional Resources

- [Installation Guide](../INSTALL.md) - Detailed installation instructions
- [Contributing Guide](../CONTRIBUTING.md) - How to contribute to the project
- [Security Policy](../SECURITY.md) - Security information and vulnerability reporting

## API Documentation

The Toggl Tools package consists of several modules:

### Core Modules

- `toggl_tools.api_client` - Client for interacting with the Toggl API
- `toggl_tools.entry_processor` - Process and manipulate Toggl time entries

### Command-line Scripts

- `toggl_tools.scripts.overlap_detector` - Identify overlapping time entries
- `toggl_tools.scripts.overnight_splitter` - Split entries that span across midnight

## Usage Examples

For usage examples, please refer to the specific tool documentation linked above.

## Troubleshooting

If you encounter issues with the tools, please check the troubleshooting sections in each tool's documentation. If your issue is not addressed, please [open an issue](https://github.com/yourusername/toggl-tools/issues/new/choose) on GitHub. 