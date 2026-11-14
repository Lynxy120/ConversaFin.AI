"use client";
import { ThemeProvider } from "next-themes";
import { SWRConfig } from "swr";
import { SwRegister } from "@/components/pwa/sw-register";
import { AppToaster } from "@/components/toaster";
import { fetcher } from "@/lib/api";

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ThemeProvider
      attribute="data-theme"
      defaultTheme="system"
      enableSystem
      disableTransitionOnChange
    >
      <SWRConfig
        value={{
          fetcher,
          revalidateOnFocus: false,
          shouldRetryOnError: false,
          dedupingInterval: 5000,
        }}
      >
        {children}
        <AppToaster />
        <SwRegister />
      </SWRConfig>
    </ThemeProvider>
  );
}
