export function MetricCard({
  icon,
  label,
  value,
  hint
}: {
  icon: string;
  label: string;
  value: number | string;
  hint?: string;
}) {
  return (
    <div className="premium-card p-5">
      <div className="mb-6 flex items-center justify-between">
        <span className="text-2xl">{icon}</span>
        <span className="rounded-full bg-violet-500/15 px-3 py-1 text-xs text-violet-200">
          Live
        </span>
      </div>
      <div className="text-3xl font-semibold tracking-tight">{value}</div>
      <div className="mt-1 text-sm text-violet-100/70">{label}</div>
      {hint ? <div className="mt-4 text-xs text-white/40">{hint}</div> : null}
    </div>
  );
}
