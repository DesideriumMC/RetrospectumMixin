# Runtime components

The shared Bootstrap retains Mixin's public package and relocates dependency
packages into `dev.desiderium.retro.mixin.internal`. The FML remapper bridge is adapted
from Mixin under its MIT license. LaunchWrapper-only service descriptors are
provided explicitly; ModLauncher entry points and annotation processors are
excluded from the player runtime.

| Component | Version | Notice source |
| --- | --- | --- |
| SpongePowered Mixin | 0.8.7 | Upstream JAR; `META-INF/LICENSE-Mixin.txt` |
| ASM modules | 9.7.1 | BSD notice from official Maven sources, `org/objectweb/asm/ClassReader.java` |
| Guava | 20.0 | Upstream tag `v20.0`, `COPYING` |
| Gson | 2.8.9 | Upstream tag `gson-parent-2.8.9`, `LICENSE` |
| Log4j API/Core | 2.12.4 | License/NOTICE files collected from both upstream JARs |

Runtime input SHA-256 values are recorded in `gradle/runtime-inputs.lock.json` and
verified before shading. The Gradle wrapper is pinned and retains its notices.

Runtime dependency notices are included in the Bootstrap JAR.
