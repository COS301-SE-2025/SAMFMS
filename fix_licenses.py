#!/usr/bin/env python3
"""
Script to fix all dependency issues in licenses.py
"""

import re

def fix_licenses_file():
    file_path = r'c:\Users\user\OneDrive\Documents\capstone\repo\SAMFMS\Sblocks\maintenance\api\routes\licenses.py'
    
    # Read the file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix function name changes
    content = re.sub(r'get_authenticated_user', 'get_current_user', content)
    content = re.sub(r'require_permissions\(\[\"([^\"]+)\"\]\)', r'require_permission("\1")', content)
    
    # Fix timer dependency pattern
    content = re.sub(r'timer: object = Depends\(get_request_timer\)', 'request: Request', content)
    
    # Fix timer references in responses
    content = re.sub(r'timer\.request_id', 'request_id', content)
    content = re.sub(r'timer\.elapsed', 'timer.execution_time_ms', content)
    
    # Add request_id and timer context to function bodies
    # Pattern: after function definition, add request_id and timer context
    def add_request_context(match):
        func_def = match.group(1)
        func_body = match.group(2)
        
        # Skip if already has request_id and timer context
        if 'request_id = await get_request_id(request)' in func_body:
            return match.group(0)
        
        # Add request_id and timer context after try:
        if 'try:' in func_body:
            func_body = func_body.replace('try:', 'request_id = await get_request_id(request)\n    \n    with RequestTimer() as timer:\n        try:', 1)
            # Add indent to the rest of the function
            lines = func_body.split('\n')
            new_lines = []
            in_try_block = False
            for line in lines:
                if 'with RequestTimer() as timer:' in line:
                    in_try_block = True
                    new_lines.append(line)
                elif in_try_block and line.strip() and not line.startswith('    '):
                    new_lines.append('    ' + line)
                else:
                    new_lines.append(line)
            func_body = '\n'.join(new_lines)
        
        return func_def + func_body
    
    # Apply the pattern to all async functions
    content = re.sub(r'(async def [^:]+:)\n(.*?)(?=\n\n@|\nclass|\n$)', add_request_context, content, flags=re.DOTALL)
    
    # Write the file back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("Fixed licenses.py file")

if __name__ == "__main__":
    fix_licenses_file()
