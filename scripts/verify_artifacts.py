"""Check the actual distribution archives and write a compact evidence record."""
import argparse
import json
import struct
import zipfile
from pathlib import Path

from verify_runtime import sha256

ROOT = Path(__file__).resolve().parents[1]


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
    lock = json.loads((ROOT / 'gradle/p0-inputs.lock.json').read_text())
    assert sha256(ROOT / 'gradle/wrapper/gradle-wrapper.jar') == lock['gradle']['wrapperJarSha256']
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bootstrap', type=Path, default=ROOT / 'runtime/mixin-bootstrap/build/libs/retrospectum-mixin-0.1.0-SNAPSHOT.jar')
    bootstrap = parser.parse_args().bootstrap
    probe = ROOT / 'samples/mixin-mapping-probe/build/libs/mixin-mapping-probe-0.1.0-SNAPSHOT.jar'
    with zipfile.ZipFile(bootstrap) as jar:
        names = jar.namelist()
        assert names.count('org/spongepowered/asm/bridge/RemapperAdapterFML.class') == 1
        assert 'dev/desiderium/retro/mixin/bootstrap/RetroMixinTweaker.class' in names
        assert 'dev/desiderium/retro/mixin/internal/asm/tree/ClassNode.class' in names
        container = jar.read('dev/desiderium/retro/mixin/forge/RetroMixinModContainer.class')
        assert b'(Lcom/google/common/eventbus/EventBus;Lcpw/mods/fml/common/LoadController;)Z' in container
        assert b'dev/desiderium/retro/mixin/internal/guava' not in container
        assert not any(n.startswith('cpw/mods/fml/') for n in names)
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
    with zipfile.ZipFile(probe) as jar:
        mod_versions = classes(jar, 50)
        refmap = json.loads(jar.read('mixins.retromixin.p2.refmap.json'))
        assert refmap['mappings'], 'Missing AP-generated member mappings'
        assert b'func_' in jar.read('mixins.retromixin.p2.refmap.json')
        assert not any(n.startswith('org/spongepowered/') for n in jar.namelist())
        assert b'RetroMixinConfigs:' in jar.read('META-INF/MANIFEST.MF')
    record = {
        'bootstrap': {'sha256': sha256(bootstrap), 'classMajors': runtime_versions},
        'probe': {'sha256': sha256(probe), 'classMajors': mod_versions},
        'privateDependencies': True, 'singleFmlBridge': True, 'srgRefmap': True,
        'minimumGameJava': 7, 'maximumRuntimeClassMajor': 51,
    }
    output = ROOT / '.work/evidence/artifacts.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps(record, indent=2))


if __name__ == '__main__':
    main()
