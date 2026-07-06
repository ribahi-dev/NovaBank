// Sidebar animée : navigation par rôle, rétractable (Framer Motion),
// anthracite avec accents orange — l'identité de la plateforme.
import { motion } from "framer-motion";
import {
  ArrowLeftRight, Banknote, Bot, ChevronsLeft, FileBarChart2, LayoutDashboard,
  Landmark, LogOut, ScrollText, Settings, ShieldAlert, ShieldCheck, Users, Wallet,
} from "lucide-react";
import { NavLink } from "react-router-dom";
import type { Role } from "@/api/types";
import { ROLE_LABEL, useAuth } from "@/contexts/AuthContext";
import { cn } from "@/lib/utils";

const MENU: Record<Role, { to: string; label: string; icon: typeof Users }[]> = {
  advisor: [
    { to: "/clients", label: "Clients", icon: Users },
    { to: "/comptes", label: "Comptes", icon: Wallet },
    { to: "/operations/nouvelle", label: "Nouvelle opération", icon: Banknote },
    { to: "/transactions", label: "Transactions", icon: ArrowLeftRight },
    { to: "/assistant", label: "Assistant IA", icon: Bot },
  ],
  director: [
    { to: "/dashboard", label: "Tableau de bord", icon: LayoutDashboard },
    { to: "/fraude", label: "Détection de fraude", icon: ShieldAlert },
    { to: "/clients", label: "Clients", icon: Users },
    { to: "/comptes", label: "Comptes", icon: Wallet },
    { to: "/transactions", label: "Transactions", icon: ArrowLeftRight },
    { to: "/rapports", label: "Rapports", icon: FileBarChart2 },
    { to: "/assistant", label: "Assistant IA", icon: Bot },
  ],
  admin: [
    { to: "/users", label: "Utilisateurs", icon: ShieldCheck },
    { to: "/audit", label: "Journal d'audit", icon: ScrollText },
  ],
};

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

export function Sidebar({ collapsed, onToggle }: SidebarProps) {
  const { user, logout } = useAuth();
  if (!user) return null;

  const items = [...MENU[user.role], { to: "/parametres", label: "Paramètres", icon: Settings }];

  return (
    <motion.aside
      animate={{ width: collapsed ? 76 : 248 }}
      transition={{ type: "spring", stiffness: 300, damping: 32 }}
      className="fixed inset-y-0 left-0 z-40 flex flex-col overflow-hidden bg-sidebar text-sidebar-foreground"
    >
      {/* Marque */}
      <div className="flex h-16 items-center gap-2.5 border-b border-white/8 px-4">
        <div className="bg-brand-gradient grid h-9 w-9 shrink-0 place-items-center rounded-xl font-bold text-white">
          <Landmark size={18} />
        </div>
        {!collapsed && (
          <div className="leading-tight">
            <div className="text-[17px] font-bold text-white">
              Nova<span className="text-primary">Bank</span>
            </div>
            <div className="text-[10px] tracking-wide">Aide à la décision</div>
          </div>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 overflow-y-auto p-2.5">
        {items.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            title={label}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-[13.5px] font-medium transition-colors",
                isActive
                  ? "bg-primary-soft text-primary"
                  : "hover:bg-white/6 hover:text-white"
              )
            }
          >
            <Icon size={18} className="shrink-0" />
            {!collapsed && <span className="truncate">{label}</span>}
          </NavLink>
        ))}
      </nav>

      {/* Utilisateur + repli */}
      <div className="border-t border-white/8 p-3">
        {!collapsed && (
          <div className="mb-2 px-1">
            <div className="truncate text-sm font-semibold text-white">
              {user.first_name} {user.last_name}
            </div>
            <div className="text-[10.5px] uppercase tracking-wider text-primary">
              {ROLE_LABEL[user.role]}
            </div>
          </div>
        )}
        <div className={cn("flex gap-1.5", collapsed && "flex-col")}>
          <button
            onClick={logout}
            title="Se déconnecter"
            className="flex flex-1 items-center justify-center gap-2 rounded-lg border border-white/12 px-2 py-2 text-xs hover:border-primary hover:text-primary cursor-pointer"
          >
            <LogOut size={15} /> {!collapsed && "Déconnexion"}
          </button>
          <button
            onClick={onToggle}
            title={collapsed ? "Déplier" : "Replier"}
            className="grid place-items-center rounded-lg border border-white/12 px-2 py-2 hover:border-primary hover:text-primary cursor-pointer"
          >
            <motion.span animate={{ rotate: collapsed ? 180 : 0 }}>
              <ChevronsLeft size={15} />
            </motion.span>
          </button>
        </div>
      </div>
    </motion.aside>
  );
}
