import subprocess
import os
import time
import shutil

repo_url = "https://github.com/karpathy/minGPT"
api_key = os.environ.get("GROQ_API_KEY", "")
if not api_key:
    raise SystemExit("Set GROQ_API_KEY environment variable")

print("Cloning minGPT into /tmp/sage-minGPT...")
temp_dir = "/tmp/sage-minGPT"
shutil.rmtree(temp_dir, ignore_errors=True)
subprocess.run(["git", "clone", "--depth", "1", repo_url, temp_dir], check=True)

print("Copying SAGE agent core into sandbox...")
base_dir = "/Volumes/MacExt/SAGE"
for item in ['agent.yaml', 'RULES.md', 'SOUL.md', 'skills', 'tools', 'src']:
    src = os.path.join(base_dir, item)
    dst = os.path.join(temp_dir, item)
    if os.path.isdir(src):
        shutil.copytree(src, dst)
    elif os.path.exists(src):
        shutil.copy2(src, dst)

env = os.environ.copy()
env["GROQ_API_KEY"] = api_key
env["GIT_SSH_COMMAND"] = "ssh -o StrictHostKeyChecking=no"

print("Starting LiteLLM Universal Proxy for Groq...")
proxy_port = "52345"
litellm_process = subprocess.Popen(
    ["uv", "run", "litellm", "--model", "groq/llama3-70b-8192", "--port", proxy_port],
    env=env,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL
)
time.sleep(3)

env["OPENAI_API_KEY"] = "sk-litellm-bypass"
env["OPENAI_BASE_URL"] = f"http://0.0.0.0:{proxy_port}/v1"

cmd = [
    "npx", "--yes", "gitclaw",
    "--dir", temp_dir,
    "-m", "openai:gpt-4o"
]

print("Starting GitClaw Orchestrator...")
process = subprocess.Popen(
    cmd,
    cwd=temp_dir,
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    env=env,
    bufsize=1
)

prompt_str = "Run scan-codebase to map this project, then hunt and summarize papers, and identify architectural gaps comparing it against latest Arxiv papers. Do not stop until all steps of the pipeline are complete."
try:
    process.stdin.write(prompt_str + "\n\n")
    time.sleep(1.0)
    process.stdin.write("/quit\n")
    process.stdin.flush()
except BrokenPipeError:
    pass

for line in process.stdout:
    print(line, end='', flush=True)

process.wait()
litellm_process.terminate()
print("\nDone!")
