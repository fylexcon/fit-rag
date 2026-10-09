"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";

type Mode = "login" | "register";

const copy: Record<Mode, { title: string; submit: string; alt: string; altHref: string; altLabel: string }> = {
  login: {
    title: "Sign in",
    submit: "Sign in",
    alt: "No account yet?",
    altHref: "/register",
    altLabel: "Create one",
  },
  register: {
    title: "Create your account",
    submit: "Create account",
    alt: "Already registered?",
    altHref: "/login",
    altLabel: "Sign in",
  },
};

export function AuthForm({ mode }: { mode: Mode }) {
  const { login, register, isAuthenticated, ready } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const text = copy[mode];

  useEffect(() => {
    if (ready && isAuthenticated) router.replace("/");
  }, [ready, isAuthenticated, router]);

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      if (mode === "login") await login(email, password);
      else await register(email, password);
      router.replace("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="flex flex-1 items-center justify-center px-4 py-16">
      <form
        onSubmit={onSubmit}
        className="w-full max-w-sm space-y-5 rounded-xl border border-zinc-200 bg-white p-8 shadow-sm dark:border-zinc-800 dark:bg-zinc-900"
      >
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-emerald-600">Fitness AI</p>
          <h1 className="mt-1 text-2xl font-semibold">{text.title}</h1>
        </div>

        <label className="block space-y-1">
          <span className="text-sm font-medium">Email</span>
          <input
            type="email"
            required
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="input"
          />
        </label>

        <label className="block space-y-1">
          <span className="text-sm font-medium">Password</span>
          <input
            type="password"
            required
            minLength={mode === "register" ? 8 : undefined}
            autoComplete={mode === "login" ? "current-password" : "new-password"}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="input"
          />
        </label>

        {error && (
          <p role="alert" className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700 dark:bg-red-950 dark:text-red-300">
            {error}
          </p>
        )}

        <button type="submit" disabled={submitting} className="btn-primary w-full">
          {submitting ? "Please wait…" : text.submit}
        </button>

        <p className="text-center text-sm text-zinc-500">
          {text.alt}{" "}
          <Link href={text.altHref} className="font-medium text-emerald-600 hover:underline">
            {text.altLabel}
          </Link>
        </p>
      </form>
    </main>
  );
}
