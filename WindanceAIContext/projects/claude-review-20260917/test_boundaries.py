import ast
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from typing import Any
import review_plugin
from private_reviewer_boundary import install_guards


class BoundaryTests(unittest.TestCase):
    def test_queue_inserts_and_promotions_block_private_reviewers(self):
        for table in ['tasks','staff_tasks']:
            c=sqlite3.connect(':memory:')
            c.execute(f'CREATE TABLE {table}(id TEXT,assignee TEXT,status TEXT)')
            c.execute(f"INSERT INTO {table} VALUES ('old','vega','completed')")
            install_guards(c,table)
            for name in ['vega','Vega','Claude',' claude ','Codex']:
                with self.assertRaises(sqlite3.IntegrityError):
                    c.execute(f'INSERT INTO {table} VALUES (?,?,?)',('new',name,'ready'))
            with self.assertRaises(sqlite3.IntegrityError):
                c.execute(f"UPDATE {table} SET status='ready' WHERE id='old'")
            c.execute(f"INSERT INTO {table} VALUES ('forge','Forge','ready')")
            c.execute(f"UPDATE {table} SET status='archived' WHERE id='old'")

    def test_packet_read_scope(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'packets'; root.mkdir()
            (root/'code.py').write_text('print(1)')
            (Path(tmp)/'private.txt').write_text('not a submitted file')
            (root/'link').symlink_to(Path(tmp)/'private.txt')
            with patch.object(review_plugin,'PACKETS',root):
                self.assertEqual(json.loads(review_plugin.read_packet({'path':'code.py'}))['content'],'print(1)')
                for p in ['../private.txt','link',str(Path(tmp)/'private.txt')]:
                    self.assertIn('error',json.loads(review_plugin.read_packet({'path':p})))

    def test_tools_are_read_only(self):
        self.assertIsNone(review_plugin.readonly_guard('review_read'))
        for tool in ['terminal','write_file','kanban_create','send_message','delegate_task']:
            self.assertEqual(review_plugin.readonly_guard(tool)['action'],'block')

    def test_harness_private_queue_and_legacy_routes(self):
        source=(Path(__file__).parent/'agent_harness.py').read_text()
        names={'normalize_staff_name','create_staff_task','create_vega_delegation_task','escalate_forge_blocker_to_vega'}
        tree=ast.parse(source)
        nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
        class HTTPException(Exception):
            def __init__(self,**kw): self.status_code=kw['status_code']
        scope={'Any':Any,'HTTPException':HTTPException,'audit':lambda *a:None,'upsert_ops_item':lambda **kw:kw}
        exec(compile(ast.Module(body=nodes,type_ignores=[]),'<actual-harness-functions>','exec'),scope)
        self.assertEqual({n.name for n in nodes},names)
        for name in ['Claude','claude','Vega','Codex']:
            with self.assertRaises(HTTPException): scope['create_staff_task'](name,'test')
        scope['create_staff_task']=lambda **kw:tuple(kw.values())
        result=scope['create_vega_delegation_task']('work','William','internal','title','normal','test')
        self.assertEqual(result,('Forge','work','William','internal','title','normal','test'))
        self.assertIsNone(scope['escalate_forge_blocker_to_vega']('x','blocked'))

    def test_no_duplicate_operational_assignment(self):
        source=(Path(__file__).parent/'agent_harness.py').read_text()
        tree=ast.parse(source)
        project=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='create_project_workflow')
        calls=[n for n in ast.walk(project) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='create_staff_task']
        owners=[ast.literal_eval(k.value) for n in calls for k in n.keywords if k.arg=='assignee']
        self.assertEqual(owners.count('Forge'),1)
        self.assertNotIn('Vega',owners)
        self.assertNotIn('vega',{n.id for n in ast.walk(project) if isinstance(n,ast.Name)})
        self.assertNotIn('("Forge", "Technology oversight",',source)

    def test_scheduler_no_private_assignment(self):
        source=(Path(__file__).parent/'windance_weekly_stack_review.py').read_text()
        tree=ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=='create_task' and node.args and isinstance(node.args[0],ast.Constant):
                self.assertNotIn(str(node.args[0].value).lower(),{'vega','claude'})


if __name__=='__main__': unittest.main(verbosity=2)
