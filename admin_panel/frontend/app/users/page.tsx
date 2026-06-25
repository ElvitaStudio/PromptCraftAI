"use client";

import { useEffect, useState } from "react";
import { AdminShell } from "../../components/AdminShell";
import { SectionHeader } from "../../components/SectionHeader";
import { apiFetch } from "../../lib/api";

type UserRow = {
  telegram_id: number;
  username: string | null;
  first_name: string | null;
  plan: string;
  plan_until: string | null;
  trial_until: string | null;
  ai_requests_used: number;
  created_at: string;
  last_activity: string | null;
  is_blocked: boolean;
};

type PageData = {
  items: UserRow[];
  page: number;
  total_pages: number;
  total: number;
};

export default function UsersPage() {
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [data, setData] = useState<PageData | null>(null);

  useEffect(() => {
    const params = new URLSearchParams({
      page: String(page),
      page_size: "25",
      sort: "last_activity",
      direction: "desc"
    });
    if (search) params.set("search", search);
    apiFetch<PageData>(`/api/users?${params}`).then(setData);
  }, [page, search]);

  return (
    <AdminShell>
      <SectionHeader
        title="Users"
        description="Search, paginate and review PromptCraftAI users without mutating bot data."
      />
      <div className="premium-card overflow-hidden">
        <div className="flex flex-col gap-3 border-b border-white/10 p-4 sm:flex-row sm:items-center sm:justify-between">
          <input
            className="premium-input w-full sm:max-w-xs"
            placeholder="Search username or Telegram ID"
            value={search}
            onChange={(event) => {
              setPage(1);
              setSearch(event.target.value);
            }}
          />
          <div className="text-sm text-white/50">{data?.total ?? 0} users</div>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full text-left text-sm">
            <thead className="bg-white/[0.04] text-xs uppercase tracking-wider text-violet-200/60">
              <tr>
                {["Telegram ID", "Username", "Имя", "Тариф", "Trial", "AI", "Дата регистрации", "Последняя активность", "Blocked"].map((head) => (
                  <th key={head} className="px-4 py-3">{head}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-white/10">
              {data?.items.map((user) => (
                <tr key={user.telegram_id} className="hover:bg-white/[0.03]">
                  <td className="px-4 py-3">{user.telegram_id}</td>
                  <td className="px-4 py-3">{user.username ? `@${user.username}` : "—"}</td>
                  <td className="px-4 py-3">{user.first_name ?? "—"}</td>
                  <td className="px-4 py-3 text-violet-200">{user.plan}</td>
                  <td className="px-4 py-3">{user.trial_until ?? "—"}</td>
                  <td className="px-4 py-3">{user.ai_requests_used}</td>
                  <td className="px-4 py-3">{user.created_at}</td>
                  <td className="px-4 py-3">{user.last_activity ?? "—"}</td>
                  <td className="px-4 py-3">{user.is_blocked ? "Yes" : "No"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="flex items-center justify-between border-t border-white/10 p-4">
          <button className="rounded-xl border border-white/10 px-4 py-2 disabled:opacity-40" disabled={page <= 1} onClick={() => setPage((value) => value - 1)}>Previous</button>
          <span className="text-sm text-white/50">Page {data?.page ?? page} / {data?.total_pages ?? 1}</span>
          <button className="rounded-xl border border-white/10 px-4 py-2 disabled:opacity-40" disabled={page >= (data?.total_pages ?? 1)} onClick={() => setPage((value) => value + 1)}>Next</button>
        </div>
      </div>
    </AdminShell>
  );
}
