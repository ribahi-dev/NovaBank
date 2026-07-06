// Tableau de bord directeur : KPI glass + graphiques Plotly + skeletons.
import { AlertTriangle, ArrowLeftRight, Gauge, Users, Wallet } from "lucide-react";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "@/api/client";
import type { Kpi, TrendPoint, TypeDistribution } from "@/api/types";
import { PageHeader } from "@/components/layout/AppLayout";
import { KpiCard } from "@/components/shared/KpiCard";
import { chartLayout, Plot } from "@/components/shared/Plot";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useTheme } from "@/contexts/ThemeContext";
import { fmtDay, fmtMAD } from "@/lib/format";

const TYPE_LABELS: Record<string, string> = {
  deposit: "Dépôts",
  withdrawal: "Retraits",
  transfer: "Virements",
};

export default function Dashboard() {
  const navigate = useNavigate();
  const { theme } = useTheme();
  const dark = theme === "dark";
  const [kpi, setKpi] = useState<Kpi | null>(null);
  const [trends, setTrends] = useState<TrendPoint[]>([]);
  const [distribution, setDistribution] = useState<TypeDistribution[]>([]);

  useEffect(() => {
    api.get<Kpi>("/analytics/kpi").then(({ data }) => setKpi(data));
    api.get<TrendPoint[]>("/analytics/trends?days=30").then(({ data }) => setTrends(data));
    api.get<TypeDistribution[]>("/analytics/distribution").then(({ data }) => setDistribution(data));
  }, []);

  return (
    <>
      <PageHeader
        title="Tableau de bord"
        subtitle="Vue d'ensemble de l'activité de l'agence — 30 derniers jours"
      />

      {!kpi ? (
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-5">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-5">
          <KpiCard index={0} label="Clients actifs" value={kpi.total_clients} icon={Users} />
          <KpiCard index={1} label="Comptes" value={kpi.total_accounts} icon={Wallet} />
          <KpiCard
            index={2}
            label="Transactions"
            value={kpi.total_transactions}
            sub={`${fmtMAD(kpi.total_deposits)} déposés`}
            icon={ArrowLeftRight}
          />
          <KpiCard
            index={3}
            label="Alertes ouvertes"
            value={kpi.open_alerts}
            sub="cliquer pour traiter"
            icon={AlertTriangle}
            danger={kpi.open_alerts > 0}
            onClick={() => navigate("/fraude")}
          />
          <KpiCard
            index={4}
            label="Risque moyen"
            value={kpi.average_risk_score === null ? "—" : `${kpi.average_risk_score.toFixed(1)}`}
            sub="score sur 100"
            icon={Gauge}
          />
        </div>
      )}

      <div className="mt-6 grid gap-4 xl:grid-cols-5">
        <Card className="xl:col-span-3">
          <CardHeader>
            <CardTitle>Activité quotidienne</CardTitle>
          </CardHeader>
          {trends.length === 0 ? (
            <Skeleton className="h-72" />
          ) : (
            <Plot
              data={[
                {
                  x: trends.map((t) => fmtDay(t.day)),
                  y: trends.map((t) => t.transaction_count),
                  type: "bar",
                  marker: { color: "#f08100", opacity: 0.9 },
                  hovertemplate: "%{y} opérations<extra></extra>",
                },
              ]}
              layout={chartLayout(dark, { height: 300 })}
              config={{ displayModeBar: false, responsive: true }}
              style={{ width: "100%" }}
            />
          )}
        </Card>
        <Card className="xl:col-span-2">
          <CardHeader>
            <CardTitle>Répartition des opérations</CardTitle>
          </CardHeader>
          {distribution.length === 0 ? (
            <Skeleton className="h-72" />
          ) : (
            <Plot
              data={[
                {
                  labels: distribution.map((d) => TYPE_LABELS[d.transaction_type] ?? d.transaction_type),
                  values: distribution.map((d) => d.count),
                  type: "pie",
                  hole: 0.55,
                  marker: { colors: ["#f08100", "#2c3338", "#fdb913"] },
                  textinfo: "label+percent",
                },
              ]}
              layout={chartLayout(dark, { height: 300, showlegend: false, margin: { t: 8, r: 8, b: 8, l: 8 } })}
              config={{ displayModeBar: false, responsive: true }}
              style={{ width: "100%" }}
            />
          )}
        </Card>
      </div>
    </>
  );
}
