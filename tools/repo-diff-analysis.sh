#!/bin/bash
# repo-diff-analysis.sh - Extract git diff into a readable document (FIXED VERSION)
# description: Analyze git diffs between commits and generate comprehensive reports
# version: 1.1.0
# category: development

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() { echo -e "${BLUE}ℹ${NC} $1"; }
print_success() { echo -e "${GREEN}✓${NC} $1"; }
print_warning() { echo -e "${YELLOW}⚠${NC} $1"; }
print_error() { echo -e "${RED}✗${NC} $1"; }

if [ $# -eq 0 ]; then
    echo "Usage: $0 <repository-directory> [commit-reference] [output-file]"
    echo ""
    echo "Examples:"
    echo "  $0 /path/to/music_theory                    # Diff from previous commit"
    echo "  $0 /path/to/music_theory HEAD~2             # Diff from 2 commits ago"
    echo "  $0 /path/to/music_theory main               # Diff from main branch"
    echo "  $0 /path/to/music_theory abc123             # Diff from specific commit"
    echo "  $0 ./music_theory HEAD~1 ./diff-report.md  # Specific output location"
    exit 1
fi

REPO_DIR="$1"
COMMIT_REF="${2:-HEAD~1}"
OUTPUT_FILE="${3:-repo-diff.md}"

# Store original directory and resolve absolute paths
ORIGINAL_DIR="$(pwd)"
REPO_DIR_ABS="$(realpath "$REPO_DIR" 2>/dev/null || echo "$REPO_DIR")"

# Handle output file path - if relative, make it relative to original directory
if [[ "$OUTPUT_FILE" = /* ]]; then
    # Absolute path - use as is
    OUTPUT_FILE_ABS="$OUTPUT_FILE"
else
    # Relative path - make it relative to where command was run
    OUTPUT_FILE_ABS="$ORIGINAL_DIR/$OUTPUT_FILE"
fi

print_info "Repository: $REPO_DIR_ABS"
print_info "Comparing: HEAD vs $COMMIT_REF"
print_info "Output: $OUTPUT_FILE_ABS"

# Validate repository directory
if [ ! -d "$REPO_DIR_ABS" ]; then
    print_error "Directory $REPO_DIR_ABS does not exist"
    exit 1
fi

# Change to repo directory
cd "$REPO_DIR_ABS"

# Check if it's a git repository
if [ ! -d ".git" ]; then
    print_error "$REPO_DIR_ABS is not a git repository"
    exit 1
fi

# Validate commit reference
if ! git rev-parse --verify "$COMMIT_REF" >/dev/null 2>&1; then
    print_error "Invalid commit reference: $COMMIT_REF"
    exit 1
fi

print_info "Generating diff analysis..."

# Initialize output file (using absolute path)
cat > "$OUTPUT_FILE_ABS" << EOF
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

# Check if there are any changes
if ! git diff --quiet "$COMMIT_REF" HEAD; then
    # Get diff statistics
    echo "### File Changes" >> "$OUTPUT_FILE_ABS"
    echo "\`\`\`" >> "$OUTPUT_FILE_ABS"
    git diff --stat "$COMMIT_REF" HEAD >> "$OUTPUT_FILE_ABS"
    echo "\`\`\`" >> "$OUTPUT_FILE_ABS"
    echo "" >> "$OUTPUT_FILE_ABS"

    # Get list of changed files
    echo "### Changed Files" >> "$OUTPUT_FILE_ABS"
    echo "" >> "$OUTPUT_FILE_ABS"
    git diff --name-status "$COMMIT_REF" HEAD | while read -r status file; do
        case "$status" in
            A) echo "- **Added:** $file" >> "$OUTPUT_FILE_ABS" ;;
            M) echo "- **Modified:** $file" >> "$OUTPUT_FILE_ABS" ;;
            D) echo "- **Deleted:** $file" >> "$OUTPUT_FILE_ABS" ;;
            R*) echo "- **Renamed:** $file" >> "$OUTPUT_FILE_ABS" ;;
            C*) echo "- **Copied:** $file" >> "$OUTPUT_FILE_ABS" ;;
            *) echo "- **$status:** $file" >> "$OUTPUT_FILE_ABS" ;;
        esac
    done
    echo "" >> "$OUTPUT_FILE_ABS"

    # Get detailed diff for each file
    echo "## Detailed Changes" >> "$OUTPUT_FILE_ABS"
    echo "" >> "$OUTPUT_FILE_ABS"

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
            echo "### $file" >> "$OUTPUT_FILE_ABS"
            echo "" >> "$OUTPUT_FILE_ABS"
            
            # Show the diff with context
            echo "\`\`\`diff" >> "$OUTPUT_FILE_ABS"
            git diff "$COMMIT_REF" HEAD -- "$file" >> "$OUTPUT_FILE_ABS"
            echo "\`\`\`" >> "$OUTPUT_FILE_ABS"
            echo "" >> "$OUTPUT_FILE_ABS"
            
            # If it's a new file, also show the full content
            if ! git cat-file -e "$COMMIT_REF:$file" 2>/dev/null; then
                echo "#### Full Content (New File)" >> "$OUTPUT_FILE_ABS"
                echo "" >> "$OUTPUT_FILE_ABS"
                echo "\`\`\`$(get_syntax "$file")" >> "$OUTPUT_FILE_ABS"
                cat "$file" >> "$OUTPUT_FILE_ABS"
                echo "\`\`\`" >> "$OUTPUT_FILE_ABS"
                echo "" >> "$OUTPUT_FILE_ABS"
            fi
        fi
    done

    # Add analysis summary
    echo "## Analysis Summary" >> "$OUTPUT_FILE_ABS"
    echo "" >> "$OUTPUT_FILE_ABS"
    echo "- **Files changed:** $(git diff --name-only "$COMMIT_REF" HEAD | wc -l)" >> "$OUTPUT_FILE_ABS"
    echo "- **Lines added:** $(git diff --shortstat "$COMMIT_REF" HEAD | grep -o '[0-9]* insertion' | cut -d' ' -f1 || echo "0")" >> "$OUTPUT_FILE_ABS"
    echo "- **Lines removed:** $(git diff --shortstat "$COMMIT_REF" HEAD | grep -o '[0-9]* deletion' | cut -d' ' -f1 || echo "0")" >> "$OUTPUT_FILE_ABS"
    echo "- **Commits between:** $(git rev-list --count "$COMMIT_REF"..HEAD)" >> "$OUTPUT_FILE_ABS"

    # List new functions/classes/interfaces (for TypeScript/JavaScript files)
    echo "" >> "$OUTPUT_FILE_ABS"
    echo "### New Code Structures" >> "$OUTPUT_FILE_ABS"
    echo "" >> "$OUTPUT_FILE_ABS"

    git diff --name-only "$COMMIT_REF" HEAD | grep -E '\.(ts|js|tsx|jsx)$' | while read -r file; do
        if [ -f "$file" ]; then
            NEW_FUNCTIONS=$(git diff "$COMMIT_REF" HEAD -- "$file" | grep '^+' | grep -E '(function |const .* = |class |interface |type )' | sed 's/^+//' | head -10)
            if [ -n "$NEW_FUNCTIONS" ]; then
                echo "#### $file" >> "$OUTPUT_FILE_ABS"
                echo "\`\`\`typescript" >> "$OUTPUT_FILE_ABS"
                echo "$NEW_FUNCTIONS" >> "$OUTPUT_FILE_ABS"
                echo "\`\`\`" >> "$OUTPUT_FILE_ABS"
                echo "" >> "$OUTPUT_FILE_ABS"
            fi
        fi
    done

else
    # No changes found
    echo "### No Changes Found" >> "$OUTPUT_FILE_ABS"
    echo "" >> "$OUTPUT_FILE_ABS"
    echo "No differences found between $COMMIT_REF and HEAD." >> "$OUTPUT_FILE_ABS"
    echo "" >> "$OUTPUT_FILE_ABS"
    print_warning "No changes detected between $COMMIT_REF and HEAD"
fi

# Return to original directory
cd "$ORIGINAL_DIR"

print_success "Diff analysis complete!"
print_info "Output saved to: $OUTPUT_FILE_ABS"

# Verify file was created
if [ -f "$OUTPUT_FILE_ABS" ]; then
    FILE_SIZE=$(wc -l < "$OUTPUT_FILE_ABS")
    print_success "Generated $FILE_SIZE lines of analysis"
    
    # Show a preview of what was generated
    echo ""
    echo "Preview of analysis:"
    echo "===================="
    head -20 "$OUTPUT_FILE_ABS"
    if [ $FILE_SIZE -gt 20 ]; then
        echo "... (${FILE_SIZE} total lines)"
    fi
else
    print_error "Failed to create output file: $OUTPUT_FILE_ABS"
    exit 1
fi
