"""Launch an exported dev client or a prepared official Forge client for visual QA."""
import argparse
import json
import subprocess
from pathlib import Path

from verify_runtime import sha256, check_game_java


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--development', type=Path)
    group.add_argument('--production', type=Path)
    parser.add_argument('--java', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.development:
        data = json.loads(args.development.read_text())['client']
        command = [str(args.java.resolve()) if args.java else data['executable'], '-Dfile.encoding=UTF-8', *data['jvmArgs'],
                   '-cp', data['classpath'], data['mainClass'], *data['args']]
        directory = data['directory']
    else:
        if not args.java:
            parser.error('--java is required for production')
        data = json.loads((args.production / 'retromixin-launch.json').read_text())
        if data['side'] != 'client':
            parser.error('Installation is not a client')
        for name, expected in data['sha256'].items():
            if sha256(args.production / name) != expected:
                raise RuntimeError(f'Frozen installation changed: {name}')
        directory = str(args.production.resolve())
        command = [str(args.java.resolve()), '-Xmx1G', '-Dfile.encoding=UTF-8',
                   '-Dfml.ignoreInvalidMinecraftCertificates=true',
                   '-Djava.library.path=' + data['natives'], '-cp', data['classpath'],
                   'net.minecraft.launchwrapper.Launch', '--username', 'RetroMixinTest',
                   '--session', '0', '--version', '1.6.4-Forge9.11.1.1345',
                   '--gameDir', directory, '--assetsDir', data['assets'],
                   '--tweakClass', 'cpw.mods.fml.common.launcher.FMLTweaker']
    check_game_java(command[0])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('w', encoding='utf-8') as log:
        result = subprocess.run(command, cwd=directory, stdout=log, stderr=subprocess.STDOUT)
    if result.returncode:
        raise SystemExit(result.returncode)


if __name__ == '__main__':
    main()
