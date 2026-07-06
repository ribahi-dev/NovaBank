// Historique des transactions : filtres type + risque, scores visibles.
import { useEffect, useMemo, useState } from "react";
import api from "@/api/client";
import type { Transaction } from "@/api/types";
import { PageHeader } from "@/components/layout/AppLayout";
import { ScoreBadge } from "@/components/shared/ScoreBadge";
import { Badge, TYPE_TONE } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Select } from "@/components/ui/input";
import { EmptyState, Table, Td, Th, Tr } from "@/components/ui/table";
import { TableSkeleton } from "@/components/ui/skeleton";
import { fmtDate, fmtMAD } from "@/lib/format";

export default function Transactions() {
  const [transactions, setTransactions] = useState<Transaction[] | null>(null);
  const [type, setType] = useState("all");
  const [risk, setRisk] = useState("all");

  useEffect(() => {
    api
      .get<Transaction[]>("/transactions", { params: { limit: 100 } })
      .then(({ data }) => setTransactions(data));
  }, []);

  const visible = useMemo(
    () =>
      (transactions ?? []).filter((t) => {
        if (type !== "all" && t.transaction_type !== type) return false;
        if (risk === "high") return (t.risk_score?.score ?? 0) >= 70;
        if (risk === "medium") {
          const s = t.risk_score?.score ?? 0;
          return s >= 40 && s < 70;
        }
        return true;
      }),
    [transactions, type, risk]
  );

  return (
    <>
      <PageHeader title="Transactions" subtitle={`${visible.length} opération(s) affichée(s)`} />
      <Card>
        <div className="mb-4 flex flex-wrap gap-2.5">
          <Select className="w-44" value={type} onChange={(e) => setType(e.target.value)}>
            <option value="all">Tous les types</option>
            <option value="deposit">Dépôts</option>
            <option value="withdrawal">Retraits</option>
            <option value="transfer">Virements</option>
          </Select>
          <Select className="w-52" value={risk} onChange={(e) => setRisk(e.target.value)}>
            <option value="all">Tous les niveaux de risque</option>
            <option value="high">Risque élevé (≥ 70)</option>
            <option value="medium">Risque moyen (40–69)</option>
          </Select>
        </div>
        {!transactions ? (
          <TableSkeleton rows={8} />
        ) : (
          <Table>
            <thead>
              <tr>
                <Th>Date</Th><Th>Type</Th><Th>Montant</Th><Th>Ville</Th><Th>Description</Th><Th>Score IA</Th>
              </tr>
            </thead>
            <tbody>
              {visible.map((t) => (
                <Tr key={t.id}>
                  <Td className="text-muted-foreground">{fmtDate(t.created_at)}</Td>
                  <Td><Badge tone={TYPE_TONE[t.transaction_type]}>{t.transaction_type}</Badge></Td>
                  <Td className="font-semibold">{fmtMAD(t.amount)}</Td>
                  <Td>{t.city ?? "—"}</Td>
                  <Td className="max-w-56 truncate text-muted-foreground">{t.description ?? "—"}</Td>
                  <Td><ScoreBadge score={t.risk_score?.score} /></Td>
                </Tr>
              ))}
            </tbody>
          </Table>
        )}
        {transactions && visible.length === 0 && <EmptyState>Aucune opération ne correspond aux filtres.</EmptyState>}
      </Card>
    </>
  );
}
