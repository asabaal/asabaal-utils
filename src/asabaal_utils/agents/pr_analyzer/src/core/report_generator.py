"""
Report Generation Module

Orchestrates the analysis process and generates comprehensive HTML reports
with visualizations and detailed breakdowns of PR changes.
"""

import json
import yaml
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

# Legacy imports - these modules are not available in the current architecture
# TODO: Either implement these modules or remove this legacy code
try:
    from analyzers.impact_analyzer import ImpactAnalyzer
    from visualizers.html_generator import HTMLGenerator
    LEGACY_COMPONENTS_AVAILABLE = True
except ImportError:
    ImpactAnalyzer = None
    HTMLGenerator = None
    LEGACY_COMPONENTS_AVAILABLE = False


class ReportGenerator:
    """Generates comprehensive PR analysis reports."""
    
    def __init__(self, config_path: str = None):
        """Initialize report generator with configuration."""
        if config_path is None:
            try:
                from utils.path_utils import get_config_path
                config_path = get_config_path("analysis_config.yaml")
            except ImportError:
                config_path = "analysis_config.yaml"  # fallback
        
        self.config = self._load_config(config_path)
        
        if LEGACY_COMPONENTS_AVAILABLE:
            self.impact_analyzer = ImpactAnalyzer(self.config)
            self.html_generator = HTMLGenerator()
        else:
            self.impact_analyzer = None
            self.html_generator = None
            print("⚠️  Legacy report generator components not available - limited functionality")
        
        # Setup Jinja2 template environment
        from utils.path_utils import find_repo_root
        repo_root = find_repo_root()
        template_dir = repo_root / "templates"  
        self.jinja_env = Environment(loader=FileSystemLoader(str(template_dir)))
    
    def _load_config(self, config_path: str | None) -> Dict[str, Any]:
        """Load analysis configuration from YAML file."""
        if config_path is None:
            return {}  # Return empty config if no path provided
        
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"⚠️  Warning: Could not load config file {config_path}: {e}")
            return {}  # Return empty config on error
    
    def generate_html_report(self, report_data: Dict[str, Any], output_path: str):
        """
        Generate comprehensive HTML report from analysis data.
        
        Args:
            report_data: Dictionary containing analysis results
            output_path: Path where HTML report should be saved
        """
        # Enhance report data with additional analysis
        enhanced_data = self._enhance_report_data(report_data)
        
        # Generate HTML content
        if self.html_generator is not None:
            html_content = self.html_generator.generate_report_html(enhanced_data)
        else:
            # Fallback: basic HTML generation
            html_content = f"<html><body><pre>{json.dumps(enhanced_data, indent=2)}</pre></body></html>"
        
        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def _enhance_report_data(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance report data with additional analysis and metrics."""
        enhanced_data = report_data.copy()
        
        # Add impact analysis
        if self.impact_analyzer is not None:
            impact_analysis = self.impact_analyzer.analyze_pr_impact(
                report_data['pr_analysis'],
                report_data['classified_files'],
                report_data['category_summary']
            )
        else:
            impact_analysis = {"status": "legacy_components_unavailable"}
        
        enhanced_data['impact_analysis'] = impact_analysis
        
        # Add executive summary
        executive_summary = self._generate_executive_summary(
            report_data['pr_analysis'],
            report_data['category_summary'],
            impact_analysis
        )
        enhanced_data['executive_summary'] = executive_summary
        
        # Add metadata
        enhanced_data['report_metadata'] = {
            'generated_at': datetime.now().isoformat(),
            'generator_version': '1.0.0',
            'analysis_duration': None,  # Could be calculated if needed
            'total_categories': len(report_data['category_summary']),
            'config_used': self.config['analysis_settings']
        }
        
        # Add visualizations data
        enhanced_data['visualizations'] = self._prepare_visualization_data(
            report_data['pr_analysis'],
            report_data['classified_files'],
            report_data['category_summary']
        )
        
        return enhanced_data
    
    def _generate_executive_summary(self, pr_analysis, category_summary, 
                                   impact_analysis) -> Dict[str, Any]:
        """Generate executive summary of the PR."""
        
        # Identify primary transformation type
        transformation_type = self._identify_transformation_type(category_summary)
        
        # Get key metrics
        total_files = len(pr_analysis.file_changes)
        net_lines = pr_analysis.total_lines_added - pr_analysis.total_lines_removed
        
        # Determine PR scale
        if total_files < 10:
            scale = "Small"
        elif total_files < 50:
            scale = "Medium"  
        elif total_files < 200:
            scale = "Large"
        else:
            scale = "Epic"
        
        return {
            'transformation_type': transformation_type,
            'scale': scale,
            'impact_score': impact_analysis.get('overall_score', 0),
            'risk_level': impact_analysis.get('risk_level', 'Unknown'),
            'key_metrics': {
                'files_changed': total_files,
                'lines_added': pr_analysis.total_lines_added,
                'lines_removed': pr_analysis.total_lines_removed,
                'net_change': net_lines
            },
            'top_categories': self._get_top_categories(category_summary, limit=5),
            'primary_impacts': impact_analysis.get('primary_impacts', []),
            'recommendations': self._generate_recommendations(impact_analysis)
        }
    
    def _identify_transformation_type(self, category_summary) -> str:
        """Identify the primary type of transformation based on changed files."""
        category_weights = {
            'CORE_BUSINESS_LOGIC': 'Business Logic Transformation',
            'USER_INTERFACE': 'UI/UX Enhancement', 
            'DATABASE': 'Data Architecture Update',
            'API_INTEGRATION': 'API Integration',
            'BLOG_CONTENT': 'Content Management System',
            'ASSETS_MEDIA': 'Asset Organization',
            'CONFIGURATION': 'Configuration Update',
            'DOCUMENTATION': 'Documentation Update'
        }
        
        # Find category with most files
        max_count = 0
        primary_category = 'UNCATEGORIZED'
        
        for category, info in category_summary.items():
            if info['count'] > max_count and category in category_weights:
                max_count = info['count']
                primary_category = category
        
        return category_weights.get(primary_category, 'Mixed Development')
    
    def _get_top_categories(self, category_summary, limit: int = 5) -> List[Dict]:
        """Get top categories by file count."""
        # Sort categories by count
        sorted_categories = sorted(
            category_summary.items(),
            key=lambda x: x[1]['count'],
            reverse=True
        )
        
        return [
            {
                'name': name,
                'count': info['count'],
                'icon': info['icon'],
                'description': info['description']
            }
            for name, info in sorted_categories[:limit]
        ]
    
    def _generate_recommendations(self, impact_analysis) -> List[str]:
        """Generate recommendations based on impact analysis."""
        recommendations = []
        
        risk_level = impact_analysis.get('risk_level', 'Unknown')
        impact_score = impact_analysis.get('overall_score', 0)
        
        if risk_level == 'High':
            recommendations.append("🚨 High risk changes detected - consider staged deployment")
            recommendations.append("🧪 Comprehensive testing recommended before merge")
        
        if impact_score > 8:
            recommendations.append("⭐ High-impact PR - ensure thorough code review")
            recommendations.append("📢 Consider announcing changes to stakeholders")
        
        # Add more contextual recommendations based on analysis
        primary_impacts = impact_analysis.get('primary_impacts', [])
        if 'database_changes' in primary_impacts:
            recommendations.append("🗄️ Database changes detected - verify migration safety")
        
        if 'security_implications' in primary_impacts:
            recommendations.append("🔒 Security review recommended")
        
        if not recommendations:
            recommendations.append("✅ Standard review process should be sufficient")
        
        return recommendations
    
    def _prepare_visualization_data(self, pr_analysis, classified_files, 
                                   category_summary) -> Dict[str, Any]:
        """Prepare data for various visualizations."""
        return {
            'category_distribution': {
                'labels': list(category_summary.keys()),
                'data': [info['count'] for info in category_summary.values()],
                'colors': [self._get_category_color(cat) for cat in category_summary.keys()]
            },
            'lines_changed_data': {
                'added': pr_analysis.total_lines_added,
                'removed': pr_analysis.total_lines_removed,
                'net': pr_analysis.total_lines_added - pr_analysis.total_lines_removed
            },
            'change_type_distribution': self._calculate_change_type_distribution(pr_analysis),
            'file_size_distribution': self._calculate_file_size_distribution(pr_analysis)
        }
    
    def _get_category_color(self, category: str) -> str:
        """Get color for category visualization."""
        color_map = {
            'CORE_BUSINESS_LOGIC': '#dc2626',
            'USER_INTERFACE': '#2563eb', 
            'DATABASE': '#059669',
            'API_INTEGRATION': '#7c3aed',
            'BLOG_CONTENT': '#ea580c',
            'ASSETS_MEDIA': '#0891b2',
            'CONFIGURATION': '#65a30d',
            'DOCUMENTATION': '#4338ca'
        }
        return color_map.get(category, '#6b7280')
    
    def _calculate_change_type_distribution(self, pr_analysis) -> Dict[str, int]:
        """Calculate distribution of change types (A/M/D/R)."""
        distribution = {'A': 0, 'M': 0, 'D': 0, 'R': 0}
        for file_change in pr_analysis.file_changes:
            change_type = file_change.change_type
            if change_type in distribution:
                distribution[change_type] += 1
        return distribution
    
    def _calculate_file_size_distribution(self, pr_analysis) -> Dict[str, int]:
        """Calculate distribution by change size."""
        distribution = {'Small': 0, 'Medium': 0, 'Large': 0, 'Massive': 0}
        
        for file_change in pr_analysis.file_changes:
            total_lines = file_change.lines_added + file_change.lines_removed
            if total_lines <= 10:
                distribution['Small'] += 1
            elif total_lines <= 50:
                distribution['Medium'] += 1
            elif total_lines <= 200:
                distribution['Large'] += 1
            else:
                distribution['Massive'] += 1
        
        return distribution