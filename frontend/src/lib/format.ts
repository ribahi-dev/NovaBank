// Formatage centralisé : mêmes montants/dates sur toute l'application.
export const fmtMAD = (value: number | string) =>
  new Intl.NumberFormat("fr-MA", { style: "currency", currency: "MAD" }).format(Number(value));

export const fmtDate = (value: string) =>
  new Date(value).toLocaleString("fr-FR", { dateStyle: "medium", timeStyle: "short" });

export const fmtDay = (value: string) =>
  new Date(value).toLocaleDateString("fr-FR", { day: "2-digit", month: "short" });

export const scoreTone = (score: number) =>
  score >= 85 ? "critical" : score >= 70 ? "danger" : score >= 40 ? "warning" : "success";
