import subprocess
import os
import time

env = os.environ.copy()

api_key = open("/Volumes/MacExt/SAGE/.tmp_test_key").read().strip()
if not api_key:
    raise ValueError("Missing GROQ_API_KEY environment variable")
env["GROQ_API_KEY"] = api_key
litellm_target = "groq/llama3-70b-8192"
proxy_port = "52345"

print("Starting Litellm proxy...")
litellm_process = subprocess.Popen(
    ["uv", "run", "litellm", "--model", litellm_target, "--port", proxy_port],
    env=env,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL
)
time.sleep(3)

env["OPENAI_API_KEY"] = "sk-litellm-bypass"
env["OPENAI_BASE_URL"] = f"http://0.0.0.0:{proxy_port}/v1"

cmd = [
    "npx", "--yes", "gitclaw",
    "--dir", "/Volumes/MacExt/SAGE/.test-repo", # Run on SSH-free sandbox directory
    "-m", "openai:gpt-4o"
]

print("Starting gitclaw...")
process = subprocess.Popen(
    cmd,
    cwd="/Volumes/MacExt/SAGE",
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    env=env,
    bufsize=1
)

prompt_str = "Run scan-codebase to map this project, then hunt and summarize papers, and identify architectural gaps comparing it against latest Arxiv papers.\n\n"
try:
    process.stdin.write(prompt_str)
    time.sleep(1.0)
    process.stdin.write("/quit\n")
    process.stdin.flush()
except BrokenPipeError:
    pass

for line in process.stdout:
    print(line, end='', flush=True)

process.wait()
litellm_process.terminate()
print("Done!")
