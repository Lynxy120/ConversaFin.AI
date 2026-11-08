import { LayoutDashboard, Package, ReceiptText, Settings } from "lucide-react";

export const NAV = [
  { href: "/", label: "Dashboard", short: "Home", icon: LayoutDashboard },
  { href: "/catalog", label: "Catalog", short: "Catalog", icon: Package },
  {
    href: "/transactions",
    label: "Transactions",
    short: "History",
    icon: ReceiptText,
  },
  { href: "/settings", label: "Settings", short: "Profile", icon: Settings },
] as const;

export const isActive = (path: string, href: string) =>
  href === "/" ? path === "/" : path.startsWith(href);
