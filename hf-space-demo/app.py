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
        ["Groq (LLaMa-3 70b)", "Anthropic (Claude-3.5-Sonnet)", "OpenAI (GPT-4o)"]
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
            
            # Subprocess execution using env dict prevents key from being logged in process explorer commands
            env = os.environ.copy()
            model_string = ""
            if "Groq" in model_provider:
                env["GROQ_API_KEY"] = api_key
                model_string = "openai:llama3-70b-8192"
            elif "Anthropic" in model_provider:
                env["ANTHROPIC_API_KEY"] = api_key
                model_string = "anthropic:claude-3-5-sonnet-20241022"
            else:
                env["OPENAI_API_KEY"] = api_key
                model_string = "openai:gpt-4o"
            
            cmd = [
                "npx", "--yes", "gitclaw",
                "--dir", "/app",
                "--prompt", "Run scan-codebase to map this project, then hunt and summarize papers, and identify architectural gaps comparing it against latest Arxiv papers.",
                "-m", model_string
            ]
            
            process = subprocess.Popen(
                cmd,
                cwd=temp_dir,  # Run against the cloned code
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                env=env,
                bufsize=1
            )
            
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
            # Always clean up the sandbox
            shutil.rmtree(temp_dir, ignore_errors=True)
