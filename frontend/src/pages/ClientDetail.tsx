// Fiche client : profil, comptes (+ ouverture), historique scoré.
import { UserX, Wallet } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import api, { apiError } from "@/api/client";
import type { Account, Client, Transaction } from "@/api/types";
import { PageHeader } from "@/components/layout/AppLayout";
import { ScoreBadge } from "@/components/shared/ScoreBadge";
import { ACCOUNT_TONE, Badge, TYPE_TONE } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Input, Select } from "@/components/ui/input";
import { EmptyState, Table, Td, Th, Tr } from "@/components/ui/table";
import { useAuth } from "@/contexts/AuthContext";
import { useToast } from "@/contexts/ToastContext";
import { fmtDate, fmtMAD } from "@/lib/format";

export default function ClientDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { toast } = useToast();
  const [client, setClient] = useState<Client | null>(null);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [newAccount, setNewAccount] = useState({ account_type: "current", initial_balance: "0" });

  const load = useCallback(async () => {
    const [c, a, t] = await Promise.all([
      api.get<Client>(`/clients/${id}`),
      api.get<Account[]>("/accounts", { params: { client_id: id } }),
      api.get<Transaction[]>("/transactions", { params: { client_id: id, limit: 10 } }),
    ]);
    setClient(c.data);
    setAccounts(a.data);
    setTransactions(t.data);
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  async function openAccount(e: React.FormEvent) {
    e.preventDefault();
    try {
      await api.post("/accounts", { client_id: Number(id), ...newAccount });
      toast("success", "Compte ouvert.");
      load();
    } catch (err) {
      toast("error", apiError(err));
    }
  }

  async function deactivate() {
    if (!window.confirm("Désactiver ce client ? (suppression logique)")) return;
    await api.delete(`/clients/${id}`);
    toast("info", "Client désactivé — historique conservé.");
    navigate("/clients");
  }

  if (!client) return null;

  return (
    <>
      <PageHeader
        title={`${client.first_name} ${client.last_name}`}
        subtitle={`CIN ${client.cin} · client depuis le ${new Date(client.created_at).toLocaleDateString("fr-FR")}`}
        actions={
          user?.role === "advisor" && client.is_active ? (
            <Button variant="destructive" size="sm" onClick={deactivate}>
              <UserX size={15} /> Désactiver
            </Button>
          ) : !client.is_active ? (
            <Badge tone="danger">désactivé</Badge>
          ) : undefined
        }
      />

      <div className="grid gap-4 xl:grid-cols-5">
        <Card className="xl:col-span-2">
          <CardHeader><CardTitle>Informations</CardTitle></CardHeader>
          <dl className="grid grid-cols-[140px_1fr] gap-y-2.5 text-sm">
            <dt className="text-muted-foreground">Téléphone</dt><dd>{client.phone ?? "—"}</dd>
            <dt className="text-muted-foreground">Adresse</dt><dd>{client.address ?? "—"}</dd>
            <dt className="text-muted-foreground">Profession</dt><dd>{client.profession ?? "—"}</dd>
            <dt className="text-muted-foreground">Revenu mensuel</dt>
            <dd className="font-semibold">{client.monthly_income ? fmtMAD(client.monthly_income) : "—"}</dd>
          </dl>
        </Card>

        <Card className="xl:col-span-3">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Wallet size={16} /> Comptes ({accounts.length})
            </CardTitle>
          </CardHeader>
          <Table>
            <thead>
              <tr><Th>Numéro</Th><Th>Type</Th><Th>Solde</Th><Th>Statut</Th></tr>
            </thead>
            <tbody>
              {accounts.map((a) => (
                <Tr key={a.id}>
                  <Td className="font-mono text-[13px]">{a.account_number}</Td>
                  <Td><Badge tone="primary">{a.account_type === "current" ? "courant" : "épargne"}</Badge></Td>
                  <Td className="font-semibold">{fmtMAD(a.balance)}</Td>
                  <Td><Badge tone={ACCOUNT_TONE[a.status]}>{a.status}</Badge></Td>
                </Tr>
              ))}
            </tbody>
          </Table>
          {user?.role === "advisor" && client.is_active && (
            <form onSubmit={openAccount} className="mt-4 flex flex-wrap items-center gap-2">
              <Select
                className="w-36"
                value={newAccount.account_type}
                onChange={(e) => setNewAccount({ ...newAccount, account_type: e.target.value })}
              >
                <option value="current">Courant</option>
                <option value="savings">Épargne</option>
              </Select>
              <Input
                className="w-40" type="number" min="0" step="0.01" placeholder="Solde initial"
                value={newAccount.initial_balance}
                onChange={(e) => setNewAccount({ ...newAccount, initial_balance: e.target.value })}
              />
              <Button size="sm" type="submit">Ouvrir un compte</Button>
            </form>
          )}
        </Card>
      </div>

      <Card className="mt-4">
        <CardHeader><CardTitle>Dernières opérations</CardTitle></CardHeader>
        <Table>
          <thead>
            <tr><Th>Date</Th><Th>Type</Th><Th>Montant</Th><Th>Ville</Th><Th>Score IA</Th></tr>
          </thead>
          <tbody>
            {transactions.map((t) => (
              <Tr key={t.id}>
                <Td className="text-muted-foreground">{fmtDate(t.created_at)}</Td>
                <Td><Badge tone={TYPE_TONE[t.transaction_type]}>{t.transaction_type}</Badge></Td>
                <Td className="font-semibold">{fmtMAD(t.amount)}</Td>
                <Td>{t.city ?? "—"}</Td>
                <Td><ScoreBadge score={t.risk_score?.score} /></Td>
              </Tr>
            ))}
          </tbody>
        </Table>
        {transactions.length === 0 && <EmptyState>Aucune opération.</EmptyState>}
      </Card>
    </>
  );
}
