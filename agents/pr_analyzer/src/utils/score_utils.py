"""
Score calculation utilities for PR analyzer - provides centralized scoring logic
"""

from typing import Dict, Any, List


def calculate_overall_quality_score(file_assessments: List[Dict[str, Any]]) -> float:
    """
    Calculate overall quality score using the same logic as Stage 6.
    
    This matches the calculation in stage6_filtering_combination.py:
    overall_score = (
        business_impact_score * 0.4 +
        technical_quality_score * 0.3 +
        risk_score * 0.3
    )
    
    Args:
        file_assessments: List of file assessment dictionaries
        
    Returns:
        Overall quality score (0-10, rounded to 1 decimal place)
    """
    if not file_assessments:
        return 0.0
    
    total_score = 0.0
    valid_files = 0
    
    for assessment in file_assessments:
        # Get individual scores
        business_impact = assessment.get('business_impact_score', 0)
        technical_risk = assessment.get('technical_risk_score', 0)
        
        # Convert technical risk to technical quality (inverse relationship)
        # Lower risk = higher quality
        technical_quality = max(0, 10 - technical_risk)
        
        # Calculate risk score (inverse of technical risk, same as technical quality)
        risk_score = technical_quality
        
        # Calculate overall score using Stage 6 formula
        overall_score = (
            business_impact * 0.4 +
            technical_quality * 0.3 +
            risk_score * 0.3
        )
        
        total_score += overall_score
        valid_files += 1
    
    # Return average score rounded to 1 decimal place
    return round(total_score / valid_files, 1) if valid_files > 0 else 0.0


def calculate_confidence_score(ready_files: int, total_files: int) -> float:
    """
    Calculate confidence score based on merge readiness distribution.
    
    Args:
        ready_files: Number of files marked as ready
        total_files: Total number of files
        
    Returns:
        Confidence score (0-1)
    """
    if total_files == 0:
        return 0.0
    
    return round(ready_files / total_files, 6)


def recalculate_assessment_summary(assessment_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recalculate all assessment summary metrics based on current file assessments.
    
    Args:
        assessment_data: Dictionary containing 'assessment_summary' and 'file_assessments'
        
    Returns:
        Updated assessment summary dictionary
    """
    file_assessments = assessment_data.get('file_assessments', [])
    
    # Count files by status
    ready_count = sum(1 for f in file_assessments if f.get('merge_readiness') == 'ready')
    conditional_count = sum(1 for f in file_assessments if f.get('merge_readiness') == 'conditional')
    not_ready_count = sum(1 for f in file_assessments if f.get('merge_readiness') == 'not_ready')
    total_count = len(file_assessments)
    
    # Calculate scores
    overall_quality_score = calculate_overall_quality_score(file_assessments)
    confidence_score = calculate_confidence_score(ready_count, total_count)
    
    # Update summary
    summary = assessment_data.get('assessment_summary', {})
    summary.update({
        'total_files': total_count,
        'ready_files': ready_count,
        'conditional_files': conditional_count,
        'not_ready_files': not_ready_count,
        'overall_confidence': confidence_score,
        'overall_quality_score': overall_quality_score,
        'assessment_timestamp': assessment_data.get('assessment_summary', {}).get('assessment_timestamp', '2025-01-04T00:00:00Z')
    })
    
    return summary