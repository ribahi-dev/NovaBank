// Assistant IA : interface conversationnelle qui répond avec les VRAIES
// données de l'API (intentions par règles — honnête : pas de LLM en backend,
// c'est documenté comme perspective d'évolution).
import { motion } from "framer-motion";
import { Bot, Send, User as UserIcon } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import api from "@/api/client";
import type { Alert, Client, Kpi } from "@/api/types";
import { PageHeader } from "@/components/layout/AppLayout";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useAuth } from "@/contexts/AuthContext";
import { fmtMAD } from "@/lib/format";

interface Message { from: "user" | "bot"; text: string }

const SUGGESTIONS = [
  "Résumé de l'activité",
  "Alertes critiques ouvertes",
  "Chercher le client Benali",
  "Que sait faire le moteur de risque ?",
];

async function answer(question: string, role: string): Promise<string> {
  const q = question.toLowerCase();

  if (q.includes("alerte")) {
    if (role !== "director") return "Seul le directeur d'agence peut consulter les alertes.";
    const { data } = await api.get<Alert[]>("/alerts", { params: { status_filter: "open" } });
    if (data.length === 0) return "Aucune alerte ouverte — tout est sous contrôle. ✅";
    const critical = data.filter((a) => a.level === "critical").length;
    const first = data[0];
    return (
      `Il y a ${data.length} alerte(s) ouverte(s), dont ${critical} critique(s). ` +
      `La plus récente : « ${first.message.slice(0, 140)}… » — rendez-vous dans Détection de fraude pour la traiter.`
    );
  }

  if (q.includes("résumé") || q.includes("activité") || q.includes("kpi")) {
    if (role !== "director") return "Le résumé d'activité est réservé au directeur d'agence.";
    const { data } = await api.get<Kpi>("/analytics/kpi");
    return (
      `L'agence compte ${data.total_clients} clients actifs et ${data.total_accounts} comptes. ` +
      `${data.total_transactions} transactions traitées : ${fmtMAD(data.total_deposits)} déposés, ` +
      `${fmtMAD(data.total_withdrawals)} retirés. ${data.open_alerts} alerte(s) ouverte(s), ` +
      `score de risque moyen ${data.average_risk_score?.toFixed(1) ?? "—"}/100.`
    );
  }

  if (q.includes("client") || q.includes("cherch")) {
    const words = question.split(/\s+/).filter((w) => w.length > 2);
    const term = words[words.length - 1];
    const { data } = await api.get<Client[]>("/clients", { params: { search: term } });
    if (data.length === 0) return `Aucun client trouvé pour « ${term} ». Essayez un nom ou un CIN.`;
    return (
      `${data.length} client(s) trouvé(s) : ` +
      data.slice(0, 3).map((c) => `${c.first_name} ${c.last_name} (CIN ${c.cin})`).join(" · ") +
      ". Ouvrez la page Clients pour voir les fiches complètes."
    );
  }

  if (q.includes("moteur") || q.includes("risque") || q.includes("score") || q.includes("modèle")) {
    return (
      "Le moteur de risque (mvp-rules-v1) analyse chaque transaction selon 4 signaux : " +
      "l'écart entre le montant et le revenu du client, l'heure inhabituelle (00h-06h), " +
      "le changement de ville par rapport aux habitudes, et la fréquence sur 24h. " +
      "Il produit un score 0-100 avec une explication lisible ; au-delà de 70, une alerte " +
      "est créée pour le directeur. Un modèle Machine Learning (Isolation Forest / Random " +
      "Forest) le remplacera derrière la même interface."
    );
  }

  return (
    "Je peux vous donner : un résumé de l'activité, l'état des alertes, rechercher un client " +
    "(« chercher le client Benali »), ou expliquer le moteur de risque. Essayez une des suggestions !"
  );
}

export default function Assistant() {
  const { user } = useAuth();
  const [messages, setMessages] = useState<Message[]>([
    {
      from: "bot",
      text: `Bonjour ${user?.first_name} 👋 — je suis l'assistant NovaBank. Je réponds à partir des données réelles de l'agence. Que voulez-vous savoir ?`,
    },
  ]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function ask(question: string) {
    if (!question.trim() || busy) return;
    setMessages((m) => [...m, { from: "user", text: question }]);
    setInput("");
    setBusy(true);
    try {
      const text = await answer(question, user?.role ?? "");
      setMessages((m) => [...m, { from: "bot", text }]);
    } catch {
      setMessages((m) => [...m, { from: "bot", text: "Désolé, une erreur est survenue en interrogeant l'API." }]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <PageHeader
        title="Assistant IA"
        subtitle="Interrogez les données de l'agence en langage naturel (moteur à intentions — LLM en perspective)"
      />
      <Card className="mx-auto flex h-[calc(100vh-240px)] max-w-3xl flex-col">
        <div className="flex-1 space-y-4 overflow-y-auto pr-1">
          {messages.map((m, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              className={`flex gap-3 ${m.from === "user" ? "flex-row-reverse" : ""}`}
            >
              <div
                className={`grid h-8 w-8 shrink-0 place-items-center rounded-lg ${
                  m.from === "bot" ? "bg-brand-gradient text-white" : "bg-muted text-muted-foreground"
                }`}
              >
                {m.from === "bot" ? <Bot size={16} /> : <UserIcon size={16} />}
              </div>
              <div
                className={`max-w-[80%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
                  m.from === "bot"
                    ? "bg-muted rounded-tl-sm"
                    : "bg-brand-gradient text-white rounded-tr-sm"
                }`}
              >
                {m.text}
              </div>
            </motion.div>
          ))}
          {busy && <div className="pl-11 text-sm text-muted-foreground">L'assistant consulte les données…</div>}
          <div ref={bottomRef} />
        </div>

        <div className="mt-4 border-t border-border pt-4">
          <div className="mb-3 flex flex-wrap gap-2">
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                onClick={() => ask(s)}
                className="cursor-pointer rounded-full border border-border px-3 py-1.5 text-xs text-muted-foreground transition-colors hover:border-primary hover:text-primary"
              >
                {s}
              </button>
            ))}
          </div>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              ask(input);
            }}
            className="flex gap-2"
          >
            <Input
              placeholder="Posez votre question…"
              value={input}
              onChange={(e) => setInput(e.target.value)}
            />
            <Button size="icon" className="h-10 w-10 shrink-0" disabled={busy} aria-label="Envoyer">
              <Send size={16} />
            </Button>
          </form>
        </div>
      </Card>
    </>
  );
}
