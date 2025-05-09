#!/usr/bin/env python3

import os
import sqlite3
import json
import platform
import datetime
import re
from pathlib import Path
import argparse

# Command type mapping
COMMAND_TYPES = {
    1: "chat",
    2: "completion",
    3: "insert",
    4: "edit",
    5: "delete",
    6: "format",
    7: "explain",
    8: "test",
    9: "fix",
    10: "optimize"
}

def get_cursor_storage_paths():
    """Get all possible Cursor storage paths based on the operating system."""
    system = platform.system()
    home = Path.home()
    paths = []
    
    # Common paths across all OS
    common_paths = [
        "Cursor/User/workspaceStorage",
        "Cursor/User/globalStorage",
        "Cursor/Storage",
        "Cursor/User/state.vscdb"
    ]
    
    if system == "Darwin":  # macOS
        base_paths = [
            home / "Library/Application Support",
            home / "Library/Caches",
            home / "Library/Preferences"
        ]
    elif system == "Windows":
        base_paths = [
            home / "AppData/Roaming",
            home / "AppData/Local",
            home / "AppData/LocalLow"
        ]
    elif system == "Linux":
        base_paths = [
            home / ".config",
            home / ".local/share",
            home / ".cache"
        ]
    else:
        base_paths = [home]
    
    # Add all possible combinations
    for base in base_paths:
        for common in common_paths:
            path = base / common
            if path.exists():
                paths.append(path)
    
    # Add custom path from environment variable if set
    custom_path = os.environ.get('CURSOR_STORAGE_PATH')
    if custom_path:
        custom_path = Path(custom_path)
        if custom_path.exists():
            paths.append(custom_path)
    
    return paths

def find_cursor_dbs():
    """Find all potential Cursor database files."""
    db_files = []
    for base_path in get_cursor_storage_paths():
        if base_path.is_file():
            db_files.append(str(base_path))
        else:
            for root, dirs, files in os.walk(base_path):
                for file in files:
                    if file.endswith('.vscdb') or file.endswith('.db'):
                        full_path = os.path.join(root, file)
                        try:
                            with sqlite3.connect(full_path) as conn:
                                conn.execute("SELECT 1")
                            db_files.append(full_path)
                        except sqlite3.Error:
                            continue
    
    return db_files

def get_project_files(workspace_path):
    """Get all files in the workspace."""
    files = set()
    for root, _, filenames in os.walk(workspace_path):
        for filename in filenames:
            if not filename.startswith('.'):  # Skip hidden files
                rel_path = os.path.relpath(os.path.join(root, filename), workspace_path)
                files.add(rel_path.lower())  # Store lowercase for case-insensitive matching
    return files

def is_prompt_related_to_workspace(prompt_text, workspace_files):
    """Check if a prompt is related to the current workspace."""
    prompt_text = prompt_text.lower()  # Convert to lowercase for case-insensitive matching
    
    # Always return True for now to see all prompts
    return True
    
    # Original filtering logic (commented out for debugging)
    """
    # Check for workspace files in the prompt
    for file in workspace_files:
        if file in prompt_text:
            return True
    
    # Check for code blocks that might contain workspace files
    if '```' in prompt_text:
        code_blocks = re.findall(r'```(?:[a-z]*\n)?(.*?)```', prompt_text, re.DOTALL)
        for block in code_blocks:
            block = block.lower()
            for file in workspace_files:
                if file in block:
                    return True
    
    return False
    """

def extract_prompts_from_value(value, workspace_files):
    """Extract prompts from the aiService.prompts value."""
    try:
        prompts_data = json.loads(value)
        if not isinstance(prompts_data, list):
            return []
            
        extracted_prompts = []
        for prompt in reversed(prompts_data):  # Process in reverse to get most recent first
            if isinstance(prompt, dict) and 'text' in prompt:
                if prompt['text'].strip():
                    command_type = prompt.get('commandType', 'unknown')
                    if isinstance(command_type, int) and command_type in COMMAND_TYPES:
                        command_type = COMMAND_TYPES[command_type]
                    
                    # Use prompt's timestamp if available, otherwise use current time
                    timestamp = prompt.get('timestamp', datetime.datetime.now().isoformat())
                    
                    extracted_prompts.append({
                        'content': prompt['text'],
                        'command_type': command_type,
                        'timestamp': timestamp,
                        'raw_data': prompt
                    })
        
        return extracted_prompts
    except json.JSONDecodeError:
        return []

def write_prompts_to_log(prompts, workspace_path, output_file="cursor-prompts.log"):
    """Write prompts to the log file."""
    if not prompts:
        return False
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"Cursor Prompts Log - Generated at {datetime.datetime.now().isoformat()}\n")
            f.write(f"Workspace: {workspace_path}\n")
            f.write("=" * 80 + "\n\n")
            
            for prompt in prompts:
                f.write(f"Timestamp: {prompt.get('timestamp', 'Unknown')}\n")
                f.write(f"Command Type: {prompt.get('command_type', 'Unknown')}\n")
                f.write("Content:\n")
                f.write(f"{prompt.get('content', 'No content')}\n")
                
                # Write raw data
                f.write("\nRaw Data:\n")
                raw_data = prompt.get('raw_data', {})
                for key, value in raw_data.items():
                    f.write(f"{key}: {json.dumps(value, indent=2)}\n")
                
                f.write("-" * 80 + "\n\n")
        
        return True
    except IOError:
        return False

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Extract AI prompt history from Cursor\'s local database.')
    parser.add_argument('--output', type=str, default='cursor-prompts.log',
                      help='Path to output log file (default: cursor-prompts.log)')
    parser.add_argument('--verbose', action='store_true',
                      help='Enable verbose output')
    args = parser.parse_args()
    
    try:
        # Get workspace path
        workspace_path = Path.cwd()
        if args.verbose:
            print(f"Current workspace: {workspace_path}")
        
        # Get workspace files (still needed for potential future filtering)
        workspace_files = get_project_files(workspace_path)
        if args.verbose:
            print(f"Found {len(workspace_files)} files in workspace")
        
        # Find Cursor databases
        db_files = find_cursor_dbs()
        if not db_files:
            print("No Cursor databases found")
            return
        
        print(f"Found {len(db_files)} database files")
        
        # Extract prompts
        all_prompts = []
        for db_path in db_files:
            try:
                with sqlite3.connect(db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT * FROM ItemTable WHERE key = 'aiService.prompts'")
                    rows = cursor.fetchall()
                    
                    print(f"\nProcessing database: {db_path}")
                    print(f"Found {len(rows)} rows with prompts")
                    
                    for row in rows:
                        row_dict = dict(zip([col[0] for col in cursor.description], row))
                        if 'value' in row_dict:
                            prompts = extract_prompts_from_value(row_dict['value'], workspace_files)
                            print(f"Extracted {len(prompts)} prompts from this row")
                            all_prompts.extend(prompts)
            except sqlite3.Error as e:
                print(f"Error processing database {db_path}: {e}")
                continue
        
        print(f"\nTotal prompts found: {len(all_prompts)}")
        
        # Sort prompts by timestamp (most recent first)
        all_prompts.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # Write prompts to log
        if write_prompts_to_log(all_prompts, workspace_path, args.output):
            print(f"\nSuccessfully wrote {len(all_prompts)} prompts to {args.output}")
        else:
            print("\nNo prompts found")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main() 