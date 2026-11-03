"""Run an exported development server or a prepared original Forge server.

Wait for actual member assertions and ready, then stop and verify world saving.
No existing worlds are used: each prepared installation has its own directory.
"""
import argparse
import hashlib
import json
import queue
import re
import subprocess
import threading
import time
from pathlib import Path


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def check_game_java(executable):
    result = subprocess.run([str(executable), '-version'], stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, timeout=15)
    if result.returncode or not re.search(rb'version "1\.[78][.\-]', result.stdout):
        raise RuntimeError('RetroMixin requires a Java 7 or Java 8 game runtime: ' + str(executable))


def run_server(command, directory, output, timeout=180):
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    process = subprocess.Popen(command, cwd=directory, stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               text=True, encoding="utf-8", errors="replace")
    lines = queue.Queue()

    def read():
        for line in process.stdout:
            lines.put(line)
        lines.put(None)

    threading.Thread(target=read, daemon=True).start()
    text, stopped = "", False
    deadline = time.monotonic() + timeout
    try:
        with output.open("w", encoding="utf-8") as log:
            while time.monotonic() < deadline:
                try:
                    line = lines.get(timeout=0.5)
                except queue.Empty:
                    continue
                if line is None:
                    break
                log.write(line)
                log.flush()
                text += line
                if not stopped and "ALL MEMBER CHECKS PASSED" in text and "Done (" in text:
                    process.stdin.write("save-all\nstop\n")
                    process.stdin.flush()
                    stopped = True
            else:
                raise RuntimeError(f"Server timed out; inspect {output}")
        code = process.wait(timeout=20)
        if code or not stopped or "Saving chunks" not in text:
            raise RuntimeError(f"Assertions/ready/save/stop failed (exit={code}); inspect {output}")
        return {"exitCode": code, "memberAssertions": True, "ready": True,
                "saved": True, "log": str(output.resolve()), "logSha256": sha256(output)}
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--development", type=Path, help="exportDevelopmentLaunches JSON")
    group.add_argument("--production", type=Path, help="prepared installation directory")
    parser.add_argument("--java", type=Path, help="Optional Java 7/8 executable override")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.development:
        data = json.loads(args.development.read_text())["server"]
        command = [str(args.java.resolve()) if args.java else data["executable"], "-Dfile.encoding=UTF-8", *data["jvmArgs"], "-cp", data["classpath"],
                   data["mainClass"], *data["args"]]
        directory = data["directory"]
    else:
        if not args.java:
            parser.error("--java is required for production")
        data = json.loads((args.production / "retromixin-launch.json").read_text())
        for name, expected in data["sha256"].items():
            if sha256(args.production / name) != expected:
                raise RuntimeError(f"Frozen installation changed: {name}")
        command = [str(args.java.resolve()), "-Xmx1G", "-Dfile.encoding=UTF-8", "-jar", data["forge"], "nogui"]
        directory = args.production
    check_game_java(command[0])
    result = run_server(command, directory, args.output)
    args.output.with_suffix(".json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
