#!/bin/bash
# Save as analyze_video_project.sh

# Default values
PROJECT_DIR=""  # Required parameter
REPORT_DIR=""   # Will default to current directory + timestamp
QUICK_MODE=true # Use faster approximations by default

# Function to display usage information
usage() {
    echo "Usage: $0 -p PROJECT_DIR [-r REPORT_DIR] [-q|-a]"
    echo
    echo "Video Project Directory Analyzer"
    echo
    echo "Options:"
    echo "  -p, --project-dir DIR    Project directory to analyze (required)"
    echo "  -r, --report-dir DIR     Directory to save reports (defaults to './video_analysis_TIMESTAMP')"
    echo "  -q, --quick              Quick mode with faster approximations (default)"
    echo "  -a, --accurate           Accurate mode with precise file counting (slower)"
    echo "  -h, --help               Show this help message"
    echo
    echo "Example:"
    echo "  $0 -p /path/to/video/project"
    echo "  $0 -p ./my_project -r ./analysis_reports -a"
    exit 1
}

# Parse command line arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        -p|--project-dir) PROJECT_DIR="$2"; shift ;;
        -r|--report-dir) REPORT_DIR="$2"; shift ;;
        -q|--quick) QUICK_MODE=true ;;
        -a|--accurate) QUICK_MODE=false ;;
        -h|--help) usage ;;
        *) echo "Unknown parameter: $1"; usage ;;
    esac
    shift
done

# Verify required parameters
if [ -z "$PROJECT_DIR" ]; then
    echo "ERROR: Project directory is required."
    usage
fi

# Check if project directory exists
if [ ! -d "$PROJECT_DIR" ]; then
    echo "ERROR: Project directory '$PROJECT_DIR' does not exist."
    exit 1
fi

# Check if pv is installed
if ! command -v pv &> /dev/null; then
    echo "WARNING: 'pv' command not found. Progress bars will not be displayed."
    echo "To install pv:"
    echo "  - On Debian/Ubuntu: sudo apt-get install pv"
    echo "  - On macOS with Homebrew: brew install pv"
    echo "  - On CentOS/RHEL: sudo yum install pv"
    HAS_PV=false
else
    HAS_PV=true
fi

# Set default report directory if not provided
if [ -z "$REPORT_DIR" ]; then
    REPORT_DIR="./video_analysis_$(date +%Y%m%d_%H%M%S)"
fi

# Function to show a spinner with elapsed time
spinner() {
    local pid=$1
    local delay=0.1
    local elapsed=0
    local spinstr='|/-\'
    local estimated=$2  # Estimated time in seconds
    
    while ps -p $pid > /dev/null; do
        local temp=${spinstr#?}
        printf "\r[%c] Running for %02d:%02d" "$spinstr" $((elapsed/60)) $((elapsed%60))
        if [ ! -z "$estimated" ]; then
            printf " (est. total: ~%02d:%02d)" $((estimated/60)) $((estimated%60))
        fi
        spinstr=$temp${spinstr%"$temp"}
        sleep $delay
        elapsed=$(echo "$elapsed + $delay" | bc)
    done
    printf "\rCompleted in %02d:%02d%s\n" $((elapsed/60)) $((elapsed%60)) "                              "
}

# Fast file count estimation using sampling
fast_estimate_files() {
    local dir="$1"
    local sample_size=3
    local avg_files_per_dir=0
    
    # Get directory count (faster than file count)
    local dir_count=$(find "$dir" -type d | wc -l)
    
    # Sample a few directories to estimate files per directory
    if [ $dir_count -gt 1 ]; then
        # Take a few random directories to sample
        local sample_dirs=$(find "$dir" -type d | sort -R | head -n $sample_size)
        local total_sample_files=0
        local sampled_dirs=0
        
        while read -r sample_dir; do
            # Count files in this directory only (not recursive)
            local files_in_dir=$(find "$sample_dir" -maxdepth 1 -type f | wc -l)
            total_sample_files=$((total_sample_files + files_in_dir))
            sampled_dirs=$((sampled_dirs + 1))
        done <<< "$sample_dirs"
        
        if [ $sampled_dirs -gt 0 ]; then
            avg_files_per_dir=$((total_sample_files / sampled_dirs))
        fi
        
        # Estimate total files based on directory count and average
        echo $((dir_count * avg_files_per_dir))
    else
        # Fallback to direct count for small directories
        find "$dir" -type f | wc -l
    fi
}

# Function to estimate duration based on file count and directory size
estimate_duration() {
    local file_count=$1
    local dir_size_kb=$2
    local operation=$3
    
    # Very rough estimates based on operation type
    case $operation in
        "du")
            # Roughly 100 files per second for du, adjusted by size
            local files_per_sec=100
            local est_time=$((file_count / files_per_sec))
            # Adjust for large directories
            if [ $dir_size_kb -gt 1000000 ]; then  # Greater than 1GB
                est_time=$((est_time * 2))
            fi
            ;;
        "find")
            # Find is faster, roughly 1000 files per second
            local est_time=$((file_count / 1000))
            ;;
        "analyze")
            # Analysis is slower, roughly 50 files per second
            local est_time=$((file_count / 50))
            ;;
        *)
            local est_time=60  # Default 1 minute
            ;;
    esac
    
    # Minimum 5 seconds, maximum reasonable time
    if [ $est_time -lt 5 ]; then
        est_time=5
    elif [ $est_time -gt 3600 ]; then
        est_time=3600  # Cap at 1 hour
    fi
    
    echo $est_time
}

# Function to run command with time tracking
run_with_timer() {
    local cmd="$1"
    local desc="$2"
    local est_duration="$3"
    
    echo "Starting: $desc"
    if [ ! -z "$est_duration" ]; then
        echo "Estimated time: $(printf "%02d:%02d" $((est_duration/60)) $((est_duration%60)))"
    fi
    
    # Start the command in background
    eval "$cmd" &
    local cmd_pid=$!
    
    # Show spinner with elapsed time
    spinner $cmd_pid $est_duration
    
    # Wait for command to complete
    wait $cmd_pid
    local status=$?
    
    if [ $status -ne 0 ]; then
        echo "WARNING: Command exited with status $status"
    fi
    
    return $status
}

echo "===== COMPREHENSIVE VIDEO PROJECT ANALYSIS ====="
echo "Project directory: $PROJECT_DIR"
echo "Creating analysis report in: $REPORT_DIR"
mkdir -p "$REPORT_DIR"

# Utility function for section headers
section() {
    echo -e "\n\n===== $1 =====" | tee -a "$REPORT_DIR/summary.txt"
}

# Basic project info
section "PROJECT OVERVIEW"
echo "Project directory: $PROJECT_DIR" | tee -a "$REPORT_DIR/summary.txt"
echo "Analysis timestamp: $(date)" | tee -a "$REPORT_DIR/summary.txt"

# Get initial stats for estimations
echo "Getting preliminary statistics..."

# Fast disk size calculation (doesn't count all files)
dir_size_kb=$(du -k -s "$PROJECT_DIR" | cut -f1)

# File and directory counts - use fast estimation or accurate count
if [ "$QUICK_MODE" = true ]; then
    echo "Using quick estimation mode..."
    # Fast directory count
    total_dirs=$(find "$PROJECT_DIR" -type d | wc -l)
    
    # Fast file count estimate
    total_files=$(fast_estimate_files "$PROJECT_DIR")
    echo "Estimated file count: $total_files (based on directory sampling)"
else
    echo "Using accurate counting mode..."
    # Accurate but slower counts
    dir_count_cmd="find \"$PROJECT_DIR\" -type d | wc -l"
    file_count_cmd="find \"$PROJECT_DIR\" -type f | wc -l"
    
    total_dirs=$(eval $dir_count_cmd)
    total_files=$(eval $file_count_cmd)
    echo "Actual file count: $total_files"
fi

# Estimate total runtime
total_est_time=$(estimate_duration $total_files $dir_size_kb "analyze")
echo "Project size: $(numfmt --to=iec-i --suffix=B $(($dir_size_kb*1024)))" | tee -a "$REPORT_DIR/summary.txt"
echo "Estimated total analysis time: $(printf "%02d:%02d" $((total_est_time/60)) $((total_est_time%60)))"
echo "Found approximately $total_files files across $total_dirs directories" | tee -a "$REPORT_DIR/summary.txt"

# Directory structure analysis
section "DIRECTORY STRUCTURE"
echo "Top-level directories by size:" | tee -a "$REPORT_DIR/summary.txt"

# Estimate time for du operation
est_du_time=$(estimate_duration $total_dirs $dir_size_kb "du")

if [ "$HAS_PV" = true ]; then
    # With progress bar
    pv_cmd="find \"$PROJECT_DIR\" -maxdepth 1 -type d -print0 | pv -0 -s \$(find \"$PROJECT_DIR\" -maxdepth 1 -type d | wc -l) -N \"Analyzing directories\" | xargs -0 du -sh | sort -rh"
    eval "$pv_cmd" | tee -a "$REPORT_DIR/directory_sizes.txt" | head -10 | tee -a "$REPORT_DIR/summary.txt"
else
    # Without progress bar, using timer
    du_cmd="find \"$PROJECT_DIR\" -maxdepth 1 -type d -print0 | xargs -0 du -sh | sort -rh > \"$REPORT_DIR/directory_sizes.txt\""
    run_with_timer "$du_cmd" "Analyzing top-level directories" "$est_du_time"
    head -10 "$REPORT_DIR/directory_sizes.txt" | tee -a "$REPORT_DIR/summary.txt"
fi

# Rest of the script remains the same as before
# ...continuing with largest files analysis, file types analysis, etc.

# Largest files analysis
section "LARGEST FILES"
echo "Finding the largest files..." | tee -a "$REPORT_DIR/summary.txt"

# Estimate time for finding largest files
est_find_time=$(estimate_duration $total_files $dir_size_kb "analyze")

if [ "$HAS_PV" = true ]; then
    # With progress bar
    find_cmd="find \"$PROJECT_DIR\" -type f -print0 | pv -0 -s $total_files -N \"Finding largest files\" | xargs -0 du -h | sort -rh > \"$REPORT_DIR/largest_files.txt\""
    eval "$find_cmd"
else
    # Without progress bar, using timer
    find_cmd="find \"$PROJECT_DIR\" -type f -print0 | xargs -0 du -h | sort -rh > \"$REPORT_DIR/largest_files.txt\""
    run_with_timer "$find_cmd" "Finding largest files" "$est_find_time"
fi

echo "Top 20 largest files:" | tee -a "$REPORT_DIR/summary.txt"
head -20 "$REPORT_DIR/largest_files.txt" | tee -a "$REPORT_DIR/summary.txt"

# File types analysis
section "FILE TYPES ANALYSIS"
echo "Analyzing file types..." | tee -a "$REPORT_DIR/summary.txt"
temp_file=$(mktemp)

# Estimate time for file type analysis
est_analyze_time=$(estimate_duration $total_files $dir_size_kb "analyze")

if [ "$HAS_PV" = true ]; then
    # With progress bar
    analyze_cmd="find \"$PROJECT_DIR\" -type f -print0 | pv -0 -s $total_files -N \"Analyzing file types\" | xargs -0 -I{} bash -c 'f=\"{}\"; ext=\"\${f##*.}\"; size=\$(du -b \"\$f\" | cut -f1); echo \"\$ext \$size \$f\"' > \"$temp_file\""
    eval "$analyze_cmd"
else
    # Without progress bar, using timer
    analyze_cmd="find \"$PROJECT_DIR\" -type f -print0 | xargs -0 -I{} bash -c 'f=\"{}\"; ext=\"\${f##*.}\"; size=\$(du -b \"\$f\" | cut -f1); echo \"\$ext \$size \$f\"' > \"$temp_file\""
    run_with_timer "$analyze_cmd" "Analyzing file types" "$est_analyze_time"
fi

# File counts
echo "File counts by type:" | tee -a "$REPORT_DIR/summary.txt"
cat "$temp_file" | awk '{print $1}' | sort | uniq -c | sort -nr | tee "$REPORT_DIR/file_counts.txt" | head -15 | tee -a "$REPORT_DIR/summary.txt"

# Size by type
echo -e "\nDisk usage by file type:" | tee -a "$REPORT_DIR/summary.txt"
cat "$temp_file" | awk '{arr[$1]+=$2} END {for (i in arr) printf("%-10s\t%.2f GB\n", i, arr[i]/1073741824)}' | sort -k2 -nr | tee "$REPORT_DIR/file_type_sizes.txt" | head -15 | tee -a "$REPORT_DIR/summary.txt"

# Media files analysis
section "MEDIA FILES ANALYSIS"
echo "Analyzing video files..." | tee -a "$REPORT_DIR/summary.txt"

# Find and analyze video files
video_extensions=("mp4" "mov" "avi" "mkv" "webm" "mxf" "m4v" "ts")
echo "Finding all video files..." | tee -a "$REPORT_DIR/summary.txt"

# Build find command for video files
find_cmd="find \"$PROJECT_DIR\" -type f"
for ext in "${video_extensions[@]}"; do
    find_cmd+=" -name \"*.$ext\" -o"
done
find_cmd=${find_cmd::-3}  # Remove last " -o"

# Estimate time for video analysis
est_video_time=$(estimate_duration $((total_files / 5)) $dir_size_kb "find")

if [ "$HAS_PV" = true ]; then
    # With progress bar
    video_cmd="$find_cmd -print0 | pv -0 -s \$($find_cmd | wc -l) -N \"Processing videos\" | xargs -0 du -h | sort -rh > \"$REPORT_DIR/video_files.txt\""
    eval "$video_cmd"
else
    # Without progress bar, using timer
    video_cmd="$find_cmd -print0 | xargs -0 du -h | sort -rh > \"$REPORT_DIR/video_files.txt\""
    run_with_timer "$video_cmd" "Processing video files" "$est_video_time"
fi

echo "Top 15 largest video files:" | tee -a "$REPORT_DIR/summary.txt"
head -15 "$REPORT_DIR/video_files.txt" | tee -a "$REPORT_DIR/summary.txt"

# Audio files
echo -e "\nAnalyzing audio files..." | tee -a "$REPORT_DIR/summary.txt"

# Estimate time for audio analysis
est_audio_time=$(estimate_duration $((total_files / 10)) $dir_size_kb "find")

audio_find_cmd="find \"$PROJECT_DIR\" -type f \( -name \"*.mp3\" -o -name \"*.wav\" -o -name \"*.aac\" -o -name \"*.ogg\" -o -name \"*.m4a\" \)"

if [ "$HAS_PV" = true ]; then
    # With progress bar
    audio_cmd="$audio_find_cmd -print0 | pv -0 -s \$($audio_find_cmd | wc -l) -N \"Processing audio\" | xargs -0 du -h | sort -rh > \"$REPORT_DIR/audio_files.txt\""
    eval "$audio_cmd"
else
    # Without progress bar, using timer
    audio_cmd="$audio_find_cmd -print0 | xargs -0 du -h | sort -rh > \"$REPORT_DIR/audio_files.txt\""
    run_with_timer "$audio_cmd" "Processing audio files" "$est_audio_time"
fi

echo "Top 10 largest audio files:" | tee -a "$REPORT_DIR/summary.txt"
head -10 "$REPORT_DIR/audio_files.txt" | tee -a "$REPORT_DIR/summary.txt"

# Project structure recommendations
section "PROJECT SPLITTING RECOMMENDATIONS"

# Calculate approximate sizes
total_bytes=$(du -b -s "$PROJECT_DIR" | cut -f1)
suggested_chunks=5
bytes_per_chunk=$((total_bytes / suggested_chunks))

echo "Project splitting recommendations:" | tee -a "$REPORT_DIR/summary.txt"
echo "- Total project size: $(numfmt --to=iec-i --suffix=B $total_bytes)" | tee -a "$REPORT_DIR/summary.txt"
echo "- Ideal chunk size for 5 parts: $(numfmt --to=iec-i --suffix=B $bytes_per_chunk)" | tee -a "$REPORT_DIR/summary.txt"
echo "" | tee -a "$REPORT_DIR/summary.txt"
echo "Based on file analysis, consider these splitting strategies:" | tee -a "$REPORT_DIR/summary.txt"
echo "1. Split by media type: separate video, audio, and project files" | tee -a "$REPORT_DIR/summary.txt"
echo "2. Split by directory structure: each major section in its own project" | tee -a "$REPORT_DIR/summary.txt"
echo "3. Split chronologically: divide timeline into logical segments" | tee -a "$REPORT_DIR/summary.txt"
echo "4. Create proxy files: use lower resolution copies for editing" | tee -a "$REPORT_DIR/summary.txt"

# Print largest directories that could be split
echo -e "\nLargest directories (potential split points):" | tee -a "$REPORT_DIR/summary.txt"
find "$PROJECT_DIR" -type d -print0 | 
  xargs -0 du -sh | sort -rh | head -10 | tee -a "$REPORT_DIR/summary.txt"

# Cleanup
rm "$temp_file"

# Final summary
echo -e "\n===== ANALYSIS SUMMARY ====="
echo "Analyzed: $(numfmt --to=iec-i --suffix=B $total_bytes) in approximately $total_files files"
echo "Analysis report saved to: $REPORT_DIR/summary.txt"
echo 
echo "Consider examining the following report files:"
echo "- $REPORT_DIR/largest_files.txt (All files by size)"
echo "- $REPORT_DIR/file_type_sizes.txt (Storage usage by file type)"
echo "- $REPORT_DIR/video_files.txt (All video files by size)"
echo "- $REPORT_DIR/audio_files.txt (All audio files by size)"
