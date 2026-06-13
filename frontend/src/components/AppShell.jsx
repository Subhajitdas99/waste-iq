import { LogOut, Recycle, Users } from "lucide-react";
import { Link } from "react-router-dom";

import { useAuth } from "../hooks/useAuth";

const roleTitles = {
  citizen: "Citizen Workspace",
  collector: "Collector Console",
  admin: "Admin Command Center"
};

export default function AppShell({ title, subtitle, children }) {
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen px-4 py-6 sm:px-6 lg:px-10">
      <div className="mx-auto max-w-7xl">
        <div className="glass-panel mb-8 rounded-[2rem] border border-white/60 px-6 py-5 shadow-glow">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <Link to="/" className="inline-flex items-center gap-3 font-display text-2xl text-ink">
                <span className="rounded-2xl bg-ink px-3 py-2 text-sand">
                  <Recycle className="h-5 w-5" />
                </span>
                Waste-IQ
              </Link>
              <p className="mt-3 text-sm uppercase tracking-[0.3em] text-leaf/70">
                Kolkata Recycling Marketplace
              </p>
            </div>
            <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
              <div className="rounded-3xl bg-white/70 px-4 py-3">
                <p className="text-sm text-ink/60">{roleTitles[user?.role] || "Waste-IQ"}</p>
                <p className="font-semibold text-ink">{user?.name}</p>
              </div>
              <button
                type="button"
                onClick={logout}
                className="inline-flex items-center justify-center gap-2 rounded-2xl bg-ink px-4 py-3 text-sm font-semibold text-sand transition hover:bg-leaf"
              >
                <LogOut className="h-4 w-4" />
                Logout
              </button>
            </div>
          </div>
          <div className="mt-6 flex items-center gap-3 rounded-3xl bg-gradient-to-r from-ember/10 via-coral/20 to-moss/10 px-4 py-4">
            <Users className="h-5 w-5 text-leaf" />
            <div>
              <h1 className="font-display text-3xl text-ink">{title}</h1>
              <p className="text-sm text-ink/70">{subtitle}</p>
            </div>
          </div>
        </div>
        {children}
      </div>
    </div>
  );
}
