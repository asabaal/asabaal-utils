#!/usr/bin/env python3
"""
Test script for the frame extractor module.

This script takes a video file as input, tests all available extraction methods,
and reports on which methods succeed or fail along with quality metrics for
extracted frames.

Usage:
    python test_frame_extractor.py video_path [timestamp] [output_dir]

Arguments:
    video_path: Path to the video file to test
    timestamp: Optional timestamp in seconds (default: 5.0)
    output_dir: Optional directory to save extracted frames (default: ./extracted_frames)
"""

import os
import sys
import argparse
import logging
from pathlib import Path
import json
from typing import Dict, Any
import time
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_frame_extractor")

# Import the frame_extractor module
try:
    from frame_extractor import FrameExtractor
except ImportError:
    # Handle the case when running from the command line
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(os.path.dirname(script_dir))
    sys.path.append(parent_dir)
    
    from asabaal_utils.video_processing.frame_extractor import FrameExtractor


def generate_test_report(results: Dict[str, Any], output_dir: str) -> Dict[str, Any]:
    """
    Generate a test report from the extraction method comparison results.
    
    Args:
        results: Results from the FrameExtractor.compare_extraction_methods method
        output_dir: Directory where the extracted frames are saved
        
    Returns:
        Dictionary with test report information
    """
    # Calculate overall statistics
    total_methods = len(results['method_results'])
    successful_methods = results['successful_methods']
    failed_methods = results['failed_methods']
    success_rate = len(successful_methods) / total_methods if total_methods > 0 else 0
    
    # Group methods by quality
    quality_groups = {
        'high': [],
        'medium': [],
        'low': [],
        'poor': []
    }
    
    # Calculate average brightness and contrast for successful methods
    brightness_values = []
    contrast_values = []
    
    for method_id, result in results['method_results'].items():
        if result['success'] and result['quality_info']:
            quality = result['quality_info']['quality']
            if quality in quality_groups:
                quality_groups[quality].append(method_id)
            
            brightness = result['quality_info']['brightness']
            contrast = result['quality_info']['contrast']
            
            if brightness is not None:
                brightness_values.append(brightness)
            
            if contrast is not None:
                contrast_values.append(contrast)
    
    avg_brightness = sum(brightness_values) / len(brightness_values) if brightness_values else 0
    avg_contrast = sum(contrast_values) / len(contrast_values) if contrast_values else 0
    
    # Find the best extraction method based on quality
    best_method = None
    best_quality_score = -1
    
    for method_id, result in results['method_results'].items():
        if result['success'] and result['quality_info']:
            # Calculate a quality score based on brightness and contrast
            brightness = result['quality_info']['brightness']
            contrast = result['quality_info']['contrast']
            
            # Ideal brightness is around 128 (mid-range)
            brightness_score = 1.0 - abs(brightness - 128) / 128
            
            # Higher contrast is generally better (up to a point)
            contrast_score = min(contrast / 50, 1.0)
            
            # Combined score (weight brightness more than contrast)
            quality_score = (brightness_score * 0.7) + (contrast_score * 0.3)
            
            if quality_score > best_quality_score:
                best_quality_score = quality_score
                best_method = method_id
    
    # Create the report
    report = {
        'timestamp': datetime.now().isoformat(),
        'video_path': results['video_path'],
        'timestamp_tested': results['timestamp'],
        'duration': results['duration'],
        'output_directory': output_dir,
        'statistics': {
            'total_methods': total_methods,
            'successful_methods_count': len(successful_methods),
            'failed_methods_count': len(failed_methods),
            'success_rate': success_rate,
            'average_brightness': avg_brightness,
            'average_contrast': avg_contrast
        },
        'successful_methods': successful_methods,
        'failed_methods': failed_methods,
        'quality_groups': quality_groups,
        'best_method': best_method,
        'detailed_results': results['method_results']
    }
    
    return report


def print_report_summary(report: Dict[str, Any]) -> None:
    """
    Print a formatted summary of the test report to the console.
    
    Args:
        report: The test report dictionary
    """
    print("\n" + "="*80)
    print(f"FRAME EXTRACTOR TEST REPORT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    stats = report['statistics']
    
    print(f"\nVideo: {report['video_path']}")
    print(f"Timestamp: {report['timestamp_tested']} seconds")
    print(f"Output Directory: {report['output_directory']}")
    
    print("\nOVERALL STATISTICS:")
    print(f"  Total methods tested:    {stats['total_methods']}")
    print(f"  Successful methods:      {stats['successful_methods_count']}")
    print(f"  Failed methods:          {stats['failed_methods_count']}")
    print(f"  Success rate:            {stats['success_rate']*100:.1f}%")
    print(f"  Average brightness:      {stats['average_brightness']:.1f}")
    print(f"  Average contrast:        {stats['average_contrast']:.1f}")
    
    print("\nQUALITY BREAKDOWN:")
    for quality, methods in report['quality_groups'].items():
        if methods:
            print(f"  {quality.title()} quality:          {len(methods)} methods")
    
    if report['best_method']:
        print(f"\nBEST METHOD: {report['best_method']}")
        quality_info = report['detailed_results'][report['best_method']]['quality_info']
        print(f"  Quality:               {quality_info['quality']}")
        print(f"  Brightness:            {quality_info['brightness']:.1f}")
        print(f"  Contrast:              {quality_info['contrast']:.1f}")
    
    print("\nSUCCESSFUL METHODS:")
    for method in report['successful_methods']:
        result = report['detailed_results'][method]
        quality = result['quality_info']['quality'] if result['quality_info'] else 'unknown'
        print(f"  {method:<20} - Quality: {quality}")
    
    print("\nFAILED METHODS:")
    for method in report['failed_methods']:
        error = report['detailed_results'][method].get('error', 'Unknown error')
        print(f"  {method:<20} - Error: {error[:50]}...")
    
    print("\n" + "="*80)
    print(f"Full report saved to: {os.path.join(report['output_directory'], 'test_report.json')}")
    print("="*80 + "\n")


def main():
    parser = argparse.ArgumentParser(description='Test the frame extractor module')
    parser.add_argument('video_path', help='Path to the video file to test')
    parser.add_argument('--timestamp', type=float, default=5.0, help='Timestamp in seconds (default: 5.0)')
    parser.add_argument('--output-dir', default=None, help='Directory to save extracted frames')
    parser.add_argument('--ffmpeg-path', default='ffmpeg', help='Path to ffmpeg executable')
    parser.add_argument('--generate-html', action='store_true', help='Generate HTML report')
    
    args = parser.parse_args()
    
    # Validate video path
    if not os.path.exists(args.video_path):
        logger.error(f"Video file not found: {args.video_path}")
        sys.exit(1)
    
    # Create output directory
    if args.output_dir is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = os.path.join(os.getcwd(), f"extracted_frames_{timestamp}")
    else:
        output_dir = args.output_dir
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Create the frame extractor
    logger.info(f"Creating frame extractor with output directory: {output_dir}")
    extractor = FrameExtractor(
        output_dir=output_dir,
        ffmpeg_path=args.ffmpeg_path
    )
    
    # Start testing
    logger.info(f"Testing frame extraction on {args.video_path} at {args.timestamp} seconds")
    
    # Test all extraction methods
    start_time = time.time()
    results = extractor.compare_extraction_methods(
        video_path=args.video_path,
        timestamp=args.timestamp
    )
    elapsed_time = time.time() - start_time
    
    # Generate the report
    report = generate_test_report(results, output_dir)
    report['test_duration'] = elapsed_time
    
    # Save the report to JSON
    report_path = os.path.join(output_dir, 'test_report.json')
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    # Print the report summary
    print_report_summary(report)
    
    # Optionally generate HTML report
    if args.generate_html:
        html_report_path = os.path.join(output_dir, 'test_report.html')
        try:
            generate_html_report(report, html_report_path)
            logger.info(f"HTML report saved to: {html_report_path}")
        except Exception as e:
            logger.error(f"Failed to generate HTML report: {e}")
    
    return 0


def generate_html_report(report: Dict[str, Any], output_path: str) -> None:
    """
    Generate an HTML report from the test results.
    
    Args:
        report: The test report dictionary
        output_path: Path to save the HTML report
    """
    # HTML template for the report
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Frame Extractor Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1, h2, h3 {{ color: #333; }}
        .stats-card {{ background-color: #f8f9fa; padding: 15px; margin-bottom: 20px; border-radius: 5px; }}
        .methods-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 15px; }}
        .method-card {{ border: 1px solid #ddd; border-radius: 5px; padding: 10px; }}
        .method-card img {{ width: 100%; height: auto; }}
        .method-card.success {{ border-color: #28a745; }}
        .method-card.fail {{ border-color: #dc3545; }}
        .quality-high {{ color: #28a745; }}
        .quality-medium {{ color: #007bff; }}
        .quality-low {{ color: #ffc107; }}
        .quality-poor {{ color: #dc3545; }}
        .best-method {{ background-color: #d4edda; border-color: #28a745; }}
        table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
        th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <h1>Frame Extractor Test Report</h1>
    <p><strong>Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    
    <div class="stats-card">
        <h2>Video Information</h2>
        <p><strong>File:</strong> {report['video_path']}</p>
        <p><strong>Timestamp:</strong> {report['timestamp_tested']} seconds</p>
        <p><strong>Output Directory:</strong> {report['output_directory']}</p>
        <p><strong>Test Duration:</strong> {report.get('test_duration', 0):.2f} seconds</p>
    </div>
    
    <div class="stats-card">
        <h2>Overall Statistics</h2>
        <table>
            <tr>
                <th>Metric</th>
                <th>Value</th>
            </tr>
            <tr>
                <td>Total Methods Tested</td>
                <td>{report['statistics']['total_methods']}</td>
            </tr>
            <tr>
                <td>Successful Methods</td>
                <td>{report['statistics']['successful_methods_count']}</td>
            </tr>
            <tr>
                <td>Failed Methods</td>
                <td>{report['statistics']['failed_methods_count']}</td>
            </tr>
            <tr>
                <td>Success Rate</td>
                <td>{report['statistics']['success_rate']*100:.1f}%</td>
            </tr>
            <tr>
                <td>Average Brightness</td>
                <td>{report['statistics']['average_brightness']:.1f}</td>
            </tr>
            <tr>
                <td>Average Contrast</td>
                <td>{report['statistics']['average_contrast']:.1f}</td>
            </tr>
        </table>
        
        <h3>Quality Breakdown</h3>
        <table>
            <tr>
                <th>Quality</th>
                <th>Count</th>
                <th>Methods</th>
            </tr>
"""
    
    # Add quality breakdown
    for quality, methods in report['quality_groups'].items():
        if methods:
            html += f"""
            <tr>
                <td class="quality-{quality}">{quality.title()}</td>
                <td>{len(methods)}</td>
                <td>{', '.join(methods)}</td>
            </tr>"""
    
    html += """
        </table>
    </div>
"""
    
    # Add best method section if there is one
    if report['best_method']:
        best_method = report['best_method']
        result = report['detailed_results'][best_method]
        best_method_path = result.get('frame_path', '')
        best_method_rel_path = os.path.relpath(best_method_path, report['output_directory']) if best_method_path else ''
        
        html += f"""
    <div class="stats-card">
        <h2>Best Method</h2>
        <div class="method-card success best-method">
            <h3>{best_method}</h3>
"""
        
        if best_method_path and os.path.exists(best_method_path):
            html += f"""
            <img src="{best_method_rel_path}" alt="{best_method}">
"""
        
        if result['quality_info']:
            html += f"""
            <p><strong>Quality:</strong> <span class="quality-{result['quality_info']['quality']}">{result['quality_info']['quality'].title()}</span></p>
            <p><strong>Brightness:</strong> {result['quality_info']['brightness']:.1f}</p>
            <p><strong>Contrast:</strong> {result['quality_info']['contrast']:.1f}</p>
"""
        
        html += """
        </div>
    </div>
"""
    
    # Add successful methods grid
    html += """
    <h2>Successful Methods</h2>
    <div class="methods-grid">
"""
    
    for method_id in report['successful_methods']:
        result = report['detailed_results'][method_id]
        method_path = result.get('frame_path', '')
        method_rel_path = os.path.relpath(method_path, report['output_directory']) if method_path else ''
        quality = result['quality_info']['quality'] if result['quality_info'] else 'unknown'
        
        html += f"""
        <div class="method-card success">
            <h3>{method_id}</h3>
"""
        
        if method_path and os.path.exists(method_path):
            html += f"""
            <img src="{method_rel_path}" alt="{method_id}">
"""
        
        html += f"""
            <p><strong>Quality:</strong> <span class="quality-{quality}">{quality.title()}</span></p>
"""
        
        if result['quality_info']:
            html += f"""
            <p><strong>Brightness:</strong> {result['quality_info']['brightness']:.1f}</p>
            <p><strong>Contrast:</strong> {result['quality_info']['contrast']:.1f}</p>
"""
        
        html += """
        </div>
"""
    
    html += """
    </div>
    
    <h2>Failed Methods</h2>
    <table>
        <tr>
            <th>Method</th>
            <th>Error</th>
        </tr>
"""
    
    # Add failed methods
    for method_id in report['failed_methods']:
        result = report['detailed_results'][method_id]
        error = result.get('error', 'Unknown error')
        
        html += f"""
        <tr>
            <td>{method_id}</td>
            <td>{error[:100]}{"..." if len(error) > 100 else ""}</td>
        </tr>
"""
    
    html += """
    </table>
    
    <script>
        // Add any interactive features here
    </script>
</body>
</html>
"""
    
    # Write the HTML to file
    with open(output_path, 'w') as f:
        f.write(html)


if __name__ == "__main__":
    sys.exit(main())