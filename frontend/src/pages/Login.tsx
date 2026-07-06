// Connexion : plein écran dégradé de marque + carte glass animée.
import { motion } from "framer-motion";
import { Landmark, Lock, Mail, ShieldCheck, Sparkles, TrendingUp } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { apiError } from "@/api/client";
import { Button } from "@/components/ui/button";
import { Field, Input } from "@/components/ui/input";
import { ROLE_HOME, useAuth } from "@/contexts/AuthContext";

const FEATURES = [
  { icon: TrendingUp, text: "Pilotage temps réel de l'activité de l'agence" },
  { icon: Sparkles, text: "Score de risque IA expliqué pour chaque opération" },
  { icon: ShieldCheck, text: "Sécurité bancaire : JWT, RBAC, journal d'audit" },
];

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      const user = await login(email, password);
      navigate(ROLE_HOME[user.role]);
    } catch (err) {
      setError(apiError(err, "Connexion impossible — vérifiez le serveur."));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="relative grid min-h-screen place-items-center overflow-hidden bg-[#141210] p-4">
      {/* Fond : dégradé de marque + halos */}
      <div className="absolute inset-0 bg-brand-gradient opacity-90" />
      <div className="absolute -left-32 -top-32 h-96 w-96 rounded-full bg-white/15 blur-3xl" />
      <div className="absolute -bottom-40 -right-24 h-[28rem] w-[28rem] rounded-full bg-black/20 blur-3xl" />

      <div className="relative z-10 grid w-full max-w-5xl gap-10 lg:grid-cols-2 lg:items-center">
        {/* Présentation */}
        <motion.div
          initial={{ opacity: 0, x: -24 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5 }}
          className="hidden text-white lg:block"
        >
          <div className="mb-6 flex items-center gap-3">
            <div className="grid h-12 w-12 place-items-center rounded-2xl bg-white/15 backdrop-blur">
              <Landmark size={24} />
            </div>
            <div className="text-3xl font-bold">
              Nova<span className="text-[#2b2117]">Bank</span>
            </div>
          </div>
          <h1 className="mb-3 text-4xl font-bold leading-tight">
            La décision bancaire,
            <br />
            éclairée par l'IA.
          </h1>
          <p className="mb-8 max-w-md text-white/85">
            Plateforme intelligente d'aide à la décision pour l'agence :
            gestion, analyse, détection d'anomalies et cybersécurité.
          </p>
          <div className="space-y-3.5">
            {FEATURES.map(({ icon: Icon, text }, i) => (
              <motion.div
                key={text}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.25 + i * 0.12 }}
                className="flex items-center gap-3 text-[15px]"
              >
                <span className="grid h-8 w-8 place-items-center rounded-lg bg-white/15">
                  <Icon size={16} />
                </span>
                {text}
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Formulaire */}
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="glass mx-auto w-full max-w-md rounded-2xl p-8 !bg-white/90 dark:!bg-white/90"
        >
          <h2 className="text-2xl font-bold text-[#1c2024]">Connexion</h2>
          <p className="mb-6 mt-1 text-sm text-[#64707d]">
            Accédez à votre espace de travail sécurisé
          </p>
          <form onSubmit={handleSubmit} className="space-y-4">
            <Field label="Email professionnel">
              <div className="relative">
                <Mail size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#98a2ae]" />
                <Input
                  type="email"
                  required
                  placeholder="prenom@novabank.ma"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="!bg-white pl-9 !text-[#1c2024]"
                />
              </div>
            </Field>
            <Field label="Mot de passe">
              <div className="relative">
                <Lock size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#98a2ae]" />
                <Input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="!bg-white pl-9 !text-[#1c2024]"
                />
              </div>
            </Field>
            {error && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="rounded-lg border border-danger/30 bg-danger/10 px-3.5 py-2.5 text-sm text-danger"
              >
                {error}
              </motion.div>
            )}
            <Button className="w-full" size="lg" disabled={busy}>
              {busy ? "Connexion…" : "Se connecter"}
            </Button>
          </form>
        </motion.div>
      </div>
    </div>
  );
}
