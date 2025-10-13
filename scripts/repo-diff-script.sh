#!/bin/bash
# repo-diff-analysis.sh - Extract git diff into a readable document

set -e

if [ $# -eq 0 ]; then
    echo "Usage: $0 <repository-directory> [commit-reference] [output-file]"
    echo ""
    echo "Examples:"
    echo "  $0 /path/to/music_theory                    # Diff from previous commit"
    echo "  $0 /path/to/music_theory HEAD~2             # Diff from 2 commits ago"
    echo "  $0 /path/to/music_theory main               # Diff from main branch"
    echo "  $0 /path/to/music_theory abc123             # Diff from specific commit"
    exit 1
fi

REPO_DIR="$1"
COMMIT_REF="${2:-HEAD~1}"
OUTPUT_FILE="${3:-repo-diff.md}"

if [ ! -d "$REPO_DIR" ]; then
    echo "Error: Directory $REPO_DIR does not exist"
    exit 1
fi

# Change to repo directory
cd "$REPO_DIR"

# Check if it's a git repository
if [ ! -d ".git" ]; then
    echo "Error: $REPO_DIR is not a git repository"
    exit 1
fi

# Initialize output file
cat > "$OUTPUT_FILE" << EOF
# Repository Diff Analysis

**Repository:** $(basename "$(pwd)")
**Analysis Date:** $(date)
**Current Commit:** $(git rev-parse HEAD)
**Comparing Against:** $COMMIT_REF ($(git rev-parse "$COMMIT_REF" 2>/dev/null || echo "invalid reference"))

## Commit Information

### Current Commit
\`\`\`
$(git log -1 --pretty=format:"Commit: %H%nAuthor: %an <%ae>%nDate: %ad%nMessage: %s%n%b" HEAD)
\`\`\`

### Comparing Against
\`\`\`
$(git log -1 --pretty=format:"Commit: %H%nAuthor: %an <%ae>%nDate: %ad%nMessage: %s%n%b" "$COMMIT_REF" 2>/dev/null || echo "Could not retrieve commit information")
\`\`\`

## Summary of Changes

EOF

# Get diff statistics
echo "### File Changes" >> "$OUTPUT_FILE"
echo "\`\`\`" >> "$OUTPUT_FILE"
git diff --stat "$COMMIT_REF" HEAD >> "$OUTPUT_FILE"
echo "\`\`\`" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# Get list of changed files
echo "### Changed Files" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
git diff --name-status "$COMMIT_REF" HEAD | while read -r status file; do
    case "$status" in
        A) echo "- **Added:** $file" >> "$OUTPUT_FILE" ;;
        M) echo "- **Modified:** $file" >> "$OUTPUT_FILE" ;;
        D) echo "- **Deleted:** $file" >> "$OUTPUT_FILE" ;;
        R*) echo "- **Renamed:** $file" >> "$OUTPUT_FILE" ;;
        C*) echo "- **Copied:** $file" >> "$OUTPUT_FILE" ;;
        *) echo "- **$status:** $file" >> "$OUTPUT_FILE" ;;
    esac
done
echo "" >> "$OUTPUT_FILE"

# Get detailed diff for each file
echo "## Detailed Changes" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

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
        *) echo "diff" ;;
    esac
}

# Process each changed file
git diff --name-only "$COMMIT_REF" HEAD | while read -r file; do
    if [ -f "$file" ]; then
        echo "### $file" >> "$OUTPUT_FILE"
        echo "" >> "$OUTPUT_FILE"
        
        # Show the diff with context
        echo "\`\`\`diff" >> "$OUTPUT_FILE"
        git diff "$COMMIT_REF" HEAD -- "$file" >> "$OUTPUT_FILE"
        echo "\`\`\`" >> "$OUTPUT_FILE"
        echo "" >> "$OUTPUT_FILE"
        
        # If it's a new file, also show the full content
        if ! git cat-file -e "$COMMIT_REF:$file" 2>/dev/null; then
            echo "#### Full Content (New File)" >> "$OUTPUT_FILE"
            echo "" >> "$OUTPUT_FILE"
            echo "\`\`\`$(get_syntax "$file")" >> "$OUTPUT_FILE"
            cat "$file" >> "$OUTPUT_FILE"
            echo "\`\`\`" >> "$OUTPUT_FILE"
            echo "" >> "$OUTPUT_FILE"
        fi
    fi
done

# Add analysis summary
echo "## Analysis Summary" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
echo "- **Files changed:** $(git diff --name-only "$COMMIT_REF" HEAD | wc -l)" >> "$OUTPUT_FILE"
echo "- **Lines added:** $(git diff --shortstat "$COMMIT_REF" HEAD | grep -o '[0-9]* insertion' | cut -d' ' -f1 || echo "0")" >> "$OUTPUT_FILE"
echo "- **Lines removed:** $(git diff --shortstat "$COMMIT_REF" HEAD | grep -o '[0-9]* deletion' | cut -d' ' -f1 || echo "0")" >> "$OUTPUT_FILE"
echo "- **Commits between:** $(git rev-list --count "$COMMIT_REF"..HEAD)" >> "$OUTPUT_FILE"

# List new functions/classes/interfaces (for TypeScript/JavaScript files)
echo "" >> "$OUTPUT_FILE"
echo "### New Code Structures" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

git diff --name-only "$COMMIT_REF" HEAD | grep -E '\.(ts|js|tsx|jsx)$' | while read -r file; do
    if [ -f "$file" ]; then
        NEW_FUNCTIONS=$(git diff "$COMMIT_REF" HEAD -- "$file" | grep '^+' | grep -E '(function |const .* = |class |interface |type )' | sed 's/^+//' | head -10)
        if [ -n "$NEW_FUNCTIONS" ]; then
            echo "#### $file" >> "$OUTPUT_FILE"
            echo "\`\`\`typescript" >> "$OUTPUT_FILE"
            echo "$NEW_FUNCTIONS" >> "$OUTPUT_FILE"
            echo "\`\`\`" >> "$OUTPUT_FILE"
            echo "" >> "$OUTPUT_FILE"
        fi
    fi
done

echo "Diff analysis complete! Output saved to: $OUTPUT_FILE"