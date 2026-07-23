# Deployment

This describes how code gets from a `git push` to a running container on
your cloud lab VM.

![Deployment flow](docs_assets/deployment.png)

## Overview

1. You push to `main` (or open a PR) on GitHub.
2. GitHub Actions ([.github/workflows/docker-build-deploy.yml](.github/workflows/docker-build-deploy.yml))
   builds the Docker image. On PRs it only builds (to catch breakage). On
   `main`, it also pushes the image to GitHub Container Registry (GHCR).
3. A **self-hosted runner** registered on your lab VM picks up the deploy
   job, pulls the new image, and restarts the stack with `docker compose`.

GitHub Actions itself never hosts the running app - it only builds/pushes
the image and, via the self-hosted runner, tells your VM to update itself.
The VM (with Docker + Ollama) is what actually serves traffic.

## One-time setup

### 1. Enable GHCR for this repo

No extra setup needed for public images - the workflow's `GITHUB_TOKEN`
already has `packages: write` (granted via the `permissions:` block in the
workflow). If you want the image private, GHCR packages inherit repo
visibility by default; the lab VM's runner will already be authenticated
(see below) so it can still pull it.

Note: GHCR image refs must be lowercase, so the workflow lowercases
`c-halik/AIThreatNotebook` to `ghcr.io/c-halik/aithreatnotebook` when
tagging - keep that in mind if you reference the image path manually.

### 2. Register a self-hosted runner on your lab VM

On your cloud lab VM (needs Docker + Docker Compose installed):

1. In GitHub: repo -> **Settings -> Actions -> Runners -> New self-hosted runner**.
2. Follow the generated `./config.sh` commands on the VM - add the label
   `security-lab` when prompted (or edit the label list), matching
   `runs-on: [self-hosted, security-lab]` in the workflow.
3. Install it as a service so it survives reboots:
   ```bash
   sudo ./svc.sh install
   sudo ./svc.sh start
   ```
4. Nothing else to pre-stage - `actions/checkout` pulls a fresh copy of the
   repo into the runner's work directory on every job.

The runner only makes **outbound** connections to GitHub to poll for jobs -
you don't need to open any inbound ports on the VM for this to work.

### 3. Authenticate the VM's Docker to pull from GHCR (private images only)

Skip this if the package is public. Otherwise, on the VM:

```bash
echo "<a GitHub PAT with read:packages scope>" | docker login ghcr.io -u <your-username> --password-stdin
```

### 4. First run on the VM

The deploy job writes `.env` itself (with
`APP_IMAGE=ghcr.io/c-halik/aithreatnotebook:latest`) before running
`docker compose pull && docker compose up -d`, so there's nothing to
pre-stage. Ollama's model volume (`ollama_data`) persists across deploys, so
models are only pulled once.

## Ongoing workflow

Every push to `main`:
1. Builds and pushes a new image tagged `latest` and with the commit SHA.
2. Deploys automatically by pulling `latest` and running
   `docker compose up -d` on the lab VM.

To roll back, re-run a previous successful workflow run from the Actions
tab, or manually on the VM:
```bash
docker compose pull app@sha256:<digest-of-known-good-build>
docker compose up -d
```

## Running on a Windows VM

Nothing in the app requires Linux - Docker abstracts the container OS away,
and Ollama/Streamlit both run fine on Windows. There are two ways to use a
Windows VM, depending on whether you want the automated GitHub Actions
pipeline above, or just to run the stack directly.

### Prerequisites (either option)

1. Windows 10/11 Pro or Enterprise, or Windows Server, with virtualization
   enabled in the VM's settings (required for WSL2).
2. Install WSL2: open PowerShell as Administrator and run `wsl --install`,
   then reboot.
3. Install [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/)
   and make sure it's using the **WSL2 backend** (Settings -> General ->
   "Use the WSL 2 based engine" - this is the default on current versions).
   Verify with `docker run hello-world` in PowerShell.
4. Install [Git for Windows](https://git-scm.com/download/win) (bundles Git
   Bash - needed below either way you use this VM).
5. In Docker Desktop, go to Settings -> Resources and give it **at least
   8GB of RAM** (see "Resource notes" below for why).
6. Clone the repo:
   ```powershell
   git clone https://github.com/c-halik/AIThreatNotebook.git
   cd AIThreatNotebook\security-chatbot
   ```

### Option A: Just run the stack on the VM (no CI/CD)

```powershell
docker compose up -d --build
docker compose exec app python ingest.py
```

Open `http://localhost:8501` on the VM, or `http://<vm-ip>:8501` from
another machine once you've opened the port (see "Reaching it remotely"
below).

### Option B: Register the VM as the self-hosted runner (full CI/CD)

Same idea as the Linux instructions above, with Windows-specific commands:

1. In GitHub: repo -> **Settings -> Actions -> Runners -> New self-hosted
   runner** -> select **Windows**.
2. Run the generated PowerShell commands on the VM, e.g.:
   ```powershell
   mkdir actions-runner; cd actions-runner
   Invoke-WebRequest -Uri <url-from-github> -OutFile actions-runner-win-x64.zip
   Expand-Archive -Path actions-runner-win-x64.zip -DestinationPath $PWD
   ./config.cmd --url https://github.com/c-halik/AIThreatNotebook --token <token-from-github>
   ```
   When prompted for labels, add `security-lab` - this must match
   `runs-on: [self-hosted, security-lab]` in the workflow.
3. Install it as a Windows service so it survives reboots:
   ```powershell
   ./svc.cmd install
   ./svc.cmd start
   ```
4. **Gotcha specific to Windows:** Docker Desktop only exposes its engine
   to the currently logged-in user (or accounts in the `docker-users`
   group) via a named pipe - a service running as `Local System` typically
   cannot reach it. Fix: open `services.msc`, find "GitHub Actions Runner
   (...)",  right-click -> Properties -> **Log On** tab, and set it to log
   on as your own Windows user account (the same one Docker Desktop runs
   under) instead of Local System. Restart the service after changing this.
5. Make sure Docker Desktop itself starts automatically on login/boot
   (Settings -> General -> "Start Docker Desktop when you log in"), since
   the runner service needs `docker compose` available whenever a deploy
   job lands.
6. Everything else - GHCR auth, `.env` handling, rollback - works exactly
   as described above; `git push` to `main` now deploys to your Windows VM
   the same way it would a Linux one. The workflow's deploy step already
   sets `shell: bash` so its `${VAR}` syntax parses correctly under
   Windows' default PowerShell runner shell - this just requires Git Bash
   (installed above) to be on the runner's `PATH`.

### Reaching it remotely (either option)

Port 8501 needs to be open in two places if you want to reach the app from
outside the VM:
1. **Windows Defender Firewall** on the VM: allow inbound TCP 8501 (New
   inbound rule -> Port -> TCP -> 8501).
2. **Cloud network security group**, if this VM is in Azure/AWS/etc.: add
   an inbound rule allowing TCP 8501 from your IP (avoid opening it to
   `0.0.0.0/0` - this app has no auth in front of it yet, see the README's
   roadmap).

## Resource notes

`llama3:8b` needs meaningfully more than its ~4.7GB of weights to run
comfortably - during local testing, Docker Desktop's default 4GB VM memory
limit caused the model process to be OOM-killed. Size your lab VM (or
Docker's resource limits, if running Docker Desktop anywhere) with **at
least 8GB of RAM** dedicated to the Ollama container, more if you switch to
a larger model. A GPU is optional but makes inference dramatically faster
than CPU-only - see the commented-out `deploy.resources.reservations`
block in `docker-compose.yml` if your VM has an NVIDIA GPU.

Also worth knowing: Docker Desktop on macOS has no GPU/Metal passthrough to
Linux containers, so if you test this stack locally on a Mac, Ollama runs
CPU-only there regardless of the host's Apple Silicon GPU. Your actual Linux
cloud lab VM doesn't have this limitation.

On Windows, an NVIDIA GPU **can** be passed through to Docker Desktop's
WSL2 containers (unlike macOS), but it needs current NVIDIA drivers on the
Windows host (not inside WSL2) plus Docker Desktop's WSL2 engine - once
that's in place, uncomment the same `deploy.resources.reservations` GPU
block in `docker-compose.yml`. Without a GPU, Windows runs Ollama CPU-only,
same as any other host - still fine per the RAM sizing above, just slower.
