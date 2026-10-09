"use client";

import Link from "next/link";
import { useAuth } from "@/context/AuthContext";

export function AppHeader({ children }: { children?: React.ReactNode }) {
  const { logout } = useAuth();

  return (
    <header className="border-b border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3">
        <Link href="/" className="font-semibold tracking-tight">
          <span className="text-emerald-600">Fitness</span> AI
        </Link>
        <div className="flex items-center gap-2">
          {children}
          <button type="button" onClick={logout} className="btn-secondary">
            Log out
          </button>
        </div>
      </div>
    </header>
  );
}
