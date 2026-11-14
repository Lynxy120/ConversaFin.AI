"use client";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { GlassCard } from "@/components/ui/glass-card";
import { inputCls } from "@/components/ui/field";

export default function Login() {
  const router = useRouter();
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setBusy(true);
    setErr("");
    const f = new FormData(e.currentTarget);
    const res = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user: f.get("user"), pass: f.get("pass") }),
    });
    if (!res.ok) {
      setErr("Username atau password salah");
      setBusy(false);
      return;
    }
    const next = new URLSearchParams(window.location.search).get("next") ?? "/";
    router.replace(next.startsWith("/") && !next.startsWith("//") ? next : "/");
    router.refresh();
  }

  return (
    <main className="grid min-h-dvh place-items-center p-4">
      <GlassCard className="w-full max-w-sm p-6">
        <Image
          src="/icons/icon-192.png"
          width={48}
          height={48}
          alt=""
          className="mb-4 rounded-xl"
        />
        <h1 className="text-xl font-extrabold">Masuk ke KasirChat.AI</h1>
        <form onSubmit={submit} className="mt-5 flex flex-col gap-3">
          <input
            name="user"
            autoComplete="username"
            placeholder="Username"
            required
            className={inputCls}
          />
          <input
            name="pass"
            type="password"
            autoComplete="current-password"
            placeholder="Password"
            required
            className={inputCls}
          />
          {err && (
            <p role="alert" className="text-sm text-danger">
              {err}
            </p>
          )}
          <Button type="submit" disabled={busy}>
            {busy ? "Memproses…" : "Masuk"}
          </Button>
        </form>
      </GlassCard>
    </main>
  );
}
