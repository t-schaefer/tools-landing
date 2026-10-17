# Tools landing page – "Thorsten's Tools @ Qvest PLS"

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

## Logos and order

- **Edit list** has ▲ / ▼ to change the order of the cards, a **Logo** choice
  and a **Note** per tool (shown as a yellow hint on the card, e.g. the Neuron
  Audio Router: "Not yet released – confirm with Thorsten before use.").
- Logos live in `logos/`: `<name>.svg|png|jpg|webp`, optionally `<name>-white.*`
  for dark mode. Shipped: `evs` (EVS, from evs.com) and `riedel` (Riedel, from
  riedel.net, with a white version), `premier-league` (premierleague.com, purple
  + white). Drop another file there and it shows up in the choice.
- Neuron Audio Router uses `evs`, the Riedel tools `riedel`. An older `tools.json`
  gets missing logo / note / task / update from `tools.example.json` on the next
  start (by tool name, capitals and spaces ignored - "MNSet" = "MNset"; only where
  the field is missing or the logo empty - your own values stay).

## Christmas

From 1 November to 31 December (by the server's date) the page shows Christmas
decoration: lights along the top, snow, a large banner with a link to Mariah
Carey's "All I Want for Christmas Is You" on YouTube and the Premier League
logo in a Christmas version (Santa hat, snow, lights, holly drawn on top - the
logo file itself is unchanged). Nothing to switch - it
turns on and off by itself. `CHRISTMAS_TEST_UNTIL` in `server.py` shows it
before that up to and including that date (a preview; empty = November and December only).
Snow is off for users who chose "reduce motion".

## Start / Stop / Update from the page

Every card of a tool on this server has a **Service** row with **Start**,
**Stop** and **Update** (each asks first; the output of an update is shown on
the card). They work once the tool's Windows name is set in `tools.json` on the
server - by hand, on purpose not in the page, so a browser can never choose
what runs here. Until then the card says **not set up**.

```json
{ "name": "Neuron Audio Router", "port": 8101, "path": "/", "host": "",
  "task": "NeuronAudioRouterService",
  "update": "../neuron-acp-toolkit/update-windows.ps1" },
{ "name": "MNset", "port": 8080, "path": "/", "host": "",
  "service": "MNsetServiceName" }
```

- `task`: a Scheduled Task name (Task Scheduler, or `schtasks /query`), or
- `service`: a Windows service name (services.msc, the "Service name" field,
  or `sc query state= all`).
- `update` (optional): the tool's update `.ps1`, relative to this folder and
  inside the folder that holds the repos (clone the tools next to each other,
  e.g. `C:\Tools\tools-landing`, `C:\Tools\neuron-acp-toolkit`). Without it,
  Update stays greyed out - vendor tools (MNset, MuoN) update their own way.
- The landing page runs as SYSTEM, so these actions run as SYSTEM. Every action
  is logged in `service.log`. The landing page does not stop or update itself
  (use `Stop-Landing.bat` / `Update-Landing.bat`).
- Pre-set: Neuron Audio Router (task `NeuronAudioRouterService`) and MNset
  (service `MNSet`) - an existing `tools.json` gets them on the next start.
  For Fusion Dashboard and MuoN config, add `task` or `service` in `tools.json` (Notepad as Administrator),
  then the page picks it up within 15 s.

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
