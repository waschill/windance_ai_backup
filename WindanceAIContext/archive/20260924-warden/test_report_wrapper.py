import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import report_wrapper

class ReportReceiptTests(unittest.TestCase):
    def test_actual_entrypoint_exit_receipt(self):
        for code, status in ((0,'delivered'),(7,'failed')):
            with tempfile.TemporaryDirectory() as folder:
                root=Path(folder)
                (root/'report-command.json').write_text(json.dumps({'argv':[sys.executable,'-c',f'raise SystemExit({code})']}))
                with patch.object(report_wrapper,'ROOT',root):
                    self.assertEqual(report_wrapper.main(),code)
                receipts=list((root/'reports').glob('*.json'))
                self.assertEqual(len(receipts),1)
                self.assertEqual(json.loads(receipts[0].read_text())['status'],status)

if __name__ == '__main__': unittest.main()
