# PR Analyzer - Actual Agent Flow Diagram

## 🎯 **WHAT THE CODE ACTUALLY DOES WITH AGENTS**

```
┌─────────────────────────────────────────────────────────────────┐
│                      USER RUNS COMMAND                         │
│  pr-analyzer --repo X --from A --to B --output report.html     │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│             MAIN ANALYZER ORCHESTRATION                         │
│  analyze_pr() method calls quality_analyzer.analyze_pr_quality │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                 AGENTIC QUALITY ANALYZER                        │
│  AgenticQualityAnalyzer.analyze_pr_quality()                   │
│                                                                 │  
│  1. Prepares analysis context with file info                   │
│  2. Launches 3 separate AI agents:                             │
│     ├─ _launch_duplicate_detection_agent()                     │
│     ├─ _launch_merge_readiness_agent()                         │
│     └─ _launch_pattern_analysis_agent()                        │
│                                                                 │
│  3. Combines results from all agents                           │
│  4. Filters issues with user exceptions                        │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│              DUPLICATE DETECTION AGENT                          │
│  _launch_duplicate_detection_agent()                           │
│                                                                 │
│  STEP 1: _prepare_files_for_content_analysis()                 │
│  ├─ Reads actual file contents (up to 100KB each)             │
│  ├─ Extracts: File Purpose, Functions, Main Workflow, Imports │
│  └─ Builds structured analysis for AI agent                   │
│                                                                 │
│  STEP 2: Creates detailed AI prompt                           │
│  ├─ "You are a senior software architect..."                  │
│  ├─ "Find files that serve similar/identical purposes..."     │
│  └─ "Focus on DISCOVERING actual content-based duplicates"    │
│                                                                 │
│  STEP 3: _call_claude_agent(agent_prompt)                     │
│  ├─ subprocess.run(['claude', '-p', clean_prompt])            │
│  ├─ timeout=120 seconds                                       │
│  └─ Returns Claude's analysis as text                         │
│                                                                 │
│  STEP 4: _parse_agent_content_analysis()                      │
│  ├─ Tries to extract structured issues from Claude response   │
│  ├─ Looks for severity indicators, file lists, recommendations│
│  └─ Creates QualityIssue objects                              │
│                                                                 │
│  FALLBACK: If Claude call fails → _enhanced_content_analysis() │
│  ├─ Basic pattern matching and heuristics                     │
│  └─ Generic issue generation                                   │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│               MERGE READINESS AGENT                             │
│  _launch_merge_readiness_agent()                               │
│                                                                 │
│  STEP 1: Creates JSON-formatted prompt                        │
│  ├─ "You are a senior engineering manager..."                 │
│  ├─ Provides PR overview and file categories                  │
│  └─ Requests structured JSON response                         │
│                                                                 │
│  STEP 2: _call_claude_agent(agent_prompt)                     │
│  ├─ Same subprocess call to claude CLI                        │
│  └─ Expects JSON response with merge readiness score          │
│                                                                 │
│  STEP 3: _parse_merge_readiness_response()                    │
│  ├─ Extracts JSON from response using regex                   │
│  ├─ Parses merge_readiness_score, status, issues             │
│  └─ Falls back to text parsing if JSON fails                  │
│                                                                 │
│  FALLBACK: _fallback_merge_readiness_analysis()               │
│  ├─ Basic scoring based on PR size                           │
│  └─ Generic recommendations                                    │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                PATTERN ANALYSIS AGENT                           │
│  _launch_pattern_analysis_agent()                              │
│                                                                 │
│  Currently just calls: _fallback_pattern_analysis()            │
│  └─ Returns empty issues list                                  │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                    RESULTS COMBINATION                          │
│                                                                 │
│  1. Combines all issues from 3 agents                         │
│  2. Runs filter_suppressed_issues() to remove exceptions      │
│  3. Calculates overall metrics:                               │
│     ├─ merge_readiness score                                  │
│     ├─ quality_score                                          │
│     └─ issue_summary                                          │
│                                                                 │
│  4. Returns complete quality analysis to main analyzer        │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                    HTML GENERATION                              │
│                                                                 │
│  HTMLGenerator.generate_report_html(report_data)               │
│  ├─ Creates dark-themed HTML with all analysis results        │
│  ├─ Includes quality issues in structured format              │
│  └─ Saves to specified output file                            │
└─────────────────────────────────────────────────────────────────┘
```

## 🔍 **KEY AGENT INTERACTIONS**

1. **Claude CLI Calls**: `subprocess.run(['claude', '-p', prompt], timeout=120)`
2. **Content Reading**: Actually reads file contents up to 100KB per file  
3. **Prompt Engineering**: Sends detailed prompts asking for duplicate detection
4. **Response Parsing**: Tries to extract structured analysis from Claude's text
5. **Fallback Logic**: Uses basic analysis if Claude calls fail

## ❓ **THE MYSTERY**

The agents ARE being called and ARE returning responses that get parsed into the 12 quality issues you see. But those issues are generic fluff instead of the intelligent content analysis the prompts are asking for.

**Question**: Is Claude CLI returning useless responses, or is the response parsing broken?