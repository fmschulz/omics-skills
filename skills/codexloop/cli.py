from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
import textwrap
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PACKAGE_ROOT = Path(__file__).resolve().parent
SCHEMA_PATH = PACKAGE_ROOT / "planner-output.schema.json"

STATE_DIR = ".codexloop"
CONFIG_PATH = Path(STATE_DIR) / "config.json"
TASKS_DIR = Path(STATE_DIR) / "tasks"
RUNS_DIR = Path(STATE_DIR) / "runs"
WORKTREES_DIR = Path(STATE_DIR) / "worktrees"
DOCTOR_PATH = Path(STATE_DIR) / "doctor.sh"
PLANS_DIR = Path("docs/plans")
ACTIVE_PLANS_DIR = PLANS_DIR / "active"
COMPLETED_PLANS_DIR = PLANS_DIR / "completed"
PLAN_INPUT_PATH = PLANS_DIR / "implementation-plan.md"
AGENT_PROMPT_PATH = PLANS_DIR / "CODEXLOOP_AGENT.md"
MEMORY_PATH = Path("MEMORY.md")


class CodexLoopError(RuntimeError):
    """User-facing codexloop error."""


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def default_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "task"


def format_task_id(raw: Any, fallback_index: int) -> str:
    if isinstance(raw, int):
        return f"{raw:03d}"
    text = str(raw).strip()
    match = re.search(r"(\d+)", text)
    if match:
        return f"{int(match.group(1)):03d}"
    return f"{fallback_index:03d}"


def dedupe_strings(values: list[Any]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value).strip()
        if not text or text in seen:
            continue
        out.append(text)
        seen.add(text)
    return out


def parse_json_file(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise CodexLoopError(f"Missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise CodexLoopError(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise CodexLoopError(f"Expected a JSON object in {path}")
    return data


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_command(
    args: list[str],
    *,
    cwd: Path,
    capture: bool = True,
    check: bool = True,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        args,
        cwd=str(cwd),
        env=env,
        text=True,
        capture_output=capture,
        check=False,
    )
    if check and result.returncode != 0:
        stderr = result.stderr.strip()
        stdout = result.stdout.strip()
        details = stderr or stdout or f"exit code {result.returncode}"
        raise CodexLoopError(f"Command failed: {' '.join(shlex.quote(arg) for arg in args)}\n{details}")
    return result


def run_shell_command(
    command: str,
    *,
    cwd: Path,
    log_path: Path | None = None,
    env: dict[str, str] | None = None,
) -> tuple[bool, str]:
    result = subprocess.run(
        command,
        cwd=str(cwd),
        env=env,
        shell=True,
        text=True,
        capture_output=True,
        check=False,
    )
    output = ""
    if result.stdout:
        output += result.stdout
    if result.stderr:
        output += result.stderr
    if log_path is not None:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(output, encoding="utf-8")
    return result.returncode == 0, output


def ensure_git_root(path: Path) -> Path:
    result = run_command(["git", "rev-parse", "--show-toplevel"], cwd=path)
    return Path(result.stdout.strip()).resolve()


def current_branch(repo_root: Path) -> str:
    result = run_command(["git", "branch", "--show-current"], cwd=repo_root)
    branch = result.stdout.strip()
    return branch or "main"


def git_head(repo_root: Path) -> str:
    result = run_command(["git", "rev-parse", "HEAD"], cwd=repo_root)
    return result.stdout.strip()


def branch_exists(repo_root: Path, branch: str) -> bool:
    result = run_command(
        ["git", "show-ref", "--verify", "--quiet", f"refs/heads/{branch}"],
        cwd=repo_root,
        capture=True,
        check=False,
    )
    return result.returncode == 0


def git_status_porcelain(repo_root: Path) -> str:
    return run_command(["git", "status", "--porcelain"], cwd=repo_root).stdout


def safe_relpath(path: Path, repo_root: Path) -> str:
    try:
        return str(path.relative_to(repo_root))
    except ValueError:
        return str(path)


def truncate_text(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 17].rstrip() + "\n...[truncated]"


def default_config(repo_root: Path) -> dict[str, Any]:
    return {
        "version": 1,
        "project": repo_root.name,
        "base_branch": current_branch(repo_root),
        "integration_branch_prefix": "codexloop/run/",
        "task_branch_prefix": "codexloop/task/",
        "doctor_command": f"./{DOCTOR_PATH.as_posix()}",
        "bootstrap_commands": [],
        "planner_model": None,
        "worker_model": None,
        "max_attempts_per_task": 5,
        "codex_bin": os.environ.get("CODEXLOOP_CODEX_BIN", "codex"),
        "sandbox": "workspace-write",
        "agent_prompt_path": AGENT_PROMPT_PATH.as_posix(),
        "memory_path": MEMORY_PATH.as_posix(),
    }


def load_config(repo_root: Path) -> dict[str, Any]:
    return parse_json_file(repo_root / CONFIG_PATH)


def ensure_runtime_layout(repo_root: Path) -> None:
    for relative in (
        TASKS_DIR,
        RUNS_DIR,
        WORKTREES_DIR,
        PLANS_DIR,
        ACTIVE_PLANS_DIR,
        COMPLETED_PLANS_DIR,
    ):
        (repo_root / relative).mkdir(parents=True, exist_ok=True)


def init_repo(repo_root: Path, *, force: bool = False) -> None:
    ensure_runtime_layout(repo_root)

    config_path = repo_root / CONFIG_PATH
    if config_path.exists() and not force:
        raise CodexLoopError(f"{config_path} already exists. Use --force to overwrite it.")
    write_json(config_path, default_config(repo_root))

    doctor_path = repo_root / DOCTOR_PATH
    doctor_path.write_text(
        textwrap.dedent(
            """\
            #!/usr/bin/env bash
            set -euo pipefail

            # Replace this with repo-specific validation.
            exit 0
            """
        ),
        encoding="utf-8",
    )
    doctor_path.chmod(0o755)

    plan_path = repo_root / PLAN_INPUT_PATH
    if force or not plan_path.exists():
        plan_path.write_text(
            textwrap.dedent(
                """\
                # Implementation Plan

                Describe the feature or change here.

                ## Constraints

                - Keep tasks independently verifiable.
                - Name specific files, commands, and acceptance criteria whenever you can.
                """
            ),
            encoding="utf-8",
        )

    agent_prompt_path = repo_root / AGENT_PROMPT_PATH
    if force or not agent_prompt_path.exists():
        agent_prompt_path.write_text(
            textwrap.dedent(
                """\
                # CodexLoop Agent Prompt

                You are the CodexLoop implementation agent.

                Operating rules:
                - Treat `docs/plans/` as the source of truth for intent and progress.
                - Read `MEMORY.md` before repeating an approach that already failed.
                - Stay inside the current task boundary. Do not start unrelated work.
                - Fix failing verification instead of stopping at diagnosis.
                - Do not create commits, branches, or pull requests; the harness owns git orchestration.
                """
            ),
            encoding="utf-8",
        )

    memory_path = repo_root / MEMORY_PATH
    if force or not memory_path.exists():
        memory_path.write_text(
            textwrap.dedent(
                """\
                # MEMORY

                This file records failures that mattered and how they were resolved, so future Codex turns can avoid repeating the same mistakes.
                """
            ),
            encoding="utf-8",
        )

    gitignore_path = repo_root / STATE_DIR / ".gitignore"
    gitignore_path.write_text(
        textwrap.dedent(
            """\
            runs/
            worktrees/
            """
        ),
        encoding="utf-8",
    )


def build_planner_prompt(repo_root: Path, config: dict[str, Any], plan_text: str) -> str:
    return textwrap.dedent(
        f"""\
        You are the planning phase of codexloop.

        Produce a compact implementation backlog for the repository at:
        - repo_root: {repo_root}
        - base_branch: {config["base_branch"]}
        - doctor_command: {config["doctor_command"]}

        Requirements:
        - Break the work into tasks that are usually 15-60 minutes each.
        - Use real repository paths whenever you can infer them by inspecting the repo.
        - Keep dependencies explicit and minimal.
        - Put concrete shell verification commands in `verification`.
        - Prefer narrow, surgical tasks over broad refactors.
        - Assume the execution harness will keep an active plan in `docs/plans/active/` and a reusable `MEMORY.md`.
        - Return JSON only matching the provided schema.

        Implementation plan:
        <implementation-plan>
        {plan_text}
        </implementation-plan>
        """
    )


def normalize_tasks(raw_payload: dict[str, Any]) -> list[dict[str, Any]]:
    raw_tasks = raw_payload.get("tasks")
    if not isinstance(raw_tasks, list) or not raw_tasks:
        raise CodexLoopError("Planner returned no tasks.")

    tasks: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for index, raw in enumerate(raw_tasks, start=1):
        if not isinstance(raw, dict):
            raise CodexLoopError("Planner returned a non-object task entry.")
        task_id = format_task_id(raw.get("id"), index)
        if task_id in seen_ids:
            raise CodexLoopError(f"Planner returned duplicate task id: {task_id}")
        title = str(raw.get("title") or raw.get("name") or raw.get("summary") or f"Task {task_id}").strip()
        slug = slugify(str(raw.get("slug") or raw.get("name") or title))
        dependencies = [format_task_id(dep, index) for dep in raw.get("dependencies", [])]
        task = {
            "id": task_id,
            "slug": slug,
            "title": title,
            "summary": str(raw.get("summary") or raw.get("description") or title).strip(),
            "dependencies": dedupe_strings(dependencies),
            "files_to_edit": dedupe_strings(list(raw.get("files_to_edit", []))),
            "acceptance_criteria": dedupe_strings(list(raw.get("acceptance_criteria", []))),
            "verification": dedupe_strings(list(raw.get("verification", []))),
            "implementation_notes": dedupe_strings(list(raw.get("implementation_notes", []))),
        }
        seen_ids.add(task_id)
        tasks.append(task)

    known_ids = {task["id"] for task in tasks}
    for task in tasks:
        unknown = [dep for dep in task["dependencies"] if dep not in known_ids]
        if unknown:
            raise CodexLoopError(
                f"Task {task['id']} references unknown dependencies: {', '.join(unknown)}"
            )

    return sorted(tasks, key=lambda item: item["id"])


def render_task_markdown(task: dict[str, Any]) -> str:
    def section(title: str, values: list[str]) -> str:
        if not values:
            return f"## {title}\n\n- None\n"
        lines = "\n".join(f"- {value}" for value in values)
        return f"## {title}\n\n{lines}\n"

    return textwrap.dedent(
        f"""\
        # {task["id"]} {task["title"]}

        **Slug**: `{task["slug"]}`

        **Summary**: {task["summary"]}

        {section("Dependencies", task["dependencies"])}
        {section("Files", task["files_to_edit"])}
        {section("Acceptance Criteria", task["acceptance_criteria"])}
        {section("Verification", task["verification"])}
        {section("Implementation Notes", task["implementation_notes"])}
        """
    ).strip() + "\n"


def save_tasks(repo_root: Path, tasks: list[dict[str, Any]], source_plan: Path) -> Path:
    tasks_root = repo_root / TASKS_DIR
    tasks_root.mkdir(parents=True, exist_ok=True)
    backlog_path = tasks_root / "backlog.json"
    backlog_payload = {
        "generated_at": now_iso(),
        "source_plan": safe_relpath(source_plan, repo_root),
        "tasks": tasks,
    }
    write_json(backlog_path, backlog_payload)

    for task in tasks:
        stem = f"{task['id']}-{task['slug']}"
        write_json(tasks_root / f"{stem}.json", task)
        (tasks_root / f"{stem}.md").write_text(render_task_markdown(task), encoding="utf-8")

    return backlog_path


def load_backlog(repo_root: Path, backlog_path: Path | None = None) -> tuple[Path, list[dict[str, Any]]]:
    path = backlog_path or repo_root / TASKS_DIR / "backlog.json"
    payload = parse_json_file(path)
    tasks = payload.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        raise CodexLoopError(f"No tasks found in {path}")
    normalized = normalize_tasks({"tasks": tasks})
    return path, normalized


def build_codex_base_command(config: dict[str, Any]) -> list[str]:
    sandbox = str(config.get("sandbox") or "workspace-write")
    codex_bin = str(config.get("codex_bin") or "codex")
    return [codex_bin, "-a", "never", "-s", sandbox]


def read_context_path(repo_root: Path, relative_path: str | Path, *, limit: int = 12000) -> str:
    path = repo_root / Path(relative_path)
    if not path.exists():
        return ""
    return truncate_text(path.read_text(encoding="utf-8"), limit)


def stream_codex(
    *,
    config: dict[str, Any],
    cwd: Path,
    prompt: str,
    last_message_path: Path,
    event_log_path: Path,
    model: str | None = None,
    session_id: str | None = None,
    output_schema: Path | None = None,
    ephemeral: bool = False,
) -> tuple[int, str | None]:
    last_message_path.parent.mkdir(parents=True, exist_ok=True)
    event_log_path.parent.mkdir(parents=True, exist_ok=True)

    if session_id:
        cmd = build_codex_base_command(config) + ["exec", "resume"]
        if model:
            cmd.extend(["-m", model])
        if ephemeral:
            cmd.append("--ephemeral")
        cmd.extend(["--json", "-o", str(last_message_path), session_id, "-"])
    else:
        cmd = build_codex_base_command(config) + ["exec"]
        if model:
            cmd.extend(["-m", model])
        if ephemeral:
            cmd.append("--ephemeral")
        if output_schema is not None:
            cmd.extend(["--output-schema", str(output_schema)])
        cmd.extend(["--json", "-o", str(last_message_path), "-"])

    proc = subprocess.Popen(
        cmd,
        cwd=str(cwd),
        text=True,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    if proc.stdin is None or proc.stdout is None:
        raise CodexLoopError("Failed to start codex subprocess.")

    discovered_session_id = session_id
    with event_log_path.open("w", encoding="utf-8") as event_log:
        proc.stdin.write(prompt)
        proc.stdin.close()
        for line in proc.stdout:
            event_log.write(line)
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if payload.get("type") == "thread.started" and payload.get("thread_id"):
                discovered_session_id = str(payload["thread_id"])

    return_code = proc.wait()
    return return_code, discovered_session_id


def read_optional_text(path: Path) -> str | None:
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8").strip() or None


def build_worker_prompt(
    task: dict[str, Any],
    *,
    resume: bool,
    last_failure: dict[str, Any] | None,
    plan_context: str,
    memory_context: str,
    agent_context: str,
) -> str:
    failure_block = ""
    if last_failure:
        failure_block = (
            "\nPrevious stop reason:\n"
            f"{json.dumps(last_failure, indent=2, sort_keys=True)}\n"
        )

    opener = "Continue this task from the current worktree state." if resume else "Implement this task."

    task_json = json.dumps(task, indent=2, sort_keys=True)
    return textwrap.dedent(
        f"""\
        {opener}

        Agent instructions:
        <agent-context>
        {agent_context or "No additional agent context."}
        </agent-context>

        Active plan and progress:
        <plan-context>
        {plan_context or "No active plan context available yet."}
        </plan-context>

        Failure memory:
        <memory-context>
        {memory_context or "No prior memory recorded."}
        </memory-context>

        Task spec:
        ```json
        {task_json}
        ```
        {failure_block}
        Operating rules:
        - Work only inside this repository and this git worktree.
        - Read relevant files before editing; stay surgical.
        - Do not create commits, branches, tags, or pull requests.
        - Run the listed verification commands yourself before finishing.
        - If verification fails, fix the code instead of stopping at diagnosis.
        - End with a short summary of changed files and any remaining risk.
        """
    )


def ensure_worktree_for_branch(
    repo_root: Path,
    *,
    branch: str,
    worktree: Path,
    start_point: str | None = None,
) -> None:
    worktree.parent.mkdir(parents=True, exist_ok=True)
    if worktree.exists():
        return
    args = ["git", "worktree", "add"]
    if branch_exists(repo_root, branch):
        args.extend([str(worktree), branch])
    else:
        if start_point is None:
            raise CodexLoopError(f"Need a start point to create branch {branch}")
        args.extend(["-b", branch, str(worktree), start_point])
    run_command(args, cwd=repo_root)


def verify_commands_for_task(task: dict[str, Any], config: dict[str, Any]) -> list[str]:
    commands = dedupe_strings(list(task.get("verification", [])))
    doctor = str(config.get("doctor_command") or "").strip()
    if doctor and doctor not in commands:
        commands.append(doctor)
    return commands


def maybe_commit_task(task_worktree: Path, task: dict[str, Any], task_state: dict[str, Any]) -> None:
    status = git_status_porcelain(task_worktree)
    if status.strip():
        run_command(["git", "add", "-A"], cwd=task_worktree)
        message = f"codexloop({task['id']}): {task['title']}"
        run_command(["git", "commit", "-m", message], cwd=task_worktree)
    head_sha = git_head(task_worktree)
    if head_sha == task_state["start_sha"]:
        raise CodexLoopError(
            f"Task {task['id']} completed without any repository changes to merge."
        )
    task_state["head_sha"] = head_sha


def merge_task_into_integration(integration_worktree: Path, branch: str) -> str:
    run_command(["git", "merge", "--ff-only", branch], cwd=integration_worktree)
    return git_head(integration_worktree)


def latest_run_state_path(repo_root: Path) -> Path:
    run_root = repo_root / RUNS_DIR
    if not run_root.exists():
        raise CodexLoopError(f"No runs found under {run_root}")
    candidates = sorted(
        [path / "run.json" for path in run_root.iterdir() if path.is_dir() and (path / "run.json").exists()]
    )
    if not candidates:
        raise CodexLoopError(f"No runs found under {run_root}")
    return candidates[-1]


def render_plan_status(run_state: dict[str, Any]) -> str:
    status = "completed" if all(
        run_state["tasks"][task_id]["status"] == "merged" for task_id in run_state["order"]
    ) else "active"
    lines = [
        f"# CodexLoop Plan {run_state['run_id']}",
        "",
        f"- Status: {status}",
        f"- Base branch: `{run_state['base_branch']}`",
        f"- Integration branch: `{run_state['integration_branch']}`",
        f"- Updated: {run_state['updated_at']}",
        "",
        "## Task Board",
        "",
    ]

    for task_id in run_state["order"]:
        task = run_state["tasks"][task_id]
        checkbox = "x" if task["status"] == "merged" else " "
        lines.append(f"- [{checkbox}] {task_id} {task['title']}")
        lines.append(f"  - Status: `{task['status']}`")
        lines.append(f"  - Summary: {task['summary']}")
        dependencies = ", ".join(task["dependencies"]) if task["dependencies"] else "none"
        lines.append(f"  - Dependencies: {dependencies}")
        if task.get("session_id"):
            lines.append(f"  - Session: `{task['session_id']}`")
        if task.get("last_failure"):
            failure = task["last_failure"]
            lines.append(f"  - Last failure: `{failure.get('kind', 'unknown')}`")
        if task.get("verification"):
            lines.append(f"  - Verification: {', '.join(task['verification'])}")
        lines.append("")

    lines.extend(["## Progress Log", ""])
    for entry in run_state.get("plan_log", []):
        lines.append(f"- {entry}")

    return "\n".join(lines).rstrip() + "\n"


def sync_plan_documents(run_state: dict[str, Any]) -> None:
    repo_root = Path(run_state["repo_root"])
    active_path = Path(run_state["active_plan_doc"])
    completed_path = Path(run_state["completed_plan_doc"])
    content = render_plan_status(run_state)
    active_path.parent.mkdir(parents=True, exist_ok=True)
    completed_path.parent.mkdir(parents=True, exist_ok=True)

    all_done = all(run_state["tasks"][task_id]["status"] == "merged" for task_id in run_state["order"])
    if all_done:
        completed_path.write_text(content, encoding="utf-8")
        if active_path.exists():
            active_path.unlink()
    else:
        active_path.write_text(content, encoding="utf-8")


def load_run_state(repo_root: Path, run_id: str | None = None) -> tuple[Path, dict[str, Any]]:
    path = repo_root / RUNS_DIR / run_id / "run.json" if run_id else latest_run_state_path(repo_root)
    return path, parse_json_file(path)


def save_run_state(path: Path, payload: dict[str, Any]) -> None:
    payload["updated_at"] = now_iso()
    write_json(path, payload)
    sync_plan_documents(payload)


def task_artifact_paths(run_dir: Path, task: dict[str, Any]) -> dict[str, Path]:
    task_dir = run_dir / "tasks" / task["id"]
    return {
        "dir": task_dir,
        "event_log": task_dir / "codex-events.jsonl",
        "last_message": task_dir / "last-message.txt",
    }


def create_run_state(
    repo_root: Path,
    *,
    config: dict[str, Any],
    tasks: list[dict[str, Any]],
    backlog_path: Path,
    run_id: str,
) -> tuple[Path, dict[str, Any]]:
    run_dir = repo_root / RUNS_DIR / run_id
    if run_dir.exists():
        raise CodexLoopError(f"Run already exists: {run_dir}")
    run_dir.mkdir(parents=True)

    integration_branch = f"{config['integration_branch_prefix']}{run_id}"
    integration_worktree = repo_root / WORKTREES_DIR / run_id / "integration"
    if branch_exists(repo_root, integration_branch):
        raise CodexLoopError(f"Integration branch already exists: {integration_branch}")

    ensure_worktree_for_branch(
        repo_root,
        branch=integration_branch,
        worktree=integration_worktree,
        start_point=str(config["base_branch"]),
    )
    integration_head = git_head(integration_worktree)

    task_states: dict[str, dict[str, Any]] = {}
    for task in tasks:
        task_branch = f"{config['task_branch_prefix']}{run_id}/{task['id']}-{task['slug']}"
        task_worktree = repo_root / WORKTREES_DIR / run_id / f"{task['id']}-{task['slug']}"
        artifacts = task_artifact_paths(run_dir, task)
        task_states[task["id"]] = {
            "id": task["id"],
            "title": task["title"],
            "slug": task["slug"],
            "summary": task["summary"],
            "dependencies": task["dependencies"],
            "verification": task["verification"],
            "branch": task_branch,
            "worktree": str(task_worktree),
            "status": "pending",
            "session_id": None,
            "attempts": 0,
            "start_sha": None,
            "head_sha": None,
            "integration_head_after_merge": None,
            "last_failure": None,
            "failure_history": [],
            "memory_recorded": False,
            "bootstrap_completed": False,
            "artifacts_dir": str(artifacts["dir"]),
            "event_log": str(artifacts["event_log"]),
            "last_message": str(artifacts["last_message"]),
            "verification_logs": [],
        }

    state = {
        "run_id": run_id,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "repo_root": str(repo_root),
        "plan_path": str(backlog_path),
        "base_branch": str(config["base_branch"]),
        "integration_branch": integration_branch,
        "integration_worktree": str(integration_worktree),
        "integration_head": integration_head,
        "active_plan_doc": str(repo_root / ACTIVE_PLANS_DIR / f"{run_id}.md"),
        "completed_plan_doc": str(repo_root / COMPLETED_PLANS_DIR / f"{run_id}.md"),
        "plan_log": [f"{now_iso()} created run {run_id} from {config['base_branch']}"],
        "tasks": task_states,
        "order": [task["id"] for task in tasks],
    }
    state_path = run_dir / "run.json"
    save_run_state(state_path, state)
    return state_path, state


def log_plan_event(run_state: dict[str, Any], message: str) -> None:
    run_state.setdefault("plan_log", []).append(f"{now_iso()} {message}")


def record_failure(task_state: dict[str, Any], failure: dict[str, Any]) -> None:
    history = task_state.setdefault("failure_history", [])
    history.append(failure)
    task_state["last_failure"] = failure


def append_memory_entry(
    repo_root: Path,
    *,
    config: dict[str, Any],
    task: dict[str, Any],
    task_state: dict[str, Any],
) -> None:
    if task_state.get("memory_recorded"):
        return
    failures = task_state.get("failure_history") or []
    if not failures:
        return

    memory_path = repo_root / Path(str(config.get("memory_path") or MEMORY_PATH.as_posix()))
    memory_path.parent.mkdir(parents=True, exist_ok=True)
    summary = task_state.get("last_response") or "Resolved after iterative retries."

    lines = [
        "",
        f"## {now_iso()} {task['id']} {task['title']}",
        "",
        "### What failed",
    ]
    for failure in failures:
        description = failure.get("command") or failure.get("kind") or "unknown"
        output = truncate_text(str(failure.get("output") or ""), 1000).strip()
        lines.append(f"- {description}")
        if output:
            lines.append("")
            lines.append("```text")
            lines.append(output)
            lines.append("```")
    lines.extend(
        [
            "",
            "### How it was solved",
            summary,
        ]
    )
    with memory_path.open("a", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")
    task_state["memory_recorded"] = True


def bootstrap_task(
    *,
    task_worktree: Path,
    task_state: dict[str, Any],
    config: dict[str, Any],
    run_dir: Path,
) -> None:
    if task_state.get("bootstrap_completed"):
        return
    commands = dedupe_strings(list(config.get("bootstrap_commands", [])))
    for index, command in enumerate(commands, start=1):
        log_path = run_dir / "tasks" / task_state["id"] / f"bootstrap-{index:02d}.log"
        ok, output = run_shell_command(command, cwd=task_worktree, log_path=log_path)
        if not ok:
            task_state["status"] = "failed"
            task_state["last_failure"] = {
                "kind": "bootstrap",
                "command": command,
                "log_path": str(log_path),
                "output": output[-4000:],
            }
            raise CodexLoopError(f"Bootstrap failed for task {task_state['id']}: {command}")
    task_state["bootstrap_completed"] = True


def run_verification(
    *,
    task: dict[str, Any],
    task_worktree: Path,
    task_state: dict[str, Any],
    config: dict[str, Any],
    run_dir: Path,
) -> tuple[bool, dict[str, Any] | None]:
    verification_logs: list[str] = []
    for index, command in enumerate(verify_commands_for_task(task, config), start=1):
        log_path = run_dir / "tasks" / task["id"] / f"verify-{index:02d}.log"
        ok, output = run_shell_command(command, cwd=task_worktree, log_path=log_path)
        verification_logs.append(str(log_path))
        task_state["verification_logs"] = verification_logs
        if not ok:
            return False, {
                "kind": "verification",
                "command": command,
                "log_path": str(log_path),
                "output": output[-4000:],
            }
    return True, None


def execute_task(
    *,
    repo_root: Path,
    config: dict[str, Any],
    run_state: dict[str, Any],
    run_state_path: Path,
    task: dict[str, Any],
    force_resume: bool = False,
) -> bool:
    run_dir = run_state_path.parent
    task_state = run_state["tasks"][task["id"]]
    integration_worktree = Path(run_state["integration_worktree"])
    task_worktree = Path(task_state["worktree"])

    if task_state["status"] == "merged":
        return True

    ensure_worktree_for_branch(
        repo_root,
        branch=task_state["branch"],
        worktree=task_worktree,
        start_point=run_state["integration_branch"],
    )
    if task_state["start_sha"] is None:
        task_state["start_sha"] = git_head(task_worktree)

    bootstrap_task(
        task_worktree=task_worktree,
        task_state=task_state,
        config=config,
        run_dir=run_dir,
    )
    max_attempts = int(config.get("max_attempts_per_task") or 5)
    if force_resume and task_state["status"] == "needs_resume":
        max_attempts = int(task_state["attempts"]) + max_attempts

    while int(task_state["attempts"]) < max_attempts:
        task_state["status"] = "running"
        task_state["attempts"] = int(task_state["attempts"]) + 1
        log_plan_event(
            run_state,
            f"task {task['id']} attempt {task_state['attempts']}/{max_attempts} started",
        )
        save_run_state(run_state_path, run_state)

        active_plan_path = Path(run_state["active_plan_doc"])
        fallback_plan = repo_root / PLAN_INPUT_PATH
        plan_context_path = active_plan_path if active_plan_path.exists() else fallback_plan
        plan_context = read_context_path(repo_root, plan_context_path.relative_to(repo_root), limit=12000)
        memory_context = read_context_path(
            repo_root,
            config.get("memory_path", MEMORY_PATH.as_posix()),
            limit=8000,
        )
        agent_context = read_context_path(
            repo_root,
            config.get("agent_prompt_path", AGENT_PROMPT_PATH.as_posix()),
            limit=4000,
        )

        prompt = build_worker_prompt(
            task,
            resume=bool(task_state.get("session_id")),
            last_failure=task_state.get("last_failure"),
            plan_context=plan_context,
            memory_context=memory_context,
            agent_context=agent_context,
        )

        return_code, session_id = stream_codex(
            config=config,
            cwd=task_worktree,
            prompt=prompt,
            last_message_path=Path(task_state["last_message"]),
            event_log_path=Path(task_state["event_log"]),
            model=config.get("worker_model"),
            session_id=task_state.get("session_id"),
        )

        if session_id:
            task_state["session_id"] = session_id

        last_message = read_optional_text(Path(task_state["last_message"]))
        if last_message:
            task_state["last_response"] = last_message

        if return_code != 0:
            failure = {
                "kind": "codex",
                "return_code": return_code,
                "event_log": task_state["event_log"],
            }
            record_failure(task_state, failure)
            task_state["status"] = "needs_resume"
            log_plan_event(run_state, f"task {task['id']} stopped on codex error")
            save_run_state(run_state_path, run_state)
            return False

        verified, failure = run_verification(
            task=task,
            task_worktree=task_worktree,
            task_state=task_state,
            config=config,
            run_dir=run_dir,
        )
        if verified:
            maybe_commit_task(task_worktree, task, task_state)
            integration_head = merge_task_into_integration(integration_worktree, task_state["branch"])
            task_state["status"] = "merged"
            task_state["integration_head_after_merge"] = integration_head
            task_state["last_failure"] = None
            run_state["integration_head"] = integration_head
            log_plan_event(run_state, f"task {task['id']} merged into {run_state['integration_branch']}")
            append_memory_entry(
                repo_root,
                config=config,
                task=task,
                task_state=task_state,
            )
            save_run_state(run_state_path, run_state)
            return True

        if failure is None:
            raise CodexLoopError(f"Verification failed for task {task['id']} without failure details.")

        record_failure(task_state, failure)
        log_plan_event(
            run_state,
            f"task {task['id']} verification failed on attempt {task_state['attempts']}: {failure['command']}",
        )
        save_run_state(run_state_path, run_state)

    task_state["status"] = "needs_resume"
    log_plan_event(run_state, f"task {task['id']} exhausted {max_attempts} automatic attempts")
    save_run_state(run_state_path, run_state)
    return False


def ready_tasks(tasks: list[dict[str, Any]], run_state: dict[str, Any]) -> list[dict[str, Any]]:
    ready: list[dict[str, Any]] = []
    for task in tasks:
        state = run_state["tasks"][task["id"]]
        if state["status"] == "merged":
            continue
        deps_ok = all(run_state["tasks"][dep]["status"] == "merged" for dep in task["dependencies"])
        if deps_ok:
            ready.append(task)
    return ready


def run_backlog(
    *,
    repo_root: Path,
    config: dict[str, Any],
    tasks: list[dict[str, Any]],
    run_state: dict[str, Any],
    run_state_path: Path,
    selected_task_id: str | None = None,
    manual_resume: bool = False,
) -> bool:
    tasks_by_id = {task["id"]: task for task in tasks}
    if selected_task_id:
        if selected_task_id not in tasks_by_id:
            raise CodexLoopError(f"Unknown task id: {selected_task_id}")
        task = tasks_by_id[selected_task_id]
        return execute_task(
            repo_root=repo_root,
            config=config,
            run_state=run_state,
            run_state_path=run_state_path,
            task=task,
            force_resume=manual_resume,
        )

    while True:
        pending = [
            run_state["tasks"][task_id]
            for task_id in run_state["order"]
            if run_state["tasks"][task_id]["status"] != "merged"
        ]
        if not pending:
            return True

        ready = ready_tasks(tasks, run_state)
        if not ready:
            unresolved = ", ".join(task_state["id"] for task_state in pending)
            raise CodexLoopError(f"No runnable tasks remain. Check dependencies or failures: {unresolved}")

        progressed = False
        for task in ready:
            ok = execute_task(
                repo_root=repo_root,
                config=config,
                run_state=run_state,
                run_state_path=run_state_path,
                task=task,
                force_resume=manual_resume,
            )
            progressed = True
            if not ok:
                return False
        if not progressed:
            return False


def print_status(state: dict[str, Any]) -> None:
    print(f"run_id: {state['run_id']}")
    print(f"integration_branch: {state['integration_branch']}")
    print(f"integration_worktree: {state['integration_worktree']}")
    for task_id in state["order"]:
        task = state["tasks"][task_id]
        line = f"{task_id} {task['status']}"
        if task.get("session_id"):
            line += f" session={task['session_id']}"
        if task.get("last_failure"):
            failure = task["last_failure"]
            line += f" failure={failure.get('kind')}"
        print(line)


def cmd_init(args: argparse.Namespace) -> int:
    repo_root = ensure_git_root(Path(args.repo).resolve())
    init_repo(repo_root, force=args.force)
    print(f"Initialized codexloop in {repo_root}")
    print(f"Config: {repo_root / CONFIG_PATH}")
    print(f"Plan: {repo_root / PLAN_INPUT_PATH}")
    print(f"Memory: {repo_root / MEMORY_PATH}")
    return 0


def cmd_plan(args: argparse.Namespace) -> int:
    repo_root = ensure_git_root(Path(args.repo).resolve())
    ensure_runtime_layout(repo_root)
    config = load_config(repo_root)
    if args.input:
        raw_path = Path(args.input)
        plan_path = raw_path.resolve() if raw_path.is_absolute() else (repo_root / raw_path).resolve()
    else:
        plan_path = repo_root / PLAN_INPUT_PATH
    plan_text = plan_path.read_text(encoding="utf-8")
    prompt = build_planner_prompt(repo_root, config, plan_text)

    tmp_dir = repo_root / RUNS_DIR / "_planner"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    event_log = tmp_dir / "planner-events.jsonl"
    last_message = tmp_dir / "planner-last-message.json"

    return_code, _ = stream_codex(
        config=config,
        cwd=repo_root,
        prompt=prompt,
        last_message_path=last_message,
        event_log_path=event_log,
        model=args.model or config.get("planner_model"),
        output_schema=SCHEMA_PATH,
        ephemeral=True,
    )
    if return_code != 0:
        raise CodexLoopError(f"Planner failed. See {event_log}")

    payload = parse_json_file(last_message)
    tasks = normalize_tasks(payload)
    backlog_path = save_tasks(repo_root, tasks, plan_path)
    print(f"Wrote {len(tasks)} tasks to {backlog_path}")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    repo_root = ensure_git_root(Path(args.repo).resolve())
    ensure_runtime_layout(repo_root)
    config = load_config(repo_root)
    if args.plan:
        raw_path = Path(args.plan)
        backlog_path = raw_path.resolve() if raw_path.is_absolute() else (repo_root / raw_path).resolve()
    else:
        backlog_path = None
    resolved_backlog, tasks = load_backlog(repo_root, backlog_path)
    run_id = args.run_id or default_run_id()
    run_state_path, run_state = create_run_state(
        repo_root,
        config=config,
        tasks=tasks,
        backlog_path=resolved_backlog,
        run_id=run_id,
    )
    ok = run_backlog(
        repo_root=repo_root,
        config=config,
        tasks=tasks,
        run_state=run_state,
        run_state_path=run_state_path,
        selected_task_id=args.task,
        manual_resume=False,
    )
    print_status(run_state)
    return 0 if ok else 2


def cmd_resume(args: argparse.Namespace) -> int:
    repo_root = ensure_git_root(Path(args.repo).resolve())
    config = load_config(repo_root)
    run_state_path, run_state = load_run_state(repo_root, args.run_id)
    stored_plan_path = Path(run_state["plan_path"])
    resolved_plan_path = (
        stored_plan_path
        if stored_plan_path.is_absolute()
        else (repo_root / stored_plan_path).resolve()
    )
    _, tasks = load_backlog(repo_root, resolved_plan_path)

    selected_task_id = args.task
    if selected_task_id is None:
        resumable = [
            task_id
            for task_id in run_state["order"]
            if run_state["tasks"][task_id]["status"] != "merged"
        ]
        if len(resumable) == 1:
            selected_task_id = resumable[0]

    ok = run_backlog(
        repo_root=repo_root,
        config=config,
        tasks=tasks,
        run_state=run_state,
        run_state_path=run_state_path,
        selected_task_id=selected_task_id,
        manual_resume=True,
    )
    print_status(run_state)
    return 0 if ok else 2


def cmd_status(args: argparse.Namespace) -> int:
    repo_root = ensure_git_root(Path(args.repo).resolve())
    _, state = load_run_state(repo_root, args.run_id)
    print_status(state)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="codexloop")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Scaffold .codexloop in a target repo")
    init_parser.add_argument("repo", nargs="?", default=".")
    init_parser.add_argument("--force", action="store_true")
    init_parser.set_defaults(func=cmd_init)

    plan_parser = subparsers.add_parser("plan", help="Generate tasks from an implementation plan")
    plan_parser.add_argument("--repo", default=".")
    plan_parser.add_argument("--input")
    plan_parser.add_argument("--model")
    plan_parser.set_defaults(func=cmd_plan)

    run_parser = subparsers.add_parser("run", help="Execute the current backlog")
    run_parser.add_argument("--repo", default=".")
    run_parser.add_argument("--plan")
    run_parser.add_argument("--run-id")
    run_parser.add_argument("--task")
    run_parser.set_defaults(func=cmd_run)

    resume_parser = subparsers.add_parser("resume", help="Resume an interrupted run")
    resume_parser.add_argument("--repo", default=".")
    resume_parser.add_argument("--run-id")
    resume_parser.add_argument("--task")
    resume_parser.set_defaults(func=cmd_resume)

    status_parser = subparsers.add_parser("status", help="Show run status")
    status_parser.add_argument("--repo", default=".")
    status_parser.add_argument("--run-id")
    status_parser.set_defaults(func=cmd_status)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except CodexLoopError as exc:
        print(f"codexloop: {exc}", file=sys.stderr)
        return 1
