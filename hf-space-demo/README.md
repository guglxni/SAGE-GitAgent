---
title: SAGE Research Agent
emoji: 🧠
colorFrom: indigo
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
---

# SAGE Web Demo

This Space uses `ttyd` (a FOSS C-library) to stream a native Linux terminal directly to the web browser. 
It securely sandboxes users so they can only run the `demo.sh` script, which executes the `gitclaw` orchestrator against the SAGE agent tools.
