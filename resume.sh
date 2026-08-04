#!/bin/bash
# Bring the stack back up after the VM (or just Docker) has been stopped and
# started again. Safe to run any time - it's a no-op for anything already
# running, and does NOT re-download images or Ollama models if they're
# already present in their persisted volumes.
#
# Why this is needed: in docker-compose.yml, `app` has
# `restart: unless-stopped` so it comes back on its own when Docker starts,
# but `ollama` has no restart policy, so it will NOT come back on its own
# after a VM reboot. Running `docker compose up -d` again reconciles this
# without rebuilding or re-pulling anything already in place.
set -e
cd "$(dirname "$0")"

echo "Bringing up the stack..."
sudo docker compose up -d

echo
echo "Container status:"
sudo docker compose ps

echo
echo "App should be reachable at http://localhost:8501 once containers show healthy/running."
echo "If viewing this remotely (e.g. an Azure lab VM with no public port open), reconnect with:"
echo "  ssh -i <path-to-key> -L 8501:localhost:8501 <username>@<vm-public-ip>"
echo "then open http://localhost:8501 locally (or via Cloud Shell's Web Preview on port 8501)."
