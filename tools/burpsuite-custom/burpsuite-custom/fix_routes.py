"""Check and fix duplicate routes in app.py"""
import re
from collections import Counter

with open('web/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find all routes
routes = re.findall(r"@app\.route\('([^']+)'", content)
dups = [(r, c) for r, c in Counter(routes).items() if c > 1]

if dups:
    print('Duplicate routes found:')
    for r, c in dups:
        print(f'  {r}: {c} times')
    
    # Remove duplicates by keeping only first occurrence
    seen = set()
    lines = content.split('\n')
    new_lines = []
    skip_until_next_route = False
    
    for i, line in enumerate(lines):
        route_match = re.search(r"@app\.route\('([^']+)'", line)
        if route_match:
            route = route_match.group(1)
            if route in seen:
                # Skip this route and its decorator line
                skip_until_next_route = True
                continue
            else:
                seen.add(route)
                skip_until_next_route = False
        
        if not skip_until_next_route:
            new_lines.append(line)
        elif line.strip().startswith('def ') or line.strip().startswith('@app'):
            skip_until_next_route = False
            new_lines.append(line)
    
    content = '\n'.join(new_lines)
    
    with open('web/app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Duplicates removed!')
else:
    print('No duplicate routes!')
