"""Verify the shipped legacy agent rejects a missing Forge remapper with a cause."""
import argparse
import os
from pathlib import Path
import subprocess
import tempfile

SOURCE = '''import java.lang.reflect.*;
import java.net.URL;
import net.minecraft.launchwrapper.Launch;
import net.minecraft.launchwrapper.LaunchClassLoader;
public class RemapperFailureProbe {
    public static void main(String[] args) throws Exception {
        Launch.blackboard = new java.util.HashMap<String, Object>();
        Launch.classLoader = new LaunchClassLoader(new URL[0]);
        Launch.classLoader.addClassLoaderExclusion("org.spongepowered.asm.");
        Class<?> agent = Class.forName("org.spongepowered.asm.launch.platform.MixinPlatformAgentFMLLegacy");
        Class<?> unsafeType = Class.forName("sun.misc.Unsafe");
        Field field = unsafeType.getDeclaredField("theUnsafe");
        field.setAccessible(true);
        Object unsafe = field.get(null);
        Object instance = unsafeType.getMethod("allocateInstance", Class.class).invoke(unsafe, agent);
        Method install = agent.getDeclaredMethod("injectRemapper");
        install.setAccessible(true);
        try {
            install.invoke(instance);
            throw new AssertionError("Missing Forge remapper was silently accepted");
        } catch (InvocationTargetException failure) {
            Throwable cause = failure.getCause();
            if (!(cause instanceof IllegalStateException) || cause.getCause() == null)
                throw new AssertionError("Missing initialization failure/root cause", cause);
            boolean missingRemapper = false;
            for (Throwable root = cause; root != null; root = root.getCause()) {
                if (root instanceof ClassNotFoundException
                    && root.getMessage().contains("FMLDeobfuscatingRemapper")) missingRemapper = true;
            }
            if (!missingRemapper) throw new AssertionError("Unexpected failure", cause);
            System.out.println("REQUIRED REMAPPER FAILURE PROPAGATED");
        }
    }
}
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--launchwrapper', type=Path, required=True)
    parser.add_argument('--asm', type=Path, required=True)
    parser.add_argument('--jopt', type=Path, required=True)
    parser.add_argument('--java', type=Path, required=True)
    args = parser.parse_args()
    classpath = os.pathsep.join(str(p.resolve()) for p in
                               (args.runtime, args.launchwrapper, args.asm, args.jopt))
    javac = Path(os.environ['JAVA_HOME']) / 'bin' / ('javac.exe' if os.name == 'nt' else 'javac')
    with tempfile.TemporaryDirectory(prefix='retrospectum-remapper-') as directory:
        source = Path(directory) / 'RemapperFailureProbe.java'
        source.write_text(SOURCE)
        subprocess.run([str(javac), '-source', '7', '-target', '7', '-cp', classpath,
                        str(source)], check=True, timeout=60)
        subprocess.run([str(args.java), '-cp', directory + os.pathsep + classpath,
                        'RemapperFailureProbe'], check=True, timeout=30)


if __name__ == '__main__':
    main()
