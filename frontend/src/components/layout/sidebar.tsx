"use client";
import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/cn";
import { NAV, isActive } from "@/lib/nav";
import { LogoutButton } from "./logout-button";

export function Sidebar() {
  const path = usePathname();
  return (
    <aside className="glass fixed inset-y-0 left-0 z-30 hidden w-[250px] flex-col p-4 lg:flex">
      <div className="mb-8 flex items-center gap-3 px-2">
        <Image
          src="/icons/icon-192.png"
          width={36}
          height={36}
          alt=""
          className="rounded-xl"
        />
        <span className="text-lg font-extrabold">
          KasirChat<span className="text-primary">.AI</span>
        </span>
      </div>
      <nav className="flex flex-1 flex-col gap-1">
        {NAV.map(({ href, label, icon: Icon }) => (
          <Link
            key={href}
            href={href}
            aria-current={isActive(path, href) ? "page" : undefined}
            className={cn(
              "flex min-h-11 items-center gap-3 rounded-xl px-3 text-sm transition",
              isActive(path, href)
                ? "bg-primary/10 font-bold text-primary"
                : "text-muted hover:bg-primary-light",
            )}
          >
            <Icon size={20} /> {label}
          </Link>
        ))}
      </nav>
      <LogoutButton className="w-full" />
    </aside>
  );
}
