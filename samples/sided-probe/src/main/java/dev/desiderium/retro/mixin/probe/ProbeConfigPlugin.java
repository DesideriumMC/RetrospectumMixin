package dev.desiderium.retro.mixin.probe;

import java.util.List;
import java.util.Set;
import dev.desiderium.retro.mixin.internal.asm.tree.ClassNode;
import org.spongepowered.asm.mixin.extensibility.IMixinConfigPlugin;
import org.spongepowered.asm.mixin.extensibility.IMixinInfo;

/** Compiles against the same relocated API that the shared runtime exposes. */
public final class ProbeConfigPlugin implements IMixinConfigPlugin {
    public void onLoad(String mixinPackage) {}
    public String getRefMapperConfig() { return null; }
    public boolean shouldApplyMixin(String targetClassName, String mixinClassName) { return true; }
    public void acceptTargets(Set<String> myTargets, Set<String> otherTargets) {}
    public List<String> getMixins() { return null; }
    public void preApply(String name, ClassNode target, String mixin, IMixinInfo info) {
        if (target.name == null) throw new IllegalStateException("Missing target ClassNode");
        System.out.println("[RETROMIXIN] private ASM config plugin: " + target.name);
    }
    public void postApply(String name, ClassNode target, String mixin, IMixinInfo info) {}
}
