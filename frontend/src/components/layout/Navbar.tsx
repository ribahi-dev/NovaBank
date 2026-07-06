// Barre supérieure : recherche client globale, bascule de thème, date.
import { Moon, Search, Sun } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Input } from "@/components/ui/input";
import { useAuth } from "@/contexts/AuthContext";
import { useTheme } from "@/contexts/ThemeContext";
import { Button } from "@/components/ui/button";

export function Navbar() {
  const { theme, toggle } = useTheme();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [query, setQuery] = useState("");

  const canSearch = user?.role === "advisor" || user?.role === "director";

  function submitSearch(e: React.FormEvent) {
    e.preventDefault();
    if (query.trim()) navigate(`/clients?search=${encodeURIComponent(query.trim())}`);
  }

  return (
    <header className="glass sticky top-0 z-30 flex h-16 items-center gap-4 border-b border-border px-6">
      {canSearch ? (
        <form onSubmit={submitSearch} className="relative w-full max-w-sm">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
          <Input
            className="h-9 pl-9"
            placeholder="Rechercher un client (nom, CIN)…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </form>
      ) : (
        <div />
      )}
      <div className="flex-1" />
      <span className="hidden text-xs text-muted-foreground md:block">
        {new Date().toLocaleDateString("fr-FR", { weekday: "long", day: "numeric", month: "long", year: "numeric" })}
      </span>
      <Button variant="ghost" size="icon" onClick={toggle} aria-label="Changer de thème">
        {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
      </Button>
    </header>
  );
}
