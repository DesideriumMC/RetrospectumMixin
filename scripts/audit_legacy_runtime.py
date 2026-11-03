"""Audit class versions and Java platform symbols against a real rt.jar.

This is a whole-archive inventory, not a reachability proof. Optional code paths,
reflection, native libraries and service discovery still require runtime tests.
"""
import argparse
from collections import Counter
from functools import lru_cache
import json
import re
import struct
import zipfile
from pathlib import Path

from verify_runtime import sha256


def parse_class(data):
    offset = 0

    def take(size):
        nonlocal offset
        value = data[offset:offset + size]
        offset += size
        return value

    def u2():
        return struct.unpack('>H', take(2))[0]

    def u4():
        return struct.unpack('>I', take(4))[0]

    if u4() != 0xCAFEBABE:
        raise ValueError('Invalid class header')
    minor, major, length = u2(), u2(), u2()
    cp = [None] * length
    i = 1
    while i < length:
        tag = take(1)[0]
        if tag == 1:
            cp[i] = (tag, take(u2()).decode('utf-8', errors='replace'))
        elif tag in (7, 8, 16, 19, 20):
            cp[i] = (tag, u2())
        elif tag in (9, 10, 11, 12, 17, 18):
            cp[i] = (tag, u2(), u2())
        elif tag in (3, 4):
            take(4)
        elif tag in (5, 6):
            take(8)
            i += 1
        elif tag == 15:
            take(3)
        else:
            raise ValueError(f'Unsupported constant-pool tag {tag}')
        i += 1

    def utf(index):
        return cp[index][1]

    def cls(index):
        return utf(cp[index][1]) if index else None

    access, name, parent = u2(), cls(u2()), cls(u2())
    interfaces = [cls(u2()) for _ in range(u2())]

    def members():
        result = set()
        for _ in range(u2()):
            flags, member, descriptor = u2(), utf(u2()), utf(u2())
            result.add((member, descriptor))
            for _ in range(u2()):
                u2()
                take(u4())
        return result

    fields, methods = members(), members()
    classes, refs = set(), []
    for member, descriptor in fields | methods:
        classes.update(re.findall(r'L([\w$/]+);', descriptor))
    for entry in cp:
        if not entry:
            continue
        if entry[0] == 7:
            classes.add(utf(entry[1]))
        elif entry[0] in (9, 10, 11):
            member = cp[entry[2]]
            refs.append((entry[0], cls(entry[1]), utf(member[1]), utf(member[2])))
        elif entry[0] in (12, 16):
            descriptor = utf(entry[2] if entry[0] == 12 else entry[1])
            classes.update(re.findall(r'L([\w$/]+);', descriptor))
    # Keep annotation/signature/descriptor-shaped strings separate. These are
    # not equivalent to executable code references (e.g. @Repeatable on Java 7).
    metadata = set()
    for entry in cp:
        if entry and entry[0] == 1:
            metadata.update(re.findall(r'L([\w$/]+);', entry[1]))
    return {'name': name, 'major': major, 'minor': minor, 'parent': parent,
            'interfaces': interfaces, 'fields': fields, 'methods': methods,
            'classes': classes, 'metadata': metadata - classes, 'refs': refs}


def platform_index(jdk):
    result = {}
    jars = [jdk / 'jre/lib/rt.jar', *sorted((jdk / 'jre/lib/ext').glob('*.jar')),
            jdk / 'jre/lib/jce.jar', jdk / 'jre/lib/jsse.jar']
    for path in jars:
        if not path.is_file():
            continue
        with zipfile.ZipFile(path) as archive:
            for name in archive.namelist():
                if name.endswith('.class'):
                    result[name[:-6]] = parse_class(archive.read(name))
    return result


def audit(archive, platform, maximum, reference_classes=()):
    @lru_cache(None)
    def member_exists(owner, name, desc, field):
        info = platform.get(owner)
        if not info:
            return False
        if (name, desc) in info['fields' if field else 'methods']:
            return True
        if name in ('<init>', '<clinit>'):
            return False
        return any(member_exists(base, name, desc, field)
                   for base in [info['parent'], *info['interfaces']] if base)

    def java_platform(name):
        return name.startswith(('java/', 'javax/', 'sun/', 'com/sun/',
                                'org/w3c/dom/', 'org/xml/sax/', 'org/ietf/jgss/'))

    versions, above, absent_classes, absent_members, external_classes = Counter(), [], {}, {}, {}
    absent_metadata = {}
    with zipfile.ZipFile(archive) as jar:
        for name in jar.namelist():
            if not name.endswith('.class'):
                continue
            info = parse_class(jar.read(name))
            versions[info['major']] += 1
            if info['major'] > maximum:
                above.append({'class': info['name'], 'major': info['major']})
            for target in info['classes']:
                # Array Class constants are descriptors; their elements are also
                # captured from UTF8 descriptors above.
                if java_platform(target) and target not in platform:
                    if target.startswith('java/') or target in reference_classes:
                        absent_classes.setdefault(target, []).append(info['name'])
                    else:
                        # javax.jms/mail/annotation, for example, are optional
                        # external libraries rather than missing Java SE APIs.
                        external_classes.setdefault(target, []).append(info['name'])
            for target in info['metadata']:
                if (target.startswith('java/') or target in reference_classes) and target not in platform:
                    absent_metadata.setdefault(target, []).append(info['name'])
            for tag, owner, member, desc in info['refs']:
                # Signature-polymorphic methods have call-site descriptors.
                if owner == 'java/lang/invoke/MethodHandle' and member in ('invoke', 'invokeExact') and owner in platform:
                    continue
                if owner in platform and not member_exists(owner, member, desc, tag == 9):
                    key = f'{owner}.{member}{desc}'
                    absent_members.setdefault(key, []).append(info['name'])
    return {'archive': str(archive), 'sha256': sha256(archive), 'maximumClassMajor': maximum,
            'classMajors': dict(sorted(versions.items())), 'classesAboveTarget': above,
            'missingPlatformClasses': absent_classes, 'missingPlatformMembers': absent_members,
            'unresolvedExternalClasses': external_classes,
            'missingMetadataSymbols': absent_metadata,
            'limitations': 'Whole archive, including InnerClasses metadata. Optional paths may be unreachable; annotation/signature strings are separate. No reflection/native/service compatibility proof.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--jar', type=Path, required=True)
    parser.add_argument('--jdk', type=Path, required=True)
    parser.add_argument('--java', choices=(6, 7), type=int, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--reference-jdk', type=Path, help='Newer JDK used to distinguish Java SE classes from optional javax/vendor dependencies')
    args = parser.parse_args()
    reference = set()
    if args.reference_jdk:
        for path in [args.reference_jdk / 'jre/lib/rt.jar', *sorted((args.reference_jdk / 'jre/lib/ext').glob('*.jar'))]:
            with zipfile.ZipFile(path) as jar:
                reference.update(name[:-6] for name in jar.namelist() if name.endswith('.class'))
    report = audit(args.jar, platform_index(args.jdk), args.java + 44, reference)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({key: len(report[key]) for key in
                      ('classesAboveTarget', 'missingPlatformClasses', 'missingPlatformMembers')}))


if __name__ == '__main__':
    main()
