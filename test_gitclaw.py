import subprocess
import os

env = os.environ.copy()
env['OPENAI_API_KEY'] = 'test-key'

cmd = ["npx", "--yes", "gitclaw", "--dir", ".", "-m", "openai:gpt-4o"]
p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env)
p.stdin.write("Show skills\n")
p.stdin.flush()
p.stdin.close()

for line in p.stdout:
    print(line, end='')

