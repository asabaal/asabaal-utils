#!/bin/bash
# repo-full-code.sh - Extract all code from a repository into a single document
# description: Extract all code from a repository into a single document with absolute path support
# version: 1.1.0
# category: development

set -e

if [ $# -eq 0 ]; then
    echo "Usage: $0 <repository-directory> [output-file]"
    echo "Example: $0 /path/to/music_theory repo-analysis.md"
    echo "Note: output-file can be a relative or absolute path"
    exit 1
fi

REPO_DIR="$1"
OUTPUT_FILE="$2"

# Set default output file if not provided
if [ -z "$OUTPUT_FILE" ]; then
    OUTPUT_FILE="repo-analysis.md"
fi

if [ ! -d "$REPO_DIR" ]; then
    echo "Error: Directory $REPO_DIR does not exist"
    exit 1
fi

# Store the original directory
ORIGINAL_DIR="$(pwd)"

# Determine if OUTPUT_FILE is absolute or relative path
if [[ "$OUTPUT_FILE" = /* ]]; then
    # Absolute path
    OUTPUT_PATH="$OUTPUT_FILE"
    echo "Using absolute output path: $OUTPUT_PATH"
else
    # Relative path (relative to current directory, not repo directory)
    OUTPUT_PATH="$ORIGINAL_DIR/$OUTPUT_FILE"
    echo "Using relative output path: $OUTPUT_PATH"
fi

# Create output directory if it doesn't exist
OUTPUT_DIR="$(dirname "$OUTPUT_PATH")"
mkdir -p "$OUTPUT_DIR"

# Change to repo directory for analysis
cd "$REPO_DIR"

# Initialize output file
cat > "$OUTPUT_PATH" << EOF
# Repository Code Analysis

**Repository:** $(basename "$(pwd)")  
**Analysis Date:** $(date)  
**Git Commit:** $(git rev-parse HEAD 2>/dev/null || echo "Not a git repository")

## Repository Structure

\`\`\`
$(find . -type f -name "*.ts" -o -name "*.js" -o -name "*.tsx" -o -name "*.jsx" -o -name "*.json" -o -name "*.md" -o -name "*.yml" -o -name "*.yaml" | grep -v node_modules | grep -v .git | grep -v dist | grep -v build | sort)
\`\`\`

## File Contents

EOF

# Function to get file extension for syntax highlighting
get_syntax() {
    case "$1" in
        *.ts) echo "typescript" ;;
        *.tsx) echo "tsx" ;;
        *.js) echo "javascript" ;;
        *.jsx) echo "jsx" ;;
        *.json) echo "json" ;;
        *.md) echo "markdown" ;;
        *.yml|*.yaml) echo "yaml" ;;
        *.sh) echo "bash" ;;
        *.py) echo "python" ;;
        *.rb) echo "ruby" ;;
        *.java) echo "java" ;;
        *.html) echo "html" ;;
        *.css) echo "css" ;;
        *.scss) echo "scss" ;;
        *.less) echo "less" ;;
        *.php) echo "php" ;;
        *.c) echo "c" ;;
        *.cpp) echo "cpp" ;;
        *.h) echo "c" ;;
        *.hpp) echo "cpp" ;;
        *) echo "text" ;;
    esac
}

# Process each relevant file
find . -type f \( -name "*.ts" -o -name "*.js" -o -name "*.tsx" -o -name "*.jsx" -o -name "*.json" -o -name "*.md" -o -name "*.yml" -o -name "*.yaml" -o -name "*.sh" -o -name "*.py" \) \
    | grep -v node_modules \
    | grep -v .git \
    | grep -v dist \
    | grep -v build \
    | sort \
    | while read -r file; do
        
        # Skip binary files and very large files
        if [ -f "$file" ] && [ "$(wc -c < "$file")" -lt 100000 ]; then
            echo "" >> "$OUTPUT_PATH"
            echo "### $file" >> "$OUTPUT_PATH"
            echo "" >> "$OUTPUT_PATH"
            echo "\`\`\`$(get_syntax "$file")" >> "$OUTPUT_PATH"
            cat "$file" >> "$OUTPUT_PATH"
            echo "" >> "$OUTPUT_PATH"
            echo "\`\`\`" >> "$OUTPUT_PATH"
            echo "" >> "$OUTPUT_PATH"
        fi
    done

echo "## Summary" >> "$OUTPUT_PATH"
echo "" >> "$OUTPUT_PATH"
echo "- **Total TypeScript files:** $(find . -name "*.ts" -o -name "*.tsx" | grep -v node_modules | wc -l)" >> "$OUTPUT_PATH"
echo "- **Total JavaScript files:** $(find . -name "*.js" -o -name "*.jsx" | grep -v node_modules | wc -l)" >> "$OUTPUT_PATH"
echo "- **Total Python files:** $(find . -name "*.py" | grep -v node_modules | wc -l)" >> "$OUTPUT_PATH"
echo "- **Total lines of code:** $(find . -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" -o -name "*.py" | grep -v node_modules | xargs wc -l 2>/dev/null | tail -1 | awk '{print $1}' || echo "0")" >> "$OUTPUT_PATH"
echo "- **Package.json exists:** $([ -f package.json ] && echo "Yes" || echo "No")" >> "$OUTPUT_PATH"
echo "- **TypeScript config exists:** $([ -f tsconfig.json ] && echo "Yes" || echo "No")" >> "$OUTPUT_PATH"
echo "- **Python setup.py exists:** $([ -f setup.py ] && echo "Yes" || echo "No")" >> "$OUTPUT_PATH"
echo "- **Tests directory exists:** $([ -d tests ] || [ -d test ] || [ -d __tests__ ] && echo "Yes" || echo "No")" >> "$OUTPUT_PATH"

# Return to original directory
cd "$ORIGINAL_DIR"

echo "Analysis complete! Output saved to: $OUTPUT_PATH"