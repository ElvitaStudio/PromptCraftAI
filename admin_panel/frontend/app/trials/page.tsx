"use client";

import { useEffect, useState } from "react";
import { AdminShell } from "../../components/AdminShell";
import { SectionHeader } from "../../components/SectionHeader";
import { apiFetch } from "../../lib/api";

type Trial = {
  telegram_id: number;
  username: string | null;
  first_name: string | null;
  trial_expires_at: string | null;
  trial_requests_used: number;
};

function TrialList({ title, items }: { title: string; items: Trial[] }) {
  return (
    <section className="premium-card p-5">
      <h2 className="mb-4 text-xl font-semibold">{title}</h2>
      <div className="space-y-3">
        {items.map((item) => (
          <div key={`${title}-${item.telegram_id}`} className="rounded-xl border border-white/10 bg-black/20 p-4">
            <div className="font-medium">{item.first_name ?? item.telegram_id}</div>
            <div className="text-sm text-white/50">@{item.username ?? "—"} · {item.trial_requests_used}/15 requests</div>
            <div className="text-xs text-violet-200/60">{item.trial_expires_at ?? "No expiry"}</div>
          </div>
        ))}
        {!items.length ? <p className="text-sm text-white/45">No users</p> : null}
      </div>
    </section>
  );
}

export default function TrialsPage() {
  const [data, setData] = useState<{ active: Trial[]; expired: Trial[] } | null>(null);

  useEffect(() => {
    apiFetch<{ active: Trial[]; expired: Trial[] }>("/api/trials").then(setData);
  }, []);

  return (
    <AdminShell>
      <SectionHeader
        title="Trials"
        description="Premium Plus trial users split by active and expired state."
      />
      <div className="grid gap-5 lg:grid-cols-2">
        <TrialList title="Активные" items={data?.active ?? []} />
        <TrialList title="Истёкшие" items={data?.expired ?? []} />
      </div>
    </AdminShell>
  );
}
