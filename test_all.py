import httpx

print('=== COMPREHENSIVE API TEST ===')

# 1. Health
r = httpx.get('http://127.0.0.1:8000/api/health')
print(f'1. Health: {r.status_code} - {r.json()["status"]}')

# 2. Tasks CRUD
r = httpx.post('http://127.0.0.1:8000/api/tasks', json={'title': 'Test Task', 'project': 'Test', 'priority': 'High', 'status': 'todo', 'due': '2026-11-30'})
task_id = r.json()['id']
print(f'2. Create Task: {r.status_code} - {task_id}')

r = httpx.get('http://127.0.0.1:8000/api/tasks')
print(f'3. List Tasks: {r.status_code} - {len(r.json())} tasks')

r = httpx.patch(f'http://127.0.0.1:8000/api/tasks/{task_id}', json={'status': 'done'})
print(f'4. Update Task: {r.status_code} - {r.json()["status"]}')

r = httpx.post(f'http://127.0.0.1:8000/api/tasks/{task_id}/toggle')
print(f'5. Toggle Task: {r.status_code} - {r.json()["status"]}')

# 6. Agent Plan
r = httpx.post('http://127.0.0.1:8000/api/agent/plan', json={'command': 'Prepare for hackathon'})
proposal_id = r.json()['proposalId']
print(f'6. Agent Plan: {r.status_code} - {proposal_id}')

# 7. Approvals
r = httpx.get('http://127.0.0.1:8000/api/approvals')
print(f'7. List Approvals: {r.status_code} - {len(r.json())} proposals')

r = httpx.post(f'http://127.0.0.1:8000/api/approvals/{proposal_id}/approve', json={'tasks': []})
print(f'8. Approve: {r.status_code} - {r.json()["status"]} created {len(r.json()["createdTasks"])} tasks')

r = httpx.get('http://127.0.0.1:8000/api/tasks')
print(f'9. Tasks after approve: {r.status_code} - {len(r.json())} tasks')

# 10. Activity
r = httpx.get('http://127.0.0.1:8000/api/activity')
print(f'10. Activity: {r.status_code} - {len(r.json())} entries')

# 11. Analytics
r = httpx.get('http://127.0.0.1:8000/api/analytics')
a = r.json()
print(f'11. Analytics: {r.status_code} - {a["totalTasks"]} tasks, {a["totalActivity"]} activities')

# 12. Settings
r = httpx.get('http://127.0.0.1:8000/api/settings')
print(f'12. Settings: {r.status_code} - {r.json()["name"]}')

# 13. Projects
r = httpx.post('http://127.0.0.1:8000/api/projects', json={'name': 'Frontend Test Project'})
print(f'13. Create Project: {r.status_code} - {r.json()["name"]}')

r = httpx.get('http://127.0.0.1:8000/api/projects')
print(f'14. List Projects: {r.status_code} - {len(r.json())} projects')

# 15. Email Accounts
r = httpx.post('http://127.0.0.1:8000/api/emails/accounts', json={'provider': 'gmail', 'email_address': 'frontend@test.com', 'app_password': 'abcd efgh ijkl mnop'})
print(f'15. Add Email Account: {r.status_code} - {r.json()["email_address"]}')

r = httpx.get('http://127.0.0.1:8000/api/emails/accounts')
print(f'16. List Email Accounts: {r.status_code} - {len(r.json())} accounts')

# 17. Cleanup
httpx.delete(f'http://127.0.0.1:8000/api/tasks/{task_id}')
print('17. Cleanup: Deleted test task')

print('\n=== ALL TESTS PASSED ===')