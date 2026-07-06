// Saisie d'opération : le verdict IA (score + explication) apparaît
// en animation dès la réponse de l'API — le moment fort de la démo.
import { motion } from "framer-motion";
import { BrainCircuit, CheckCircle2, Siren } from "lucide-react";
import { useEffect, useState } from "react";
import api, { apiError } from "@/api/client";
import type { Account, Client, Transaction } from "@/api/types";
import { PageHeader } from "@/components/layout/AppLayout";
import { ScoreBadge } from "@/components/shared/ScoreBadge";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Field, Input, Select } from "@/components/ui/input";
import { useToast } from "@/contexts/ToastContext";
import { fmtMAD } from "@/lib/format";

export default function NewTransaction() {
  const { toast } = useToast();
  const [clients, setClients] = useState<Client[]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [allAccounts, setAllAccounts] = useState<Account[]>([]);
  const [form, setForm] = useState({
    client_id: "", account_id: "", transaction_type: "deposit",
    amount: "", city: "", description: "", destination_account_id: "",
  });
  const [result, setResult] = useState<Transaction | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.get<Client[]>("/clients", { params: { limit: 100 } }).then(({ data }) => setClients(data));
    api.get<Account[]>("/accounts", { params: { limit: 100 } }).then(({ data }) => setAllAccounts(data));
  }, []);

  useEffect(() => {
    if (!form.client_id) return setAccounts([]);
    api
      .get<Account[]>("/accounts", { params: { client_id: form.client_id } })
      .then(({ data }) => setAccounts(data));
  }, [form.client_id]);

  const set =
    (field: keyof typeof form) =>
    (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
      setForm({ ...form, [field]: e.target.value });

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setResult(null);
    setBusy(true);
    try {
      const { data } = await api.post<Transaction>("/transactions", {
        transaction_type: form.transaction_type,
        amount: form.amount,
        account_id: Number(form.account_id),
        city: form.city || null,
        description: form.description || null,
        destination_account_id:
          form.transaction_type === "transfer" ? Number(form.destination_account_id) : null,
      });
      setResult(data);
      toast(
        data.risk_score && data.risk_score.score >= 70 ? "error" : "success",
        data.risk_score && data.risk_score.score >= 70
          ? "Opération à risque — alerte transmise au directeur."
          : "Opération enregistrée."
      );
    } catch (err) {
      setError(apiError(err, "Saisie invalide — vérifiez les champs."));
    } finally {
      setBusy(false);
    }
  }

  const selected = accounts.find((a) => a.id === Number(form.account_id));

  return (
    <>
      <PageHeader
        title="Nouvelle opération"
        subtitle="Chaque opération est analysée en temps réel par le moteur de risque"
      />
      <div className="grid gap-4 xl:grid-cols-2">
        <Card>
          <form onSubmit={handleSubmit} className="grid gap-4 sm:grid-cols-2">
            <Field label="Client *">
              <Select required value={form.client_id} onChange={set("client_id")}>
                <option value="">— choisir —</option>
                {clients.map((c) => (
                  <option key={c.id} value={c.id}>{c.first_name} {c.last_name} ({c.cin})</option>
                ))}
              </Select>
            </Field>
            <Field label="Compte *">
              <Select required value={form.account_id} onChange={set("account_id")}>
                <option value="">— choisir —</option>
                {accounts.map((a) => (
                  <option key={a.id} value={a.id}>{a.account_number} · {fmtMAD(a.balance)}</option>
                ))}
              </Select>
            </Field>
            <Field label="Type *">
              <Select value={form.transaction_type} onChange={set("transaction_type")}>
                <option value="deposit">Dépôt</option>
                <option value="withdrawal">Retrait</option>
                <option value="transfer">Virement</option>
              </Select>
            </Field>
            <Field label="Montant (MAD) *">
              <Input required type="number" min="0.01" step="0.01" value={form.amount} onChange={set("amount")} />
            </Field>
            {form.transaction_type === "transfer" && (
              <Field label="Compte destinataire *">
                <Select required value={form.destination_account_id} onChange={set("destination_account_id")}>
                  <option value="">— choisir —</option>
                  {allAccounts
                    .filter((a) => a.id !== Number(form.account_id))
                    .map((a) => (
                      <option key={a.id} value={a.id}>{a.account_number}</option>
                    ))}
                </Select>
              </Field>
            )}
            <Field label="Ville">
              <Input placeholder="Casablanca" value={form.city} onChange={set("city")} />
            </Field>
            <div className="sm:col-span-2">
              <Field label="Description">
                <Input value={form.description} onChange={set("description")} />
              </Field>
            </div>
            {selected && (
              <p className="sm:col-span-2 text-sm text-muted-foreground">
                Solde actuel : <strong className="text-foreground">{fmtMAD(selected.balance)}</strong>
              </p>
            )}
            {error && (
              <div className="sm:col-span-2 rounded-lg border border-danger/30 bg-danger/10 px-3.5 py-2.5 text-sm text-danger">
                {error}
              </div>
            )}
            <div className="sm:col-span-2">
              <Button disabled={busy} className="w-full sm:w-auto">
                {busy ? "Analyse en cours…" : "Valider l'opération"}
              </Button>
            </div>
          </form>
        </Card>

        <Card glass>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BrainCircuit size={17} className="text-primary" /> Analyse du risque
            </CardTitle>
          </CardHeader>
          {!result?.risk_score ? (
            <div className="grid h-48 place-items-center text-sm text-muted-foreground">
              Le verdict du moteur IA s'affichera ici après la saisie.
            </div>
          ) : (
            <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}>
              <div className="flex items-center gap-3">
                <ScoreBadge score={result.risk_score.score} />
                <div>
                  <div className="font-bold">Score {result.risk_score.score}/100</div>
                  <div className="text-xs text-muted-foreground">
                    confiance : {result.risk_score.confidence_level} · modèle {result.risk_score.model_version}
                  </div>
                </div>
              </div>
              <div className="mt-4 rounded-r-lg border-l-4 border-primary bg-primary-soft p-3.5 text-sm leading-relaxed">
                {result.risk_score.explanation}
              </div>
              <div
                className={`mt-4 flex items-center gap-2 rounded-lg px-3.5 py-2.5 text-sm ${
                  result.risk_score.score >= 70
                    ? "bg-danger/10 text-danger"
                    : "bg-success/10 text-success"
                }`}
              >
                {result.risk_score.score >= 70 ? (
                  <>
                    <Siren size={16} /> Alerte créée automatiquement pour le directeur d'agence.
                  </>
                ) : (
                  <>
                    <CheckCircle2 size={16} /> Opération n°{result.id} enregistrée ({fmtMAD(result.amount)}).
                  </>
                )}
              </div>
            </motion.div>
          )}
        </Card>
      </div>
    </>
  );
}
