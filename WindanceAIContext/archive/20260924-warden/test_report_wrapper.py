import json
import sys
import tempfile
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch,Mock
import report_wrapper

class ReportReceiptTests(unittest.TestCase):
    def test_actual_entrypoint_exit_receipt(self):
        for code, status in ((0,'completed'),(7,'failed')):
            with tempfile.TemporaryDirectory() as folder:
                root=Path(folder)
                (root/'report-command.json').write_text(json.dumps({'argv':[sys.executable,'-c',f'raise SystemExit({code})']}))
                with patch.object(report_wrapper,'ROOT',root):
                    self.assertEqual(report_wrapper.main(),code)
                receipts=list((root/'reports').glob('*.json'))
                self.assertEqual(len(receipts),1)
                self.assertEqual(json.loads(receipts[0].read_text())['status'],status)
                self.assertFalse(json.loads(receipts[0].read_text())['delivery_verified'])
    def test_timeout_kills_group_and_marks_unknown(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            (root/'report-command.json').write_text(json.dumps({'argv':['fixture']}))
            process=Mock(pid=1234)
            process.wait.side_effect=[subprocess.TimeoutExpired('fixture',1200),0]
            with patch.object(report_wrapper,'ROOT',root),patch.object(report_wrapper.subprocess,'Popen',return_value=process),patch.object(report_wrapper.os,'killpg') as kill:
                self.assertEqual(report_wrapper.main(),124)
            kill.assert_called_once_with(1234,report_wrapper.signal.SIGKILL)
            receipt=json.loads(next((root/'reports').glob('*.json')).read_text())
            self.assertEqual(receipt['status'],'unknown')

if __name__ == '__main__': unittest.main()
