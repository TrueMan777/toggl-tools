# Contributing to Toggl Tools

Thank you for considering contributing to Toggl Tools! This document provides guidelines and instructions for contributing.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for everyone.

## How Can I Contribute?

### Reporting Bugs

- Check if the bug has already been reported in the Issues section
- Use the bug report template when creating a new issue
- Include detailed steps to reproduce the bug
- Include information about your environment (OS, Python version, etc.)

### Suggesting Enhancements

- Check if the enhancement has already been suggested in the Issues section
- Use the feature request template when creating a new issue
- Clearly describe the problem and solution
- Explain why this enhancement would be useful

### Pull Requests

1. Fork the repository
2. Create a new branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests to ensure your changes don't break existing functionality
5. Commit your changes (`git commit -m 'Add some amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## Development Setup

1. Clone your fork of the repository
   ```
   git clone https://github.com/yourusername/toggl-tools.git
   cd toggl-tools
   ```

2. Create a virtual environment
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies
   ```
   pip install -r requirements.txt
   pip install -e .  # Install in development mode
   ```

4. Create a `.env` file with your Toggl API key (see `.env.example`)

## Coding Guidelines

- Follow PEP 8 style guide
- Use type hints for function arguments and returns
- Document classes and functions with docstrings
- Keep functions focused and under 50 lines
- Use meaningful variable names

## Testing

- Add tests for new features
- Ensure all tests pass before submitting a pull request
- Run tests with `python -m unittest discover`

## Documentation

- Update documentation for any changes to functionality
- Use clear and concise language
- Include examples where appropriate

## Commit Messages

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Reference issues and pull requests where appropriate

## License

By contributing to Toggl Tools, you agree that your contributions will be licensed under the project's MIT License.