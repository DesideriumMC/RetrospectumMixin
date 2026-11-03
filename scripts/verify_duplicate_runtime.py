"""Verify a second shared runtime is diagnosed before game startup.

LaunchWrapper may return exit 0 on startup exceptions, so inspect the diagnostic.
"""
import argparse
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--launches', type=Path, default=ROOT / 'samples/mixin-mapping-probe/build/retromixin/launches.json')
    args = parser.parse_args()
    data = json.loads(args.launches.read_text())['server']
    duplicate = ROOT / '.work/negative-runtime/duplicate.jar'
    duplicate.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / 'runtime/mixin-bootstrap/build/libs/retrospectum-mixin-0.1.0-SNAPSHOT.jar', duplicate)
    import os
    command = [data['executable'], '-Dfile.encoding=UTF-8', *data['jvmArgs'],
               '-cp', data['classpath'] + os.pathsep + str(duplicate),
               data['mainClass'], *data['args']]
    result = subprocess.run(command, cwd=data['directory'], stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, timeout=40)
    output = ROOT / '.work/evidence/duplicate-runtime.log'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(result.stdout)
    if b'Expected one shared Mixin runtime' not in result.stdout:
        raise RuntimeError(f'Missing collision diagnostic; inspect {output}')
    print(f'Duplicate Mixin runtime diagnosed before startup (LaunchWrapper exit={result.returncode})')


if __name__ == '__main__':
    main()
