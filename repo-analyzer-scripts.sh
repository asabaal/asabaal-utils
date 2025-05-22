#!/bin/bash
# repo-full-code.sh - Extract all code from a repository into a single document

set -e

if [ $# -eq 0 ]; then
    echo "Usage: $0 <repository-directory> [output-file]"
    echo "Example: $0 /path/to/music_theory repo-analysis.md"
    exit 1
fi

REPO_DIR="$1"
OUTPUT_FILE="${2:-repo-analysis.md}"

if [ ! -d "$REPO_DIR" ]; then
    echo "Error: Directory $REPO_DIR does not exist"
    exit 1
fi

# Change to repo directory
cd "$REPO_DIR"

# Initialize output file
cat > "$OUTPUT_FILE" << EOF
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
        *) echo "text" ;;
    esac
}

# Process each relevant file
find . -type f \( -name "*.ts" -o -name "*.js" -o -name "*.tsx" -o -name "*.jsx" -o -name "*.json" -o -name "*.md" -o -name "*.yml" -o -name "*.yaml" -o -name "*.sh" \) \
    | grep -v node_modules \
    | grep -v .git \
    | grep -v dist \
    | grep -v build \
    | sort \
    | while read -r file; do
        
        # Skip binary files and very large files
        if [ -f "$file" ] && [ "$(wc -c < "$file")" -lt 100000 ]; then
            echo "" >> "$OUTPUT_FILE"
            echo "### $file" >> "$OUTPUT_FILE"
            echo "" >> "$OUTPUT_FILE"
            echo "\`\`\`$(get_syntax "$file")" >> "$OUTPUT_FILE"
            cat "$file" >> "$OUTPUT_FILE"
            echo "" >> "$OUTPUT_FILE"
            echo "\`\`\`" >> "$OUTPUT_FILE"
            echo "" >> "$OUTPUT_FILE"
        fi
    done

echo "## Summary" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
echo "- **Total TypeScript files:** $(find . -name "*.ts" -o -name "*.tsx" | grep -v node_modules | wc -l)" >> "$OUTPUT_FILE"
echo "- **Total JavaScript files:** $(find . -name "*.js" -o -name "*.jsx" | grep -v node_modules | wc -l)" >> "$OUTPUT_FILE"
echo "- **Total lines of code:** $(find . -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" | grep -v node_modules | xargs wc -l 2>/dev/null | tail -1 | awk '{print $1}' || echo "0")" >> "$OUTPUT_FILE"
echo "- **Package.json exists:** $([ -f package.json ] && echo "Yes" || echo "No")" >> "$OUTPUT_FILE"
echo "- **TypeScript config exists:** $([ -f tsconfig.json ] && echo "Yes" || echo "No")" >> "$OUTPUT_FILE"
echo "- **Tests directory exists:** $([ -d tests ] || [ -d test ] || [ -d __tests__ ] && echo "Yes" || echo "No")" >> "$OUTPUT_FILE"

echo "Analysis complete! Output saved to: $OUTPUT_FILE"