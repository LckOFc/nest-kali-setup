"""Add all missing API routes to app.py"""
with open('web/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

missing_routes = [
    "/api/alerts",
    "/api/alerts/unread",
    "/api/alerts/acknowledge",
    "/api/alerts/clear",
    "/api/organizer/items",
    "/api/organizer/add",
    "/api/organizer/stats",
    "/api/target/scope",
    "/api/session/create",
    "/api/session/list",
    "/api/session/",
    "/api/sequencer/analyze",
    "/api/comparer/compare",
    "/api/collaborator/start",
    "/api/collaborator/stop",
    "/api/collaborator/interactions",
    "/api/collaborator/payloads",
    "/api/match-replace/rules",
    "/api/match-replace/add",
    "/api/projects/list",
    "/api/projects/create",
    "/api/projects/current",
    "/api/extender/plugins",
    "/api/extender/install",
    "/api/extender/store",
    "/api/browser/status",
    "/api/browser/start",
    "/api/browser/stop",
    "/api/browser/open",
    "/api/payload-processor/operations",
    "/api/payload-processor/process",
]

missing = []
for route in missing_routes:
    if route not in content:
        missing.append(route)

if missing:
    print('Missing routes:', len(missing))
    for r in missing[:5]:
        print(' ', r)
else:
    print('All routes present!')
