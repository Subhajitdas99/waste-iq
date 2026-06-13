import { ArrowRight, MapPinned, Recycle, ShieldCheck, Truck } from "lucide-react";
import { Link } from "react-router-dom";

const features = [
  {
    icon: Recycle,
    title: "Citizens turn waste into action",
    body: "Create pickup requests in minutes, upload a waste photo, and track every collection from one dashboard."
  },
  {
    icon: Truck,
    title: "Collectors get qualified leads",
    body: "See open pickup requests across Kolkata, accept nearby jobs, and log completed weight after collection."
  },
  {
    icon: ShieldCheck,
    title: "Admins keep supply moving",
    body: "Monitor user growth, pickup volume, and completion metrics with one operational view."
  }
];

export default function HomePage() {
  return (
    <div className="min-h-screen px-4 py-6 sm:px-6 lg:px-10">
      <div className="mx-auto max-w-7xl">
        <div className="glass-panel overflow-hidden rounded-[2rem] border border-white/60 shadow-glow">
          <div className="grid gap-10 px-6 py-10 lg:grid-cols-[1.2fr_0.8fr] lg:px-10 lg:py-14">
            <div>
              <p className="inline-flex items-center gap-2 rounded-full bg-white/80 px-4 py-2 text-xs font-semibold uppercase tracking-[0.35em] text-leaf">
                <MapPinned className="h-4 w-4" />
                Launching In Kolkata
              </p>
              <h1 className="mt-6 max-w-3xl font-display text-5xl leading-tight text-ink sm:text-6xl">
                Waste pickup, routed to the right collector before recyclables go missing.
              </h1>
              <p className="mt-6 max-w-2xl text-lg leading-8 text-ink/75">
                Waste-IQ is a recyclable waste marketplace for neighborhoods, informal scrap collectors, and city
                operators who need supply and demand to meet faster.
              </p>
              <div className="mt-8 flex flex-col gap-4 sm:flex-row">
                <Link
                  to="/register"
                  className="inline-flex items-center justify-center gap-2 rounded-2xl bg-ink px-6 py-4 font-semibold text-sand transition hover:bg-leaf"
                >
                  Create account
                  <ArrowRight className="h-4 w-4" />
                </Link>
                <Link
                  to="/login"
                  className="inline-flex items-center justify-center rounded-2xl border border-ink/10 bg-white/70 px-6 py-4 font-semibold text-ink transition hover:border-ink/20"
                >
                  Sign in
                </Link>
              </div>
            </div>

            <div className="rounded-[2rem] bg-ink p-6 text-sand">
              <div className="rounded-[1.5rem] border border-white/10 bg-white/5 p-5">
                <p className="text-xs uppercase tracking-[0.35em] text-sand/60">MVP Workflow</p>
                <div className="mt-6 space-y-4">
                  <div className="rounded-2xl bg-white/10 p-4">
                    <p className="font-display text-2xl">1. Citizen</p>
                    <p className="mt-1 text-sm text-sand/70">Creates pickup request with location and photo.</p>
                  </div>
                  <div className="rounded-2xl bg-white/10 p-4">
                    <p className="font-display text-2xl">2. Collector</p>
                    <p className="mt-1 text-sm text-sand/70">Accepts the lead and schedules a pickup.</p>
                  </div>
                  <div className="rounded-2xl bg-gradient-to-r from-ember to-coral p-4 text-ink">
                    <p className="font-display text-2xl">3. Completed</p>
                    <p className="mt-1 text-sm text-ink/80">Collected waste is weighed and the request closes.</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="grid gap-5 border-t border-white/60 bg-white/30 px-6 py-8 lg:grid-cols-3 lg:px-10">
            {features.map(({ icon: Icon, title, body }) => (
              <div key={title} className="rounded-3xl bg-white/70 p-5">
                <Icon className="h-8 w-8 text-leaf" />
                <h2 className="mt-4 font-display text-2xl text-ink">{title}</h2>
                <p className="mt-3 text-sm leading-7 text-ink/70">{body}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
