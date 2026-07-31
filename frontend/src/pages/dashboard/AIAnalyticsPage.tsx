import {
  CheckCircle2,
  ClipboardList,
  Clock,
  Home,
  Leaf,
  Percent,
  RefreshCcw,
  Recycle,
  Scale,
  Sparkles,
  Store,
  TrendingUp,
  Truck,
  Users,
  XCircle,
  type LucideIcon,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/EmptyState";
import { PageHeader } from "@/components/PageHeader";
import { SeoHead } from "@/components/seo/SeoHead";
import { StatsCard } from "@/components/dashboard/StatsCard";
import { CarbonImpactCard } from "@/components/dashboard/CarbonImpactCard";
import { DashboardCard } from "@/components/dashboard/DashboardCard";
import { LoadingSkeleton } from "@/components/dashboard/LoadingSkeleton";
import { MaterialBreakdown } from "@/components/dashboard/MaterialBreakdown";
import { MonthlyTrendChart } from "@/components/dashboard/MonthlyTrendChart";
import {
  useAnalyticsInsights,
  useAnalyticsOverview,
  useCarbonSavings,
  useCollectorPerformance,
  useDealerPerformance,
  useMaterialBreakdown,
  useMonthlyAnalytics,
} from "@/hooks/useAnalytics";
import { getApiErrorMessage } from "@/lib/api-error";
import {
  formatAnalyticsNumber,
  formatPercent,
  formatResponseTime,
} from "@/lib/analytics";
import { formatWeight } from "@/lib/pickup";
import type { AnalyticsInsight } from "@/types/analytics";

const INSIGHT_ICON_BY_KEY: Record<string, LucideIcon> = {
  most_recycled_material: Recycle,
  top_collector: Truck,
  top_dealer: Store,
  carbon_savings: Leaf,
  pickup_trend: TrendingUp,
};

function InsightIcon({ insight }: { insight: AnalyticsInsight }) {
  const Icon = INSIGHT_ICON_BY_KEY[insight.key] ?? Sparkles;
  return <Icon className="h-4 w-4" />;
}

function ErrorAlert({ message }: { message: string }) {
  return (
    <div
      role="alert"
      className="rounded-2xl border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive"
    >
      {message}
    </div>
  );
}

export function AIAnalyticsPage() {
  const overviewQuery = useAnalyticsOverview();
  const materialsQuery = useMaterialBreakdown();
  const monthlyQuery = useMonthlyAnalytics();
  const collectorsQuery = useCollectorPerformance();
  const dealersQuery = useDealerPerformance();
  const carbonQuery = useCarbonSavings();
  const insightsQuery = useAnalyticsInsights();

  const queries = [
    overviewQuery,
    materialsQuery,
    monthlyQuery,
    collectorsQuery,
    dealersQuery,
    carbonQuery,
    insightsQuery,
  ];
  const isRefreshing = queries.some((query) => query.isFetching);

  const overview = overviewQuery.data;

  return (
    <>
      <SeoHead
        title="AI Analytics Dashboard"
        description="Platform-wide AI analytics: pickup trends, material distribution, collector and dealer performance, and carbon savings."
        path="/admin/analytics"
      />

      <PageHeader
        title="AI Analytics Dashboard"
        description="Rule-based insights and live analytics computed from the admin analytics API."
        actions={
          <Button
            type="button"
            variant="outline"
            className="gap-2"
            disabled={isRefreshing}
            onClick={() => {
              void Promise.all(queries.map((query) => query.refetch()));
            }}
          >
            <RefreshCcw className="h-4 w-4" />
            {isRefreshing ? "Refreshing..." : "Refresh"}
          </Button>
        }
      />

      <section
        aria-label="Overview key performance indicators"
        className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5"
      >
        {overviewQuery.isPending && !overview ? (
          <LoadingSkeleton count={3} />
        ) : overviewQuery.isError ? (
          <ErrorAlert
            message={getApiErrorMessage(
              overviewQuery.error,
              "Unable to load analytics overview.",
            )}
          />
        ) : overview ? (
          <>
            <StatsCard
              label="Total Users"
              value={formatAnalyticsNumber(overview.total_users)}
              helper="All registered accounts."
              icon={<Users className="h-5 w-5" />}
            />
            <StatsCard
              label="Citizens"
              value={formatAnalyticsNumber(overview.citizens)}
              helper="Citizen accounts."
              icon={<Home className="h-5 w-5" />}
            />
            <StatsCard
              label="Collectors"
              value={formatAnalyticsNumber(overview.collectors)}
              helper="Collector accounts."
              icon={<Truck className="h-5 w-5" />}
            />
            <StatsCard
              label="Dealers"
              value={formatAnalyticsNumber(overview.dealers)}
              helper="Dealer accounts."
              icon={<Store className="h-5 w-5" />}
            />
            <StatsCard
              label="Total Pickups"
              value={formatAnalyticsNumber(overview.total_pickups)}
              helper="All requests created."
              icon={<ClipboardList className="h-5 w-5" />}
            />
            <StatsCard
              label="Completed Pickups"
              value={formatAnalyticsNumber(overview.completed_pickups)}
              helper="Requests fully collected."
              icon={<CheckCircle2 className="h-5 w-5" />}
              tone="success"
            />
            <StatsCard
              label="Pending Pickups"
              value={formatAnalyticsNumber(overview.pending_pickups)}
              helper="Requests awaiting a collector."
              icon={<Clock className="h-5 w-5" />}
              tone="warning"
            />
            <StatsCard
              label="Cancelled Pickups"
              value={formatAnalyticsNumber(overview.cancelled_pickups)}
              helper="Requests cancelled."
              icon={<XCircle className="h-5 w-5" />}
              tone="danger"
            />
            <StatsCard
              label="Total Weight"
              value={formatWeight(overview.total_weight_kg)}
              helper="Reported collection weight."
              icon={<Scale className="h-5 w-5" />}
            />
            <StatsCard
              label="Completion Rate"
              value={formatPercent(overview.completed_rate)}
              helper="Completed vs total requests."
              icon={<Percent className="h-5 w-5" />}
              tone="primary"
            />
          </>
        ) : null}
      </section>

      <section className="mt-8 grid gap-6 xl:grid-cols-[1.4fr_1fr]">
        <DashboardCard
          title="Monthly Pickup Trend"
          description="Total and completed pickups over the last 12 months from GET /admin/analytics/monthly."
        >
          {monthlyQuery.isPending && !monthlyQuery.data ? (
            <LoadingSkeleton count={2} />
          ) : monthlyQuery.isError ? (
            <ErrorAlert
              message={getApiErrorMessage(
                monthlyQuery.error,
                "Unable to load monthly analytics.",
              )}
            />
          ) : monthlyQuery.data ? (
            <MonthlyTrendChart data={monthlyQuery.data} />
          ) : null}
        </DashboardCard>

        <DashboardCard
          title="Material Distribution"
          description="Completed pickups grouped by detected material from GET /admin/analytics/materials."
        >
          {materialsQuery.isPending && !materialsQuery.data ? (
            <LoadingSkeleton count={2} />
          ) : materialsQuery.isError ? (
            <ErrorAlert
              message={getApiErrorMessage(
                materialsQuery.error,
                "Unable to load material distribution.",
              )}
            />
          ) : materialsQuery.data ? (
            <MaterialBreakdown data={materialsQuery.data} />
          ) : null}
        </DashboardCard>
      </section>

      <section className="mt-8 grid gap-6 xl:grid-cols-2">
        <DashboardCard
          title="Collector Performance"
          description="Ranked collector metrics from GET /admin/analytics/collectors."
        >
          {collectorsQuery.isPending && !collectorsQuery.data ? (
            <LoadingSkeleton count={2} />
          ) : collectorsQuery.isError ? (
            <ErrorAlert
              message={getApiErrorMessage(
                collectorsQuery.error,
                "Unable to load collector performance.",
              )}
            />
          ) : collectorsQuery.data && collectorsQuery.data.length > 0 ? (
            <div className="space-y-3">
              {collectorsQuery.data.map((collector) => (
                <div
                  key={collector.collector_id}
                  className="flex flex-col gap-2 rounded-2xl border bg-muted/20 p-4 sm:flex-row sm:items-center sm:justify-between"
                >
                  <div>
                    <p className="font-medium">{collector.collector_name}</p>
                    <p className="text-sm text-muted-foreground">
                      {formatAnalyticsNumber(collector.completed_jobs)} completed
                      job{collector.completed_jobs === 1 ? "" : "s"}
                    </p>
                  </div>
                  <div className="flex items-center gap-4 text-sm">
                    <span className="rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1 font-semibold text-emerald-700 dark:text-emerald-300">
                      {formatPercent(collector.completion_rate)}
                    </span>
                    <span className="text-muted-foreground">
                      Avg response {formatResponseTime(collector.average_response_time)}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState
              title="No collector activity"
              description="Collector performance appears once pickups are assigned and completed."
            />
          )}
        </DashboardCard>

        <DashboardCard
          title="Dealer Performance"
          description="Dealer material processing from GET /admin/analytics/dealers."
        >
          {dealersQuery.isPending && !dealersQuery.data ? (
            <LoadingSkeleton count={2} />
          ) : dealersQuery.isError ? (
            <ErrorAlert
              message={getApiErrorMessage(
                dealersQuery.error,
                "Unable to load dealer performance.",
              )}
            />
          ) : dealersQuery.data && dealersQuery.data.length > 0 ? (
            <div className="space-y-3">
              {dealersQuery.data.map((dealer) => (
                <div
                  key={dealer.dealer_id}
                  className="flex flex-col gap-2 rounded-2xl border bg-muted/20 p-4 sm:flex-row sm:items-center sm:justify-between"
                >
                  <div>
                    <p className="font-medium">{dealer.dealer_name}</p>
                    <p className="text-sm text-muted-foreground">
                      {formatAnalyticsNumber(dealer.materials_processed)} material
                      {dealer.materials_processed === 1 ? "" : "s"} processed
                    </p>
                  </div>
                  <span className="text-sm font-semibold">
                    {formatWeight(dealer.total_weight)}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState
              title="No dealer activity"
              description="Dealer performance appears once inventory lots are sold."
            />
          )}
        </DashboardCard>
      </section>

      <section className="mt-8 grid gap-6">
        <DashboardCard
          title="Recent Analytics"
          description="Deterministic rule-based insights computed server-side from live platform data."
        >
          {insightsQuery.isPending && !insightsQuery.data ? (
            <LoadingSkeleton count={2} />
          ) : insightsQuery.isError ? (
            <ErrorAlert
              message={getApiErrorMessage(
                insightsQuery.error,
                "Unable to load analytics insights.",
              )}
            />
          ) : insightsQuery.data && insightsQuery.data.length > 0 ? (
            <ul className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
              {insightsQuery.data.map((insight) => (
                <li
                  key={insight.key}
                  className="flex items-start gap-3 rounded-2xl border bg-muted/20 p-4"
                >
                  <span className="rounded-xl bg-primary/10 p-2 text-primary">
                    <InsightIcon insight={insight} />
                  </span>
                  <div>
                    <p className="font-semibold">{insight.title}</p>
                    <p className="mt-0.5 text-sm text-muted-foreground">
                      {insight.message}
                    </p>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <EmptyState
              title="No insights yet"
              description="Insights will appear once there is platform activity to analyse."
            />
          )}
        </DashboardCard>
      </section>

      <section className="mt-8">
        <DashboardCard
          title="Carbon Savings"
          description="Estimated environmental impact from GET /admin/analytics/carbon."
        >
          {carbonQuery.isPending && !carbonQuery.data ? (
            <LoadingSkeleton count={1} />
          ) : carbonQuery.isError ? (
            <ErrorAlert
              message={getApiErrorMessage(
                carbonQuery.error,
                "Unable to load carbon savings.",
              )}
            />
          ) : (
            <CarbonImpactCard data={carbonQuery.data ?? null} />
          )}
        </DashboardCard>
      </section>
    </>
  );
}
