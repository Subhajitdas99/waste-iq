import { useEffect, useState } from "react";

import api, { getApiError } from "../../api/client";
import RequestCard from "../../components/RequestCard";

export default function CollectorDashboard() {
  const [requests, setRequests] = useState([]);
  const [weights, setWeights] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [busyRequestId, setBusyRequestId] = useState(null);

  async function loadRequests() {
    setLoading(true);
    try {
      const response = await api.get("/pickup-requests");
      setRequests(response.data);
      setError("");
    } catch (err) {
      setError(getApiError(err, "Unable to load collector requests."));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadRequests();
  }, []);

  async function acceptRequest(requestId) {
    setBusyRequestId(requestId);
    try {
      await api.post(`/collector/accept/${requestId}`);
      await loadRequests();
    } catch (err) {
      setError(getApiError(err, "Unable to accept request."));
    } finally {
      setBusyRequestId(null);
    }
  }

  async function completeRequest(requestId) {
    const weight = Number(weights[requestId]);
    if (!weight || weight <= 0) {
      setError("Please enter a valid collected weight before completing.");
      return;
    }
    setBusyRequestId(requestId);
    try {
      await api.post(`/collector/complete/${requestId}`, { weight_kg: weight });
      await loadRequests();
    } catch (err) {
      setError(getApiError(err, "Unable to complete request."));
    } finally {
      setBusyRequestId(null);
    }
  }

  // Open to all collectors
  const openRequests = requests.filter((r) => r.status === "pending");

  // Only this collector's accepted/completed jobs (assignment exists)
  const myAssignments = requests.filter(
    (r) => r.status !== "pending" && r.assignment !== null
  );

  return (
    <div className="space-y-8">
      {error ? (
        <p className="rounded-2xl bg-rose-100 px-4 py-3 text-sm text-rose-700">{error}</p>
      ) : null}

      {/* Open leads */}
      <section>
        <div className="mb-5 flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.35em] text-leaf/70">
              Available leads
            </p>
            <h2 className="mt-2 font-display text-3xl text-ink">Open pickup requests</h2>
          </div>
          <button
            type="button"
            onClick={loadRequests}
            className="rounded-2xl border border-ink/10 bg-white/70 px-4 py-3 text-sm font-semibold text-ink"
          >
            Refresh
          </button>
        </div>

        {loading ? <p className="text-sm text-ink/70">Loading requests...</p> : null}

        <div className="space-y-5">
          {openRequests.map((request) => (
            <RequestCard
              key={request.id}
              request={request}
              actions={
                <button
                  type="button"
                  disabled={busyRequestId === request.id}
                  onClick={() => acceptRequest(request.id)}
                  className="w-full rounded-2xl bg-ink px-4 py-3 font-semibold text-sand transition hover:bg-leaf disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {busyRequestId === request.id ? "Accepting..." : "Accept request"}
                </button>
              }
            />
          ))}

          {!loading && openRequests.length === 0 ? (
            <div className="glass-panel rounded-[2rem] border border-white/60 p-6 shadow-glow">
              <p className="font-display text-2xl text-ink">No open leads right now</p>
              <p className="mt-2 text-sm text-ink/70">
                Check back soon for new recyclable waste requests in Kolkata.
              </p>
            </div>
          ) : null}
        </div>
      </section>

      {/* My assignments */}
      <section>
        <div className="mb-5">
          <p className="text-xs font-semibold uppercase tracking-[0.35em] text-leaf/70">
            Your assignments
          </p>
          <h2 className="mt-2 font-display text-3xl text-ink">Accepted and completed jobs</h2>
        </div>

        <div className="space-y-5">
          {myAssignments.map((request) => (
            <RequestCard
              key={request.id}
              request={request}
              actions={
                request.status === "accepted" ? (
                  <div className="space-y-3">
                    <input
                      type="number"
                      min="0.1"
                      step="0.1"
                      placeholder="Collected weight (kg)"
                      value={weights[request.id] || ""}
                      onChange={(e) =>
                        setWeights((current) => ({
                          ...current,
                          [request.id]: e.target.value,
                        }))
                      }
                      className="w-full rounded-2xl border border-ink/10 bg-white/80 px-4 py-3 outline-none transition focus:border-leaf"
                    />
                    <button
                      type="button"
                      disabled={busyRequestId === request.id || !weights[request.id]}
                      onClick={() => completeRequest(request.id)}
                      className="w-full rounded-2xl bg-leaf px-4 py-3 font-semibold text-sand transition hover:bg-moss disabled:cursor-not-allowed disabled:opacity-60"
                    >
                      {busyRequestId === request.id ? "Completing..." : "Mark completed"}
                    </button>
                  </div>
                ) : null
              }
            />
          ))}

          {!loading && myAssignments.length === 0 ? (
            <div className="glass-panel rounded-[2rem] border border-white/60 p-6 shadow-glow">
              <p className="font-display text-2xl text-ink">No assignments yet</p>
              <p className="mt-2 text-sm text-ink/70">
                Accepted jobs and completed collections will show up here.
              </p>
            </div>
          ) : null}
        </div>
      </section>
    </div>
  );
}