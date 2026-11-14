"use client";
import { useTheme } from "next-themes";
import { Toaster } from "sonner";
import { useMedia } from "@/hooks/use-media";

export function AppToaster() {
  const { resolvedTheme } = useTheme();
  const desktop = useMedia("(min-width: 1024px)");
  return (
    <Toaster
      theme={resolvedTheme === "dark" ? "dark" : "light"}
      position={desktop ? "top-right" : "bottom-center"}
      offset={{ top: 24, right: 24, bottom: 96 }}
      mobileOffset={{ bottom: 96, left: 16, right: 16 }}
      toastOptions={{
        unstyled: true,
        classNames: {
          toast:
            "glass flex w-full items-center gap-3 rounded-2xl px-4 py-3 text-sm font-semibold text-ink",
          success: "[&_[data-icon]]:text-success",
          error: "[&_[data-icon]]:text-danger",
          closeButton: "glass",
        },
      }}
    />
  );
}
