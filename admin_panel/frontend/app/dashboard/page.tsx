"use client";

import { useEffect, useState } from "react";
import { AdminShell } from "../../components/AdminShell";
import { MetricCard } from "../../components/MetricCard";
import { SectionHeader } from "../../components/SectionHeader";
import { apiFetch } from "../../lib/api";

type Dashboard = {
  total_users: number;
  active_users_24h: number;
  free_users: number;
  premium_users: number;
  premium_plus_users: number;
  trial_users: number;
  active_trial_users: number;
  total_payments: number;
  total_stars: number;
  total_gpt_chats: number;
  total_claude_chats: number;
};

export default function DashboardPage() {
  const [data, setData] = useState<Dashboard | null>(null);

  useEffect(() => {
    apiFetch<Dashboard>("/api/dashboard").then(setData);
  }, []);

  return (
    <AdminShell>
      <SectionHeader
        title="Dashboard"
        description="Premium read-only overview of PromptCraftAI users, monetization, trials and assistant activity."
      />
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        <MetricCard icon="👥" label="Users" value={data?.total_users ?? "—"} hint={`${data?.active_users_24h ?? "—"} active in 24h`} />
        <MetricCard icon="⭐" label="Premium" value={data?.premium_users ?? "—"} hint={`${data?.free_users ?? "—"} free users`} />
        <MetricCard icon="💎" label="Premium Plus" value={data?.premium_plus_users ?? "—"} hint="AI Workspace access" />
        <MetricCard icon="🎁" label="Trial" value={data?.active_trial_users ?? "—"} hint={`${data?.trial_users ?? "—"} total trials`} />
        <MetricCard icon="💰" label="Stars" value={data?.total_stars ?? "—"} hint={`${data?.total_payments ?? "—"} payments`} />
        <MetricCard icon="🤖" label="AI Requests" value={(data?.total_gpt_chats ?? 0) + (data?.total_claude_chats ?? 0) || "—"} hint={`${data?.total_gpt_chats ?? "—"} GPT · ${data?.total_claude_chats ?? "—"} Claude chats`} />
      </div>
    </AdminShell>
  );
}
