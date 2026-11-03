# Mixin source subset

The 12 Java files under `src/upstream/java` are unmodified source files from the
official `org.spongepowered:mixin:0.8.7:sources` artifact, under the upstream MIT
license. Their individual SHA-256 values and the source archive hash are recorded
in `gradle/mixin-upstream.lock.json`; compilation verifies the source hashes.

These LaunchWrapper/FML integration files were distributed as Java 8 bytecode.
This project recompiles them with JDK 8 against the Java 7 runtime API and emits
Java 7 bytecode. Other Mixin classes come from the pinned official binary artifact.
Duplicate upstream binary entries are superseded by the compiled project output.

The project-owned `RemapperAdapterFML` is adapted from Mixin and preserves its MIT
notice. It uses reflection across the boundary between private ASM and Forge's
original ASM4.

The runtime retains LaunchWrapper providers and removes ModLauncher adapters,
annotation processors and unrelated modern Forge platform adapters. ASM, Guava,
Gson and Log4j dependencies are relocated into `dev.desiderium.retro.mixin.internal` while
Mixin's public API keeps its `org.spongepowered.asm` namespace.
