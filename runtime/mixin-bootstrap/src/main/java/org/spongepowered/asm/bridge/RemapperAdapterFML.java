/*
 * Adapted from Mixin, Copyright (c) SpongePowered and contributors.
 * Licensed under the MIT license; see META-INF/LICENSE-Mixin.txt.
 * RetroMixin change: delegate across the isolated ASM boundary with reflection.
 */
package org.spongepowered.asm.bridge;

import java.lang.reflect.Method;
import net.minecraft.launchwrapper.Launch;
import org.objectweb.asm.commons.Remapper;
import org.spongepowered.asm.mixin.extensibility.IRemapper;

/** Reflective bridge between relocated ASM and Forge's original ASM4 remapper. */
public final class RemapperAdapterFML extends RemapperAdapter {
    private final Object fml;
    private final Method unmap;

    private RemapperAdapterFML(Object fml) throws Exception {
        super(new ReflectiveRemapper(fml));
        this.fml = fml;
        this.unmap = fml.getClass().getMethod("unmap", String.class);
    }

    public static IRemapper create() {
        try {
            Class<?> type = Class.forName("cpw.mods.fml.common.asm.transformers.deobf.FMLDeobfuscatingRemapper", true, Launch.classLoader);
            IRemapper bridge = new RemapperAdapterFML(type.getField("INSTANCE").get(null));
            System.out.println("[RETROMIXIN] isolated FML remapper bridge installed");
            return bridge;
        } catch (Exception e) {
            throw new IllegalStateException("Cannot bridge Forge .1345 remapper", e);
        }
    }

    @Override public String unmap(String name) { return invoke(unmap, fml, name); }

    private static String invoke(Method method, Object receiver, String... args) {
        try { return (String) method.invoke(receiver, (Object[]) args); }
        catch (Exception e) { throw new IllegalStateException("FML remapper call failed: " + method, e); }
    }

    private static final class ReflectiveRemapper extends Remapper {
        private final Object receiver;
        private final Method map, method, field;
        ReflectiveRemapper(Object receiver) throws Exception {
            this.receiver = receiver;
            Class<?> type = receiver.getClass();
            map = type.getMethod("map", String.class);
            method = type.getMethod("mapMethodName", String.class, String.class, String.class);
            field = type.getMethod("mapFieldName", String.class, String.class, String.class);
        }
        @Override public String map(String name) { return invoke(map, receiver, name); }
        @Override public String mapMethodName(String owner, String name, String desc) { return invoke(method, receiver, owner, name, desc); }
        @Override public String mapFieldName(String owner, String name, String desc) { return invoke(field, receiver, owner, name, desc); }
    }
}
