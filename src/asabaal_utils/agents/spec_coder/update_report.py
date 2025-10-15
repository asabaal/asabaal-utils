#!/usr/bin/env python3
"""Update the markdown alignment report."""

import json
from pathlib import Path

# Load the alignment report
with open('../alignment/alignment_report.json', 'r') as f:
    report = json.load(f)

# Generate markdown report
md_content = """# Behavioral Alignment Report

## Summary

- **Total Tests**: {total_tests}
- **Specified Tests**: {specified_tests}
- **Additional Tests**: {additional_tests}
- **Direct Matches**: {direct_matches}
- **Partial Matches**: {partial_matches}
- **Alignment Rate**: {alignment_rate:.1%}

## Test Coverage by Requirement

""".format(**report['summary'])

# Add requirement coverage
for req_id, req_data in report['requirement_coverage'].items():
    md_content += f"""### {req_id}: {req_data['requirement_title']}

- **Coverage Score**: {req_data['coverage_score']:.1%}
- **Number of Tests**: {len(req_data['tests'])}

| Test Name | File | Confidence | Alignment Type | Implied Behavior |
|-----------|------|------------|----------------|------------------|
"""
    for test in req_data['tests']:
        behavior = test.get('implied_behavior', 'N/A')
        # Truncate long behaviors for table readability
        if len(behavior) > 100:
            behavior = behavior[:97] + "..."
        md_content += f"| {test['test_name']} | {test['test_file']} | {test['confidence']:.2f} | {test['alignment_type']} | {behavior} |\n"
    md_content += "\n"

# Add additional tests section if any
if report['additional_tests']:
    md_content += """## Additional Tests (Not in OpenSpec)

| Test Name | File | Test Type | Implied Behavior |
|-----------|------|-----------|------------------|
"""
    for test in report['additional_tests']:
        md_content += f"| {test['test_name']} | {test['test_file']} | {test['test_type']} | {test['implied_behavior']} |\n"

# Save markdown report
with open('../alignment/BEHAVIORAL_ALIGNMENT_REPORT.md', 'w') as f:
    f.write(md_content)

print('Markdown report updated successfully')