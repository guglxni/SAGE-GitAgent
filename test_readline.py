import subprocess
import os
import time

env = os.environ.copy()
env['OPENAI_API_KEY'] = 'test-key'
env['OPENAI_BASE_URL'] = 'https://api.openai.com/v1'

cmd = ["npx", "--yes", "gitclaw", "--dir", "/Volumes/MacExt/SAGE", "-m", "openai:gpt-4o"]
p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env)

p.stdin.write("Show skills\n")
p.stdin.flush()
p.stdin.write("/quit\n")
p.stdin.flush()
# WE DO NOT CLOSE STDIN!

for line in p.stdout:
    print(line, end='', flush=True)

p.wait()
