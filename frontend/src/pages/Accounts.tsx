// Comptes : vue globale avec filtres statut/type et actions de statut.
import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import api, { apiError } from "@/api/client";
import type { Account } from "@/api/types";
import { PageHeader } from "@/components/layout/AppLayout";
import { ACCOUNT_TONE, Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input, Select } from "@/components/ui/input";
import { EmptyState, Table, Td, Th, Tr } from "@/components/ui/table";
import { TableSkeleton } from "@/components/ui/skeleton";
import { useAuth } from "@/contexts/AuthContext";
import { useToast } from "@/contexts/ToastContext";
import { fmtMAD } from "@/lib/format";

export default function Accounts() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { toast } = useToast();
  const [accounts, setAccounts] = useState<Account[] | null>(null);
  const [status, setStatus] = useState("all");
  const [query, setQuery] = useState("");

  const load = () =>
    api.get<Account[]>("/accounts", { params: { limit: 100 } }).then(({ data }) => setAccounts(data));

  useEffect(() => {
    load();
  }, []);

  const visible = useMemo(
    () =>
      (accounts ?? []).filter(
        (a) =>
          (status === "all" || a.status === status) &&
          (!query || a.account_number.toLowerCase().includes(query.toLowerCase()))
      ),
    [accounts, status, query]
  );

  async function setAccountStatus(account: Account, next: string) {
    try {
      await api.patch(`/accounts/${account.id}`, { status: next });
      toast("success", `Compte ${account.account_number} : ${next}.`);
      load();
    } catch (err) {
      toast("error", apiError(err));
    }
  }

  return (
    <>
      <PageHeader title="Comptes" subtitle={`${visible.length} compte(s) affiché(s)`} />
      <Card>
        <div className="mb-4 flex flex-wrap gap-2.5">
          <Input
            className="max-w-xs"
            placeholder="Rechercher un numéro (NB…)"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <Select className="w-44" value={status} onChange={(e) => setStatus(e.target.value)}>
            <option value="all">Tous les statuts</option>
            <option value="active">Actifs</option>
            <option value="blocked">Bloqués</option>
            <option value="closed">Clôturés</option>
          </Select>
        </div>
        {!accounts ? (
          <TableSkeleton rows={6} />
        ) : (
          <Table>
            <thead>
              <tr>
                <Th>Numéro</Th><Th>Type</Th><Th>Solde</Th><Th>Statut</Th>
                <Th>Client</Th>{user?.role === "advisor" && <Th></Th>}
              </tr>
            </thead>
            <tbody>
              {visible.map((a) => (
                <Tr key={a.id}>
                  <Td className="font-mono text-[13px]">{a.account_number}</Td>
                  <Td><Badge tone="primary">{a.account_type === "current" ? "courant" : "épargne"}</Badge></Td>
                  <Td className="font-semibold">{fmtMAD(a.balance)}</Td>
                  <Td><Badge tone={ACCOUNT_TONE[a.status]}>{a.status}</Badge></Td>
                  <Td>
                    <Button variant="ghost" size="sm" onClick={() => navigate(`/clients/${a.client_id}`)}>
                      voir la fiche
                    </Button>
                  </Td>
                  {user?.role === "advisor" && (
                    <Td>
                      {a.status === "active" ? (
                        <Button variant="secondary" size="sm" onClick={() => setAccountStatus(a, "blocked")}>
                          Bloquer
                        </Button>
                      ) : a.status === "blocked" ? (
                        <Button variant="secondary" size="sm" onClick={() => setAccountStatus(a, "active")}>
                          Débloquer
                        </Button>
                      ) : null}
                    </Td>
                  )}
                </Tr>
              ))}
            </tbody>
          </Table>
        )}
        {accounts && visible.length === 0 && <EmptyState>Aucun compte ne correspond aux filtres.</EmptyState>}
      </Card>
    </>
  );
}
