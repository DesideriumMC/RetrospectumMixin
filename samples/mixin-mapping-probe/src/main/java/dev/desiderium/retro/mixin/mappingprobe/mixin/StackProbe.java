package dev.desiderium.retro.mixin.mappingprobe.mixin;

import dev.desiderium.retro.mixin.mappingprobe.MappingProbeMod;
import net.minecraft.item.Item;
import net.minecraft.item.ItemStack;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Overwrite;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.Redirect;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

@Mixin(ItemStack.class)
public abstract class StackProbe {
    @Shadow public int itemID;
    @Shadow public abstract int getMaxStackSize();

    @Inject(method = "getMaxStackSize()I", at = @At("HEAD"))
    private void retromixin$inject(CallbackInfoReturnable<Integer> callback) {
        if (itemID == Item.appleRed.itemID) MappingProbeMod.injected = true;
    }

    @Redirect(method = "getMaxStackSize()I", at = @At(value = "INVOKE", target = "Lnet/minecraft/item/ItemStack;getItem()Lnet/minecraft/item/Item;"))
    private Item retromixin$redirect(ItemStack stack) {
        MappingProbeMod.redirected = true;
        return stack.getItem();
    }

    /**
     * @author RetroMixin
     * @reason Controlled P2 fixture proving AP-generated overwrite renaming.
     */
    @Overwrite
    public boolean isStackable() {
        MappingProbeMod.overwritten = true;
        return getMaxStackSize() > 1;
    }
}
