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

Hidden by default: press **🔧 Engineering** (top right) to show them and
**Edit list**; a yellow bar shows the mode is on. It is not remembered - a
reload or new visitor starts without it.

In engineering mode every card of a tool on this server has a **Service** row with **Start**,
**Stop** and (where the tool has an update script) **Update**. Each asks first;
the output is shown on the card. They work once the tool is set up in
`tools.json` on the server - by hand, on purpose not in the page, so a browser
can never choose what runs here. Until then the card says **not set up**.

| Field | Meaning |
|---|---|
| `task` | Scheduled Task name - Start/Stop use it directly, the state comes from it |
| `service` | Windows service name instead (services.msc → "Service name") |
| `start` / `stop` | optional: the tool's own `.ps1` (what its Start/Stop .bat runs) - used instead of the task |
| `update` | the tool's `update-windows.ps1` - shows the Update button |
| `controls` | `false` = no Service row on that card (e.g. MNset) |

Script paths are relative to this folder and must be a `.ps1` inside the folder
that holds the tools. **Clone everything into `C:\Apps`** like the Fusion
Dashboard:

```
C:\Apps\tools-landing
C:\Apps\neuron-acp-toolkit
C:\Apps\Fusion Dashboard\RiedelFusionDashboard
C:\Apps\RiedelMuoNConfig
```

Pre-set (an existing `tools.json` gets these on the next start):

| Tool | Unit | Stop | Update |
|---|---|---|---|
| Neuron Audio Router | task `NeuronAudioRouterService` | `stop-windows.ps1` | `update-windows.ps1` |
| Fusion Dashboard | task `PLSFusionDashboardService` | `stop-windows.ps1` | `update-windows.ps1` |
| MNset | – no Service row (`"controls": false`) | | |
| MuoN config | task `MuoNConfigToolService` | task | `update-windows.ps1` |

Start uses the task / service directly: Fusion's `start-windows.ps1` would run
the dashboard in a console window when the task is missing, which hangs in the
background. The landing page runs as SYSTEM, so all actions run as SYSTEM and
are logged in `service.log`. It does not stop or update itself (use
`Stop-Landing.bat` / `Update-Landing.bat`).

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
