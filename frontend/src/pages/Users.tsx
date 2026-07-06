// Administration des utilisateurs (admin).
import { Plus } from "lucide-react";
import { useEffect, useState } from "react";
import api, { apiError } from "@/api/client";
import type { User } from "@/api/types";
import { PageHeader } from "@/components/layout/AppLayout";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Dialog } from "@/components/ui/dialog";
import { Field, Input, Select } from "@/components/ui/input";
import { Table, Td, Th, Tr } from "@/components/ui/table";
import { TableSkeleton } from "@/components/ui/skeleton";
import { ROLE_LABEL } from "@/contexts/AuthContext";
import { useToast } from "@/contexts/ToastContext";
import { fmtDate } from "@/lib/format";

const EMPTY = { first_name: "", last_name: "", email: "", password: "", role: "advisor" };

export default function Users() {
  const { toast } = useToast();
  const [users, setUsers] = useState<User[] | null>(null);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState(EMPTY);
  const [error, setError] = useState("");

  const load = () => api.get<User[]>("/users").then(({ data }) => setUsers(data));
  useEffect(() => {
    load();
  }, []);

  const set =
    (field: keyof typeof EMPTY) =>
    (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
      setForm({ ...form, [field]: e.target.value });

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    try {
      await api.post("/users", form);
      toast("success", `Utilisateur ${form.email} créé.`);
      setForm(EMPTY);
      setOpen(false);
      load();
    } catch (err) {
      setError(apiError(err, "Formulaire invalide (mot de passe : 8 caractères minimum)."));
    }
  }

  async function toggleActive(user: User) {
    await api.patch(`/users/${user.id}`, { is_active: !user.is_active });
    toast("info", `${user.email} ${user.is_active ? "désactivé" : "réactivé"}.`);
    load();
  }

  return (
    <>
      <PageHeader
        title="Utilisateurs"
        subtitle="Comptes de la plateforme et attribution des rôles"
        actions={
          <Button onClick={() => setOpen(true)}>
            <Plus size={16} /> Nouvel utilisateur
          </Button>
        }
      />
      <Card>
        {!users ? (
          <TableSkeleton rows={5} />
        ) : (
          <Table>
            <thead>
              <tr><Th>Nom</Th><Th>Email</Th><Th>Rôle</Th><Th>Statut</Th><Th>Créé le</Th><Th></Th></tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <Tr key={u.id}>
                  <Td className="font-semibold">{u.first_name} {u.last_name}</Td>
                  <Td>{u.email}</Td>
                  <Td><Badge tone={u.role === "advisor" ? "primary" : "dark"}>{ROLE_LABEL[u.role]}</Badge></Td>
                  <Td><Badge tone={u.is_active ? "success" : "danger"}>{u.is_active ? "actif" : "désactivé"}</Badge></Td>
                  <Td className="text-muted-foreground">{fmtDate(u.created_at)}</Td>
                  <Td>
                    <Button variant="secondary" size="sm" onClick={() => toggleActive(u)}>
                      {u.is_active ? "Désactiver" : "Réactiver"}
                    </Button>
                  </Td>
                </Tr>
              ))}
            </tbody>
          </Table>
        )}
      </Card>

      <Dialog open={open} onClose={() => setOpen(false)} title="Nouvel utilisateur">
        {error && (
          <div className="mb-3 rounded-lg border border-danger/30 bg-danger/10 px-3.5 py-2.5 text-sm text-danger">
            {error}
          </div>
        )}
        <form onSubmit={handleCreate} className="grid gap-4 sm:grid-cols-2">
          <Field label="Prénom *"><Input required value={form.first_name} onChange={set("first_name")} /></Field>
          <Field label="Nom *"><Input required value={form.last_name} onChange={set("last_name")} /></Field>
          <Field label="Email *"><Input required type="email" value={form.email} onChange={set("email")} /></Field>
          <Field label="Mot de passe *">
            <Input required type="password" minLength={8} value={form.password} onChange={set("password")} />
          </Field>
          <Field label="Rôle *">
            <Select value={form.role} onChange={set("role")}>
              <option value="advisor">Conseiller</option>
              <option value="director">Directeur d'agence</option>
              <option value="admin">Administrateur</option>
            </Select>
          </Field>
          <div className="flex items-end justify-end gap-2">
            <Button type="button" variant="secondary" onClick={() => setOpen(false)}>Annuler</Button>
            <Button type="submit">Créer</Button>
          </div>
        </form>
      </Dialog>
    </>
  );
}
