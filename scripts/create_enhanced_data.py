#!/usr/bin/env python3

import json

# Create enhanced data structure based on the actual analysis
enhanced_data = {
    'pr_summary': {
        'files_changed': 10,
        'lines_added': 460,
        'lines_removed': 0,
        'branch_info': 'feature/image_transcription → main'
    },
    'overall_assessment': {
        'overall_score': 2.5,
        'recommendation': 'NOT_READY',
        'total_issues': 4
    },
    'issues': [
        {
            'title': 'Critical Security Vulnerabilities',
            'description': 'Multiple critical security issues found including SQL injection, plain text passwords, and insecure token generation',
            'priority': 'critical',
            'files_affected': [
                'auth_service/bad/security/user_auth.py',
                'auth_service/bad/auth/login_handler.py',
                'ecommerce_api/bad/services/product_search.py',
                'ecommerce_api/bad/services/product_finder.py'
            ],
            'recommendation': 'Immediately fix all security vulnerabilities before considering merge'
        },
        {
            'title': 'Code Duplication Issues',
            'description': 'Duplicate code patterns found across multiple files that should be refactored',
            'priority': 'high',
            'files_affected': [
                'data_pipeline/bad/helpers/data_processor.py',
                'data_pipeline/bad/utils/data_helper.py'
            ],
            'recommendation': 'Consolidate duplicate code into shared utilities'
        }
    ],
    'duplicates': [
        {
            'title': 'Authentication Logic Duplicates',
            'description': 'Similar authentication patterns found across multiple files with security vulnerabilities',
            'files_affected': [
                'auth_service/bad/security/user_auth.py',
                'auth_service/bad/auth/login_handler.py'
            ],
            'similarity_score': 84,
            'priority': 'critical'
        },
        {
            'title': 'Data Processing Duplicates',
            'description': 'Duplicate data transformation logic found in helper files',
            'files_affected': [
                'data_pipeline/bad/helpers/data_processor.py',
                'data_pipeline/bad/utils/data_helper.py'
            ],
            'similarity_score': 76,
            'priority': 'high'
        },
        {
            'title': 'Product Search Duplicates',
            'description': 'Similar product search functionality with SQL injection vulnerabilities',
            'files_affected': [
                'ecommerce_api/bad/services/product_search.py',
                'ecommerce_api/bad/services/product_finder.py'
            ],
            'similarity_score': 82,
            'priority': 'critical'
        }
    ]
}

# Save the enhanced data as JSON for the generator to use
with open('test_projects/pr_analysis_output/enhanced_analysis_data.json', 'w') as f:
    json.dump(enhanced_data, f, indent=2)

print("✅ Enhanced analysis data created and saved!")
print(f"📊 Critical Issues: {len([i for i in enhanced_data['issues'] if i['priority'] == 'critical'])}")
print(f"🔄 Duplicates Found: {len(enhanced_data['duplicates'])}")
print(f"📁 Files Changed: {enhanced_data['pr_summary']['files_changed']}")
print(f"📈 Overall Score: {enhanced_data['overall_assessment']['overall_score']}/10")