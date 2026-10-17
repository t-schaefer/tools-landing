"""
Tools landing page - one start page for the web tools running on this server.

- Standard library only (Python 3.8+), ThreadingHTTPServer, default port 80.
- tools.json (git-ignored, created from tools.example.json on first start):
  [{"name", "description", "port", "path", "host"}]. "host" empty = the same
  host the browser used to open this page, so links work from every PC.
- Every 15 s the service checks each tool with one HTTP GET (2 s timeout) and
  shows up / down. The browser talks only to this service.
- The tool list can be edited in the page (add / change / remove).
- Service control (Windows): a tool with "task" (Scheduled Task name) gets
  Start / Stop buttons, with "update" (path to its update-windows.ps1, relative
  to this folder) an Update button. "task" and "update" are only read from
  tools.json on the server - the page can not set them, so a browser can never
  choose what runs here. Every action is logged in service.log.

    python server.py               # http://<this pc>/
    python server.py --port 8100
"""
import argparse
import json
import logging
import os
import re
import subprocess
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from logging.handlers import RotatingFileHandler
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PAGE_FILE = BASE_DIR / "index.html"
TOOLS_FILE = BASE_DIR / "tools.json"
TOOLS_EXAMPLE_FILE = BASE_DIR / "tools.example.json"
LOGO_DIR = BASE_DIR / "logos"       # <name>.svg/.png, optional <name>-white.* for dark mode
LOGO_FILE_RE = re.compile(r'^[a-z0-9\-]{1,40}\.(svg|png|jpg|jpeg|webp)$')
LOGO_TYPES = {"svg": "image/svg+xml", "png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "webp": "image/webp"}
LOG_FILE = BASE_DIR / "service.log"
CHECK_INTERVAL_SEC = 15
CHECK_TIMEOUT_SEC = 2
HOST_RE = re.compile(r'^[A-Za-z0-9.\-]{0,253}$')
PATH_RE = re.compile(r'^/[\w\-./?=&%#~]*$')
TASK_RE = re.compile(r'^[\w .\-]{1,80}$')
UPDATE_TIMEOUT_SEC = 900
# Christmas decoration on the page: automatic from 1 November to 31 December (server date).
# CHRISTMAS_TEST_UNTIL shows it before that up to and including this date (preview).
CHRISTMAS_TEST_UNTIL = "2026-10-17"
IS_WINDOWS = os.name == "nt"
VERSION = "2026-10-17.4"            # shown in the page footer - bump with every change
STARTED = datetime.now().isoformat(timespec="seconds")
# logo when a tool has none set: first keyword found in its name (case and spaces ignored)
LOGO_BY_NAME = [("neuron", "evs"), ("evs", "evs"), ("mnset", "riedel"), ("mediornet", "riedel"),
                ("muon", "riedel"), ("fusion", "riedel"), ("riedel", "riedel"), ("artist", "riedel"),
                ("bolero", "riedel"), ("premier", "premier-league")]

log = logging.getLogger("landing")
log.setLevel(logging.INFO)
_h = RotatingFileHandler(LOG_FILE, maxBytes=1_000_000, backupCount=2, encoding="utf-8")
_h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
log.addHandler(_h)
log.addHandler(logging.StreamHandler())

_tools_lock = threading.Lock()
STATUS = {}          # tool key -> {"up", "ms", "code", "error", "checked"}
TASKS = {}           # task name -> "Running" / "Ready" / "Disabled" / "not installed" / error text
JOBS = {}            # task name -> {"action", "state", "started", "finished", "output"}
_job_lock = threading.Lock()


def load_tools():
    with _tools_lock:
        if not TOOLS_FILE.exists():
            TOOLS_FILE.write_text(TOOLS_EXAMPLE_FILE.read_text(encoding="utf-8"), encoding="utf-8")
            log.info("created tools.json from tools.example.json")
        return json.loads(TOOLS_FILE.read_text(encoding="utf-8"))


def fill_from_example():
    """A tools.json made by an older version lacks newer fields (logo, note, task,
    update). Copy them from tools.example.json for tools with the same name (case and
    spaces ignored) - only when the field is missing (or the logo empty), never over a
    value set here."""
    if not TOOLS_FILE.exists():
        return
    tools = load_tools()
    norm = lambda n: re.sub(r"[^a-z0-9]", "", str(n or "").lower())     # "MNSet" = "MNset" = "MN set"
    example = {norm(t["name"]): t for t in json.loads(TOOLS_EXAMPLE_FILE.read_text(encoding="utf-8"))}
    changed = []
    for t in tools:
        ex = example.get(norm(t.get("name")))
        if not ex:
            continue
        for f in ("logo", "note", "task", "update"):
            # a missing field is filled; an empty logo too (a card without logo is never wanted)
            if (f not in t or (f == "logo" and not t[f])) and ex.get(f):
                t[f] = ex[f]
                changed.append(f"{t['name']}.{f}")
    if changed:
        save_tools(tools)
        log.info("tools.json: added from tools.example.json: %s", ", ".join(changed))


def save_tools(tools):
    with _tools_lock:
        tmp = TOOLS_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(tools, indent=2) + "\n", encoding="utf-8")
        tmp.replace(TOOLS_FILE)


def logos():
    """Available logos: {name: {"file": ..., "white": ... or None}}"""
    out = {}
    if LOGO_DIR.is_dir():
        files = sorted(p.name for p in LOGO_DIR.iterdir() if LOGO_FILE_RE.match(p.name))
        for f in files:
            base = f.rsplit(".", 1)[0]
            if not base.endswith("-white"):
                out.setdefault(base, {"file": f, "white": None})
        for f in files:
            base = f.rsplit(".", 1)[0]
            if base.endswith("-white") and base[:-6] in out:
                out[base[:-6]]["white"] = f
    return out


def clean_tool(t):
    name = str(t.get("name", "")).strip()
    if not 1 <= len(name) <= 60:
        raise ValueError("name: 1-60 characters")
    port = int(t.get("port") or 0)
    if not 1 <= port <= 65535:
        raise ValueError("port: 1-65535")
    host = str(t.get("host", "") or "").strip()
    if not HOST_RE.match(host):
        raise ValueError("host: name or IP, or empty for this server")
    path = str(t.get("path", "") or "/").strip() or "/"
    if not PATH_RE.match(path):
        raise ValueError("path must start with /")
    logo = str(t.get("logo", "") or "").strip()
    if logo and logo not in logos():
        raise ValueError(f"logo {logo!r} not found in logos/")
    return {"name": name, "description": str(t.get("description", "")).strip()[:200],
            "port": port, "path": path, "host": host, "logo": logo,
            "note": str(t.get("note", "") or "").strip()[:160]}


def merge_server_fields(new_tools, old_tools):
    """task / update are server-only: keep them from the old tools.json entry with the
    same host + port (the page can not set or change them)."""
    old = {(o.get("host") or "", int(o.get("port") or 0)): o for o in old_tools}
    for t in new_tools:
        o = old.get((t["host"], t["port"]), {})
        for f in ("task", "update"):
            if o.get(f):
                t[f] = o[f]
    return new_tools


def guess_logo(name):
    n = re.sub(r"[^a-z0-9]", "", str(name or "").lower())
    return next((logo for kw, logo in LOGO_BY_NAME if kw in n), "")


def public(t):
    """What the browser gets: no script paths, only whether actions exist."""
    out = {k: t.get(k, "") for k in ("name", "description", "port", "path", "host", "logo", "note")}
    if not out["logo"] or out["logo"] not in logos():
        out["logo"] = guess_logo(t.get("name")) if guess_logo(t.get("name")) in logos() else ""
    out["task"] = t.get("task") or ""
    out["can_update"] = bool(t.get("update"))
    return out


def update_script(t):
    """The tool's update script, resolved and checked: an existing *.ps1 inside the
    folder that holds this repo and its sibling repos."""
    rel = t.get("update") or ""
    if not rel:
        raise ValueError(f"{t['name']}: no update script configured in tools.json")
    p = (BASE_DIR / rel).resolve()
    root = BASE_DIR.parent.resolve()
    if p.suffix.lower() != ".ps1" or root not in p.parents or not p.is_file():
        raise ValueError(f"{t['name']}: update script not found or not allowed: {rel}")
    return p


def task_state(task):
    if not IS_WINDOWS:
        return "only on Windows"
    r = subprocess.run(["schtasks", "/query", "/tn", task, "/fo", "csv", "/nh"],
                       capture_output=True, text=True, timeout=15)
    if r.returncode != 0:
        return "not installed"
    cols = [c.strip('"') for c in r.stdout.strip().splitlines()[-1].split('","')]
    return cols[-1] if cols else "?"


def run_action(t, action):
    """start / stop / update one tool's service. Returns the job record."""
    task = t.get("task") or ""
    if not TASK_RE.match(task):
        raise ValueError(f"{t['name']}: no Windows task configured in tools.json")
    if not IS_WINDOWS:
        raise ValueError("service control works only on the Windows server")
    script = update_script(t) if action == "update" else None
    with _job_lock:
        j = JOBS.get(task)
        if j and j["state"] == "running":
            raise ValueError(f"{t['name']}: '{j['action']}' is still running")
        job = {"action": action, "state": "running", "started": datetime.now().isoformat(timespec="seconds"),
               "finished": None, "output": ""}
        JOBS[task] = job
    log.warning("SERVICE %s %s (task %s) requested from the page", action.upper(), t["name"], task)

    def work():
        try:
            if action == "start":
                cmd, timeout = ["schtasks", "/run", "/tn", task], 30
            elif action == "stop":
                cmd, timeout = ["schtasks", "/end", "/tn", task], 30
            else:
                cmd, timeout = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script)], UPDATE_TIMEOUT_SEC
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=str(script.parent) if script else None)
            job["output"] = (r.stdout + r.stderr).strip()[-8000:]
            job["state"] = "done" if r.returncode == 0 else "failed"
        except Exception as e:
            job["output"] += f"\n{e}"
            job["state"] = "failed"
        job["finished"] = datetime.now().isoformat(timespec="seconds")
        TASKS[task] = task_state(task)
        log.warning("SERVICE %s %s: %s", action.upper(), t["name"], job["state"])

    threading.Thread(target=work, daemon=True).start()
    return job


def christmas(today=None):
    today = today or datetime.now().date()
    return today.month in (11, 12) or (bool(CHRISTMAS_TEST_UNTIL) and today.isoformat() <= CHRISTMAS_TEST_UNTIL)


def key(t):
    return f"{t.get('host') or 'localhost'}:{t['port']}{t.get('path') or '/'}"


def check(t):
    url = f"http://{t.get('host') or '127.0.0.1'}:{t['port']}{t.get('path') or '/'}"
    t0 = time.time()
    try:
        with urllib.request.urlopen(url, timeout=CHECK_TIMEOUT_SEC) as r:
            r.read(64)
            code = r.status
        return {"up": True, "code": code, "ms": round((time.time() - t0) * 1000), "error": None}
    except urllib.error.HTTPError as e:            # it answers, just not with 200
        return {"up": True, "code": e.code, "ms": round((time.time() - t0) * 1000), "error": None}
    except Exception as e:
        return {"up": False, "code": None, "ms": None, "error": str(e)[:120]}


def check_loop():
    pool = ThreadPoolExecutor(max_workers=8)
    while True:
        try:
            tools = load_tools()
            for t, res in zip(tools, pool.map(check, tools)):
                STATUS[key(t)] = {**res, "checked": datetime.now().isoformat(timespec="seconds")}
            for t in tools:
                if t.get("task") and TASK_RE.match(t["task"]):
                    try:
                        TASKS[t["task"]] = task_state(t["task"])
                    except Exception as e:
                        TASKS[t["task"]] = f"? ({str(e)[:60]})"
        except Exception as e:
            log.warning("check failed: %s", e)
        time.sleep(CHECK_INTERVAL_SEC)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def _send(self, body, ctype="application/json", code=200):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, obj, code=200):
        self._send(json.dumps(obj).encode(), code=code)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._send(PAGE_FILE.read_bytes(), "text/html; charset=utf-8")
        elif self.path == "/api/tools":
            tools = load_tools()
            self._json({"tools": [{**public(t), "status": STATUS.get(key(t)), "task_state": TASKS.get(t.get("task") or ""),
                                   "job": JOBS.get(t.get("task") or "")} for t in tools],
                        "interval": CHECK_INTERVAL_SEC, "windows": IS_WINDOWS, "logos": logos(),
                        "christmas": christmas(), "server_date": datetime.now().date().isoformat(),
                        "version": VERSION, "started": STARTED})
        elif self.path.startswith("/logos/") and LOGO_FILE_RE.match(self.path[7:]) and (LOGO_DIR / self.path[7:]).is_file():
            body = (LOGO_DIR / self.path[7:]).read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", LOGO_TYPES[self.path.rsplit(".", 1)[1]])
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "max-age=3600")
            self.send_header("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'; sandbox")
            self.end_headers()
            self.wfile.write(body)
        else:
            self._json({"error": "not found"}, 404)

    def do_POST(self):
        try:
            n = int(self.headers.get("Content-Length") or 0)
            if n > 100_000:
                raise ValueError("request too large")
            req = json.loads(self.rfile.read(n) or b"{}")
            if self.path == "/api/tools":
                # the whole list, as edited in the page
                tools = [clean_tool(t) for t in req.get("tools", [])]
                if len(tools) > 50:
                    raise ValueError("at most 50 tools")
                save_tools(merge_server_fields(tools, load_tools()))
                log.info("tool list saved: %s", ", ".join(f"{t['name']}:{t['port']}" for t in tools))
                for t in tools:
                    STATUS[key(t)] = {**check(t), "checked": datetime.now().isoformat(timespec="seconds")}
                self._json({"ok": True})
            elif self.path == "/api/service":
                action = req.get("action")
                if action not in ("start", "stop", "update"):
                    raise ValueError("action must be start, stop or update")
                hit = [t for t in load_tools() if t["name"] == req.get("name")]
                if not hit:
                    raise ValueError("unknown tool")
                self._json(run_action(hit[0], action))
            else:
                self._json({"error": "not found"}, 404)
        except (ValueError, TypeError, json.JSONDecodeError) as e:
            self._json({"error": str(e)}, 400)


class Server(ThreadingHTTPServer):
    request_queue_size = 128
    daemon_threads = True


def main():
    ap = argparse.ArgumentParser(description="Tools landing page")
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--port", type=int, default=80)
    args = ap.parse_args()
    load_tools()
    fill_from_example()
    threading.Thread(target=check_loop, daemon=True).start()
    srv = Server((args.host, args.port), Handler)
    log.info("Tools landing page on http://%s:%d/", args.host, args.port)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
