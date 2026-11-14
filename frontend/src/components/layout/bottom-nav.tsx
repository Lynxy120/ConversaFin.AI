"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/cn";
import { MOBILE_NAV, isActive } from "@/lib/nav";

export function BottomNav() {
  const path = usePathname();
  return (
    <nav
      aria-label="Main"
      className="glass fixed inset-x-0 bottom-0 z-30 flex pb-[env(safe-area-inset-bottom)] lg:hidden"
    >
      {MOBILE_NAV.map(({ href, short, icon: Icon }) => (
        <Link
          key={href}
          href={href}
          aria-current={isActive(path, href) ? "page" : undefined}
          className={cn(
            "flex min-h-16 flex-1 flex-col items-center justify-center gap-1 text-xs",
            isActive(path, href) ? "font-bold text-primary" : "text-muted",
          )}
        >
          <Icon size={22} /> {short}
        </Link>
      ))}
    </nav>
  );
}
