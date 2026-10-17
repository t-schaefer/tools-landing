# Tools landing page

One start page for the web tools running on a server: a card per tool with
an up / down status, links that work from every PC. Standard-library Python
(3.8+), no installs. Runs unattended as a Windows Scheduled Task.

Default tools (`tools.example.json`):

| Tool | Port |
|---|---|
| Neuron Audio Router | 8101 |
| Fusion Dashboard | 8090 |
| MNset | 8080 |
| MuoN config | 8091 |

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

## Start / Stop / Update from the page

A tool with a Windows task name gets **Start** and **Stop** buttons and its
service state, and with an update script also **Update** (each asks first, the
output of an update is shown on the card). Set them in `tools.json` on the
server - on purpose not in the page, so a browser can never choose what runs:

```json
{ "name": "Neuron Audio Router", "port": 8101, "path": "/", "host": "",
  "task": "NeuronAudioRouterService",
  "update": "../neuron-acp-toolkit/update-windows.ps1" }
```

- `task`: the Scheduled Task name (Task Scheduler / `schtasks /query`).
- `update`: path to the tool's update `.ps1`, relative to this folder. It must
  be a `.ps1` inside the folder that holds this repo and its sibling repos
  (clone the tools next to each other, e.g. `C:\Tools\tools-landing`,
  `C:\Tools\neuron-acp-toolkit`).
- The landing page runs as SYSTEM, so these actions run as SYSTEM. Every action
  is logged in `service.log`. The landing page does not stop or update itself
  (use `Stop-Landing.bat` / `Update-Landing.bat`).
- Only the Neuron Audio Router is pre-set. For Fusion Dashboard, MNset and
  MuoN config add their task names (and update scripts) to `tools.json`.
- An already installed page keeps its `tools.json`: add `task` / `update` there by hand.

## Update

Double-click **`Update-Landing.bat`**: stops the task, `git pull` (or the
GitHub zip copied over when git is not installed), starts the task again.
`tools.json` is never touched.

## Other

- `Start-Landing.bat [port]` runs it in a console window for a test (port 8099 by default).
- `Stop-Landing.bat` stops the service (task and any leftover python). It starts again at the next boot, with `Update-Landing.bat`, or `schtasks /run /tn ToolsLandingPage`.
- `uninstall-task-windows.ps1` removes the task and firewall rule (`tools.json` stays).
- `python server.py --port 8099` on any OS.

### Moving from neuron-acp-toolkit\landing

The landing page used to live in `neuron-acp-toolkit\landing`. Installing this
repo replaces the task of the same name, so the old copy is no longer used.
To keep an edited tool list, copy `neuron-acp-toolkit\landing\tools.json` into
this folder before running `Install-Landing.bat`.
