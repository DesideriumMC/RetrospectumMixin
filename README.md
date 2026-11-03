# Retrospectum Mixin

Mixin 0.8.7 Bootstrap for Minecraft Forge 1.6.4 / 9.11.1.1345 on Java 7 and 8.

## Build

Use JDK 17 for Gradle 8.14.6 and JDK 8 for compilation. Set `java7Home` to a JDK 7
installation and configure the JDK paths as shown in `gradle.properties.example`.

```sh
./gradlew -PintegrationProbes=false build
```

Output: `runtime/mixin-bootstrap/build/libs/retrospectum-mixin-0.1.0-SNAPSHOT.jar`.

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
the `RetroMixinConfigs` manifest attribute:

```groovy
jar {
    manifest.attributes('RetroMixinConfigs': 'mixins.example.json')
}
```

The development property `retromixin.mixin.configs` accepts comma-separated config
resources. Config plugins that use ASM's `ClassNode` import
`dev.desiderium.retro.mixin.internal.asm.tree.ClassNode`.

## Develop a mod

Start with [Retrospectum Mod Template](https://github.com/DesideriumMC/RetrospectumModTemplate),
which uses [Retrospectum Loom](https://github.com/DesideriumMC/RetrospectumLoom).
The Gradle plugin ID is `dev.desiderium.retro.loom`, with the `retrospectum` DSL.

For integration probes, place the Loom checkout at `../RetrospectumLoom` or set
`retrospectumLoomCheckout`. See [verification](docs/VERIFYING.md).

## License

MIT. See [runtime components](docs/THIRD-PARTY.md) and
[upstream Mixin sources](runtime/mixin-bootstrap/UPSTREAM.md).
