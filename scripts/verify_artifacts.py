"""Check the actual distribution archives and write a compact evidence record."""
import argparse
import json
import struct
import zipfile
import xml.etree.ElementTree as ET
import os
from pathlib import Path

from hashlib import sha256 as digest

def sha256(path):
    return digest(path.read_bytes()).hexdigest()

ROOT = Path(__file__).resolve().parents[1]
VERSION = dict(line.split('=', 1) for line in (ROOT / 'gradle.properties').read_text().splitlines() if '=' in line)['version']
VERSION = os.environ.get('RELEASE_VERSION', VERSION)


def classes(jar, maximum):
    versions = set()
    for name in jar.namelist():
        if not name.endswith('.class'):
            continue
        magic, minor, major = struct.unpack('>IHH', jar.read(name)[:8])
        assert magic == 0xCAFEBABE and minor != 65535 and major <= maximum, (name, major)
        versions.add(major)
    assert versions, 'Archive contains no classes'
    return sorted(versions)


def main():
    lock = json.loads((ROOT / 'gradle/build-inputs.lock.json').read_text())
    assert sha256(ROOT / 'gradle/wrapper/gradle-wrapper.jar') == lock['gradle']['wrapperJarSha256']
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bootstrap', type=Path, default=ROOT / f'runtime/mixin-bootstrap/build/libs/retrospectum-mixin-{VERSION}.jar')
    bootstrap = parser.parse_args().bootstrap
    with zipfile.ZipFile(bootstrap) as jar:
        names = jar.namelist()
        assert len(names) == len(set(names)), 'Duplicate archive entries'
        for notice in ('META-INF/LICENSE', 'META-INF/THIRD-PARTY.md', 'META-INF/UPSTREAM.md'):
            assert notice in names, notice
        assert names.count('org/spongepowered/asm/bridge/RemapperAdapterFML.class') == 1
        assert 'dev/desiderium/retro/mixin/bootstrap/RetroMixinTweaker.class' in names
        assert 'dev/desiderium/retro/mixin/internal/asm/tree/ClassNode.class' in names
        container = jar.read('dev/desiderium/retro/mixin/forge/RetroMixinModContainer.class')
        assert b'(Lcom/google/common/eventbus/EventBus;Lcpw/mods/fml/common/LoadController;)Z' in container
        assert b'dev/desiderium/retro/mixin/internal/guava' not in container
        assert not any(n.startswith('cpw/mods/fml/') for n in names)
        assert not any(n.startswith('net/minecraft/') for n in names)
        for prefix in ('org/objectweb/asm/', 'com/google/common/', 'com/google/thirdparty/', 'com/google/gson/', 'org/apache/logging/log4j/'):
            assert not any(n.startswith(prefix) for n in names), prefix
        assert b'dev.desiderium.retro.mixin.bootstrap.RetroMixinTweaker' in jar.read('META-INF/MANIFEST.MF').replace(b'\r\n ', b'')
        for license_name in ('LICENSE-ASM-9.7.1.txt', 'LICENSE-Guava-20.0.txt', 'LICENSE-Gson-2.8.9.txt'):
            assert 'META-INF/licenses/' + license_name in names, license_name
        assert 'META-INF/services/javax.annotation.processing.Processor' not in names
        for name in names:
            if name.startswith('META-INF/services/org.spongepowered.asm.service.'):
                assert b'modlauncher' not in jar.read(name)
        runtime_versions = classes(jar, 51)
    repository = ROOT / f'build/maven/dev/desiderium/retro/retrospectum-mixin/{VERSION}'
    primary = repository / f'retrospectum-mixin-{VERSION}.jar'
    assert sha256(primary) == sha256(bootstrap), 'Maven artifact must be the complete runtime'
    for classifier in ('sources', 'javadoc'):
        with zipfile.ZipFile(repository / f'retrospectum-mixin-{VERSION}-{classifier}.jar') as jar:
            assert any(n.endswith('.java' if classifier == 'sources' else '.html') for n in jar.namelist())
    with zipfile.ZipFile(repository / f'retrospectum-mixin-{VERSION}-sources.jar') as jar:
        assert 'dev/desiderium/retro/mixin/forge/RetroMixinModContainer.java' in jar.namelist()
    ns = {'m': 'http://maven.apache.org/POM/4.0.0'}
    pom = ET.parse(repository / f'retrospectum-mixin-{VERSION}.pom')
    assert pom.findtext('m:version', namespaces=ns) == VERSION
    assert pom.find('m:dependencies', ns) is None, 'Shaded dependencies must not leak into the runtime POM'
    with zipfile.ZipFile(ROOT / f'build/distributions/retrospectum-mixin-{VERSION}-maven.zip') as jar:
        assert any(n.endswith(f'retrospectum-mixin-{VERSION}.jar') for n in jar.namelist())
    record = {
        'bootstrap': {'sha256': sha256(bootstrap), 'classMajors': runtime_versions},
        'privateDependencies': True, 'singleFmlBridge': True,
        'minimumGameJava': 7, 'maximumRuntimeClassMajor': 51,
    }
    output = ROOT / 'build/reports/artifacts.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps(record, indent=2))


if __name__ == '__main__':
    main()
