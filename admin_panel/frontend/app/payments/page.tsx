"use client";

import { useEffect, useState } from "react";
import { AdminShell } from "../../components/AdminShell";
import { SectionHeader } from "../../components/SectionHeader";
import { apiFetch } from "../../lib/api";

type Payment = {
  user_id: number;
  tariff: string;
  stars: number;
  charge_id: string;
  payment_date: string;
};

export default function PaymentsPage() {
  const [items, setItems] = useState<Payment[]>([]);

  useEffect(() => {
    apiFetch<{ items: Payment[] }>("/api/payments").then((data) =>
      setItems(data.items)
    );
  }, []);

  return (
    <AdminShell>
      <SectionHeader
        title="Payments"
        description="Telegram Stars payment ledger, charge IDs and paid tariffs."
      />
      <div className="premium-card overflow-x-auto">
        <table className="min-w-full text-left text-sm">
          <thead className="bg-white/[0.04] text-xs uppercase tracking-wider text-violet-200/60">
            <tr>
              {["Дата", "Пользователь", "Тариф", "Stars", "Charge ID"].map((head) => (
                <th key={head} className="px-4 py-3">{head}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-white/10">
            {items.map((payment) => (
              <tr key={payment.charge_id}>
                <td className="px-4 py-3">{payment.payment_date}</td>
                <td className="px-4 py-3">{payment.user_id}</td>
                <td className="px-4 py-3 text-violet-200">{payment.tariff}</td>
                <td className="px-4 py-3">{payment.stars}</td>
                <td className="px-4 py-3 font-mono text-xs text-white/60">{payment.charge_id}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </AdminShell>
  );
}
