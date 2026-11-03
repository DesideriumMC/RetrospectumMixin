# Verification

Configure JDK 17 for Gradle, JDK 8 for compilation and JDK 7 for the target API
and game runtime. Place Retrospectum Loom at `../RetrospectumLoom` or set
`retrospectumLoomCheckout`.

## Build and inspect

```sh
../RetrospectumLoom/gradlew -p ../RetrospectumLoom test
./gradlew build :mixin-mapping-probe:exportDevelopmentLaunches
python scripts/verify_artifacts.py
python scripts/verify_duplicate_runtime.py
```

The checks cover dependency hashes, Java class versions, relocated packages,
LaunchWrapper services and SRG refmaps.

## Development server

```sh
python scripts/verify_runtime.py --development samples/mixin-mapping-probe/build/retromixin/launches.json --output .work/development-server.log
```

The helper runs the member-mapping assertions, waits for startup, then saves and
stops the server. Use `--java /path/to/jdk8/bin/java` to select Java 8.

## Production server

Provide a Forge installation containing
`minecraftforge-universal-1.6.4-9.11.1.1345.jar`, `minecraft_server.1.6.4.jar`
and `libraries/`. The preparation helper creates a new test instance with the
Bootstrap and integration probes.

```sh
python scripts/prepare_production.py --base /path/to/forge-server --output .work/production --versioned-probe
python scripts/verify_runtime.py --production .work/production --java /path/to/jdk7/bin/java --output .work/production-server.log
```

On Windows, use `java.exe`.

## Client

```sh
python scripts/start_client.py --development samples/mixin-mapping-probe/build/retromixin/launches.json --output .work/development-client.log
```

Check world rendering, inventory, saving and normal shutdown.
