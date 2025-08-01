"""
Impact Analysis Module

Analyzes the business, technical, and operational impact of PR changes
to help understand the significance and risk level of modifications.
"""

from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class ImpactScore:
    """Represents an impact score with breakdown."""
    overall_score: float
    business_impact: float
    technical_impact: float
    user_experience_impact: float
    risk_score: float


class ImpactAnalyzer:
    """Analyzes the impact of PR changes across multiple dimensions."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize with analysis configuration."""
        self.config = config
        self.analysis_settings = config.get('analysis_settings', {})
        self.impact_weights = self.analysis_settings.get('impact_weights', {})
        self.business_factors = self.analysis_settings.get('business_impact_factors', {})
        self.technical_factors = self.analysis_settings.get('technical_impact_factors', {})
        self.risk_factors = self.analysis_settings.get('risk_factors', {})
    
    def analyze_pr_impact(self, pr_analysis, classified_files, category_summary) -> Dict[str, Any]:
        """
        Analyze the overall impact of a PR.
        
        Returns:
            Dictionary containing comprehensive impact analysis
        """
        # Calculate individual impact scores
        business_impact = self._calculate_business_impact(classified_files, category_summary)
        technical_impact = self._calculate_technical_impact(pr_analysis, classified_files)
        ux_impact = self._calculate_ux_impact(classified_files, category_summary)
        risk_score = self._calculate_risk_score(pr_analysis, classified_files)
        
        # Calculate weighted overall score
        overall_score = (
            business_impact * self.impact_weights.get('business_value', 0.4) +
            technical_impact * self.impact_weights.get('technical_quality', 0.3) +
            ux_impact * self.impact_weights.get('user_experience', 0.2) +
            (10 - risk_score) * self.impact_weights.get('maintainability', 0.1)
        )
        
        # Determine risk level
        risk_level = self._determine_risk_level(risk_score)
        
        # Identify primary impacts
        primary_impacts = self._identify_primary_impacts(classified_files, category_summary)
        
        return {
            'overall_score': round(overall_score, 1),
            'business_impact': round(business_impact, 1),
            'technical_impact': round(technical_impact, 1), 
            'ux_impact': round(ux_impact, 1),
            'risk_score': round(risk_score, 1),
            'risk_level': risk_level,
            'primary_impacts': primary_impacts,
            'impact_breakdown': self._generate_impact_breakdown(
                business_impact, technical_impact, ux_impact, risk_score
            ),
            'recommendations': self._generate_impact_recommendations(
                overall_score, risk_score, primary_impacts
            )
        }
    
    def _calculate_business_impact(self, classified_files, category_summary) -> float:
        """Calculate business impact score (0-10)."""
        score = 0.0
        
        # Impact based on categories affected
        category_impacts = {
            'CORE_BUSINESS_LOGIC': 9,
            'API_INTEGRATION': 8,
            'DATABASE': 8,
            'USER_INTERFACE': 7,
            'BLOG_CONTENT': 6,
            'CONFIGURATION': 5,
            'ASSETS_MEDIA': 3
        }
        
        total_files = sum(info['count'] for info in category_summary.values())
        if total_files == 0:
            return 0
        
        for category, info in category_summary.items():
            category_weight = category_impacts.get(category, 2)
            category_proportion = info['count'] / total_files
            score += category_weight * category_proportion
        
        # Boost score for large-scale changes
        if total_files > 50:
            score += 1
        if total_files > 200:
            score += 1
        
        return min(score, 10.0)
    
    def _calculate_technical_impact(self, pr_analysis, classified_files) -> float:
        """Calculate technical impact score (0-10)."""
        score = 0.0
        
        # Lines of code impact
        total_lines = pr_analysis.total_lines_added + pr_analysis.total_lines_removed
        if total_lines > 1000:
            score += 3
        elif total_lines > 500:
            score += 2
        elif total_lines > 100:
            score += 1
        
        # Architecture impact based on categories
        architecture_categories = {
            'CORE_BUSINESS_LOGIC', 'DATABASE', 'API_INTEGRATION', 'CONFIGURATION'
        }
        
        architecture_files = len([f for f in classified_files 
                                if f.category in architecture_categories])
        if architecture_files > 0:
            score += min(architecture_files * 0.5, 4)
        
        # New vs modified files
        new_files = len([f for f in pr_analysis.file_changes if f.change_type == 'A'])
        if new_files > 10:
            score += 2
        elif new_files > 5:
            score += 1
        
        return min(score, 10.0)
    
    def _calculate_ux_impact(self, classified_files, category_summary) -> float:
        """Calculate user experience impact score (0-10)."""
        score = 0.0
        
        # UI/UX related categories
        ux_categories = {
            'USER_INTERFACE': 8,
            'ASSETS_MEDIA': 5,
            'BLOG_CONTENT': 6,
            'API_INTEGRATION': 4
        }
        
        total_files = sum(info['count'] for info in category_summary.values())
        if total_files == 0:
            return 0
        
        for category, info in category_summary.items():
            if category in ux_categories:
                impact_weight = ux_categories[category]
                proportion = info['count'] / total_files
                score += impact_weight * proportion
        
        return min(score, 10.0)
    
    def _calculate_risk_score(self, pr_analysis, classified_files) -> float:
        """Calculate risk score (0-10, higher = more risky)."""
        risk_score = 0.0
        
        # Large change risk
        total_lines = pr_analysis.total_lines_added + pr_analysis.total_lines_removed
        if total_lines > 10000:
            risk_score += 3
        elif total_lines > 5000:
            risk_score += 2
        elif total_lines > 1000:
            risk_score += 1
        
        # High-impact category changes
        risky_categories = {'CORE_BUSINESS_LOGIC', 'DATABASE', 'API_INTEGRATION'}
        risky_files = [f for f in classified_files if f.category in risky_categories]
        if len(risky_files) > 10:
            risk_score += 2
        elif len(risky_files) > 5:
            risk_score += 1
        
        # Many deleted files can be risky
        deleted_files = len([f for f in pr_analysis.file_changes if f.change_type == 'D'])
        if deleted_files > 20:
            risk_score += 2
        elif deleted_files > 10:
            risk_score += 1
        
        # Configuration changes can be risky
        config_files = [f for f in classified_files if f.category == 'CONFIGURATION']
        if len(config_files) > 5:
            risk_score += 1
        
        return min(risk_score, 10.0)
    
    def _determine_risk_level(self, risk_score: float) -> str:
        """Determine risk level from risk score."""
        if risk_score >= 7:
            return 'High'
        elif risk_score >= 4:
            return 'Medium'
        else:
            return 'Low'
    
    def _identify_primary_impacts(self, classified_files, category_summary) -> List[str]:
        """Identify the primary types of impact from this PR."""
        impacts = []
        
        # Check for major category impacts
        major_categories = {
            'CORE_BUSINESS_LOGIC': 'business_logic_changes',
            'DATABASE': 'database_changes', 
            'USER_INTERFACE': 'ui_changes',
            'API_INTEGRATION': 'api_changes',
            'BLOG_CONTENT': 'content_changes',
            'CONFIGURATION': 'configuration_changes',
            'ASSETS_MEDIA': 'asset_changes'
        }
        
        total_files = sum(info['count'] for info in category_summary.values())
        
        for category, info in category_summary.items():
            if category in major_categories and info['count'] / total_files > 0.2:
                impacts.append(major_categories[category])
        
        # Check for specific patterns
        if any(f.category == 'CORE_BUSINESS_LOGIC' for f in classified_files):
            impacts.append('business_model_changes')
        
        if len([f for f in classified_files if f.category == 'DATABASE']) > 0:
            impacts.append('data_architecture_changes')
        
        return impacts
    
    def _generate_impact_breakdown(self, business_impact: float, technical_impact: float,
                                 ux_impact: float, risk_score: float) -> Dict[str, Dict]:
        """Generate detailed breakdown of impact scores."""
        return {
            'business': {
                'score': business_impact,
                'level': self._score_to_level(business_impact),
                'description': 'Impact on business operations and value'
            },
            'technical': {
                'score': technical_impact,
                'level': self._score_to_level(technical_impact),
                'description': 'Technical complexity and architecture impact'
            },
            'user_experience': {
                'score': ux_impact,
                'level': self._score_to_level(ux_impact),
                'description': 'Impact on user interface and experience'
            },
            'risk': {
                'score': risk_score,
                'level': self._determine_risk_level(risk_score),
                'description': 'Potential risks and deployment concerns'
            }
        }
    
    def _score_to_level(self, score: float) -> str:
        """Convert numeric score to level description."""
        if score >= 8:
            return 'Very High'
        elif score >= 6:
            return 'High'
        elif score >= 4:
            return 'Medium'
        elif score >= 2:
            return 'Low'
        else:
            return 'Very Low'
    
    def _generate_impact_recommendations(self, overall_score: float, 
                                       risk_score: float, primary_impacts: List[str]) -> List[str]:
        """Generate recommendations based on impact analysis."""
        recommendations = []
        
        if overall_score >= 8:
            recommendations.append("⭐ High-impact changes - ensure stakeholder awareness")
        
        if risk_score >= 7:
            recommendations.append("🚨 High-risk PR - consider phased deployment")
            recommendations.append("🧪 Extensive testing recommended")
        elif risk_score >= 4:
            recommendations.append("⚠️ Medium risk - standard testing should be sufficient")
        
        if 'database_changes' in primary_impacts:
            recommendations.append("🗄️ Database migrations detected - verify rollback plan")
        
        if 'business_logic_changes' in primary_impacts:
            recommendations.append("🏛️ Business logic changes - ensure business validation")
        
        if 'api_changes' in primary_impacts:
            recommendations.append("🔗 API changes detected - check backward compatibility")
        
        return recommendations