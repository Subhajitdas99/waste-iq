import { LayoutDashboard, ListChecks } from "lucide-react";
import { NavLink } from "react-router-dom";

const links = [
  {
    to: "/dashboard",
    label: "Overview",
    icon: LayoutDashboard,
    end: true
  },
  {
    to: "/dashboard/requests",
    label: "My Requests",
    icon: ListChecks
  }
];

export default function CitizenDashboardNav() {
  return (
    <nav className="mb-8 flex flex-wrap gap-3">
      {links.map(({ to, label, icon: Icon, end }) => (
        <NavLink
          key={to}
          to={to}
          end={end}
          className={({ isActive }) =>
            `inline-flex items-center gap-2 rounded-2xl border px-4 py-3 text-sm font-semibold transition ${
              isActive
                ? "border-ink/10 bg-ink text-sand shadow-glow"
                : "border-white/60 bg-white/60 text-ink hover:border-ink/20"
            }`
          }
        >
          <Icon className="h-4 w-4" />
          {label}
        </NavLink>
      ))}
    </nav>
  );
}
