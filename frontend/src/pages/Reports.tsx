// Rapports : aperçu + export CSV (compatible Excel) côté client.
// L'export PDF/Excel serveur (reportlab/openpyxl) est l'étape backend suivante.
import { Download, FileSpreadsheet } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import api from "@/api/client";
import type { Client, Transaction } from "@/api/types";
import { PageHeader } from "@/components/layout/AppLayout";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Field, Select } from "@/components/ui/input";
import { Table, Td, Th, Tr } from "@/components/ui/table";
import { useToast } from "@/contexts/ToastContext";
import { fmtDate, fmtMAD } from "@/lib/format";

type Dataset = "transactions" | "clients";

function toCsv(rows: Record<string, unknown>[]): string {
  if (rows.length === 0) return "";
  const headers = Object.keys(rows[0]);
  const escape = (v: unknown) => `"${String(v ?? "").replaceAll('"', '""')}"`;
  return [
    headers.join(";"),
    ...rows.map((r) => headers.map((h) => escape(r[h])).join(";")),
  ].join("\r\n");
}

function download(filename: string, csv: string) {
  // ﻿ = BOM UTF-8 : Excel ouvre le fichier avec les accents corrects.
  const blob = new Blob(["﻿" + csv], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

export default function Reports() {
  const { toast } = useToast();
  const [dataset, setDataset] = useState<Dataset>("transactions");
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [clients, setClients] = useState<Client[]>([]);

  useEffect(() => {
    api.get<Transaction[]>("/transactions", { params: { limit: 100 } }).then(({ data }) => setTransactions(data));
    api.get<Client[]>("/clients", { params: { limit: 100 } }).then(({ data }) => setClients(data));
  }, []);

  const rows = useMemo(() => {
    if (dataset === "transactions")
      return transactions.map((t) => ({
        id: t.id,
        date: fmtDate(t.created_at),
        type: t.transaction_type,
        montant_MAD: t.amount,
        ville: t.city ?? "",
        score_risque: t.risk_score?.score ?? "",
        explication: t.risk_score?.explanation ?? "",
      }));
    return clients.map((c) => ({
      id: c.id,
      nom: c.last_name,
      prenom: c.first_name,
      cin: c.cin,
      profession: c.profession ?? "",
      revenu_mensuel_MAD: c.monthly_income ?? "",
      telephone: c.phone ?? "",
      actif: c.is_active ? "oui" : "non",
    }));
  }, [dataset, transactions, clients]);

  function exportCsv() {
    download(`novabank_${dataset}_${new Date().toISOString().slice(0, 10)}.csv`, toCsv(rows));
    toast("success", `Export ${dataset} téléchargé (${rows.length} lignes) — ouvrable dans Excel.`);
  }

  return (
    <>
      <PageHeader
        title="Rapports"
        subtitle="Génération et export des données de l'agence"
        actions={
          <Button onClick={exportCsv} disabled={rows.length === 0}>
            <Download size={16} /> Exporter (Excel/CSV)
          </Button>
        }
      />
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileSpreadsheet size={17} className="text-primary" /> Aperçu du rapport
          </CardTitle>
          <div className="w-52">
            <Field label="Jeu de données">
              <Select value={dataset} onChange={(e) => setDataset(e.target.value as Dataset)}>
                <option value="transactions">Transactions (avec scores)</option>
                <option value="clients">Clients</option>
              </Select>
            </Field>
          </div>
        </CardHeader>
        <Table>
          <thead>
            <tr>{rows[0] && Object.keys(rows[0]).slice(0, 7).map((h) => <Th key={h}>{h}</Th>)}</tr>
          </thead>
          <tbody>
            {rows.slice(0, 12).map((r, i) => (
              <Tr key={i}>
                {Object.values(r).slice(0, 7).map((v, j) => (
                  <Td key={j} className="max-w-64 truncate">
                    {typeof v === "string" && v.includes("MAD") ? v : String(v)}
                  </Td>
                ))}
              </Tr>
            ))}
          </tbody>
        </Table>
        <p className="mt-3 text-xs text-muted-foreground">
          Aperçu limité à 12 lignes — l'export contient les {rows.length} lignes.
          Montants en MAD : {dataset === "transactions" && transactions[0] ? fmtMAD(transactions[0].amount) : ""}
        </p>
      </Card>
    </>
  );
}
