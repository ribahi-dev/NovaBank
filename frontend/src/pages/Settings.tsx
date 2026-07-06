// Paramètres : profil, thème, informations sur la plateforme.
import { Moon, Sun } from "lucide-react";
import { PageHeader } from "@/components/layout/AppLayout";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { ROLE_LABEL, useAuth } from "@/contexts/AuthContext";
import { useTheme } from "@/contexts/ThemeContext";
import { fmtDate } from "@/lib/format";

export default function Settings() {
  const { user } = useAuth();
  const { theme, toggle } = useTheme();
  if (!user) return null;

  return (
    <>
      <PageHeader title="Paramètres" subtitle="Profil et préférences de l'application" />
      <div className="grid max-w-4xl gap-4 md:grid-cols-2">
        <Card>
          <CardHeader><CardTitle>Mon profil</CardTitle></CardHeader>
          <dl className="grid grid-cols-[130px_1fr] gap-y-2.5 text-sm">
            <dt className="text-muted-foreground">Nom</dt>
            <dd className="font-semibold">{user.first_name} {user.last_name}</dd>
            <dt className="text-muted-foreground">Email</dt><dd>{user.email}</dd>
            <dt className="text-muted-foreground">Rôle</dt>
            <dd><Badge tone="primary">{ROLE_LABEL[user.role]}</Badge></dd>
            <dt className="text-muted-foreground">Membre depuis</dt><dd>{fmtDate(user.created_at)}</dd>
          </dl>
          <p className="mt-4 text-xs text-muted-foreground">
            La modification du mot de passe passe par l'administrateur (procédure sécurisée).
          </p>
        </Card>

        <Card>
          <CardHeader><CardTitle>Apparence</CardTitle></CardHeader>
          <p className="mb-4 text-sm text-muted-foreground">
            Thème actuel : <strong className="text-foreground">{theme === "dark" ? "sombre" : "clair"}</strong>
          </p>
          <Button variant="secondary" onClick={toggle}>
            {theme === "dark" ? <Sun size={16} /> : <Moon size={16} />}
            Passer en mode {theme === "dark" ? "clair" : "sombre"}
          </Button>
          <p className="mt-4 text-xs text-muted-foreground">
            Préférence enregistrée sur cet appareil. Le mode sombre est appliqué à tous les écrans, graphiques compris.
          </p>
        </Card>

        <Card className="md:col-span-2">
          <CardHeader><CardTitle>À propos de la plateforme</CardTitle></CardHeader>
          <div className="grid gap-3 text-sm sm:grid-cols-3">
            <div>
              <div className="text-muted-foreground">Version</div>
              <div className="font-semibold">NovaBank MVP 0.1.0</div>
            </div>
            <div>
              <div className="text-muted-foreground">Moteur de risque</div>
              <div className="font-semibold">mvp-rules-v1</div>
            </div>
            <div>
              <div className="text-muted-foreground">Sécurité</div>
              <div className="font-semibold">JWT · RBAC · Audit</div>
            </div>
          </div>
        </Card>
      </div>
    </>
  );
}
