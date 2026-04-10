# SAGE (Search, Analyze, Gap-detect, Explain)
### A Research Intelligence GitAgent

SAGE is a framework-agnostic, git-native AI agent designed to bridge the gap between applied ML/AI engineering and theoretical research. Built on the open **GitAgent** standard, SAGE intelligently scans your local machine learning codebase, pulls structural details using AST graphing, cross-references implementations against cutting-edge academic papers via the arXiv API, and generates localized gap analysis reports.

## What it does
SAGE operates as a sequential, multi-agent automated pipeline directly within your repository:
1. **scan-codebase**: Scans your local Python/ML codebase and extracts structural data (classes, optimizers, layers) using the `gitnexus-query` AST tool.
2. **hunt-papers**: Dynamically constructs arXiv API queries and pulls matching academic papers based on the extracted codebase structure using `arxiv-search`.
3. **summarize-paper**: Synthesizes the dense academic XML results into readable, engineering-focused summaries using `fetch-abstract`.
4. **identify-gaps**: Cross-references the theoretical paper summaries with your exact implementation code, identifying optimization opportunities, out-of-date techniques, or missing components.

## Quick Start (Running Locally)
SAGE requires Python 3.12+ (managed via `uv`) to execute its network and AST tooling efficiently. Because of this powerful native tooling, SAGE runs natively via **gitclaw**, not the browser-based `clawless` environment.

### Prerequisites:
- `node` and `npm` installed
- `uv` installed (Python package manager)
- An active IDE or Terminal

### Execution
1. Clone this repository into your target ML project:
   ```bash
   git clone https://github.com/your-username/SAGE.git ./sage-agent
   ```
2. Navigate to the agent directory and install dependencies:
   ```bash
   cd sage-agent
   uv sync --all-groups
   uv pip install -e .
   ```
3. Run the agent using `gitclaw` (pointing to the root of your project):
   ```bash
   npx gitclaw --dir . --prompt "Analyze my codebase using SAGE and identify architectural gaps."
   ```

## Built With
- **GitAgent Standard**: Fully compliant manifest (`agent.yaml`), identity (`SOUL.md`), and boundary constraint (`RULES.md`) definitions.
- **Gitclaw SDK**: Runtime orchestration orchestrating the step-by-step SAGE assembly pipeline.
- **uv Runtime**: Blazing fast Python environment handling the internal tool execution.
- **GitNexus**: Node-based AST querying to deterministically map code structure.
- **Lyzr AI Hackathon**: Built as a submission for the Lyzr GitAgent Hackathon 2026.

## License
MIT License
