"use client";
import { SWRConfig } from "swr";
import { Toaster } from "sonner";
import { SwRegister } from "@/components/pwa/sw-register";
import { fetcher } from "@/lib/api";

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <SWRConfig
      value={{
        fetcher,
        revalidateOnFocus: false,
        shouldRetryOnError: false,
        dedupingInterval: 5000,
      }}
    >
      {children}
      <Toaster position="top-center" richColors closeButton />
      <SwRegister />
    </SWRConfig>
  );
}
