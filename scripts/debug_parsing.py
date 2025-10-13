#!/usr/bin/env python3

import sys
import re
sys.path.insert(0, 'src')

# Test the parsing logic directly
with open('test_projects/pr_analysis_output/detailed_analysis_summary.txt', 'r') as f:
    content = f.read()

print("=== DEBUG: Parsing detailed analysis ===")
print("Content length:", len(content))
print("\n=== Looking for NOT READY FILES section ===")

lines = content.split('\n')
in_not_ready_section = False
issues_found = []

for i, line in enumerate(lines):
    line = line.strip()
    
    if 'NOT READY FILES' in line:
        in_not_ready_section = True
        print(f"Found NOT READY section at line {i}")
        continue
    elif line.endswith('FILES:') and 'NOT READY' not in line:
        in_not_ready_section = False
        print(f"Leaving NOT READY section at line {i}")
        continue
    
    if in_not_ready_section:
            print(f"Line in not-ready section: '{line}'")
            if line.startswith('- ') and '.py:' in line:
                current_file = line.split(':')[0][2:]  # Remove "- " prefix
                print(f"Found not-ready file: {current_file}")
        
        # Look ahead for issue description
        issue_desc = ""
        for j in range(i + 1, min(i + 10, len(lines))):
            next_line = lines[j].strip()
            if next_line.startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.')):
                issue_desc += next_line.split('.', 1)[1].strip() + " "
            elif next_line.startswith('-') or next_line.endswith('.py:') or not next_line:
                break
        
        if issue_desc:
            priority = 'critical' if any(keyword in issue_desc.lower() for keyword in ['critical', 'security', 'vulnerabilit', 'injection', 'plaintext']) else 'high'
            issues_found.append({
                'file': current_file,
                'description': issue_desc.strip(),
                'priority': priority
            })
            print(f"  -> Issue: {issue_desc[:100]}...")
            print(f"  -> Priority: {priority}")

print(f"\n=== Total issues found: {len(issues_found)} ===")
for issue in issues_found:
    print(f"- {issue['file']}: {issue['priority']}")