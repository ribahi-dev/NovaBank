// Journal d'audit (admin) : trace append-only des actions sensibles.
import { useEffect, useMemo, useState } from "react";
import api from "@/api/client";
import type { AuditLog } from "@/api/types";
import { PageHeader } from "@/components/layout/AppLayout";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { EmptyState, Table, Td, Th, Tr } from "@/components/ui/table";
import { TableSkeleton } from "@/components/ui/skeleton";
import { fmtDate } from "@/lib/format";

export default function Audit() {
  const [logs, setLogs] = useState<AuditLog[] | null>(null);
  const [filter, setFilter] = useState("");

  useEffect(() => {
    api.get<AuditLog[]>("/audit-logs", { params: { limit: 100 } }).then(({ data }) => setLogs(data));
  }, []);

  const visible = useMemo(
    () =>
      (logs ?? []).filter(
        (l) =>
          !filter ||
          l.action.includes(filter) ||
          (l.details ?? "").toLowerCase().includes(filter.toLowerCase())
      ),
    [logs, filter]
  );

  return (
    <>
      <PageHeader
        title="Journal d'audit"
        subtitle={`Trace append-only des actions sensibles — ${visible.length} entrée(s)`}
        actions={
          <Input
            className="w-72"
            placeholder="Filtrer (login_failed, transaction…)"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
          />
        }
      />
      <Card>
        {!logs ? (
          <TableSkeleton rows={8} />
        ) : (
          <Table>
            <thead>
              <tr>
                <Th>Date</Th><Th>Action</Th><Th>Entité</Th><Th>Utilisateur</Th><Th>IP</Th><Th>Résultat</Th><Th>Détails</Th>
              </tr>
            </thead>
            <tbody>
              {visible.map((l) => (
                <Tr key={l.id}>
                  <Td className="text-muted-foreground">{fmtDate(l.created_at)}</Td>
                  <Td><code className="rounded bg-muted px-1.5 py-0.5 text-[12px]">{l.action}</code></Td>
                  <Td className="text-muted-foreground">{l.entity_type ? `${l.entity_type} #${l.entity_id}` : "—"}</Td>
                  <Td>{l.user_id ?? "—"}</Td>
                  <Td className="text-muted-foreground">{l.ip_address ?? "—"}</Td>
                  <Td><Badge tone={l.success ? "success" : "danger"}>{l.success ? "succès" : "échec"}</Badge></Td>
                  <Td className="max-w-64 truncate text-muted-foreground">{l.details ?? "—"}</Td>
                </Tr>
              ))}
            </tbody>
          </Table>
        )}
        {logs && visible.length === 0 && <EmptyState>Aucune entrée.</EmptyState>}
      </Card>
    </>
  );
}
