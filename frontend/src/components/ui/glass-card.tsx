import { cn } from "@/lib/cn";

export function GlassCard({ className, ...p }: React.ComponentProps<"div">) {
  return <div className={cn("glass rounded-2xl", className)} {...p} />;
}
