package dev.desiderium.retro.mixin.probe;

import cpw.mods.fml.common.Mod;
import cpw.mods.fml.common.event.FMLInitializationEvent;

@Mod(modid = "retromixinp1", name = "RetroMixin P1 Mixin Probe", version = "0.1.0-p1")
public final class ProbeMod {
    @Mod.EventHandler
    public void init(FMLInitializationEvent event) {
        System.out.println("[RETROMIXIN-P1] probe mod initialized");
    }
}
