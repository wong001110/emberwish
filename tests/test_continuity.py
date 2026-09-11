import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import subprocess
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('continuity',ROOT/'tools/continuity.py')
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
class ContinuityTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        base=self.root/'.agent-continuity';(base/'plans').mkdir(parents=True);(base/'evidence').mkdir()
        shutil.copy2(ROOT/'.agent-continuity/plans/mvp.json',base/'plans/mvp.json')
        shutil.copy2(ROOT/'.agent-continuity/sources.json',base/'sources.json')
        (self.root/'code.ts').write_text('source-v1')
        self.store=mod.Store(self.root);self.store.bootstrap()
    def tearDown(self):self.tmp.cleanup()
    def evidence(self,cid='C-ENV-01'):
        a=self.root/'.agent-continuity/evidence/test.txt';a.write_text('actual command output')
        self.store.record([cid],self.store.checks[cid]['evidence_kind'],a,0,'fixture command')
    def test_scope_coverage(self):self.assertGreater(self.store.capture()['checks'],20)
    def test_new_store_resumes_same_pending_ids(self):
        before=self.store.incomplete(self.store.load());after=mod.Store(self.root).incomplete(self.store.load());self.assertEqual(before,after)
    def test_missing_checks_cannot_pass(self):self.assertFalse(self.store.gate()['passed'])
    def test_current_evidence_only_satisfies_its_check(self):
        self.evidence();remaining=self.store.incomplete(self.store.load());self.assertNotIn('C-ENV-01',[x['check'] for x in remaining]);self.assertGreater(len(remaining),0)
    def test_later_source_change_stales_evidence(self):
        self.evidence();(self.root/'code.ts').write_text('source-v2');self.assertIn({'check':'C-ENV-01','reason':'stale workspace evidence'},self.store.incomplete(self.store.load()))
    def test_modified_artifact_rejected(self):
        self.evidence();(self.root/'.agent-continuity/evidence/test.txt').write_text('fabricated');self.assertIn({'check':'C-ENV-01','reason':'modified evidence'},self.store.incomplete(self.store.load()))
    def test_missing_state_fails_closed(self):
        self.store.state_path.unlink();self.assertRaises(RuntimeError,self.store.load)
    def test_unknown_extra_check_requires_reconciliation(self):
        data=self.store.load();data['checks']['invented']={'status':'passed'};self.assertRaises(RuntimeError,self.store.incomplete,data)
    def test_scope_drift_requires_reasoned_reconciliation(self):
        p=self.store.manifest_path;p.write_text(p.read_text()+' ');new=mod.Store(self.root);self.assertRaises(RuntimeError,new.incomplete,new.load());new.reconcile('explicit fixture scope reconciliation');self.assertGreater(len(new.incomplete(new.load())),0)
    def test_unmapped_finding_blocks_capture(self):
        self.store.sources['sources'].append({'id':'FND-X','disposition':'unmapped'});self.assertRaises(RuntimeError,self.store.capture)
    def test_false_done_does_not_make_gate_pass(self):
        d=self.store.load();d['status']='DONE';self.store.save(d,'TEST','false done');self.assertFalse(self.store.gate()['passed'])
    def test_failed_gate_is_durable(self):
        self.store.gate();self.assertIn('GATE_FAILED',(self.root/'.agent-continuity/events.jsonl').read_text());self.assertFalse(self.store.load()['last_gate']['passed'])
    def test_existing_writer_refused(self):
        with self.store.lock():
            with self.assertRaises(RuntimeError):
                with self.store.lock():pass
    def test_state_prose_never_executed(self):
        d=self.store.load();d['next_action']='touch SHOULD_NOT_EXIST';self.store.save(d,'TEST','untrusted prose');self.store.incomplete(self.store.load());self.assertFalse((self.root/'SHOULD_NOT_EXIST').exists())
    def test_wrong_evidence_kind_rejected(self):
        a=self.root/'.agent-continuity/evidence/a';a.write_text('x');self.assertRaises(RuntimeError,self.store.record,['C-ENV-03'],'browser',a,0,'x')
    def test_actual_fresh_process_resumes_without_chat(self):
        (self.root/'tools').mkdir()
        shutil.copy2(ROOT/'tools/continuity.py',self.root/'tools/continuity.py')
        result=subprocess.run([sys.executable,str(self.root/'tools/continuity.py'),'resume'],cwd=self.root,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(json.loads(result.stdout)['incomplete'],self.store.incomplete(self.store.load()))
    def test_generated_directory_does_not_change_source_identity(self):
        before=mod.fingerprint(self.root)
        (self.root/'target').mkdir();(self.root/'target/huge-binary').write_bytes(b'generated')
        self.assertEqual(before,mod.fingerprint(self.root))
    def test_missing_published_fingerprint_does_not_pass_resume(self):
        (self.root/'tools').mkdir();shutil.copy2(ROOT/'tools/continuity.py',self.root/'tools/continuity.py')
        d=self.store.load();d['expected_fingerprint']='wrong-workspace';self.store.save(d,'TEST','drift fixture')
        result=subprocess.run([sys.executable,str(self.root/'tools/continuity.py'),'resume'],cwd=self.root,capture_output=True,text=True)
        self.assertNotEqual(result.returncode,0)
if __name__=='__main__':unittest.main()
