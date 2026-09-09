import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import refresh_context_index as updater

spec=importlib.util.spec_from_file_location('indexer',updater.SERVICE/'second_brain.py')
indexer=importlib.util.module_from_spec(spec);spec.loader.exec_module(indexer)

class Tests(unittest.TestCase):
    def test_refresh_preserves_unrelated_and_rolls_back_failed_document(self):
        with tempfile.TemporaryDirectory() as folder:
            base=Path(folder);source=base/'context';source.mkdir()
            file=source/'record.md';file.write_text('Original documented decision')
            unrelated=base/'unrelated.md';unrelated.write_text('Keep this unrelated business record')
            conn=indexer.connect(base/'test.sqlite')
            with patch.object(indexer,'embed',side_effect=lambda texts:[[1.0,0.0] for _ in texts]):
                indexer.upsert_file(conn,base,unrelated,True);conn.commit()
                first=updater.refresh(indexer,conn,source,base)
                self.assertEqual(first['changed_files'],1)
                self.assertEqual(updater.refresh(indexer,conn,source,base)['changed_files'],0)
                before=dict(conn.execute('SELECT * FROM source_files WHERE path=?',(str(file),)).fetchone())
                file.write_text('Changed decision needing refreshed embedding')
                with patch.object(indexer,'embed',side_effect=RuntimeError('Simulated embedding failure')):
                    with self.assertRaises(RuntimeError): updater.refresh(indexer,conn,source,base)
                after=dict(conn.execute('SELECT * FROM source_files WHERE path=?',(str(file),)).fetchone())
                self.assertEqual(before,after)
                self.assertEqual(updater.refresh(indexer,conn,source,base)['changed_files'],1)
                row=conn.execute('SELECT deleted_at FROM source_files WHERE path=?',(str(unrelated),)).fetchone()
                self.assertIsNone(row['deleted_at'])
            conn.close()

if __name__=='__main__': unittest.main()
