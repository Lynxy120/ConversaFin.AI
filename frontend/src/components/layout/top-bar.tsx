"use client";
import { Search } from "lucide-react";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { ThemeToggle } from "@/components/theme-toggle";

export function TopBar() {
  const router = useRouter();
  return (
    <div className="sticky top-[env(safe-area-inset-top)] z-20 mx-auto max-w-6xl px-4 pt-3 md:px-8 lg:pt-5">
      <header className="glass flex items-center justify-between gap-3 rounded-2xl px-3 py-2">
        <div className="flex items-center gap-2 lg:hidden">
          <Image
            src="/icons/icon-192.png"
            width={32}
            height={32}
            alt=""
            className="rounded-lg"
          />
          <span className="font-extrabold tracking-tight">
            KasirChat<span className="text-primary">.AI</span>
          </span>
        </div>
        <form
          role="search"
          className="relative hidden max-w-md flex-1 lg:block"
          onSubmit={(e) => {
            e.preventDefault();
            const q = String(
              new FormData(e.currentTarget).get("q") ?? "",
            ).trim();
            router.push(
              q ? `/transactions?q=${encodeURIComponent(q)}` : "/transactions",
            );
          }}
        >
          <Search
            size={17}
            className="pointer-events-none absolute top-1/2 left-4 -translate-y-1/2 text-muted"
          />
          <input
            name="q"
            aria-label="Search transactions"
            placeholder="Search transactions"
            className="field min-h-12 w-full rounded-xl pr-4 pl-11 text-sm"
          />
        </form>
        <ThemeToggle />
      </header>
    </div>
  );
}
