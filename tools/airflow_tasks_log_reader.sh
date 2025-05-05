#!/bin/bash

# Check if a folder parameter is provided
if [[ -z "$1" ]]; then
    echo "Usage: $0 <folder>"
    exit 1
fi

# Get the folder from the parameter
FOLDER_TO_SEARCH="$1"

# Define the separator
SEPARATOR="=========================================="

# Check if the provided folder exists
if [[ ! -d "$FOLDER_TO_SEARCH" ]]; then
    echo "Error: Folder '$FOLDER_TO_SEARCH' does not exist."
    exit 1
fi

# Find all log files in the folder and its subdirectories
LOG_FILES=$(find "$FOLDER_TO_SEARCH" -type f -name "*.log")

# Check if any log files were found
if [[ -z "$LOG_FILES" ]]; then
    echo "No log files found in the folder '$FOLDER_TO_SEARCH'."
    exit 0
fi

# Iterate through each log file and print its content with separators
for LOG_FILE in $LOG_FILES; do
    echo "$SEPARATOR"
    echo "Contents of: $LOG_FILE"
    echo "$SEPARATOR"
    cat "$LOG_FILE"
    echo ""
done
