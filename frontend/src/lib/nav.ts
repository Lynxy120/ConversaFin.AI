import {
  ClipboardList,
  Package,
  PiggyBank,
  ReceiptText,
  Settings,
  Store,
  type LucideIcon,
} from "lucide-react";

export interface NavItem {
  href: string;
  label: string;
  short: string;
  icon: LucideIcon;
}

export const NAV_GROUPS: { label: string; items: NavItem[] }[] = [
  {
    label: "Dashboard",
    items: [
      { href: "/", label: "Bisnis", short: "Bisnis", icon: Store },
      {
        href: "/dashboard/keuangan",
        label: "Keuangan",
        short: "Keuangan",
        icon: PiggyBank,
      },
    ],
  },
  {
    label: "Operasional",
    items: [
      {
        href: "/orders",
        label: "Orders",
        short: "Orders",
        icon: ClipboardList,
      },
      { href: "/catalog", label: "Catalog", short: "Catalog", icon: Package },
      {
        href: "/transactions",
        label: "Transactions",
        short: "History",
        icon: ReceiptText,
      },
      {
        href: "/settings",
        label: "Settings",
        short: "Profile",
        icon: Settings,
      },
    ],
  },
];

export const NAV: NavItem[] = NAV_GROUPS.flatMap((g) => g.items);
export const MOBILE_NAV: NavItem[] = NAV.filter(
  (n) => n.href !== "/transactions",
); // 5 tabs max on phones

export const isActive = (path: string, href: string) =>
  href === "/" ? path === "/" : path.startsWith(href);
