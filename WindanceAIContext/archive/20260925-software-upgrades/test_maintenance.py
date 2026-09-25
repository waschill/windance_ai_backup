import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import windance_software_maintenance as m


def item(output='', code=0):
    return {'code': code, 'output': output}


class RepairTests(unittest.TestCase):
    def test_stable_release_does_not_follow_development_main(self):
        self.assertFalse(m.needs_update('herald-hermes', item(json.dumps({'update_available': False}))))
        self.assertTrue(m.needs_update('herald-hermes', item(json.dumps({'update_available': True}))))
        with patch.object(m, 'run') as run:
            self.assertNotEqual(m.apply_updates({'herald-hermes': item()})['herald-hermes']['code'], 0)
            run.assert_not_called()

    def test_pinned_runtime_is_not_upgraded_or_reported_as_actionable(self):
        packages=item(json.dumps({'formulae':[{'name':'node','pinned':True}], 'casks':[]}))
        self.assertFalse(m.needs_update('sal-homebrew', packages))
        with patch.object(m,'run',return_value=item()) as run:
            m.apply_updates({'sal-homebrew':packages})
            self.assertFalse(any('brew upgrade' in call.args[0] for call in run.call_args_list))

    def test_npm_outdated_exit_one_is_success(self):
        output = json.dumps({'node-red': {'current': '5.0.4', 'wanted': '5.0.7', 'latest': '5.0.7'}})
        with patch.object(m, 'run', return_value=item(output, 1)) as run:
            self.assertEqual(m.npm_audit()['code'], 0)
            self.assertNotIn('|| true', run.call_args.args[0])

    def test_npm_failures_are_not_outdated_success(self):
        for value in (item('connection refused', 255), item('{"error":{"code":"E404"}}', 1), item('truncated', 0)):
            with self.subTest(value=value), patch.object(m, 'run', return_value=value):
                self.assertNotEqual(m.npm_audit()['code'], 0)

    def test_inventory_does_not_prove_outdated(self):
        self.assertFalse(m.needs_update('hal-ollama-models', item('NAME ID SIZE\nwindance-herald:latest abc 4 GB')))
        self.assertFalse(m.needs_update('al-containers', item('open-webui|image:latest|Up')))

    def test_model_container_and_os_paths_never_execute_unsafe_upgrades(self):
        for target in ('hal-ollama-models', 'al-containers', 'herald-macos', 'sal-macos'):
            with self.subTest(target=target), patch.object(m, 'run', return_value=item()) as run:
                results = m.apply_updates({target: item('inventory')})
                self.assertNotEqual(results[target]['code'], 0)
                commands = ' '.join(call.args[0] for call in run.call_args_list)
                for unsafe in ('ollama pull', 'watchtower', 'install-all', '--cleanup'):
                    self.assertNotIn(unsafe, commands)

    def test_brew_selects_names_and_excludes_syncthing(self):
        packages = item(json.dumps({'formulae': [{'name': 'node'}, {'name': 'syncthing'}], 'casks': []}))
        with patch.object(m, 'run', return_value=item()) as run:
            m.apply_updates({'sal-homebrew': packages})
            command = run.call_args_list[0].args[0]
            self.assertIn('brew upgrade node', command)
            self.assertNotIn('syncthing', command)

    def test_brew_rejects_shell_metacharacters(self):
        packages = item(json.dumps({'formulae': [{'name': 'node; touch bad'}], 'casks': []}))
        with patch.object(m, 'run', return_value=item()) as run:
            self.assertEqual(m.apply_updates({'sal-homebrew': packages})['sal-homebrew']['code'], 1)
            self.assertFalse(any('brew upgrade' in call.args[0] for call in run.call_args_list))

    def test_apt_guards_syncthing(self):
        with patch.object(m, 'run', return_value=item()) as run:
            m.apply_updates({'al-apt': item(), 'sam-apt': item()})
            for call in run.call_args_list:
                self.assertIn('dpkg-query -l syncthing', call.args[0])
                self.assertIn('exit 1; fi;', call.args[0])

    def winget_table(self, identifiers):
        return '\n'.join([f"{'Name':20}{'Id':32}{'Version':12}Available", '-' * 80] +
                         [f"{'Package':20}{identifier:32}{'1.0':12}1.1" for identifier in identifiers] +
                         ['2 upgrades available.'])

    def test_winget_excludes_syncthing_and_uses_numeric_status(self):
        table = self.winget_table(['Syncthing.Syncthing', 'Ollama.Ollama'])
        with patch.object(m, 'run', return_value=item('unrelated log EXIT 0', 7)) as run:
            result = m.apply_updates({'hal-winget': item(table)})
            self.assertEqual(run.call_count, 1)
            self.assertIn('--id Ollama.Ollama', run.call_args.args[0])
            self.assertEqual(result['hal-winget']['code'], 1)

    def test_winget_unparseable_table_is_failure(self):
        with patch.object(m, 'run') as run:
            result = m.apply_updates({'hal-winget': item('localized unexpected format')})
            run.assert_not_called()
            self.assertEqual(result['hal-winget']['code'], 1)

    def test_invalid_homebrew_audit_is_reported(self):
        status, record, applied = self.run_main({'sal-homebrew': item('[]')})
        self.assertEqual(status, 1)
        self.assertFalse(applied)
        self.assertIn('sal-homebrew', record['check_failures'])

    def test_macos_label_detection(self):
        self.assertTrue(m.needs_update('sal-macos', item('Software Update found the following new or updated software:\n* Label: macOS Tahoe 26.0')))

    def run_main(self, before, after=None, backup=None):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            audits = [before] + ([after] if after is not None else [])
            with patch.object(m, 'audit', side_effect=audits), patch.object(m, 'make_backup', return_value=backup or item('a' * 40)), patch.object(m, 'apply_updates', return_value={'herald-hermes': item('updated')}) as apply, patch.object(m, 'STATE', root / 'state.json'), patch.object(m, 'REPORT', root / 'report.md'), patch.object(m.sys, 'argv', ['test', '--apply']), patch.object(m, 'run', side_effect=AssertionError('Unmocked command')):
                status = m.main()
                record = json.loads((root / 'state.json').read_text())
                return status, record, apply.called

    def test_empty_or_nonhex_backup_never_authorizes_update(self):
        for backup in (item(''), item('x' * 40), item('a' * 40, 1)):
            with self.subTest(backup=backup):
                status, record, applied = self.run_main({'herald-hermes': item(json.dumps({'update_available': True}))}, backup=backup)
                self.assertEqual(status, 1)
                self.assertFalse(applied)
                self.assertNotEqual(record['check_failures']['github-restore-point']['code'], 0)

    def test_postflight_failure_returns_failure(self):
        status, record, applied = self.run_main({'herald-hermes': item(json.dumps({'update_available': True}))}, {'herald-hermes': item('offline', 255)})
        self.assertTrue(applied)
        self.assertEqual(status, 1)
        self.assertIn('postflight-herald-hermes', record['check_failures'])

    def test_remaining_updates_never_report_complete(self):
        status, record, _ = self.run_main({'herald-hermes': item(json.dumps({'update_available': True}))}, {'herald-hermes': item(json.dumps({'update_available': True}))})
        self.assertEqual(status, 1)
        self.assertIn('updates-remain', record['check_failures'])

    def test_success_and_record_schema(self):
        status, record, applied = self.run_main({'herald-hermes': item(json.dumps({'update_available': True}))}, {'herald-hermes': item(json.dumps({'update_available': False}))})
        self.assertEqual(status, 0)
        self.assertTrue(applied)
        for key in ('generated', 'updates_found', 'sop_policy', 'sop_impact', 'check_failures', 'backup', 'updates', 'after', 'before', 'audit_limits'):
            self.assertIn(key, record)
        self.assertNotIn('none detected', str(record['sop_impact']))


if __name__ == '__main__':
    unittest.main()
