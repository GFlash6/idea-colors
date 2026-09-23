"""Isolated server-mode graph checks; never opens or edits the user's data."""
import importlib.util
from copy import deepcopy
from pathlib import Path

spec = importlib.util.spec_from_file_location('idea_ops', Path(__file__).resolve().parent.parent / 'idea-ops' / 'scripts' / 'idea_ops.py')
ops = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ops)
idea = {'logs': []}

def add(text, parents=None):
    ops.add_log(idea, 'step', text, parents)
    return idea['logs'][-1]['id']

a = add('A')
b = add('B', [a])
c = add('C', [a, b])
ops.insert_log(idea, a, c, 'step', 'N')
n = idea['logs'][-1]['id']
assert ops.find_log(idea, c)['after'] == [n, b]
assert ops.find_log(idea, n)['after'] == [a]
assert ops.find_log(idea, b)['after'] == [a]
snapshot = deepcopy(idea)
try:
    ops.insert_log(idea, a, c, 'step', 'invalid')
    raise AssertionError('Expected missing-edge error')
except ValueError:
    assert idea == snapshot
ops.unlink_logs(idea, n, c)
assert ops.find_log(idea, c)['after'] == [b]
assert len(idea['logs']) == 4
snapshot = deepcopy(idea['logs'])
ops.delete_log(idea, b)
expected = [log for log in snapshot if log['id'] != b]
for log in expected:
    log['after'] = [parent for parent in log['after'] if parent != b]
assert idea['logs'] == expected
assert ops.find_log(idea, c)['after'] == []
ops.set_log_positions(idea, {a: {'x': -23000.5, 'y': 56000}, c: {'x': 20, 'y': 50}})
snapshot = deepcopy(idea)
try:
    ops.set_log_positions(idea, {a: {'x': 1, 'y': 2}, c: {'x': float('inf'), 'y': 5}})
    raise AssertionError('Expected invalid coordinates')
except ValueError:
    assert idea == snapshot
ops.delete_log(idea, n)
assert ops.find_log(idea, a)['position'] == {'x': -23000.5, 'y': 56000}
assert ops.find_log(idea, c)['position'] == {'x': 20, 'y': 50}
ops.move_log(idea, a, -45000, 120000)
assert ops.find_log(idea, a)['position'] == {'x': -45000, 'y': 120000}
print('PASS: server insert, other parents preserved, invalid insert unchanged, unlink, exact node deletion')
print('PASS: server fixed coordinates, unbounded movement, atomic validation, deletion preserves positions')
snapshot = deepcopy(ops.find_log(idea, a))
ops.update_log(idea, a, 'progress', '修改后的完整内容\n第二行')
edited = ops.find_log(idea, a)
assert edited['kind'] == 'progress'
assert edited['text'] == '修改后的完整内容\n第二行'
for key in ('id', 'at', 'after', 'position'):
    assert edited[key] == snapshot[key]
snapshot = deepcopy(idea)
try:
    ops.update_log(idea, a, 'step', '  ')
    raise AssertionError('Expected empty text error')
except ValueError:
    assert idea == snapshot
print('PASS: server node editing and validation preserve graph and coordinates')
idea.update(id='PROJECT',title='项目',status='active',blocker='',next_action='旧行动')
graph_snapshot = deepcopy(idea['logs'])
ops.update_idea({}, idea, {'summary':'项目简介','tags':['AI','效率','AI'],'priority':'high','project_name':'个人项目'})
assert idea['tags'] == ['AI','效率']
assert idea['priority'] == 'high' and idea['project_name'] == '个人项目'
ops.update_idea({},idea,{'status':'blocked','blocker':'缺少资源'})
assert idea['blocker_updated_at']
task = {'id':'T1','text':'下一步行动','owner':'我','hours':2.5,'due':'2026-09-30','done':False}
ops.update_idea({},idea,{'next_steps':[task]})
task['done'] = True
ops.update_idea({},idea,{'next_steps':[task],'next_action':''})
assert idea['next_steps'][0]['done']
assert idea['logs'] == graph_snapshot
for invalid in ({'next_steps':[{**task,'due':'2026-02-30'}]}, {'next_steps':[{**task,'hours':-1}]}, {'status':'blocked','blocker':''}, {'next_steps':[task,task]}):
    before = deepcopy(idea)
    try:
        ops.update_idea({},idea,invalid)
        raise AssertionError('Expected invalid update error')
    except ValueError:
        assert idea == before
print('PASS: server workbench fields, tasks, dates, priority, blocker validation and graph preservation')

ops.update_log(idea, a, "step", "", "独立标题")
assert ops.find_log(idea, a)["title"] == "独立标题"
assert ops.find_log(idea, a)["text"] == ""
print("PASS: server separate title and optional details")
