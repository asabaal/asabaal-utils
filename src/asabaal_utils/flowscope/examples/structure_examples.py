"""
Comprehensive example functions demonstrating all control flow structures
across different line count ranges for systematic visualization testing.
"""

import os
import requests

# ===== LINEAR FUNCTIONS =====

# 1-5 lines: Simple linear
def linear_3_lines(x):
    return x + 1

def linear_5_lines(a, b):
    temp = a * 2
    result = temp + b
    return result

# 6-10 lines: Medium linear
def linear_8_lines(data):
    cleaned = data.strip()
    normalized = cleaned.lower()
    processed = normalized.replace(' ', '_')
    return processed

def linear_10_lines(items):
    filtered = [x for x in items if x is not None]
    unique = list(set(filtered))
    sorted_items = sorted(unique)
    return len(sorted_items)

# 11-20 lines: Complex linear
def linear_15_lines(user_data):
    # Extract basic info
    name = user_data.get('name', '').strip()
    email = user_data.get('email', '').lower()
    
    # Process name
    first_name = name.split()[0] if name else 'Unknown'
    last_name = name.split()[-1] if len(name.split()) > 1 else ''
    
    # Process email
    domain = email.split('@')[-1] if '@' in email else 'unknown'
    
    # Create summary
    summary = f"{first_name} ({domain})"
    return summary

def linear_20_lines(log_entry):
    # Parse timestamp
    timestamp_str = log_entry.split(' ')[0]
    timestamp = int(timestamp_str)
    
    # Extract level
    level_start = len(timestamp_str) + 1
    level_end = log_entry.find(' ', level_start)
    level = log_entry[level_start:level_end]
    
    # Extract message
    message = log_entry[level_end + 1:]
    
    # Create structured data
    structured = {
        'timestamp': timestamp,
        'level': level.upper(),
        'message': message.strip(),
        'length': len(message)
    }
    
    return structured


# ===== BINARY BRANCHING FUNCTIONS =====

# 5-10 lines: Simple binary branching
def binary_6_lines(x):
    if x > 0:
        return "positive"
    else:
        return "non-positive"

def binary_9_lines(age):
    if age >= 18:
        status = "adult"
        can_vote = True
    else:
        status = "minor"
        can_vote = False
    return status, can_vote

# 11-20 lines: Medium binary branching
def binary_14_lines(user):
    if user.is_authenticated:
        profile = get_user_profile(user.id)
        preferences = load_user_preferences(user.id)
        context = {
            'user': profile,
            'prefs': preferences,
            'access_level': 'full'
        }
    else:
        context = {
            'user': None,
            'prefs': {},
            'access_level': 'limited'
        }
    return context

def binary_18_lines(file_path):
    if os.path.exists(file_path):
        stat = os.stat(file_path)
        size = stat.st_size
        modified = stat.st_mtime
        readable = os.access(file_path, os.R_OK)
        return {
            'exists': True,
            'size': size,
            'modified': modified,
            'readable': readable
        }
    else:
        return {
            'exists': False,
            'error': 'File not found',
            'suggestions': ['Check path', 'Check permissions']
        }


# ===== MULTI-WAY BRANCHING FUNCTIONS =====

# 8-15 lines: Simple multi-way branching
def multi_10_lines(score):
    if score >= 90:
        grade = 'A'
    elif score >= 80:
        grade = 'B'
    elif score >= 70:
        grade = 'C'
    elif score >= 60:
        grade = 'D'
    else:
        grade = 'F'
    return grade

def multi_14_lines(status_code):
    if 200 <= status_code < 300:
        category = 'Success'
        action = 'Process response'
    elif 300 <= status_code < 400:
        category = 'Redirection'
        action = 'Follow redirect'
    elif 400 <= status_code < 500:
        category = 'Client Error'
        action = 'Fix request'
    elif 500 <= status_code < 600:
        category = 'Server Error'
        action = 'Retry later'
    else:
        category = 'Unknown'
        action = 'Investigate'
    return category, action

# 16-25 lines: Complex multi-way branching
def multi_22_lines(user_role, permissions):
    if user_role == 'admin':
        access_level = 'full'
        allowed_actions = ['create', 'read', 'update', 'delete', 'manage']
        rate_limit = 10000
    elif user_role == 'moderator':
        access_level = 'high'
        allowed_actions = ['create', 'read', 'update', 'moderate']
        rate_limit = 5000
    elif user_role == 'editor':
        access_level = 'medium'
        allowed_actions = ['create', 'read', 'update']
        rate_limit = 2000
    elif user_role == 'viewer':
        access_level = 'low'
        allowed_actions = ['read']
        rate_limit = 1000
    else:
        access_level = 'none'
        allowed_actions = []
        rate_limit = 100
    
    # Check permissions
    final_permissions = [p for p in allowed_actions if p in permissions]
    
    return {
        'access_level': access_level,
        'permissions': final_permissions,
        'rate_limit': rate_limit
    }


# ===== LOOP STRUCTURES =====

# 6-12 lines: Simple loops
def loop_8_lines(numbers):
    total = 0
    for num in numbers:
        total += num
    return total

def loop_11_lines(text):
    vowels = 0
    for char in text.lower():
        if char in 'aeiou':
            vowels += 1
    return vowels

# 13-20 lines: Medium loops
def loop_16_lines(data_list):
    results = []
    for item in data_list:
        if item is not None:
            processed = item.strip().lower()
            if len(processed) > 0:
                results.append(processed)
    return results

def loop_19_lines(numbers, threshold):
    filtered = []
    count = 0
    for num in numbers:
        if num > threshold:
            filtered.append(num)
            count += 1
            if count >= 10:  # Limit results
                break
    return filtered, count


# ===== NESTED STRUCTURES =====

# 10-20 lines: Simple nesting
def nested_12_lines(matrix):
    results = []
    for row in matrix:
        row_sum = 0
        for value in row:
            if value > 0:
                row_sum += value
        results.append(row_sum)
    return results

def nested_18_lines(data, filters):
    results = []
    for category in data:
        if category in filters:
            for item in data[category]:
                if item.get('active', False):
                    processed = {
                        'id': item['id'],
                        'name': item['name'],
                        'category': category
                    }
                    results.append(processed)
    return results

# 21-30 lines: Complex nesting
def nested_25_lines(complex_data, config):
    output = []
    for section in complex_data['sections']:
        if section['type'] in config['allowed_types']:
            for item in section['items']:
                if item.get('active', False):
                    for subitem in item['subitems']:
                        if subitem['enabled']:
                            processed = {
                                'section_id': section['id'],
                                'item_id': item['id'],
                                'subitem': subitem['name'],
                                'value': subitem['value'] * config['multiplier']
                            }
                            output.append(processed)
    return output


# ===== EXCEPTION HANDLING =====

# 8-15 lines: Simple exception handling
def exception_10_lines(filename):
    try:
        with open(filename, 'r') as f:
            content = f.read()
        return content
    except FileNotFoundError:
        return None
    except IOError:
        return None

def exception_14_lines(data, key):
    try:
        value = data[key]
        processed = value.upper()
        return processed
    except KeyError:
        return f"Key '{key}' not found"
    except AttributeError:
        return "Invalid data type"
    except Exception as e:
        return f"Unexpected error: {str(e)}"

# 16-25 lines: Complex exception handling
def exception_20_lines(url, timeout=5):
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        data = response.json()
        return {
            'success': True,
            'data': data,
            'status_code': response.status_code
        }
    except requests.exceptions.Timeout:
        return {
            'success': False,
            'error': 'Request timeout',
            'retry_after': timeout * 2
        }
    except requests.exceptions.ConnectionError:
        return {
            'success': False,
            'error': 'Connection failed',
            'action': 'Check network'
        }
    except requests.exceptions.HTTPError as e:
        return {
            'success': False,
            'error': f'HTTP error: {e.response.status_code}',
            'status_code': e.response.status_code
        }
    except ValueError:
        return {
            'success': False,
            'error': 'Invalid JSON response'
        }


# ===== MULTIPLE RETURNS =====

# 5-12 lines: Simple multiple returns
def multi_return_7_lines(value):
    if value is None:
        return None
    if value < 0:
        return 0
    return value * 2

def multi_return_11_lines(text):
    if not text:
        return False
    if len(text) < 3:
        return False
    if not text.isalnum():
        return False
    return True

# 13-20 lines: Complex multiple returns
def multi_return_16_lines(user, action, resource):
    if not user.is_authenticated:
        return {'allowed': False, 'reason': 'Not authenticated'}
    
    if user.is_suspended:
        return {'allowed': False, 'reason': 'Account suspended'}
    
    if action not in user.permissions:
        return {'allowed': False, 'reason': 'Insufficient permissions'}
    
    if resource.is_deleted:
        return {'allowed': False, 'reason': 'Resource not available'}
    
    if resource.owner_id != user.id and not user.is_admin:
        return {'allowed': False, 'reason': 'Access denied'}
    
    return {'allowed': True, 'resource': resource.to_dict()}


# ===== COMBINATION EXAMPLES =====

# 20-30 lines: Mixed structures
def complex_25_lines(data, options):
    """Complex function combining multiple structures."""
    results = []
    
    # Guard clauses (multiple returns)
    if not data:
        return []
    if not options.get('enabled', True):
        return []
    
    # Loop with nested branching
    for item in data:
        # Binary branching
        if item.get('type') == 'special':
            processed = process_special_item(item)
        else:
            processed = process_regular_item(item)
        
        # Multi-way branching
        if processed['status'] == 'success':
            results.append(processed)
        elif processed['status'] == 'warning':
            if options.get('include_warnings', False):
                results.append(processed)
        elif processed['status'] == 'error':
            if options.get('include_errors', False):
                results.append(processed)
    
    # Exception handling
    try:
        final_results = apply_transformations(results, options)
    except TransformationError as e:
        return {'error': str(e), 'partial_results': results}
    
    return final_results


# Helper functions for examples
def get_user_profile(user_id):
    pass

def load_user_preferences(user_id):
    pass

def process_special_item(item):
    return {'status': 'success', 'data': item}

def process_regular_item(item):
    return {'status': 'success', 'data': item}

def apply_transformations(results, options):
    return results

class TransformationError(Exception):
    pass