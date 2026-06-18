import { LayoutGrid, RefreshCw, Rows3 } from "lucide-react";
import { useEffect, useState } from "react";
import { Navigate } from "react-router-dom";

import { getApiError } from "../../api/client";
import { cancelPickupRequest, listPickupRequests } from "../../api/pickupRequests";
import CitizenRequestsList from "../../components/citizen/CitizenRequestsList";
import { useAuth } from "../../hooks/useAuth";

export default function CitizenRequestsPage() {
  const { user } = useAuth();
  const [requests, setRequests] = useState([]);
  const [viewMode, setViewMode] = useState("table");
  const [loading, setLoading] = useState(true);
  const [busyRequestId, setBusyRequestId] = useState(null);
  const [error, setError] = useState("");

  async function loadRequests() {
    setLoading(true);
    try {
      const data = await listPickupRequests();
      setRequests(data);
      setError("");
    } catch (err) {
      setError(getApiError(err, "Unable to load your pickup requests."));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadRequests();
  }, []);

  async function handleCancel(requestId) {
    setBusyRequestId(requestId);
    try {
      await cancelPickupRequest(requestId);
      await loadRequests();
    } catch (err) {
      setError(getApiError(err, "Unable to cancel this pickup request."));
    } finally {
      setBusyRequestId(null);
    }
  }

  if (user?.role !== "citizen") {
    return <Navigate to="/dashboard" replace />;
  }

  return (
    <div className="space-y-6">
      {error ? <p className="rounded-2xl bg-rose-100 px-4 py-3 text-sm text-rose-700">{error}</p> : null}

      <section className="glass-panel rounded-[2rem] border border-white/60 p-6 shadow-glow">
        <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.35em] text-leaf/70">My Requests</p>
            <h2 className="mt-2 font-display text-3xl text-ink">Pickup request board</h2>
            <p className="mt-2 text-sm text-ink/70">
              Switch between table and card layouts, open any request, and cancel pending ones without leaving the list.
            </p>
          </div>
          <div className="flex flex-wrap gap-3">
            <button
              type="button"
              onClick={() => setViewMode("table")}
              className={`inline-flex items-center gap-2 rounded-2xl px-4 py-3 text-sm font-semibold transition ${
                viewMode === "table" ? "bg-ink text-sand" : "border border-ink/10 bg-white/70 text-ink"
              }`}
            >
              <Rows3 className="h-4 w-4" />
              Table view
            </button>
            <button
              type="button"
              onClick={() => setViewMode("cards")}
              className={`inline-flex items-center gap-2 rounded-2xl px-4 py-3 text-sm font-semibold transition ${
                viewMode === "cards" ? "bg-ink text-sand" : "border border-ink/10 bg-white/70 text-ink"
              }`}
            >
              <LayoutGrid className="h-4 w-4" />
              Card view
            </button>
            <button
              type="button"
              onClick={loadRequests}
              className="inline-flex items-center gap-2 rounded-2xl border border-ink/10 bg-white/70 px-4 py-3 text-sm font-semibold text-ink transition hover:border-ink/20"
            >
              <RefreshCw className="h-4 w-4" />
              Refresh
            </button>
          </div>
        </div>
      </section>

      {loading ? <p className="text-sm text-ink/70">Loading your requests...</p> : null}

      {!loading && requests.length === 0 ? (
        <div className="glass-panel rounded-[2rem] border border-white/60 p-6 shadow-glow">
          <p className="font-display text-2xl text-ink">No requests created yet</p>
          <p className="mt-2 text-sm text-ink/70">
            Head back to the dashboard overview to create your first recyclable waste pickup request.
          </p>
        </div>
      ) : null}

      {requests.length > 0 ? (
        <CitizenRequestsList
          requests={requests}
          viewMode={viewMode}
          busyRequestId={busyRequestId}
          onCancel={handleCancel}
        />
      ) : null}
    </div>
  );
}
