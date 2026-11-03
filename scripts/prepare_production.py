"""Create an isolated original Forge .1345 server from an existing clean install.

The two original game archives are checked against pinned official downloads.
Only libraries are imported; no mods, configuration or worlds are copied.
"""
import argparse
import json
import shutil
from pathlib import Path

from verify_runtime import sha256

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--versioned-probe", action="store_true", help="Place sided probe in mods/1.6.4")
    parser.add_argument("--side", choices=("server", "client"), default="server")
    args = parser.parse_args()
    target = args.output.resolve()
    if target.exists():
        parser.error("Use a new output directory to prevent stale mods or world reuse")
    lock = json.loads((ROOT / "gradle/p0-inputs.lock.json").read_text())
    pins = {item["name"]: item["sha256"] for item in lock["artifacts"]}
    forge = "forge.jar" if args.side == "client" else "minecraftforge-universal-1.6.4-9.11.1.1345.jar"
    game = "minecraft.jar" if args.side == "client" else "minecraft_server.1.6.4.jar"
    files = {forge: pins["forge-1.6.4-9.11.1.1345-universal.jar"],
             game: pins["minecraft-" + args.side]}
    for name, expected in files.items():
        if sha256(args.base / name) != expected:
            raise RuntimeError(f"Original game checksum mismatch: {name}")
    bootstrap = ROOT / "runtime/mixin-bootstrap/build/libs/retrospectum-mixin-0.1.0-SNAPSHOT.jar"
    probe = ROOT / "samples/mixin-mapping-probe/build/libs/mixin-mapping-probe-0.1.0-SNAPSHOT.jar"
    sided = ROOT / "samples/sided-probe/build/libs/sided-probe-0.1.0-SNAPSHOT.jar"
    for path in (bootstrap, probe, sided):
        if not path.is_file():
            raise RuntimeError(f"Run the build first: missing {path}")
    if not (args.base / "libraries").is_dir():
        raise RuntimeError("Base install has no libraries directory")
    (target / "mods").mkdir(parents=True)
    for name in files:
        shutil.copy2(args.base / name, target / name)
    shutil.copytree(args.base / "libraries", target / "libraries")
    for path in (bootstrap, probe, sided):
        mod_dir = target / "mods" / "1.6.4" if args.versioned_probe and path == sided else target / "mods"
        mod_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, mod_dir / path.name)
    (target / "server.properties").write_text(
        "server-ip=127.0.0.1\nserver-port=25575\nonline-mode=false\n"
        "level-name=retromixin-test-world\nview-distance=3\n")
    hashes = {str(p.relative_to(target)).replace("\\", "/"): sha256(p)
              for p in target.rglob("*.jar")}
    metadata = {"forge": forge, "sha256": hashes, "minimumGameJava": 7, "side": args.side}
    if args.side == "client":
        original = json.loads((args.base / "launch.json").read_text(encoding="utf-8-sig"))
        shutil.copytree(args.base / "natives", target / "natives")
        # Preserve library order; all game libraries point into the new instance.
        metadata["classpath"] = original["classpath"].replace(str(args.base.resolve()), str(target))
        metadata["natives"] = str(target / "natives")
        metadata["assets"] = original["assets"]
    (target / "retromixin-launch.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(target)


if __name__ == "__main__":
    main()
