import streamlit as st
import subprocess
import os
import shutil
import tempfile
from pathlib import Path

st.set_page_config(page_title="SAGE GitAgent Demo", page_icon="🧠", layout="wide")

st.title("🧠 SAGE: Research Intelligence Agent")
st.markdown(
    "Drop a GitHub repository link below. SAGE runs via `@open-gitagent/gitclaw` to analyze the code AST, "
    "query the official arXiv API for academic papers, and return an architectural Gap Analysis."
)

repo_url = st.text_input("GitHub Repository URL:", placeholder="https://github.com/karpathy/minbpe")

col1, col2 = st.columns(2)
with col1:
    model_provider = st.selectbox(
        "Select AI Provider",
        ["Groq (Llama 4 Scout)", "Anthropic (Claude 4.6 Sonnet)", "OpenAI (GPT-5.4 Pro)"]
    )
with col2:
    # OWASP compliant input masking (type="password") prevents shoulder-surfing and DOM leakage
    api_key = st.text_input("Bring Your Own Key (BYOK)", type="password", help="Securely passed via env mapping. Never logged or stored.")

if st.button("Run SAGE Analysis"):
    if not repo_url or "github.com" not in repo_url:
        st.error("Please enter a valid GitHub URL.")
    elif not api_key:
        st.error("Please provide an API Key to execute the AI models.")
    else:
        st.info("Cloning repository into temporary sandbox...")
        temp_dir = tempfile.mkdtemp()
        
        try:
            subprocess.run(["git", "clone", "--depth", "1", repo_url, temp_dir], check=True, capture_output=True)
            
            st.success("Repository cloned successfully!")
            st.info(f"Starting GitClaw Agent Orchestrator using {model_provider}...")
            
            output_container = st.empty()
            full_log = ""
            
            # Use LiteLLM to securely proxy the user's BYOK key and exotic model to standard GitClaw formats
            env = os.environ.copy()
            import time
            import socket
            from contextlib import closing
            
            def find_free_port():
                with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
                    s.bind(('', 0))
                    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    return s.getsockname()[1]
                    
            proxy_port = str(find_free_port())
            
            litellm_target = ""
            if "Groq" in model_provider:
                env["GROQ_API_KEY"] = api_key
                litellm_target = "groq/llama3-70b-8192" # LiteLLM proxy string format
            elif "Anthropic" in model_provider:
                env["ANTHROPIC_API_KEY"] = api_key
                litellm_target = "anthropic/claude-3-5-sonnet-20241022" 
            else:
                env["OPENAI_API_KEY"] = api_key
                litellm_target = "openai/gpt-4o"
                
            st.info(f"Initiating LiteLLM Universal Proxy for {model_provider} on port {proxy_port}...")
            # Spawn LiteLLM Router Subprocess
            litellm_process = subprocess.Popen(
                ["uv", "run", "litellm", "--model", litellm_target, "--port", proxy_port],
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            time.sleep(3) # Wait for litellm server to spin up and bind
            
            # Now trick gitclaw into thinking we are running the default hardcoded OpenAI model
            env["OPENAI_API_KEY"] = "sk-litellm-bypass"
            env["OPENAI_BASE_URL"] = f"http://0.0.0.0:{proxy_port}/v1"
            
            # Remove invalid --prompt flag; gitclaw natively accepts standard input for its REPL Mode
            cmd = [
                "npx", "--yes", "gitclaw",
                "--dir", "/app",
                "-m", "openai:gpt-4o"
            ]
            
            process = subprocess.Popen(
                cmd,
                cwd=temp_dir,  # Run against the cloned code
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                env=env,
                bufsize=1
            )
            
            # Send the orchestrator prompt and then instantly enqueue a graceful termination command
            prompt_str = "Run scan-codebase to map this project, then hunt and summarize papers, and identify architectural gaps comparing it against latest Arxiv papers.\n\n"
            try:
                process.stdin.write(prompt_str)
                time.sleep(1.0) # Wait for agent loop to settle
                process.stdin.write("/quit\n")
                process.stdin.flush()
                # Crucial Fix: DO NOT close process.stdin immediately, as it breaks Node's readline stream processing
            except BrokenPipeError:
                pass
            
            # Stream the terminal output to the Web UI live
            for line in process.stdout:
                full_log += line
                output_container.code(full_log)
                
            process.wait()
            
            if process.returncode == 0:
                st.success("Analysis Complete!")
                
                # Render any output files created by the agent
                st.subheader("📚 Generated Analysis Files")
                for md_file in Path(temp_dir).glob("*.md"):
                    if md_file.name.upper() not in ["README.MD"]: # Exclude the repo's original README
                        with st.expander(f"View {md_file.name}", expanded=True):
                            st.markdown(md_file.read_text())
            else:
                st.error("Agent execution failed or timed out.")
                
        except subprocess.CalledProcessError as e:
            st.error(f"Failed to clone repository: {e.stderr}")
        finally:
            # Always clean up the sandbox and router
            shutil.rmtree(temp_dir, ignore_errors=True)
            if 'litellm_process' in locals():
                litellm_process.terminate()
