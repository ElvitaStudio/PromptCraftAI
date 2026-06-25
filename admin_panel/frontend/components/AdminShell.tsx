"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { clearToken } from "../lib/api";

const nav = [
  ["/dashboard", "Dashboard"],
  ["/users", "Users"],
  ["/payments", "Payments"],
  ["/trials", "Trials"],
  ["/stats", "AI Statistics"]
];

export function AdminShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();

  return (
    <div className="min-h-screen">
      <aside className="fixed inset-x-0 top-0 z-20 border-b border-white/10 bg-graphite-950/80 backdrop-blur xl:inset-y-0 xl:left-0 xl:right-auto xl:w-72 xl:border-b-0 xl:border-r">
        <div className="flex items-center justify-between px-5 py-4 xl:block xl:p-6">
          <div>
            <div className="text-lg font-semibold tracking-tight">
              PromptCraftAI
            </div>
            <div className="text-xs text-violet-200/60">Admin Workspace</div>
          </div>
          <button
            className="rounded-xl border border-white/10 px-3 py-2 text-xs text-violet-100 hover:border-violet-400/60 xl:mt-8 xl:w-full"
            onClick={() => {
              clearToken();
              router.push("/login");
            }}
          >
            Logout
          </button>
        </div>
        <nav className="flex gap-2 overflow-x-auto px-5 pb-4 xl:block xl:space-y-2 xl:px-6">
          {nav.map(([href, label]) => {
            const active = pathname === href;
            return (
              <Link
                key={href}
                href={href}
                className={`whitespace-nowrap rounded-xl px-4 py-3 text-sm transition ${
                  active
                    ? "bg-violet-500 text-white shadow-premium"
                    : "text-violet-100/70 hover:bg-white/10 hover:text-white"
                }`}
              >
                {label}
              </Link>
            );
          })}
        </nav>
      </aside>
      <main className="px-4 pb-10 pt-32 sm:px-6 xl:ml-72 xl:px-10 xl:pt-10">
        {children}
      </main>
    </div>
  );
}
