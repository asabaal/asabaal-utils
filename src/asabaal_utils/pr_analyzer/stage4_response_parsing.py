#!/usr/bin/env python3
"""
Stage 4: Response Parsing Testing
Parse agent responses into structured QualityIssue objects with full debugging visibility
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

# Add the parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))


class IssueType(Enum):
    """Quality issue types"""
    DUPLICATE = "duplicate"
    MERGE_BLOCKER = "merge_blocker"
    MERGE_WARNING = "merge_warning"
    PATTERN_ISSUE = "pattern_issue"
    ORGANIZATION = "organization"
    CODE_QUALITY = "code_quality"


class Priority(Enum):
    """Issue priority levels"""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


@dataclass
class QualityIssue:
    """Structured quality issue from agent analysis"""
    id: str
    type: IssueType
    priority: Priority
    title: str
    description: str
    files_affected: List[str]
    recommendation: str
    source_agent: str
    raw_text: str
    confidence: float  # 0.0 to 1.0


class ResponseParser:
    """Parse agent responses into structured quality issues"""
    
    def __init__(self, output_dir: str = None):
        if output_dir:
            self.test_output_dir = Path(output_dir) / "debug_outputs" / "stage4"
            self.stage3_dir = Path(output_dir) / "debug_outputs" / "stage3"
        else:
            self.test_output_dir = Path(__file__).parent / "debug_outputs" / "stage4"
            self.stage3_dir = Path(__file__).parent / "debug_outputs" / "stage3"
        self.test_output_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"🔧 Response Parser initialized:")
        print(f"   Loading responses from: {self.stage3_dir}")
        print(f"   Debug outputs to: {self.test_output_dir}")
    
    def load_stage3_responses(self) -> Dict[str, str]:
        """Load successful agent responses from Stage 3"""
        print("\n📂 Loading Stage 3 responses...")
        
        responses = {}
        
        # Load each agent response
        for agent_name in ['duplicate_detection', 'merge_readiness', 'pattern_analysis']:
            response_file = self.stage3_dir / f"{agent_name}_full_response.txt"
            
            if response_file.exists():
                with open(response_file, 'r') as f:
                    content = f.read().strip()
                    
                if content:
                    responses[agent_name] = content
                    print(f"   ✅ {agent_name}: {len(content):,} chars")
                else:
                    print(f"   ❌ {agent_name}: empty response")
            else:
                print(f"   ❌ {agent_name}: no response file")
        
        # Save loaded responses summary
        summary = {
            'loaded_agents': list(responses.keys()),
            'response_lengths': {name: len(content) for name, content in responses.items()},
            'total_content': sum(len(content) for content in responses.values())
        }
        
        with open(self.test_output_dir / "loaded_responses_summary.json", 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"   Total content loaded: {summary['total_content']:,} chars")
        return responses
    
    def parse_duplicate_detection_response(self, response_text: str) -> List[QualityIssue]:
        """Parse duplicate detection agent response into structured issues"""
        print("\n🔍 Parsing duplicate detection response...")
        
        issues = []
        
        # Split into sections by priority level
        sections = {
            'CRITICAL': r'## CRITICAL[:\s]*(.*?)(?=## HIGH|## MEDIUM|## Summary|$)',
            'HIGH': r'## HIGH[:\s]*(.*?)(?=## MEDIUM|## LOW|## Summary|$)',
            'MEDIUM': r'## MEDIUM[:\s]*(.*?)(?=## LOW|## Summary|$)'
        }
        
        for priority_name, pattern in sections.items():
            matches = re.findall(pattern, response_text, re.DOTALL | re.IGNORECASE)
            
            if matches:
                section_text = matches[0]
                
                # Extract file groups within this priority
                file_groups = self._extract_duplicate_file_groups(section_text)
                
                for group_idx, file_group in enumerate(file_groups):
                    issue_id = f"dup_{priority_name.lower()}_{group_idx + 1}"
                    
                    issue = QualityIssue(
                        id=issue_id,
                        type=IssueType.DUPLICATE,
                        priority=Priority[priority_name],
                        title=file_group['title'],
                        description=file_group['description'],
                        files_affected=file_group['files'],
                        recommendation=file_group['recommendation'],
                        source_agent="duplicate_detection",
                        raw_text=file_group['raw_text'],
                        confidence=file_group['confidence']
                    )
                    
                    issues.append(issue)
        
        print(f"   Extracted {len(issues)} duplicate issues")
        return issues
    
    def _extract_duplicate_file_groups(self, section_text: str) -> List[Dict[str, Any]]:
        """Extract duplicate file groups from a section"""
        groups = []
        
        # Look for subsection headers (### patterns)
        subsections = re.split(r'\n### \*\*(.*?)\*\*', section_text)
        
        for i in range(1, len(subsections), 2):  # Skip first empty part, then take pairs
            if i + 1 < len(subsections):
                title = subsections[i].strip()
                content = subsections[i + 1].strip()
                
                # Extract files from bullet points
                files = []
                file_matches = re.findall(r'[-*]\s*`([^`]+)`', content)
                files.extend(file_matches)
                
                # Also look for file paths without backticks
                path_matches = re.findall(r'[-*]\s*([A-Za-z0-9_/.-]+\.[a-z]+)', content)
                files.extend([f for f in path_matches if f not in files])
                
                # Extract recommendation
                rec_match = re.search(r'\*\*Recommendation\*\*[:\s]*(.*?)(?=\n\n|\n###|$)', content, re.DOTALL)
                recommendation = rec_match.group(1).strip() if rec_match else "Consolidate or remove duplicates"
                
                # Extract description/evidence
                evidence_match = re.search(r'\*\*Evidence\*\*[:\s]*(.*?)(?=\*\*Recommendation\*\*|\n\n|\n###|$)', content, re.DOTALL)
                description = evidence_match.group(1).strip() if evidence_match else content[:200]
                
                # Calculate confidence based on detail level
                confidence = min(1.0, len(files) * 0.2 + (len(description) / 500))
                
                if files and title:
                    groups.append({
                        'title': title,
                        'description': description,
                        'files': files,
                        'recommendation': recommendation,
                        'raw_text': content,
                        'confidence': confidence
                    })
        
        return groups
    
    def parse_merge_readiness_response(self, response_text: str) -> List[QualityIssue]:
        """Parse merge readiness agent response into structured issues"""
        print("\n🔍 Parsing merge readiness response...")
        
        issues = []
        
        # Extract JSON from response
        json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
        if not json_match:
            # Try finding JSON without code blocks
            json_match = re.search(r'\{[^}]*"merge_readiness_score"[^}]*\}', response_text, re.DOTALL)
        
        if json_match:
            try:
                merge_data = json.loads(json_match.group(1) if json_match.group(1).startswith('{') else json_match.group(0))
                
                # Create issue for merge readiness score
                score = merge_data.get('merge_readiness_score', 0)
                status = merge_data.get('status', 'UNKNOWN')
                
                if score < 90 or status != 'READY':
                    issue_type = IssueType.MERGE_BLOCKER if score < 70 else IssueType.MERGE_WARNING
                    priority = Priority.CRITICAL if score < 70 else Priority.HIGH
                    
                    merge_issue = QualityIssue(
                        id="merge_readiness_main",
                        type=issue_type,
                        priority=priority,
                        title=f"Merge Readiness: {status} (Score: {score}/100)",
                        description=merge_data.get('recommendation', 'PR requires attention before merge'),
                        files_affected=[],
                        recommendation=merge_data.get('recommendation', 'Address concerns before merging'),
                        source_agent="merge_readiness",
                        raw_text=json_match.group(0),
                        confidence=0.9
                    )
                    
                    issues.append(merge_issue)
                
                # Create issues for key concerns
                concerns = merge_data.get('key_concerns', [])
                for idx, concern in enumerate(concerns):
                    concern_issue = QualityIssue(
                        id=f"merge_concern_{idx + 1}",
                        type=IssueType.MERGE_WARNING,
                        priority=Priority.MEDIUM,
                        title=f"Merge Concern: {concern}",
                        description=f"Identified concern from merge readiness analysis: {concern}",
                        files_affected=[],
                        recommendation="Review and address this concern",
                        source_agent="merge_readiness",
                        raw_text=concern,
                        confidence=0.7
                    )
                    
                    issues.append(concern_issue)
            
            except json.JSONDecodeError as e:
                print(f"   ❌ Failed to parse JSON from merge readiness response: {e}")
                
                # Create fallback issue
                fallback_issue = QualityIssue(
                    id="merge_parse_error",
                    type=IssueType.CODE_QUALITY,
                    priority=Priority.MEDIUM,
                    title="Merge Readiness Analysis Available",
                    description="Could not parse structured data, but analysis is available",
                    files_affected=[],
                    recommendation="Manual review of merge readiness response needed",
                    source_agent="merge_readiness",
                    raw_text=response_text[:500],
                    confidence=0.3
                )
                
                issues.append(fallback_issue)
        
        print(f"   Extracted {len(issues)} merge readiness issues")
        return issues
    
    def parse_pattern_analysis_response(self, response_text: str) -> List[QualityIssue]:
        """Parse pattern analysis agent response into structured issues"""
        print("\n🔍 Parsing pattern analysis response...")
        
        issues = []
        
        # Look for priority sections
        priority_sections = {
            'High Priority': Priority.HIGH,
            'Medium Priority': Priority.MEDIUM,
            'Low Priority': Priority.LOW
        }
        
        for section_name, priority in priority_sections.items():
            pattern = rf'\*\*{section_name}:\*\*\s*(.*?)(?=\*\*\w+\s+Priority:|\*\*\w+\s+Priority|\n\n[A-Z]|$)'
            matches = re.findall(pattern, response_text, re.DOTALL | re.IGNORECASE)
            
            if matches:
                section_content = matches[0].strip()
                
                # Extract individual items from bullet points
                items = re.findall(r'[-*]\s*([^\n]+)', section_content)
                
                for idx, item in enumerate(items):
                    issue_id = f"pattern_{priority.value.lower()}_{idx + 1}"
                    
                    # Clean up the item text
                    item = item.strip()
                    
                    issue = QualityIssue(
                        id=issue_id,
                        type=IssueType.PATTERN_ISSUE,
                        priority=priority,
                        title=f"Pattern Issue: {item[:50]}...",
                        description=item,
                        files_affected=[],  # Pattern issues are usually cross-cutting
                        recommendation="Establish and follow consistent patterns",
                        source_agent="pattern_analysis",
                        raw_text=item,
                        confidence=0.6
                    )
                    
                    issues.append(issue)
        
        print(f"   Extracted {len(issues)} pattern issues")
        return issues
    
    def test_individual_parsers(self, responses: Dict[str, str]) -> Dict[str, List[QualityIssue]]:
        """Test each parser individually with full debugging"""
        print("\n🧪 Testing individual parsers...")
        
        parser_results = {}
        
        # Test duplicate detection parser
        if 'duplicate_detection' in responses:
            print("\n   Testing duplicate detection parser:")
            try:
                dup_issues = self.parse_duplicate_detection_response(responses['duplicate_detection'])
                parser_results['duplicate_detection'] = dup_issues
                
                # Save detailed debug info
                debug_info = {
                    'input_length': len(responses['duplicate_detection']),
                    'issues_extracted': len(dup_issues),
                    'issues_by_priority': {},
                    'sample_issues': []
                }
                
                for issue in dup_issues:
                    priority = issue.priority.value
                    debug_info['issues_by_priority'][priority] = debug_info['issues_by_priority'].get(priority, 0) + 1
                    
                    if len(debug_info['sample_issues']) < 3:
                        debug_info['sample_issues'].append({
                            'id': issue.id,
                            'title': issue.title,
                            'files_count': len(issue.files_affected),
                            'confidence': issue.confidence
                        })
                
                with open(self.test_output_dir / "duplicate_parser_debug.json", 'w') as f:
                    json.dump(debug_info, f, indent=2)
                
                print(f"      ✅ Extracted {len(dup_issues)} duplicate issues")
                
            except Exception as e:
                print(f"      ❌ Duplicate parser failed: {e}")
                parser_results['duplicate_detection'] = []
        
        # Test merge readiness parser
        if 'merge_readiness' in responses:
            print("\n   Testing merge readiness parser:")
            try:
                merge_issues = self.parse_merge_readiness_response(responses['merge_readiness'])
                parser_results['merge_readiness'] = merge_issues
                
                # Save debug info
                debug_info = {
                    'input_length': len(responses['merge_readiness']),
                    'issues_extracted': len(merge_issues),
                    'json_found': 'merge_readiness_score' in responses['merge_readiness'],
                    'sample_issues': [
                        {
                            'id': issue.id,
                            'type': issue.type.value,
                            'title': issue.title
                        }
                        for issue in merge_issues[:3]
                    ]
                }
                
                with open(self.test_output_dir / "merge_parser_debug.json", 'w') as f:
                    json.dump(debug_info, f, indent=2)
                
                print(f"      ✅ Extracted {len(merge_issues)} merge issues")
                
            except Exception as e:
                print(f"      ❌ Merge parser failed: {e}")
                parser_results['merge_readiness'] = []
        
        # Test pattern analysis parser
        if 'pattern_analysis' in responses:
            print("\n   Testing pattern analysis parser:")
            try:
                pattern_issues = self.parse_pattern_analysis_response(responses['pattern_analysis'])
                parser_results['pattern_analysis'] = pattern_issues
                
                # Save debug info
                debug_info = {
                    'input_length': len(responses['pattern_analysis']),
                    'issues_extracted': len(pattern_issues),
                    'priority_sections_found': len(re.findall(r'\*\*\w+\s+Priority:', responses['pattern_analysis'])),
                    'sample_issues': [
                        {
                            'id': issue.id,
                            'priority': issue.priority.value,
                            'title': issue.title
                        }
                        for issue in pattern_issues[:3]
                    ]
                }
                
                with open(self.test_output_dir / "pattern_parser_debug.json", 'w') as f:
                    json.dump(debug_info, f, indent=2)
                
                print(f"      ✅ Extracted {len(pattern_issues)} pattern issues")
                
            except Exception as e:
                print(f"      ❌ Pattern parser failed: {e}")
                parser_results['pattern_analysis'] = []
        
        return parser_results
    
    def consolidate_all_issues(self, parser_results: Dict[str, List[QualityIssue]]) -> List[QualityIssue]:
        """Consolidate all issues from all parsers"""
        print("\n🔗 Consolidating all issues...")
        
        all_issues = []
        
        for agent_name, issues in parser_results.items():
            all_issues.extend(issues)
            print(f"   {agent_name}: {len(issues)} issues")
        
        # Sort by priority and confidence
        priority_order = {Priority.CRITICAL: 0, Priority.HIGH: 1, Priority.MEDIUM: 2, Priority.LOW: 3}
        
        all_issues.sort(key=lambda x: (priority_order[x.priority], -x.confidence))
        
        print(f"   Total consolidated: {len(all_issues)} issues")
        return all_issues
    
    def analyze_parsing_results(self, all_issues: List[QualityIssue]) -> Dict[str, Any]:
        """Analyze the parsing results"""
        print("\n📊 Analyzing parsing results...")
        
        analysis = {
            'total_issues': len(all_issues),
            'issues_by_type': {},
            'issues_by_priority': {},
            'issues_by_agent': {},
            'average_confidence': 0,
            'files_affected': set(),
            'recommendations': [],
            'parsing_success': True
        }
        
        total_confidence = 0
        
        for issue in all_issues:
            # Count by type
            issue_type = issue.type.value
            analysis['issues_by_type'][issue_type] = analysis['issues_by_type'].get(issue_type, 0) + 1
            
            # Count by priority
            priority = issue.priority.value
            analysis['issues_by_priority'][priority] = analysis['issues_by_priority'].get(priority, 0) + 1
            
            # Count by agent
            agent = issue.source_agent
            analysis['issues_by_agent'][agent] = analysis['issues_by_agent'].get(agent, 0) + 1
            
            # Track confidence
            total_confidence += issue.confidence
            
            # Track affected files
            analysis['files_affected'].update(issue.files_affected)
        
        # Calculate averages
        if all_issues:
            analysis['average_confidence'] = total_confidence / len(all_issues)
        
        analysis['files_affected'] = list(analysis['files_affected'])
        analysis['unique_files_affected'] = len(analysis['files_affected'])
        
        # Generate recommendations
        if analysis['total_issues'] == 0:
            analysis['recommendations'].append("❌ No issues extracted - check parser implementations")
            analysis['parsing_success'] = False
        else:
            analysis['recommendations'].append(f"✅ Successfully parsed {analysis['total_issues']} issues")
            
            if analysis['average_confidence'] > 0.7:
                analysis['recommendations'].append("✅ High confidence in parsed results")
            else:
                analysis['recommendations'].append("⚠️ Medium confidence - review parsing accuracy")
        
        # Display results
        print(f"   Total issues: {analysis['total_issues']}")
        print(f"   Average confidence: {analysis['average_confidence']:.2f}")
        print(f"   Unique files affected: {analysis['unique_files_affected']}")
        
        if analysis['issues_by_priority']:
            print(f"   Issues by priority:")
            for priority, count in analysis['issues_by_priority'].items():
                print(f"     • {priority}: {count}")
        
        if analysis['issues_by_type']:
            print(f"   Issues by type:")
            for issue_type, count in analysis['issues_by_type'].items():
                print(f"     • {issue_type}: {count}")
        
        print(f"   Recommendations:")
        for rec in analysis['recommendations']:
            print(f"     • {rec}")
        
        return analysis
    
    def save_consolidated_results(self, all_issues: List[QualityIssue], analysis: Dict[str, Any]):
        """Save all consolidated results"""
        print("\n💾 Saving consolidated results...")
        
        # Save all issues as JSON
        issues_data = []
        for issue in all_issues:
            issue_dict = asdict(issue)
            # Convert enums to strings
            issue_dict['type'] = issue.type.value
            issue_dict['priority'] = issue.priority.value
            issues_data.append(issue_dict)
        
        with open(self.test_output_dir / "all_issues.json", 'w') as f:
            json.dump(issues_data, f, indent=2)
        
        # Save analysis results
        # Convert set to list for JSON serialization
        analysis_copy = analysis.copy()
        if isinstance(analysis_copy.get('files_affected'), set):
            analysis_copy['files_affected'] = list(analysis_copy['files_affected'])
        
        with open(self.test_output_dir / "parsing_analysis.json", 'w') as f:
            json.dump(analysis_copy, f, indent=2)
        
        # Save human-readable summary
        summary_lines = [
            "STAGE 4: RESPONSE PARSING RESULTS",
            "=" * 40,
            f"Total Issues Extracted: {len(all_issues)}",
            f"Average Confidence: {analysis['average_confidence']:.2f}",
            f"Files Affected: {analysis['unique_files_affected']}",
            "",
            "ISSUES BY PRIORITY:",
        ]
        
        for priority in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
            count = analysis['issues_by_priority'].get(priority, 0)
            if count > 0:
                summary_lines.append(f"  {priority}: {count}")
        
        summary_lines.extend([
            "",
            "ISSUES BY TYPE:",
        ])
        
        for issue_type, count in analysis['issues_by_type'].items():
            summary_lines.append(f"  {issue_type}: {count}")
        
        summary_lines.extend([
            "",
            "SAMPLE ISSUES:",
        ])
        
        for i, issue in enumerate(all_issues[:5]):
            summary_lines.append(f"  {i+1}. [{issue.priority.value}] {issue.title}")
        
        with open(self.test_output_dir / "parsing_summary.txt", 'w') as f:
            f.write('\n'.join(summary_lines))
        
        print(f"   Saved {len(all_issues)} issues to: {self.test_output_dir}/all_issues.json")
        print(f"   Analysis saved to: {self.test_output_dir}/parsing_analysis.json")
        print(f"   Summary saved to: {self.test_output_dir}/parsing_summary.txt")
    
    def run_full_stage4_test(self) -> Dict[str, Any]:
        """Run complete Stage 4 testing pipeline"""
        print("=" * 60)
        print("🧪 STAGE 4: RESPONSE PARSING TESTING")
        print("=" * 60)
        
        # Step 1: Load Stage 3 responses
        responses = self.load_stage3_responses()
        
        if not responses:
            print("❌ No responses available from Stage 3")
            return {
                'stage': 'Response Parsing',
                'success': False,
                'error': 'No Stage 3 responses available',
                'ready_for_stage5': False
            }
        
        # Step 2: Test individual parsers
        parser_results = self.test_individual_parsers(responses)
        
        # Step 3: Consolidate all issues
        all_issues = self.consolidate_all_issues(parser_results)
        
        # Step 4: Analyze results
        analysis = self.analyze_parsing_results(all_issues)
        
        # Step 5: Save results
        self.save_consolidated_results(all_issues, analysis)
        
        # Create stage summary
        stage4_summary = {
            'stage': 'Response Parsing',
            'success': analysis['parsing_success'],
            'total_issues_extracted': len(all_issues),
            'parser_results': {
                agent: len(issues) for agent, issues in parser_results.items()
            },
            'analysis': analysis,
            'ready_for_stage5': analysis['parsing_success'] and len(all_issues) > 0
        }
        
        with open(self.test_output_dir / "stage4_test_summary.json", 'w') as f:
            json.dump(stage4_summary, f, indent=2)
        
        print(f"\n✅ STAGE 4 COMPLETE:")
        print(f"   Parsing successful: {analysis['parsing_success']}")
        print(f"   Issues extracted: {len(all_issues)}")
        print(f"   Average confidence: {analysis['average_confidence']:.2f}")
        print(f"   Debug outputs saved to: {self.test_output_dir}")
        
        return stage4_summary


def main():
    """Test Stage 4: Response Parsing"""
    try:
        parser = ResponseParser()
        results = parser.run_full_stage4_test()
        
        if results['ready_for_stage5']:
            print(f"\n🎉 Stage 4 successful!")
            print(f"Ready to proceed to Stage 5: Issue Extraction")
            print(f"Extracted {results['total_issues_extracted']} quality issues for validation")
        else:
            print(f"\n❌ Stage 4 failed - response parsing not working")
            print(f"Check parser implementations and Stage 3 outputs")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Stage 4 testing failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()