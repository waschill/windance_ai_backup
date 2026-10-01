import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

class RecipientTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.pin = self.home / '.config/windance-recipients/shawn-email.json'
        self.pin.parent.mkdir(parents=True)
        self.pin.write_text(json.dumps({'recipient': '+12025550123'}))
        self.flows = self.home / 'flows.json'
        self.flows.write_text(json.dumps([{'id': 'wr_brief_format', 'func': 'msg.recipient = "+12025550124";'},
                                          {'id': 'wr_train_format', 'func': 'return msg;'}]))
        ns = {'FLOWS_FILE': self.flows}
        exec((Path(__file__).parent / 'recipient_function.py').read_text(), ns)
        self.resolve = ns['shawn_recipient']
        self.patch = patch('pathlib.Path.home', return_value=self.home)
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def test_uses_pin_when_old_training_field_removed(self):
        self.assertEqual(self.resolve(), '+12025550123')

    def test_missing_pin_does_not_fall_back(self):
        self.pin.unlink()
        with self.assertRaisesRegex(RuntimeError, 'delivery withheld'):
            self.resolve()

    def test_william_pin_rejected_without_disclosing_number(self):
        self.pin.write_text(json.dumps({'recipient': '+1 (202) 555-0124'}))
        with self.assertRaises(RuntimeError) as caught:
            self.resolve()
        self.assertNotIn('555', str(caught.exception))

    def test_invalid_pin_types_and_values_rejected(self):
        for value in (None, 123, '', 'unexpected@example.invalid', '1234', '+12025550123;bad'):
            with self.subTest(value=value):
                self.pin.write_text(json.dumps({'recipient': value}))
                with self.assertRaises(RuntimeError): self.resolve()

    def test_missing_owner_separation_evidence_rejected(self):
        self.flows.write_text('[]')
        with self.assertRaises(RuntimeError): self.resolve()

    def test_upstream_formatting_recipient_cannot_override_pin(self):
        nodes = json.loads(self.flows.read_text())
        nodes[1]['func'] = 'msg.recipient = "+12025550199";'
        self.flows.write_text(json.dumps(nodes))
        self.assertEqual(self.resolve(), '+12025550123')

if __name__ == '__main__': unittest.main(verbosity=2)
