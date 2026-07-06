// Détection de fraude (directeur) : file d'alertes + détail explicable.
import { motion } from "framer-motion";
import { ShieldAlert } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import api, { apiError } from "@/api/client";
import type { Alert } from "@/api/types";
import { PageHeader } from "@/components/layout/AppLayout";
import { ScoreBadge } from "@/components/shared/ScoreBadge";
import { Badge, LEVEL_TONE, STATUS_TONE } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState, Table, Td, Th, Tr } from "@/components/ui/table";
import { TableSkeleton } from "@/components/ui/skeleton";
import { useToast } from "@/contexts/ToastContext";
import { fmtDate, fmtMAD } from "@/lib/format";

const TABS = [
  { key: "open", label: "Ouvertes" },
  { key: "in_progress", label: "En cours" },
  { key: "closed", label: "Clôturées" },
] as const;

const LEVELS: Record<Alert["level"], string> = {
  low: "faible", medium: "moyen", high: "élevé", critical: "critique",
};

export default function Fraud() {
  const { toast } = useToast();
  const [tab, setTab] = useState<(typeof TABS)[number]["key"]>("open");
  const [alerts, setAlerts] = useState<Alert[] | null>(null);
  const [selected, setSelected] = useState<Alert | null>(null);

  const load = useCallback(async () => {
    setAlerts(null);
    const { data } = await api.get<Alert[]>("/alerts", { params: { status_filter: tab } });
    setAlerts(data);
    setSelected(null);
  }, [tab]);

  useEffect(() => {
    load();
  }, [load]);

  async function changeStatus(alert: Alert, status: "in_progress" | "closed") {
    try {
      await api.patch(`/alerts/${alert.id}`, { status });
      toast("success", status === "closed" ? "Alerte clôturée." : "Alerte prise en charge.");
      load();
    } catch (err) {
      toast("error", apiError(err));
    }
  }

  return (
    <>
      <PageHeader
        title="Détection de fraude"
        subtitle="Anomalies détectées par le moteur IA et événements de sécurité"
        actions={
          <div className="flex gap-1.5">
            {TABS.map((t) => (
              <Button
                key={t.key}
                size="sm"
                variant={tab === t.key ? "default" : "secondary"}
                onClick={() => setTab(t.key)}
              >
                {t.label}
              </Button>
            ))}
          </div>
        }
      />

      <div className="grid gap-4 xl:grid-cols-5">
        <Card className="xl:col-span-3">
          {!alerts ? (
            <TableSkeleton rows={6} />
          ) : (
            <Table>
              <thead>
                <tr><Th>Date</Th><Th>Niveau</Th><Th>Type</Th><Th>Statut</Th></tr>
              </thead>
              <tbody>
                {alerts.map((a) => (
                  <Tr
                    key={a.id}
                    clickable
                    onClick={() => setSelected(a)}
                    className={selected?.id === a.id ? "bg-primary-soft/70" : ""}
                  >
                    <Td className="text-muted-foreground">{fmtDate(a.created_at)}</Td>
                    <Td><Badge tone={LEVEL_TONE[a.level]}>{LEVELS[a.level]}</Badge></Td>
                    <Td>{a.alert_type === "transaction_risk" ? "Transaction à risque" : "Sécurité connexion"}</Td>
                    <Td><Badge tone={STATUS_TONE[a.status]}>{a.status}</Badge></Td>
                  </Tr>
                ))}
              </tbody>
            </Table>
          )}
          {alerts?.length === 0 && <EmptyState>Aucune alerte dans cette catégorie.</EmptyState>}
        </Card>

        <Card glass className="xl:col-span-2 self-start">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ShieldAlert size={17} className="text-danger" /> Détail de l'alerte
            </CardTitle>
          </CardHeader>
          {!selected ? (
            <div className="grid h-40 place-items-center text-sm text-muted-foreground">
              Sélectionnez une alerte dans la liste.
            </div>
          ) : (
            <motion.div
              key={selected.id}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
            >
              <div className="mb-3 flex items-center gap-2">
                <Badge tone={LEVEL_TONE[selected.level]}>{LEVELS[selected.level]}</Badge>
                <span className="text-xs text-muted-foreground">créée le {fmtDate(selected.created_at)}</span>
              </div>
              <p className="text-sm leading-relaxed">{selected.message}</p>

              {selected.transaction && (
                <div className="mt-4 space-y-2 rounded-lg border border-border bg-card/60 p-3.5 text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Montant</span>
                    <strong>{fmtMAD(selected.transaction.amount)}</strong>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Ville</span>
                    <span>{selected.transaction.city ?? "—"}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">Score IA</span>
                    <ScoreBadge score={selected.transaction.risk_score?.score} />
                  </div>
                  {selected.transaction.risk_score && (
                    <div className="rounded-r-lg border-l-4 border-primary bg-primary-soft p-3 text-[13px] leading-relaxed">
                      {selected.transaction.risk_score.explanation}
                    </div>
                  )}
                </div>
              )}

              {selected.status !== "closed" ? (
                <div className="mt-4 flex gap-2">
                  {selected.status === "open" && (
                    <Button variant="secondary" size="sm" onClick={() => changeStatus(selected, "in_progress")}>
                      Prendre en charge
                    </Button>
                  )}
                  <Button size="sm" onClick={() => changeStatus(selected, "closed")}>
                    Clôturer l'alerte
                  </Button>
                </div>
              ) : (
                selected.closed_at && (
                  <p className="mt-3 text-xs text-muted-foreground">
                    Clôturée le {fmtDate(selected.closed_at)} — une alerte clôturée est immuable.
                  </p>
                )
              )}
            </motion.div>
          )}
        </Card>
      </div>
    </>
  );
}
