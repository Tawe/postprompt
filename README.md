# Cursor Prompt Logger

A Python script to extract and log prompt history from Cursor's local database. This tool helps you keep track of your interactions with Cursor's AI assistant.

## Features

- Extracts all prompts from Cursor's local databases
- Includes command type information (chat, completion, edit, etc.)
- Preserves raw prompt data for reference
- Works across different operating systems (macOS, Windows, Linux)
- Supports custom database locations via environment variables

## Requirements

- Python 3.6 or higher
- SQLite3 (usually comes with Python)

## Installation

1. Clone this repository or download the script
2. Make the script executable (Unix-like systems):
   ```bash
   chmod +x cursor_prompt_logger.py
   ```

## Usage

Basic usage:
```bash
python3 cursor_prompt_logger.py
```

This will:
- Find all Cursor databases on your system
- Extract all prompts from these databases
- Sort them by timestamp (most recent first)
- Save them to `cursor-prompts.log` in the current directory

### Command Line Options

- `--output`: Specify a custom output file path
  ```bash
  python3 cursor_prompt_logger.py --output my-prompts.log
  ```

- `--verbose`: Enable detailed output about the extraction process
  ```bash
  python3 cursor_prompt_logger.py --verbose
  ```

## Output Format

The log file contains:
- Timestamp of each prompt
- Command type (chat, completion, edit, etc.)
- Full prompt content
- Raw prompt data for reference

Example output:
```
Cursor Prompts Log - Generated at 2024-03-14T12:34:56.789Z
Workspace: /path/to/your/workspace
================================================================================

Timestamp: 2024-03-14T12:34:56.789Z
Command Type: chat
Content:
Your prompt text here...

Raw Data:
{
  "text": "Your prompt text here...",
  "commandType": 1,
  ...
}
--------------------------------------------------------------------------------
```

## Custom Database Location

If your Cursor databases are stored in a non-standard location, you can set the `CURSOR_STORAGE_PATH` environment variable:

```bash
export CURSOR_STORAGE_PATH=/path/to/your/cursor/storage
python3 cursor_prompt_logger.py
```

## Troubleshooting

If you encounter any issues:

1. Run with `--verbose` to see detailed output
2. Check that you have read permissions for the Cursor database files
3. Verify that Cursor is installed and has been used (to generate prompt history)
