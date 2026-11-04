#!/usr/bin/env python3
"""Run the selected Brás Drive -> RustFS copy in restartable, bounded sessions.

This script does not transfer anything unless called with the ``run`` subcommand.
No credentials are stored here; rclone uses the existing local remotes.
"""

from __future__ import annotations

import argparse
import csv
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone


HERE = Path(__file__).resolve().parent
MANIFEST = HERE.parent / "docs/datasets/bras-captures.csv"
RUN = HERE.parent / "data/_transfers/bras"  # local run record, git-ignored
STATE = RUN / ".bras-transfer-state.json"
LOCK = RUN / ".bras-transfer.lock"
LOG_DIR = RUN / ".bras-transfer-logs"
DRIVE_ROOT_ID = "1cIKFRLeKXzYAJ7VakP9dHFL1T3GKDzrV"
DEST_ROOT = "rustfs:sideseeing/sao-paulo/bras"
CAPTURE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2}-\d{3}$")
ROUTE_RE = re.compile(r"^D\d+P\d+$")


def compact_id(capture_id: str) -> str:
    parts = capture_id.split("-")
    return "".join(parts[:3]) + "-" + "".join(parts[3:])


def load_jobs() -> tuple[str, list[tuple[str, str, str, str]]]:
    manifest_bytes = MANIFEST.read_bytes()
    digest = hashlib.sha256(manifest_bytes).hexdigest()
    jobs = [
        (
            "gpkg",
            "copyto",
            "03_analises/auditoria_calcadas_bras.gpkg",
            "processed/auditoria_calcada_bras.gpkg",
        )
    ]
    seen: set[str] = set()
    with MANIFEST.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            route = row["route_group"]
            capture = row["capture_id"]
            expected = f"00_dados_originais/MultiSensor/{route}/{capture}"
            if not ROUTE_RE.fullmatch(route) or not CAPTURE_RE.fullmatch(capture):
                raise ValueError(f"Unexpected route or capture name: {route}/{capture}")
            if row["source_relative_folder"] != expected or capture in seen:
                raise ValueError(f"Invalid or repeated source mapping: {route}/{capture}")
            seen.add(capture)
            compact = compact_id(capture)
            jobs.extend(
                [
                    (f"{capture}:raw", "copy", expected, f"raw/{route}/{capture}"),
                    (
                        f"{capture}:images",
                        "copy",
                        f"01_dados_processados/01_image_sequences/{compact}",
                        f"processed/image-sequences/{capture}",
                    ),
                    (
                        f"{capture}:video",
                        "copyto",
                        f"01_dados_processados/02_videos_low_res/{compact}.mp4",
                        f"processed/videos-low-res/{capture}.mp4",
                    ),
                ]
            )
    if len(seen) != 216:
        raise ValueError(f"Expected 216 captures, found {len(seen)}")
    return digest, jobs


def load_state(digest: str, valid_ids: set[str]) -> set[str]:
    if not STATE.exists():
        return set()
    state = json.loads(STATE.read_text(encoding="utf-8"))
    expected = {"version": 1, "manifest_sha256": digest, "drive_root_id": DRIVE_ROOT_ID, "dest_root": DEST_ROOT}
    for key, value in expected.items():
        if state.get(key) != value:
            raise ValueError(f"Progress file has a different {key}; inspect {STATE} before continuing")
    completed = state.get("completed")
    if not isinstance(completed, list) or not all(isinstance(job, str) and job in valid_ids for job in completed):
        raise ValueError(f"Invalid completed jobs in {STATE}")
    return set(completed)


def save_state(digest: str, completed: set[str]) -> None:
    payload = {
        "version": 1,
        "manifest_sha256": digest,
        "drive_root_id": DRIVE_ROOT_ID,
        "dest_root": DEST_ROOT,
        "completed": sorted(completed),
        "updated_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=HERE, prefix=".bras-state-", delete=False) as handle:
        temporary = Path(handle.name)
        try:
            json.dump(payload, handle, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise
    os.replace(temporary, STATE)


def command_for(job: tuple[str, str, str, str], remaining_seconds: int | None = None) -> list[str]:
    _, action, source, destination = job
    command = [
        "rclone",
        action,
        f"gdrive:{source}",
        f"{DEST_ROOT}/{destination}",
        "--drive-root-folder-id",
        DRIVE_ROOT_ID,
        "--checksum",
        "--immutable",
        "--transfers",
        "2",
        "--checkers",
        "4",
        "--stats",
        "30s",
    ]
    if remaining_seconds is not None:
        command.extend(["--max-duration", f"{remaining_seconds}s", "--cutoff-mode", "SOFT"])
    return command


def run_jobs(
    digest: str,
    jobs: list[tuple[str, str, str, str]],
    minutes: float,
    max_jobs: int | None,
) -> int:
    LOG_DIR.mkdir(exist_ok=True)
    with LOCK.open("w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print("Another Brás transfer session is already running.", file=sys.stderr)
            return 2
        completed = load_state(digest, {job[0] for job in jobs})
        pending = [job for job in jobs if job[0] not in completed]
        if not pending:
            print("All jobs are marked complete. Run a separate destination audit before relying on the copy.")
            return 0
        deadline = time.monotonic() + minutes * 60
        log_path = LOG_DIR / f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{os.getpid()}.log"
        print(f"Session log: {log_path}", flush=True)
        count = 0
        with log_path.open("a", encoding="utf-8") as log:
            for job in pending:
                if time.monotonic() >= deadline or (max_jobs is not None and count >= max_jobs):
                    break
                print(f"Starting {job[0]} ({len(completed)}/{len(jobs)} complete)", flush=True)
                remaining_seconds = max(1, int(deadline - time.monotonic()))
                command = command_for(job, remaining_seconds)
                log.write(f"\n=== {job[0]}: {shlex.join(command)} ===\n")
                log.flush()
                try:
                    result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=False)
                except KeyboardInterrupt:
                    print("Interrupted. The current job was not marked complete; rerun to retry it.", file=sys.stderr)
                    return 130
                if result.returncode == 10:
                    print(f"Time window reached during {job[0]}; it remains pending for the next session.")
                    return 0
                if result.returncode != 0:
                    print(f"Job {job[0]} failed (rclone exit {result.returncode}); see {log_path}", file=sys.stderr)
                    return result.returncode
                completed.add(job[0])
                save_state(digest, completed)
                count += 1
                print(f"Completed {job[0]} ({len(completed)}/{len(jobs)})", flush=True)
        print(f"Session finished: {count} jobs; {len(jobs) - len(completed)} remain.")
        return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="action", required=True)
    subparsers.add_parser("status", help="Show local progress without network access")
    plan = subparsers.add_parser("plan", help="Print the next commands without transferring")
    plan.add_argument("--limit", type=int, default=3)
    run = subparsers.add_parser("run", help="Transfer until the time budget or job limit is reached")
    run.add_argument("--minutes", type=float, required=True, help="Stop starting new jobs after this many minutes")
    run.add_argument("--max-jobs", type=int, help="Also limit this session to this many jobs")
    args = parser.parse_args()
    if args.action == "run" and (not 0 < args.minutes <= 1440 or (args.max_jobs is not None and args.max_jobs < 1)):
        parser.error("--minutes must be 0–1440 and --max-jobs must be positive")
    if args.action == "plan" and args.limit < 1:
        parser.error("--limit must be positive")
    digest, jobs = load_jobs()
    completed = load_state(digest, {job[0] for job in jobs})
    pending = [job for job in jobs if job[0] not in completed]
    if args.action == "status":
        print(f"{len(completed)}/{len(jobs)} jobs complete; {len(pending)} pending. Local state: {STATE}")
        if pending:
            print(f"Next: {pending[0][0]}")
        print("Progress markers are not an independent destination audit.")
        return 0
    if args.action == "plan":
        for job in pending[: args.limit]:
            print(f"{job[0]}: {shlex.join(command_for(job))}")
        return 0
    return run_jobs(digest, jobs, args.minutes, args.max_jobs)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"Error: {error}", file=sys.stderr)
        raise SystemExit(2) from error
