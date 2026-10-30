#!/usr/bin/env python3
"""Host mock tests for the init wrapper only; no GPIO/ARM execution."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1] / 'layers/meta-yocto-lab/recipes-core/lab-gpio-autostart/files/lab-gpio-init'

class InitTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.env = dict(os.environ, MOCK_ROOT=str(self.root), PATH=str(self.root)+':'+os.environ['PATH'])
        # Mock device nodes and /run remain entirely inside the temporary directory.
        text = SOURCE.read_text().replace('/usr/bin/lab_gpio_test', str(self.root/'app'))
        text = text.replace('/run/lab-gpio', str(self.root/'run')).replace('[ -c "$node" ]', '[ -e "$MOCK_ROOT${node}" ]')
        (self.root/'init').write_text(text)
        (self.root/'state').write_text('stopped')
        for name, body in {
            'modprobe': '#!/bin/sh\necho modprobe >> "$MOCK_ROOT/calls"\nexit "${MODFAIL:-0}"\n',
            'sleep': '#!/bin/sh\necho sleep >> "$MOCK_ROOT/calls"\n',
            'app': '''#!/usr/bin/env python3
import os
from pathlib import Path
import sys
r=Path(os.environ['MOCK_ROOT']); cmd=sys.argv[-1]
with (r/'calls').open('a') as f: f.write(cmd+'\\n')
s=(r/'state').read_text()
if cmd in ('start','stop'):
    (r/'state').write_text('running' if cmd=='start' else 'stopped')
else:
    nodes=['/dev/lab_gpio-lab-gpio']+['/dev/lab_gpio-lab-gpio-d'+str(i) for i in range(1,8)]
    if s=='missing': nodes.pop()
    if s=='duplicate': nodes[-1]=nodes[0]
    for i,n in enumerate(nodes):
        state=('stopped' if i==7 else 'running') if s=='partial' else ('running' if s in ('missing','duplicate') else s)
        print(n+': Toggle controller '+state+'.')
'''
        }.items():
            p=self.root/name; p.write_text(body); p.chmod(0o755)
        (self.root/'dev').mkdir()
        for suffix in ['']+['-d'+str(n) for n in range(1,8)]:
            (self.root/('dev/lab_gpio-lab-gpio'+suffix)).touch()

    def tearDown(self): self.tmp.cleanup()
    def run_init(self, action):
        return subprocess.run(['sh',str(self.root/'init'),action],env=self.env,capture_output=True,text=True)
    def calls(self): return (self.root/'calls').read_text().splitlines()
    def test_status(self):
        for state, code in [('running',0),('stopped',3),('partial',3),('missing',3),('duplicate',3)]:
            (self.root/'state').write_text(state)
            self.assertEqual(self.run_init('status').returncode,code,state)
    def test_start_idempotent_stop_restart(self):
        self.assertEqual(self.run_init('start').returncode,0)
        self.assertEqual(self.run_init('start').returncode,0)
        self.assertEqual(self.calls().count('start'),1)
        self.assertEqual(self.run_init('restart').returncode,0)
        self.assertEqual(self.calls().count('start'),2)
        self.assertEqual(self.run_init('stop').returncode,0)
        self.assertEqual((self.root/'state').read_text(),'stopped')
    def test_partial_refuses_start(self):
        (self.root/'state').write_text('partial')
        self.assertNotEqual(self.run_init('start').returncode,0)
        self.assertNotIn('start',self.calls())
    def test_timeout(self):
        (self.root/'dev/lab_gpio-lab-gpio-d7').unlink()
        self.assertNotEqual(self.run_init('start').returncode,0)
        self.assertEqual(self.calls().count('sleep'),50)
        self.assertNotIn('start',self.calls())
    def test_modprobe_failure(self):
        self.env['MODFAIL']='1'
        self.assertNotEqual(self.run_init('start').returncode,0)
        self.assertEqual(self.calls(),['modprobe'])
    def test_operation_lock(self):
        (self.root/'run/init.lock').mkdir(parents=True)
        self.assertNotEqual(self.run_init('start').returncode,0)
        self.assertFalse((self.root/'calls').exists())

if __name__=='__main__': unittest.main(verbosity=2)
