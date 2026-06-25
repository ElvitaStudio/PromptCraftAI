"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { API_BASE, setToken } from "../../lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError("");
    const response = await fetch(`${API_BASE}/api/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ password })
    });
    setLoading(false);
    if (!response.ok) {
      setError("Invalid password");
      return;
    }
    const data = (await response.json()) as { token: string };
    setToken(data.token);
    router.push("/dashboard");
  }

  return (
    <main className="flex min-h-screen items-center justify-center px-4">
      <form
        onSubmit={submit}
        className="premium-card w-full max-w-md space-y-6 p-8"
      >
        <div>
          <h1 className="text-3xl font-semibold">PromptCraftAI Admin</h1>
          <p className="mt-2 text-sm text-violet-100/65">
            Enter the admin panel password to open the read-only workspace.
          </p>
        </div>
        <input
          className="premium-input w-full"
          type="password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          placeholder="ADMIN_PANEL_PASSWORD"
        />
        {error ? <p className="text-sm text-red-300">{error}</p> : null}
        <button
          className="w-full rounded-xl bg-violet-500 px-4 py-3 text-sm font-semibold text-white shadow-premium transition hover:bg-violet-400 disabled:opacity-60"
          disabled={loading}
        >
          {loading ? "Signing in..." : "Sign in"}
        </button>
        <p className="text-xs text-white/35">
          Development fallback password: admin123
        </p>
      </form>
    </main>
  );
}
