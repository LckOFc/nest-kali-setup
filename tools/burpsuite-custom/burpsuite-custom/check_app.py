"""Check app.py structure"""
with open('web/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Count triple quotes
triple_count = content.count("'''")
print(f'Triple quotes count: {triple_count}')

# Find MAIN_TEMPLATE boundaries
start_idx = content.find("MAIN_TEMPLATE = '''")
end_idx = content.find("'''\n\n\n#", start_idx)
if end_idx == -1:
    end_idx = content.find("'''\n\n# Rotas", start_idx)
if end_idx == -1:
    end_idx = content.find("'''\n\n\n@app", start_idx)

print(f'MAIN_TEMPLATE starts at: {start_idx}')
print(f'MAIN_TEMPLATE ends at: {end_idx}')

if end_idx > 0:
    after_template = content[end_idx+4:end_idx+200]
    print(f'After template:\n{after_template[:150]}')

# Check if routes are outside template
python_routes = []
lines = content.split('\n')
in_template = False
for line in lines:
    if "MAIN_TEMPLATE = '''" in line:
        in_template = True
    if "'''" in line and in_template and "MAIN_TEMPLATE = '''" not in line:
        in_template = False
    if '@app.route' in line and not in_template:
        python_routes.append(line.strip())

print(f'\nPython routes found: {len(python_routes)}')
for r in python_routes[:5]:
    print(f'  {r}')
