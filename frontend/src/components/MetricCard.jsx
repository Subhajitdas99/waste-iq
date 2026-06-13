export default function MetricCard({ label, value, hint }) {
  return (
    <div className="glass-panel rounded-3xl border border-white/60 p-5 shadow-glow">
      <p className="text-xs font-semibold uppercase tracking-[0.3em] text-leaf/70">{label}</p>
      <p className="mt-3 font-display text-4xl text-ink">{value}</p>
      <p className="mt-2 text-sm text-ink/70">{hint}</p>
    </div>
  );
}
