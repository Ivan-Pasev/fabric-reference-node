#!/usr/bin/env python3
from __future__ import annotations
import os, subprocess, sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
env=dict(os.environ); env['PYTHONPATH']=str(root/'src') + (os.pathsep + env['PYTHONPATH'] if env.get('PYTHONPATH') else '')
cmds=[
    [sys.executable,'-m','unittest','discover','-s',str(root/'tests'),'-v'],
    [sys.executable,str(root/'scripts'/'validate_schemas.py')],
    [sys.executable,str(root/'examples'/'governed_decision.py')],
]
for cmd in cmds:
    print('+',' '.join(cmd))
    subprocess.run(cmd,cwd=root,env=env,check=True)
print('PASS: public genesis verification complete')
