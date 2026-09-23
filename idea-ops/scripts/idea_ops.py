#!/usr/bin/env python3
"""Tiny local idea tracker: one JSON file, no dependencies."""

import argparse
import json
import math
import sys
import webbrowser
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

STATUSES = ("inbox", "exploring", "active", "blocked", "parked", "done", "dropped")
RELATIONS = {
    "related": "related",
    "supports": "supported-by",
    "supported-by": "supports",
    "conflicts": "conflicts",
    "depends-on": "unlocks",
    "unlocks": "depends-on",
    "duplicate-of": "has-duplicate",
    "has-duplicate": "duplicate-of",
    "flows-to": "comes-from",
    "comes-from": "flows-to",
}
PUBLIC_RELATIONS = ("related", "supports", "conflicts", "depends-on", "duplicate-of", "flows-to")
LOG_KINDS = ("step", "progress", "resistance", "blocker", "decision", "lesson")


def now():
    return datetime.now().astimezone().replace(microsecond=0).isoformat()


def is_user_log(log):
    text = str(log.get("text", ""))
    return log.get("source") == "user" or (
        log.get("kind") != "capture"
        and text != "Idea updated"
        and not text.startswith("Updated:")
        and not text.startswith("Linked ")
    )


def normalize_logs(idea):
    logs = idea.setdefault("logs", [])
    used = {log.get("id") for log in logs if log.get("id")}
    for index, log in enumerate(logs, 1):
        if not is_user_log(log):
            continue
        if not log.get("id"):
            base, suffix = f"LOG-legacy-{index}", 2
            log["id"] = base
            while log["id"] in used:
                log["id"] = f"{base}-{suffix}"
                suffix += 1
            used.add(log["id"])
        parents = log.get("after", [])
        log["after"] = list(dict.fromkeys(parents)) if isinstance(parents, list) else []
        position = log.get("position")
        if not isinstance(position, dict) or not all(isinstance(position.get(axis), (int, float)) and math.isfinite(position[axis]) for axis in ("x", "y")):
            log.pop("position", None)


def paths(root):
    folder = Path(root).resolve() / ".ideas"
    return folder, folder / "ideas.json", folder / "DASHBOARD.md"


def load(root, create=False):
    folder, db_path, _ = paths(root)
    if not db_path.exists():
        if not create:
            raise SystemExit(f"Not initialized: {db_path}. Run init first.")
        folder.mkdir(parents=True, exist_ok=True)
        return {"version": 1, "ideas": []}
    try:
        data = json.loads(db_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Cannot read {db_path}: {exc}") from exc
    if data.get("version") != 1 or not isinstance(data.get("ideas"), list):
        raise SystemExit(f"Unsupported or invalid database: {db_path}")
    # Migrate the earlier one-level parent model into general flow edges.
    for idea in data["ideas"]:
        idea.setdefault("relations", [])
        normalize_logs(idea)
    for idea in data["ideas"]:
        parent_id = idea.pop("parent_id", "")
        if parent_id and any(item["id"] == parent_id for item in data["ideas"]):
            parent = find(data, parent_id)
            ensure_relation(parent, "flows-to", idea["id"])
            ensure_relation(idea, "comes-from", parent_id)
    return data


def save(root, data):
    folder, db_path, dashboard_path = paths(root)
    folder.mkdir(parents=True, exist_ok=True)
    tmp = db_path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(db_path)
    dashboard_path.write_text(render_dashboard(data), encoding="utf-8")


def render_dashboard(data):
    ideas = data["ideas"]
    counts = {status: sum(i["status"] == status for i in ideas) for status in STATUSES}
    lines = ["# Idea Dashboard", "", f"Updated: {now()}", "", "## Counts", ""]
    lines.append(" | ".join(f"{key}: {value}" for key, value in counts.items()))
    for status in ("blocked", "active", "exploring", "inbox"):
        items = sorted((i for i in ideas if i["status"] == status), key=lambda i: i["updated_at"], reverse=True)
        lines += ["", f"## {status.title()}", ""]
        if not items:
            lines.append("_None._")
            continue
        for item in items:
            detail = item.get("blocker") or item.get("next_action") or "No next action"
            lines.append(f"- **{item['id']} — {item['title']}**: {detail}")
    return "\n".join(lines) + "\n"


def find(data, idea_id):
    for idea in data["ideas"]:
        if idea["id"] == idea_id:
            return idea
    raise SystemExit(f"Unknown idea: {idea_id}")


def add_log(idea, kind, text, after=None):
    after = list(dict.fromkeys(after or []))
    available = {log["id"] for log in idea["logs"] if is_user_log(log) and log.get("id")}
    if any(log_id not in available for log_id in after):
        raise ValueError("前置记录不存在")
    stamp = datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")
    used = {log.get("id") for log in idea["logs"]}
    log_id, suffix = f"LOG-{stamp}", 2
    while log_id in used:
        log_id, suffix = f"LOG-{stamp}-{suffix}", suffix + 1
    idea["logs"].append({"id": log_id, "at": now(), "kind": kind, "text": text, "source": "user", "after": after})
    idea["updated_at"] = now()


def find_log(idea, log_id):
    for log in idea["logs"]:
        if is_user_log(log) and log.get("id") == log_id:
            return log
    raise ValueError("记录节点不存在")


def log_reaches(idea, start_id, goal_id):
    children = {log["id"]: [] for log in idea["logs"] if is_user_log(log) and log.get("id")}
    for log in idea["logs"]:
        if not is_user_log(log) or not log.get("id"):
            continue
        for parent_id in log.get("after", []):
            if parent_id in children:
                children[parent_id].append(log["id"])
    seen, pending = set(), [start_id]
    while pending:
        current = pending.pop()
        if current == goal_id:
            return True
        if current not in seen:
            seen.add(current)
            pending.extend(children.get(current, []))
    return False


def link_logs(idea, source_id, target_id):
    if source_id == target_id:
        raise ValueError("记录节点不能连接自身")
    find_log(idea, source_id)
    target = find_log(idea, target_id)
    if log_reaches(idea, target_id, source_id):
        raise ValueError("记录连线不能形成循环")
    target.setdefault("after", [])
    if source_id not in target["after"]:
        target["after"].append(source_id)
        idea["updated_at"] = now()
    return idea


def move_log(idea, log_id, x, y):
    try:
        x, y = float(x), float(y)
    except (TypeError, ValueError) as exc:
        raise ValueError("节点位置无效") from exc
    if not math.isfinite(x) or not math.isfinite(y):
        raise ValueError("节点位置无效")
    find_log(idea, log_id)["position"] = {"x": round(x, 1), "y": round(y, 1)}
    idea["updated_at"] = now()
    return idea


def unlink_logs(idea, source_id, target_id):
    find_log(idea, source_id)
    target = find_log(idea, target_id)
    parents = target.setdefault("after", [])
    if source_id not in parents:
        raise ValueError("记录连线不存在")
    parents.remove(source_id)
    idea["updated_at"] = now()
    return idea


def set_log_positions(idea, positions):
    if not isinstance(positions, dict):
        raise ValueError("节点位置无效")
    updates = []
    for log_id, position in positions.items():
        log = find_log(idea, log_id)
        if not isinstance(position, dict) or not all(type(position.get(axis)) in (int, float) and math.isfinite(position[axis]) for axis in ("x", "y")):
            raise ValueError("节点位置无效")
        updates.append((log, {axis: position[axis] for axis in ("x", "y")}))
    for log, position in updates:
        log["position"] = position
    return idea


def delete_log(idea, log_id):
    find_log(idea, log_id)
    idea["logs"] = [log for log in idea["logs"] if log.get("id") != log_id]
    for log in idea["logs"]:
        if is_user_log(log) and log_id in log.get("after", []):
            log["after"] = [parent for parent in log["after"] if parent != log_id]
    idea["updated_at"] = now()
    return idea


def update_log(idea, log_id, kind, text, title=None):
    log = find_log(idea, log_id)
    if kind not in LOG_KINDS or not (title or text).strip():
        raise ValueError("请选择记录类型并填写内容")
    log.update(kind=kind, text=text.strip(), updated_at=now())
    if title is not None:
        log['title'] = str(title).strip()
    idea["updated_at"] = now()
    return idea


def insert_log(idea, source_id, target_id, kind, text, title=None):
    target = find_log(idea, target_id)
    if source_id not in target.get("after", []):
        raise ValueError("记录连线不存在")
    if kind not in LOG_KINDS or not (title or text).strip():
        raise ValueError("请选择记录类型并填写内容")
    add_log(idea, kind, text.strip(), [source_id])
    if title is not None:
        idea['logs'][-1]['title'] = str(title).strip()
    new_id = idea["logs"][-1]["id"]
    target["after"] = [new_id if parent == source_id else parent for parent in target["after"]]
    return idea


def create_idea(data, title, summary="", next_action="", after_id=""):
    stamp = datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")
    base = f"IDEA-{stamp}"
    used = {i["id"] for i in data["ideas"]}
    idea_id, suffix = base, 2
    while idea_id in used:
        idea_id, suffix = f"{base}-{suffix}", suffix + 1
    timestamp = now()
    idea = {
        "id": idea_id,
        "title": title.strip(),
        "summary": summary.strip(),
        "status": "inbox",
        "next_action": next_action.strip(),
        "blocker": "",
        "created_at": timestamp,
        "updated_at": timestamp,
        "relations": [],
        "logs": [],
    }
    if not idea["title"]:
        raise ValueError("标题不能为空")
    data["ideas"].append(idea)
    if after_id:
        link_ideas(data, after_id, "flows-to", idea_id)
    return idea


def update_idea(data, idea, changes):
    extras = {}
    if "priority" in changes:
        if changes["priority"] not in ("", "low", "medium", "high"):
            raise ValueError("无效优先级")
        extras["priority"] = changes["priority"]
    if "tags" in changes:
        if not isinstance(changes["tags"], list) or any(not isinstance(tag, str) for tag in changes["tags"]):
            raise ValueError("标签格式无效")
        extras["tags"] = list(dict.fromkeys(tag.strip().removeprefix("#") for tag in changes["tags"] if tag.strip().removeprefix("#")))
    if "next_steps" in changes:
        if not isinstance(changes["next_steps"], list):
            raise ValueError("下一步格式无效")
        tasks, used = [], set()
        for task in changes["next_steps"]:
            if not isinstance(task, dict) or not isinstance(task.get("id"), str) or not task["id"] or task["id"] in used or not isinstance(task.get("text"), str) or not task["text"].strip() or type(task.get("done")) is not bool:
                raise ValueError("行动内容无效")
            used.add(task["id"])
            due, hours = task.get("due") or "", task.get("hours")
            if due:
                try:
                    if datetime.strptime(due, "%Y-%m-%d").strftime("%Y-%m-%d") != due:
                        raise ValueError()
                except (ValueError, TypeError):
                    raise ValueError("截止日期无效")
            if hours is not None and (type(hours) not in (int, float) or not math.isfinite(hours) or hours < 0):
                raise ValueError("预计用时无效")
            tasks.append({"id": task["id"], "text": task["text"].strip(), "done": task["done"], "owner": str(task.get("owner") or "").strip(), "due": due, "hours": hours})
        extras["next_steps"] = tasks
    if "title" in changes and not str(changes["title"]).strip():
        raise ValueError("标题不能为空")
    status = changes.get("status")
    if status is not None:
        if status not in STATUSES:
            raise ValueError("无效状态")
        if status == "blocked" and not str(changes.get("blocker", idea.get("blocker", ""))).strip():
            raise ValueError("设置为阻塞时必须填写具体阻塞")
        idea["status"] = status
        if status != "blocked" and "blocker" not in changes:
            idea["blocker"] = ""
    if (status or idea.get("status")) == "blocked" and not str(changes.get("blocker", idea.get("blocker", ""))).strip():
        raise ValueError("设置为阻塞时必须填写具体阻塞")
    changed = []
    for key in ("title", "summary", "next_action", "blocker", "project_name"):
        if key in changes:
            value = str(changes[key]).strip()
            if key == "title" and not value:
                raise ValueError("标题不能为空")
            if key == "blocker" and value != idea.get("blocker", ""):
                idea["blocker_updated_at"] = now()
            idea[key] = value
            changed.append(key)
    if status is not None:
        changed.append("status")
    if not changed and not extras:
        raise ValueError("没有可保存的更改")
    idea.update(extras)
    idea["updated_at"] = now()
    return idea


def link_ideas(data, source_id, relation_type, target_id):
    if relation_type not in PUBLIC_RELATIONS:
        raise ValueError("无效关系")
    if source_id == target_id:
        raise ValueError("想法不能关联自身")
    source, target = find(data, source_id), find(data, target_id)
    if relation_type == "flows-to" and reaches(data, target_id, source_id):
        raise ValueError("流程不能形成循环")
    ensure_relation(source, relation_type, target["id"])
    ensure_relation(target, RELATIONS[relation_type], source["id"])
    timestamp = now()
    source["updated_at"] = timestamp
    target["updated_at"] = timestamp
    return source


def reaches(data, start_id, goal_id):
    seen, pending = set(), [start_id]
    while pending:
        current = pending.pop()
        if current == goal_id:
            return True
        if current in seen:
            continue
        seen.add(current)
        pending.extend(r["target"] for r in find(data, current)["relations"] if r["type"] == "flows-to")
    return False


def cmd_init(args):
    data = load(args.root, create=True)
    save(args.root, data)
    print(paths(args.root)[1])


def cmd_capture(args):
    data = load(args.root)
    try:
        idea = create_idea(data, args.title, args.summary, args.next_action, args.after)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    save(args.root, data)
    print(json.dumps(idea, ensure_ascii=False, indent=2))


def cmd_update(args):
    data = load(args.root)
    idea = find(data, args.id)
    changes = {key: getattr(args, key) for key in ("status", "title", "summary", "next_action", "blocker") if getattr(args, key) is not None}
    try:
        update_idea(data, idea, changes)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    save(args.root, data)
    print(json.dumps(idea, ensure_ascii=False, indent=2))


def cmd_log(args):
    data = load(args.root)
    idea = find(data, args.id)
    add_log(idea, args.kind, args.text.strip(), args.after)
    save(args.root, data)
    print(f"Logged {args.kind} on {idea['id']}")


def cmd_link_log(args):
    data = load(args.root)
    idea = link_logs(find(data, args.id), args.source, args.target)
    save(args.root, data)
    print(f"Linked {args.source} -> {args.target} on {idea['id']}")


def cmd_move_log(args):
    data = load(args.root)
    idea = move_log(find(data, args.id), args.log, args.x, args.y)
    save(args.root, data)
    print(f"Moved {args.log} on {idea['id']}")


def cmd_unlink_log(args):
    data = load(args.root)
    idea = unlink_logs(find(data, args.id), args.source, args.target)
    save(args.root, data)
    print(f"Unlinked {args.source} -> {args.target} on {idea['id']}")


def cmd_delete_log(args):
    data = load(args.root)
    idea = delete_log(find(data, args.id), args.log)
    save(args.root, data)
    print(f"Deleted {args.log} on {idea['id']}")


def ensure_relation(idea, relation_type, target):
    relation = {"type": relation_type, "target": target}
    if relation not in idea["relations"]:
        idea["relations"].append(relation)


def cmd_link(args):
    data = load(args.root)
    try:
        source = link_ideas(data, args.source, args.type, args.target)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    save(args.root, data)
    print(f"{source['id']} --{args.type}--> {args.target}")


def cmd_show(args):
    data = load(args.root)
    print(json.dumps(find(data, args.id), ensure_ascii=False, indent=2))


def cmd_list(args):
    data = load(args.root)
    ideas = data["ideas"]
    if args.status:
        ideas = [i for i in ideas if i["status"] == args.status]
    if args.query:
        query = args.query.casefold()
        ideas = [i for i in ideas if query in (i["title"] + " " + i["summary"]).casefold()]
    for idea in sorted(ideas, key=lambda i: i["updated_at"], reverse=True):
        detail = idea.get("blocker") or idea.get("next_action") or "-"
        print(f"{idea['id']}\t{idea['status']}\t{idea['title']}\t{detail}")


def make_handler(root, asset):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            return

        def reply(self, status, payload):
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def body(self):
            if self.headers.get_content_type() != "application/json":
                raise ValueError("请求必须使用 application/json")
            length = int(self.headers.get("Content-Length", "0"))
            return json.loads(self.rfile.read(length) or b"{}")

        def do_GET(self):
            path = urlparse(self.path).path
            if path == "/":
                body = asset.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(body)
            elif path in ("/vendor/drawflow.min.js", "/vendor/drawflow.min.css", "/offline-inbox.js", "/offline-bridge.js"):
                file = asset.parent / path.removeprefix("/")
                body = file.read_bytes()
                content_type = "text/javascript" if path.endswith(".js") else "text/css"
                self.send_response(200)
                self.send_header("Content-Type", f"{content_type}; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(body)
            elif path == "/api/ideas":
                self.reply(200, load(root))
            else:
                self.reply(404, {"error": "未找到"})

        def mutate(self):
            path = unquote(urlparse(self.path).path)
            payload = self.body()
            data = load(root)
            if path == "/api/capture":
                result = create_idea(data, payload.get("title", ""), payload.get("summary", ""), payload.get("next_action", ""), payload.get("after_id", ""))
            elif path.startswith("/api/ideas/") and path.endswith("/log-position"):
                idea_id = path[len("/api/ideas/"):-len("/log-position")]
                result = move_log(find(data, idea_id), str(payload.get("log", "")), payload.get("x"), payload.get("y"))
            elif path.startswith("/api/ideas/") and path.endswith("/log-positions"):
                idea_id = path[len("/api/ideas/"):-len("/log-positions")]
                result = set_log_positions(find(data, idea_id), payload.get("positions"))
            elif path.startswith("/api/ideas/") and path.endswith("/log-link"):
                idea_id = path[len("/api/ideas/"):-len("/log-link")]
                result = link_logs(find(data, idea_id), str(payload.get("source", "")), str(payload.get("target", "")))
            elif path.startswith("/api/ideas/") and path.endswith("/log-unlink"):
                idea_id = path[len("/api/ideas/"):-len("/log-unlink")]
                result = unlink_logs(find(data, idea_id), str(payload.get("source", "")), str(payload.get("target", "")))
            elif path.startswith("/api/ideas/") and path.endswith("/log-delete"):
                idea_id = path[len("/api/ideas/"):-len("/log-delete")]
                result = delete_log(find(data, idea_id), str(payload.get("log", "")))
            elif path.startswith("/api/ideas/") and path.endswith("/log-insert"):
                idea_id = path[len("/api/ideas/"):-len("/log-insert")]
                result = insert_log(find(data, idea_id), str(payload.get("source", "")), str(payload.get("target", "")), payload.get("kind"), str(payload.get("text", "")), payload.get("title"))
            elif path.startswith("/api/ideas/") and path.endswith("/log-update"):
                idea_id = path[len("/api/ideas/"):-len("/log-update")]
                result = update_log(find(data, idea_id), str(payload.get("log", "")), payload.get("kind"), str(payload.get("text", "")), payload.get("title"))
            elif path.startswith("/api/ideas/") and path.endswith("/log"):
                idea_id = path[len("/api/ideas/"):-len("/log")]
                result = find(data, idea_id)
                kind, text = payload.get("kind"), str(payload.get("text", "")).strip()
                if kind not in LOG_KINDS or not str(payload.get("title") or text).strip():
                    raise ValueError("请选择记录类型并填写内容")
                after = payload.get("after", [])
                if not isinstance(after, list):
                    raise ValueError("前置记录必须是列表")
                add_log(result, kind, text, after)
                if "title" in payload:
                    result["logs"][-1]["title"] = str(payload["title"]).strip()
            elif path.startswith("/api/ideas/"):
                result = update_idea(data, find(data, path[len("/api/ideas/"):]), payload)
            elif path == "/api/link":
                result = link_ideas(data, payload.get("source", ""), payload.get("type", ""), payload.get("target", ""))
            else:
                self.reply(404, {"error": "未找到"})
                return
            save(root, data)
            self.reply(200, result)

        def do_POST(self):
            try:
                self.mutate()
            except (ValueError, json.JSONDecodeError, SystemExit) as exc:
                self.reply(400, {"error": str(exc)})

        def do_PATCH(self):
            self.do_POST()

    return Handler


def cmd_serve(args):
    data = load(args.root, create=True)
    save(args.root, data)
    asset = Path(__file__).resolve().parent.parent / "assets" / "index.html"
    server = HTTPServer(("127.0.0.1", args.port), make_handler(args.root, asset))
    url = f"http://127.0.0.1:{server.server_port}/"
    print(url, flush=True)
    if not args.no_open:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def cmd_offline(args):
    data = load(args.root)
    assets = Path(__file__).resolve().parent.parent / "assets"
    package = {"workspace": str(Path(args.root).resolve()), "data": data}
    # Encode as a JSON string, so user text is never executable JavaScript.
    literal = json.dumps(json.dumps(package, ensure_ascii=False), ensure_ascii=True)
    target = assets / "offline-inbox.js"
    tmp = target.with_suffix(".js.tmp")
    tmp.write_text("window.IDEA_OPS_INBOX = JSON.parse(" + literal + ");\n", encoding="utf-8")
    tmp.replace(target)
    url = (assets / "index.html").as_uri()
    print(url)
    if not args.no_open:
        webbrowser.open(url)


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", default=".", help="Workspace root; defaults to current directory")
    commands = p.add_subparsers(dest="command", required=True)
    init = commands.add_parser("init")
    init.set_defaults(func=cmd_init)
    capture = commands.add_parser("capture")
    capture.add_argument("--title", required=True)
    capture.add_argument("--summary", default="")
    capture.add_argument("--next-action", default="")
    capture.add_argument("--after", default="", help="Previous step ID; omit to create a new flow root")
    capture.set_defaults(func=cmd_capture)
    update = commands.add_parser("update")
    update.add_argument("id")
    update.add_argument("--status", choices=STATUSES)
    update.add_argument("--title")
    update.add_argument("--summary")
    update.add_argument("--next-action")
    update.add_argument("--blocker")
    update.set_defaults(func=cmd_update)
    log = commands.add_parser("log")
    log.add_argument("id")
    log.add_argument("--kind", required=True, choices=LOG_KINDS)
    log.add_argument("--text", required=True)
    log.add_argument("--after", action="append", default=[], help="Previous log ID; repeat to converge branches")
    log.set_defaults(func=cmd_log)
    log_link = commands.add_parser("link-log")
    log_link.add_argument("id")
    log_link.add_argument("source")
    log_link.add_argument("target")
    log_link.set_defaults(func=cmd_link_log)
    move = commands.add_parser("move-log")
    move.add_argument("id")
    move.add_argument("log")
    move.add_argument("x", type=float)
    move.add_argument("y", type=float)
    move.set_defaults(func=cmd_move_log)
    unlink = commands.add_parser("unlink-log")
    unlink.add_argument("id")
    unlink.add_argument("source")
    unlink.add_argument("target")
    unlink.set_defaults(func=cmd_unlink_log)
    delete = commands.add_parser("delete-log")
    delete.add_argument("id")
    delete.add_argument("log")
    delete.set_defaults(func=cmd_delete_log)
    link = commands.add_parser("link")
    link.add_argument("source")
    link.add_argument("type", choices=PUBLIC_RELATIONS)
    link.add_argument("target")
    link.set_defaults(func=cmd_link)
    show = commands.add_parser("show")
    show.add_argument("id")
    show.set_defaults(func=cmd_show)
    listing = commands.add_parser("list")
    listing.add_argument("--status", choices=STATUSES)
    listing.add_argument("--query")
    listing.set_defaults(func=cmd_list)
    serve = commands.add_parser("serve")
    serve.add_argument("--port", type=int, default=0, help="Port; defaults to an available port")
    serve.add_argument("--no-open", action="store_true")
    serve.set_defaults(func=cmd_serve)
    offline = commands.add_parser("offline", help="Prepare local-file handoff and open the existing offline page; no server")
    offline.add_argument("--no-open", action="store_true")
    offline.set_defaults(func=cmd_offline)
    return p


if __name__ == "__main__":
    try:
        args = parser().parse_args()
        args.func(args)
    except ValueError as exc:
        print(exc, file=sys.stderr)
        sys.exit(1)
    except BrokenPipeError:
        sys.exit(0)
