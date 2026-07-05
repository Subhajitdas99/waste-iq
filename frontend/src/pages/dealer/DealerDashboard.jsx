import { ClipboardCheck, FileBadge2, ShieldCheck } from "lucide-react";
import { useEffect, useState } from "react";

import { getApiError } from "../../api/errors";
import { createDealerProfile, getDealerProfile, updateDealerProfile } from "../../api/dealers";
import MetricCard from "../../components/MetricCard";
import StatusBadge from "../../components/StatusBadge";
import DealerProfileForm from "../../components/dealer/DealerProfileForm";
import { formatDateTime } from "../../utils/pickupRequests";

const statusContent = {
  pending: {
    title: "Verification pending",
    body: "Your profile is under review. Dealer marketplace access stays locked until an admin approves the account."
  },
  approved: {
    title: "Verification approved",
    body: "Your business profile has been approved. Marketplace features are still intentionally out of scope for this release."
  },
  rejected: {
    title: "Verification rejected",
    body: "Please review your details, update the profile, and resubmit for another admin review."
  }
};

export default function DealerDashboard() {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  async function loadProfile() {
    setLoading(true);
    try {
      const data = await getDealerProfile();
      setProfile(data);
      setError("");
    } catch (err) {
      if (err?.response?.status === 404) {
        setProfile(null);
        setError("");
      } else {
        setError(getApiError(err, "Unable to load dealer profile."));
      }
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadProfile();
  }, []);

  async function handleSave(payload) {
    setSaving(true);
    try {
      const data = profile ? await updateDealerProfile(payload) : await createDealerProfile(payload);
      setProfile(data);
      setError("");
    } catch (err) {
      setError(getApiError(err, "Unable to save dealer profile."));
    } finally {
      setSaving(false);
    }
  }

  const currentStatus = profile?.verification_status || "pending";
  const statusCopy = statusContent[currentStatus] || statusContent.pending;

  return (
    <div className="space-y-8">
      {error ? <p className="rounded-2xl bg-rose-100 px-4 py-3 text-sm text-rose-700">{error}</p> : null}

      <section className="glass-panel overflow-hidden rounded-[2rem] border border-white/60 shadow-glow">
        <div className="bg-gradient-to-br from-ink via-leaf to-moss px-6 py-8 text-sand sm:px-8">
          <p className="text-xs font-semibold uppercase tracking-[0.35em] text-sand/70">Dealer Verification</p>
          <h2 className="mt-3 max-w-3xl font-display text-4xl leading-tight">
            Build your verified buyer identity first. Dealer marketplace features remain intentionally disabled for now.
          </h2>
          <p className="mt-4 max-w-2xl text-sm leading-7 text-sand/75">
            This release only covers dealer profile submission, admin review, and status tracking. No dealer listings,
            pricing, or order actions are included yet.
          </p>
        </div>

        <div className="grid gap-5 bg-white/25 px-6 py-6 md:grid-cols-3 sm:px-8">
          <MetricCard
            label="Profile Completion"
            value={`${profile?.profile_completion || 0}%`}
            hint="Required dealer identity and business fields completed"
          />
          <div className="glass-panel rounded-3xl border border-white/60 p-5 shadow-glow">
            <p className="text-xs font-semibold uppercase tracking-[0.3em] text-leaf/70">Verification Status</p>
            <div className="mt-4">
              <StatusBadge status={currentStatus} />
            </div>
            <p className="mt-4 text-sm text-ink/70">{statusCopy.body}</p>
          </div>
          <MetricCard
            label="Approval Date"
            value={profile?.approved_at ? formatDateTime(profile.approved_at) : "Awaiting Review"}
            hint="Shown after the admin approves your dealer profile"
          />
        </div>
      </section>

      <section className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
        <div className="glass-panel rounded-[2rem] border border-white/60 p-6 shadow-glow">
          <div className="flex items-center gap-3">
            <ClipboardCheck className="h-5 w-5 text-leaf" />
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.35em] text-leaf/70">Dealer Profile</p>
              <h3 className="mt-2 font-display text-3xl text-ink">
                {profile ? "Update business information" : "Submit your business details"}
              </h3>
            </div>
          </div>
          <p className="mt-3 text-sm text-ink/70">
            Changes to an approved or rejected profile automatically move the account back to pending review so the admin
            can verify the updated details.
          </p>

          <div className="mt-6">
            <DealerProfileForm profile={profile} submitting={saving} onSubmit={handleSave} />
          </div>
        </div>

        <div className="space-y-6">
          <div className="glass-panel rounded-[2rem] border border-white/60 p-6 shadow-glow">
            <div className="flex items-center gap-3">
              <ShieldCheck className="h-5 w-5 text-leaf" />
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.35em] text-leaf/70">Review Outcome</p>
                <h3 className="mt-2 font-display text-3xl text-ink">{statusCopy.title}</h3>
              </div>
            </div>
            <p className="mt-4 text-sm leading-7 text-ink/75">{statusCopy.body}</p>

            {loading ? <p className="mt-4 text-sm text-ink/60">Loading dealer verification details...</p> : null}

            {profile ? (
              <div className="mt-6 rounded-[2rem] bg-white/70 p-5">
                <p className="text-xs uppercase tracking-[0.28em] text-ink/45">Materials accepted</p>
                <div className="mt-4 flex flex-wrap gap-3">
                  {profile.materials_accepted.map((item) => (
                    <span key={item} className="rounded-full bg-white px-4 py-2 text-sm font-medium text-ink shadow-sm">
                      {item}
                    </span>
                  ))}
                </div>
              </div>
            ) : null}
          </div>

          <div className="glass-panel rounded-[2rem] border border-white/60 p-6 shadow-glow">
            <div className="flex items-center gap-3">
              <FileBadge2 className="h-5 w-5 text-leaf" />
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.35em] text-leaf/70">Release Boundary</p>
                <h3 className="mt-2 font-display text-3xl text-ink">Not included yet</h3>
              </div>
            </div>
            <div className="mt-5 space-y-3">
              {[
                "No dealer marketplace listings or lot browsing.",
                "No dealer verification automation beyond admin approve or reject actions.",
                "No dealer pricing, transaction, reservation, or profile marketplace permissions."
              ].map((item) => (
                <div key={item} className="rounded-3xl bg-white/70 p-4 text-sm leading-7 text-ink/75">
                  {item}
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
