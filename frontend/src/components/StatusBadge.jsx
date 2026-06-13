const statusStyles = {
  pending: "bg-amber-100 text-amber-800",
  accepted: "bg-sky-100 text-sky-800",
  completed: "bg-emerald-100 text-emerald-800",
  cancelled: "bg-rose-100 text-rose-800"
};

export default function StatusBadge({ status }) {
  const style = statusStyles[status] || "bg-stone-200 text-stone-800";
  return (
    <span className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] ${style}`}>
      {status}
    </span>
  );
}
