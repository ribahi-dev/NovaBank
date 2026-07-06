// Clients : recherche (synchronisée avec la navbar), création en modale.
import { Plus, Search } from "lucide-react";
import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import api, { apiError } from "@/api/client";
import type { Client } from "@/api/types";
import { PageHeader } from "@/components/layout/AppLayout";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Dialog } from "@/components/ui/dialog";
import { Field, Input } from "@/components/ui/input";
import { EmptyState, Table, Td, Th, Tr } from "@/components/ui/table";
import { TableSkeleton } from "@/components/ui/skeleton";
import { useAuth } from "@/contexts/AuthContext";
import { useToast } from "@/contexts/ToastContext";
import { fmtMAD } from "@/lib/format";

const EMPTY = {
  first_name: "", last_name: "", cin: "", phone: "",
  address: "", profession: "", monthly_income: "",
};

export default function Clients() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { toast } = useToast();
  const [params, setParams] = useSearchParams();
  const search = params.get("search") ?? "";

  const [clients, setClients] = useState<Client[] | null>(null);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState(EMPTY);
  const [error, setError] = useState("");

  useEffect(() => {
    setClients(null);
    api
      .get<Client[]>("/clients", { params: search ? { search } : {} })
      .then(({ data }) => setClients(data));
  }, [search]);

  const set = (field: keyof typeof EMPTY) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm({ ...form, [field]: e.target.value });

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    try {
      const payload = Object.fromEntries(Object.entries(form).filter(([, v]) => v !== ""));
      const { data } = await api.post<Client>("/clients", payload);
      toast("success", `Client ${data.first_name} ${data.last_name} créé.`);
      navigate(`/clients/${data.id}`);
    } catch (err) {
      setError(apiError(err, "Vérifiez les champs (CIN : 1-2 lettres puis chiffres)."));
    }
  }

  return (
    <>
      <PageHeader
        title="Clients"
        subtitle={clients ? `${clients.length} client(s) affiché(s)` : "Chargement…"}
        actions={
          user?.role === "advisor" && (
            <Button onClick={() => setOpen(true)}>
              <Plus size={16} /> Nouveau client
            </Button>
          )
        }
      />

      <Card>
        <div className="relative mb-4 max-w-sm">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
          <Input
            className="pl-9"
            placeholder="Nom, prénom ou CIN…"
            value={search}
            onChange={(e) => setParams(e.target.value ? { search: e.target.value } : {})}
          />
        </div>
        {!clients ? (
          <TableSkeleton rows={6} />
        ) : (
          <Table>
            <thead>
              <tr>
                <Th>Client</Th><Th>CIN</Th><Th>Profession</Th><Th>Revenu mensuel</Th><Th>Téléphone</Th>
              </tr>
            </thead>
            <tbody>
              {clients.map((c) => (
                <Tr key={c.id} clickable onClick={() => navigate(`/clients/${c.id}`)}>
                  <Td className="font-semibold">{c.first_name} {c.last_name}</Td>
                  <Td>{c.cin}</Td>
                  <Td>{c.profession ?? "—"}</Td>
                  <Td>{c.monthly_income ? fmtMAD(c.monthly_income) : "—"}</Td>
                  <Td className="text-muted-foreground">{c.phone ?? "—"}</Td>
                </Tr>
              ))}
            </tbody>
          </Table>
        )}
        {clients?.length === 0 && <EmptyState>Aucun client trouvé.</EmptyState>}
      </Card>

      <Dialog open={open} onClose={() => setOpen(false)} title="Nouveau client">
        {error && (
          <div className="mb-3 rounded-lg border border-danger/30 bg-danger/10 px-3.5 py-2.5 text-sm text-danger">
            {error}
          </div>
        )}
        <form onSubmit={handleCreate} className="grid gap-4 sm:grid-cols-2">
          <Field label="Prénom *"><Input required value={form.first_name} onChange={set("first_name")} /></Field>
          <Field label="Nom *"><Input required value={form.last_name} onChange={set("last_name")} /></Field>
          <Field label="CIN *"><Input required placeholder="AB123456" value={form.cin} onChange={set("cin")} /></Field>
          <Field label="Téléphone"><Input value={form.phone} onChange={set("phone")} /></Field>
          <Field label="Profession"><Input value={form.profession} onChange={set("profession")} /></Field>
          <Field label="Revenu mensuel (MAD)">
            <Input type="number" min="0" step="0.01" value={form.monthly_income} onChange={set("monthly_income")} />
          </Field>
          <div className="sm:col-span-2">
            <Field label="Adresse"><Input value={form.address} onChange={set("address")} /></Field>
          </div>
          <div className="sm:col-span-2 flex justify-end gap-2">
            <Button type="button" variant="secondary" onClick={() => setOpen(false)}>Annuler</Button>
            <Button type="submit">Créer le client</Button>
          </div>
        </form>
      </Dialog>
    </>
  );
}
