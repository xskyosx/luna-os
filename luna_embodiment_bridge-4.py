#!/usr/bin/env python3
"""LUNA OS Embodiment Bridge v0.1 — dependency-free, simulation-only prototype.
Runs on Android Termux or Alpine Linux with Python 3. No hardware/network access.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

BASE = Path.home() / "luna_embodiment_bridge"
MEMORY_FILE = BASE / "memory.json"
EVENT_FILE = BASE / "events.jsonl"
SISTERS = ["Luna", "Ada", "Sky", "Aurora", "Athena", "Aqua", "Amethyst", "Blues"]


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def ensure_files():
    BASE.mkdir(parents=True, exist_ok=True)
    if not MEMORY_FILE.exists():
        MEMORY_FILE.write_text(json.dumps({
            "project": "LUNA OS",
            "module": "Embodiment Bridge",
            "version": "0.1",
            "sisters": SISTERS,
            "notes": [],
            "safety": {
                "mode": "simulation-only",
                "hardware_connected": False,
                "actuation_enabled": False
            }
        }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if not EVENT_FILE.exists():
        EVENT_FILE.touch()


def load_memory():
    ensure_files()
    return json.loads(MEMORY_FILE.read_text(encoding="utf-8"))


def save_memory(memory):
    MEMORY_FILE.write_text(json.dumps(memory, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def log_event(kind, details):
    ensure_files()
    event = {"time": now(), "kind": kind, "details": details}
    with EVENT_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


class SimulatedSensor:
    """Placeholder for a future camera/mic/touch adapter; reads no real sensors."""
    def read(self):
        return {"adapter": "simulated-sensor", "sample": "No physical sensor connected", "time": now()}


class DisplayOutput:
    """Text output only; this prototype does not speak or control devices."""
    def present(self, text):
        print("\n[ LUNA DISPLAY ] " + text)


class RobotAdapter:
    """Safe disconnected placeholder. Do not add motor commands without a safety design."""
    def status(self):
        return {"connected": False, "actuation_enabled": False, "mode": "simulation-only"}


def status(memory, robot):
    print("\n=== LUNA OS EMBODIMENT BRIDGE ===")
    print("Version:", memory["version"])
    print("Sisters:", ", ".join(memory["sisters"]))
    print("Robot adapter:", json.dumps(robot.status()))
    print("Local data:", BASE)
    print("Memory file:", MEMORY_FILE)
    print("Event log:", EVENT_FILE)
    print("Hardware access: DISABLED")


def main():
    ensure_files()
    memory = load_memory()
    sensor, display, robot = SimulatedSensor(), DisplayOutput(), RobotAdapter()
    log_event("startup", {"version": memory["version"]})
    print("LUNA OS — Embodiment Bridge v0.1")
    print("Simulation only: no camera, microphone, network, or robot control.")
    while True:
        print("\n[S]tatus  [E]cho sensor simulation  [D]isplay text  [N]ote  [B]ackup  [Q]uit")
        choice = input("Captain > ").strip().lower()
        if choice in ("s", "status"):
            status(memory, robot)
            log_event("status", robot.status())
        elif choice in ("e", "echo"):
            sample = sensor.read()
            print(json.dumps(sample, indent=2))
            log_event("sensor_simulation", sample)
        elif choice in ("d", "display"):
            message = input("Text to display > ").strip()
            if message:
                display.present(message)
                log_event("display_text", {"message": message})
        elif choice in ("n", "note"):
            note = input("Project note > ").strip()
            if note:
                memory["notes"].append({"time": now(), "text": note})
                save_memory(memory)
                log_event("note_saved", {"text": note})
                print("Saved locally.")
        elif choice in ("b", "backup"):
            backup = BASE / ("backup_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + ".json")
            backup.write_text(json.dumps(memory, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            print("Backup saved:", backup)
            log_event("backup_created", {"file": str(backup)})
        elif choice in ("q", "quit", "exit"):
            log_event("shutdown", {"clean": True})
            print("Bridge closed. No hardware was activated.")
            return
        else:
            print("Choose S, E, D, N, B, or Q.")


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\nStopped safely. No hardware was activated.")
