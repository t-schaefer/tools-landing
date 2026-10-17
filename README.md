# Tools landing page

One start page for the web tools running on a server: a card per tool with
an up / down status, links that work from every PC. Standard-library Python
(3.8+), no installs. Runs unattended as a Windows Scheduled Task.

Default tools (`tools.example.json`):

| Tool | Port |
|---|---|
| Neuron Audio Router | 8101 |
| Fusion Dashboard | 8100 (check) |
| MNset | 8080 |
| MuoN config | 8090 |

## Install on the Windows server (once)

```bat
git clone https://github.com/t-schaefer/tools-landing.git
```

Then double-click **`Install-Landing.bat`** (asks for admin rights). It
registers the task `ToolsLandingPage` (SYSTEM, at boot, restarts on failure),
opens the port in the firewall and starts it. Port 80 by default; another
port: `Install-Landing.bat 8080`. If the port is already taken it stops and
says by which program.

Open `http://<server>/` and use **Edit list** to add, change or remove tools.
The list is stored in `tools.json` (git-ignored, created from
`tools.example.json` on the first start). Host empty = the server the page was
opened from.

Without git: download https://github.com/t-schaefer/tools-landing/archive/refs/heads/main.zip,
unpack it and run `Install-Landing.bat` from there.

## Update

Double-click **`Update-Landing.bat`**: stops the task, `git pull` (or the
GitHub zip copied over when git is not installed), starts the task again.
`tools.json` is never touched.

## Other

- `Start-Landing.bat [port]` runs it in a console window for a test (port 8099 by default).
- `uninstall-task-windows.ps1` removes the task and firewall rule (`tools.json` stays).
- `python server.py --port 8099` on any OS.

### Moving from neuron-acp-toolkit\landing

The landing page used to live in `neuron-acp-toolkit\landing`. Installing this
repo replaces the task of the same name, so the old copy is no longer used.
To keep an edited tool list, copy `neuron-acp-toolkit\landing\tools.json` into
this folder before running `Install-Landing.bat`.
