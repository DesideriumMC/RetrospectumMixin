package dev.desiderium.retro.mixin.bootstrap;

import java.io.File;
import java.net.URL;
import java.util.Arrays;
import java.util.Enumeration;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;
import java.util.jar.JarFile;
import java.util.jar.Manifest;
import net.minecraft.launchwrapper.ITweaker;
import net.minecraft.launchwrapper.Launch;
import net.minecraft.launchwrapper.LaunchClassLoader;
import org.spongepowered.asm.launch.MixinTweaker;
import org.spongepowered.asm.mixin.Mixins;

/** One shared runtime, discovered by the unmodified Forge .1345 cascading tweaker path. */
public final class RetroMixinTweaker implements ITweaker {
    private final MixinTweaker delegate;
    private final Set<String> configs = new LinkedHashSet<String>();

    public RetroMixinTweaker() {
        Launch.classLoader.addClassLoaderExclusion("dev.desiderium.retro.mixin.internal.");
        verifyRuntime();
        org.apache.logging.log4j.core.config.Configurator.setRootLevel(org.apache.logging.log4j.Level.INFO);
        delegate = new MixinTweaker();
        System.out.println("[RETROMIXIN] shared Mixin 0.8.7 bootstrap; game JVM=" + System.getProperty("java.version"));
    }

    private static void verifyRuntime() {
        try {
            Set<String> sources = new LinkedHashSet<String>();
            Enumeration<URL> resources = Launch.classLoader.getResources("org/spongepowered/asm/launch/MixinBootstrap.class");
            while (resources.hasMoreElements()) sources.add(resources.nextElement().toExternalForm());
            if (sources.size() != 1) throw new IllegalStateException(
                "Expected one shared Mixin runtime; found " + sources + ". Remove embedded/duplicate Mixin runtimes.");
        } catch (java.io.IOException e) { throw new IllegalStateException("Cannot inspect Mixin runtime sources", e); }
    }

    public void acceptOptions(List<String> args, File gameDir, File assetsDir, String profile) {
        delegate.acceptOptions(args, gameDir, assetsDir, profile);
        addConfigs(System.getProperty("retromixin.mixin.configs", ""));
        File mods = new File(gameDir == null ? new File(".") : gameDir, "mods");
        discover(mods);
        discover(new File(mods, "1.6.4"));
    }

    private void discover(File directory) {
        File[] jars = directory.listFiles();
        if (jars == null) return;
        Arrays.sort(jars);
        for (File file : jars) {
            if (!file.isFile() || !file.getName().endsWith(".jar")) continue;
            try {
                JarFile jar = new JarFile(file);
                try {
                    Manifest manifest = jar.getManifest();
                    String declared = manifest == null ? null : manifest.getMainAttributes().getValue("MixinConfigs");
                    if (declared == null) continue;
                    Launch.classLoader.addURL(file.getCanonicalFile().toURI().toURL());
                    // Early config visibility must not cause a second @Mod discovery.
                    Class<?> manager = Class.forName("cpw.mods.fml.relauncher.CoreModManager", true, Launch.classLoader);
                    @SuppressWarnings("unchecked")
                    List<String> reparseable = (List<String>) manager.getMethod("getReparseableCoremods").invoke(null);
                    if (!reparseable.contains(file.getName())) reparseable.add(file.getName());
                    for (String name : declared.split(",", -1)) {
                        validateConfig(name.trim());
                        if (jar.getJarEntry(name.trim()) == null) throw new IllegalStateException("Missing config " + name);
                    }
                    // Early discovery is needed for ordinary Forge mods. Mixin 0.8.7
                    // caches and deduplicates configs by name if its platform agent
                    // encounters the same standard manifest entry later.
                    addConfigs(declared);
                } finally { jar.close(); }
            } catch (Exception e) { throw new IllegalStateException("Cannot discover Mixin configs in " + file, e); }
        }
    }

    private static void validateConfig(String name) {
        if (!name.matches("[A-Za-z0-9_./-]+\\.json") || name.contains("..") || name.startsWith("/"))
            throw new IllegalArgumentException("Mixin config must be a relative JSON resource path: " + name);
    }

    private void addConfigs(String declared) {
        if (declared.trim().length() == 0) return;
        for (String name : declared.split(",", -1)) {
            name = name.trim();
            validateConfig(name);
            if (configs.add(name)) {
                Mixins.addConfiguration(name);
                System.out.println("[RETROMIXIN] config=" + name);
            }
        }
    }

    public void injectIntoClassLoader(LaunchClassLoader loader) {
        // Explicit dev --tweakClass bypasses CoreModManager's manifest discovery.
        try {
            File self = new File(RetroMixinTweaker.class.getProtectionDomain().getCodeSource().getLocation().toURI());
            Class<?> manager = Class.forName("cpw.mods.fml.relauncher.CoreModManager", true, loader);
            @SuppressWarnings("unchecked")
            List<String> ignored = (List<String>) manager.getMethod("getLoadedCoremods").invoke(null);
            if (!ignored.contains(self.getName())) ignored.add(self.getName());
            Class<?> injection = Class.forName("cpw.mods.fml.relauncher.FMLInjectionData", true, loader);
            @SuppressWarnings("unchecked")
            List<String> containers = (List<String>) injection.getField("containers").get(null);
            // LaunchWrapper delegates the Tweaker package to its parent; keep the container in a separate package.
            String container = "dev.desiderium.retro.mixin.forge.RetroMixinModContainer";
            if (!containers.contains(container)) containers.add(container);
        } catch (Exception e) { throw new IllegalStateException("Cannot exclude shared runtime from Forge ASM4 discovery", e); }
        delegate.injectIntoClassLoader(loader);
        System.out.println("[RETROMIXIN] transformer chain=" + loader.getTransformers());
    }
    public String getLaunchTarget() { return delegate.getLaunchTarget(); }
    public String[] getLaunchArguments() { return delegate.getLaunchArguments(); }
}
