# Retrospectum Mixin

Mixin 0.8.7 Bootstrap for Minecraft Forge 1.6.4 / 9.11.1.1345 on Java 7 and 8.

## Build

Use JDK 17 for Gradle 8.14.6 and JDK 8 for compilation. Set `java7Home` to a JDK 7
installation and configure the JDK paths as shown in `gradle.properties.example`.

```sh
./gradlew build :mixin-bootstrap:mixinDistribution
```

Output: `runtime/mixin-bootstrap/build/libs/retrospectum-mixin-0.2.0.jar`.

On Windows, the build helper configures the JDK paths:

```powershell
./scripts/Invoke-Build.ps1 -BuildJdk C:/jdks/17 -CompileJdk C:/jdks/8 -GameJdk C:/jdks/7
```

## Install

1. Install Minecraft 1.6.4 with Forge 9.11.1.1345 and select Java 7 or 8 in your launcher.
2. Download the `retrospectum-mixin-*.jar` asset from
   [Releases](https://github.com/DesideriumMC/RetrospectumMixin/releases).
3. Place the JAR in the instance's `mods/` directory, alongside mods that require it.
4. Launch the Forge profile. The log will contain `[RETROMIXIN] shared Mixin 0.8.7 bootstrap`.

Open **Mods** and select **Retrospectum Mixin** to view its version, author and description.

For a dedicated server, place the same JAR in the server's `mods/` directory and
start Forge as usual. Keep one copy of the Bootstrap per instance.

## Configure a mod

Mod configurations are discovered in JARs under `mods/` and `mods/1.6.4/` through
the `MixinConfigs` manifest attribute:

```groovy
jar {
    manifest.attributes('MixinConfigs': 'mixins.example.json')
}
```

The development property `retromixin.mixin.configs` accepts comma-separated config
resources. Config plugins that use ASM's `ClassNode` import
`dev.desiderium.retro.mixin.internal.asm.tree.ClassNode`.

## Develop a mod

Start with [Retrospectum Mod Template](https://github.com/DesideriumMC/RetrospectumModTemplate),
which uses [Retrospectum Loom](https://github.com/DesideriumMC/RetrospectumLoom).
The Gradle plugin ID is `dev.desiderium.retro.loom`, with the `retrospectum` DSL.

The runtime builds independently; a sibling Loom checkout is not required.

## License

MIT. See [runtime components](THIRD-PARTY.md) and
[upstream Mixin sources](runtime/mixin-bootstrap/UPSTREAM.md).

## Maven artifacts

The next release version is `0.2.0`, shared with Retrospectum Loom.
Coordinate: `dev.desiderium.retro:retrospectum-mixin:0.2.0`.
Use `-Pversion=<version>` to override it for a future build.

`./gradlew :mixin-bootstrap:mixinDistribution` writes a portable Maven repository
ZIP under `build/distributions/` and the repository under `build/maven/`.
The primary artifact is the complete shaded runtime, including the Forge mod
metadata class. Sources, Javadoc and upstream notices accompany it. Thin and
intermediate shaded JARs are build intermediates; install the unclassified JAR.

## Reference

- [Compatibility and stable interface names](https://github.com/DesideriumMC/RetrospectumModTemplate/blob/main/docs/COMPATIBILITY.md)
- [Troubleshooting](https://github.com/DesideriumMC/RetrospectumModTemplate/blob/main/docs/TROUBLESHOOTING.md)
- [Release procedure](https://github.com/DesideriumMC/RetrospectumLoom/blob/main/RELEASING.md)
