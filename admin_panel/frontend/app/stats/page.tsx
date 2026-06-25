"use client";

import { useEffect, useState } from "react";
import { AdminShell } from "../../components/AdminShell";
import { MetricCard } from "../../components/MetricCard";
import { SectionHeader } from "../../components/SectionHeader";
import { apiFetch } from "../../lib/api";

type Stats = {
  gpt_requests: number;
  claude_requests: number;
  total_ai_requests: number;
  average_requests_per_user: number;
};

export default function StatsPage() {
  const [stats, setStats] = useState<Stats | null>(null);

  useEffect(() => {
    apiFetch<Stats>("/api/stats").then(setStats);
  }, []);

  return (
    <AdminShell>
      <SectionHeader
        title="AI Statistics"
        description="GPT and Claude usage across prompt generation and assistant workspaces."
      />
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard icon="🟢" label="GPT" value={stats?.gpt_requests ?? "—"} />
        <MetricCard icon="🟠" label="Claude" value={stats?.claude_requests ?? "—"} />
        <MetricCard icon="🤖" label="Всего запросов" value={stats?.total_ai_requests ?? "—"} />
        <MetricCard icon="∅" label="Среднее на пользователя" value={stats?.average_requests_per_user ?? "—"} />
      </div>
    </AdminShell>
  );
}
