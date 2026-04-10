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

if st.button("Run SAGE Analysis"):
    if not repo_url or "github.com" not in repo_url:
        st.error("Please enter a valid GitHub URL.")
    else:
        st.info("Cloning repository into temporary sandbox...")
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Clone repo
            subprocess.run(["git", "clone", "--depth", "1", repo_url, temp_dir], check=True, capture_output=True)
            
            st.success("Repository cloned successfully!")
            st.info("Starting GitClaw Agent Orchestrator (Using LLaMa-3 via Groq)...")
            
            # Create a scrolling text area for logs
            output_container = st.empty()
            full_log = ""
            
            env = os.environ.copy()
            
            # Force gitclaw non-interactive (passes yes to all tool approvals)
            cmd = [
                "npx", "--yes", "@open-gitagent/gitclaw",
                "--dir", "/app",  # The agent manifest definition is in /app
                "--prompt", "Run scan-codebase to map this project, then hunt and summarize papers, and identify architectural gaps comparing it against latest Arxiv papers.",
                "-m", "openai:llama3-70b-8192"
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
