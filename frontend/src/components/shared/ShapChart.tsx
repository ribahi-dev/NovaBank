// Graphique d'explicabilité SHAP : contribution de chaque variable au score.
// Barre vers la DROITE (orange) = pousse vers la fraude ; vers la GAUCHE
// (vert) = pousse vers le normal. C'est l'explication "boîte blanche" du modèle.
import { motion } from "framer-motion";

// Libellés lisibles pour des variables techniques.
const LABELS: Record<string, string> = {
  amount_over_income: "Montant / revenu du client",
  amount_over_avg: "Montant / moyenne du compte",
  is_night: "Opération nocturne",
  city_changed: "Changement de ville",
  tx_last_24h: "Fréquence sur 24h",
};

export function ShapChart({ values }: { values: Record<string, number> | null }) {
  if (!values || Object.keys(values).length === 0) return null;

  const entries = Object.entries(values).sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]));
  const max = Math.max(...entries.map(([, v]) => Math.abs(v)), 0.0001);

  return (
    <div className="mt-4">
      <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
        Explication du modèle (SHAP)
      </div>
      <div className="space-y-2">
        {entries.map(([key, value], i) => {
          const pct = (Math.abs(value) / max) * 50; // % de la demi-largeur
          const positive = value >= 0;
          return (
            <div key={key} className="flex items-center gap-2 text-xs">
              <div className="w-40 shrink-0 truncate text-right text-muted-foreground">
                {LABELS[key] ?? key}
              </div>
              {/* Axe central : barres à droite (fraude) / gauche (normal) */}
              <div className="relative h-4 flex-1">
                <div className="absolute inset-y-0 left-1/2 w-px bg-border" />
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${pct}%` }}
                  transition={{ delay: i * 0.05, duration: 0.4 }}
                  className={`absolute inset-y-0 ${positive ? "left-1/2 rounded-r bg-danger" : "right-1/2 rounded-l bg-success"}`}
                />
              </div>
              <div className={`w-12 shrink-0 font-mono ${positive ? "text-danger" : "text-success"}`}>
                {value >= 0 ? "+" : ""}
                {value.toFixed(2)}
              </div>
            </div>
          );
        })}
      </div>
      <div className="mt-2 flex justify-between text-[10px] text-muted-foreground">
        <span>← pousse vers « normal »</span>
        <span>pousse vers « fraude » →</span>
      </div>
    </div>
  );
}
