// Routage : routes publiques, protégées (auth) et restreintes (rôle).
import { Navigate, Route, Routes } from "react-router-dom";
import type { Role } from "@/api/types";
import { AppLayout } from "@/components/layout/AppLayout";
import { ROLE_HOME, useAuth } from "@/contexts/AuthContext";
import Accounts from "@/pages/Accounts";
import Assistant from "@/pages/Assistant";
import Audit from "@/pages/Audit";
import ClientDetail from "@/pages/ClientDetail";
import Clients from "@/pages/Clients";
import Dashboard from "@/pages/Dashboard";
import Fraud from "@/pages/Fraud";
import Login from "@/pages/Login";
import NewTransaction from "@/pages/NewTransaction";
import Reports from "@/pages/Reports";
import Settings from "@/pages/Settings";
import Transactions from "@/pages/Transactions";
import Users from "@/pages/Users";

// Garde de route. Rappel : le vrai contrôle d'accès est le RBAC serveur ;
// ceci n'est que du confort de navigation.
function Guard({ roles, children }: { roles?: Role[]; children: React.ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return null;
  if (!user) return <Navigate to="/login" replace />;
  if (roles && !roles.includes(user.role)) return <Navigate to={ROLE_HOME[user.role]} replace />;
  return <>{children}</>;
}

function Home() {
  const { user, loading } = useAuth();
  if (loading) return null;
  return <Navigate to={user ? ROLE_HOME[user.role] : "/login"} replace />;
}

const STAFF: Role[] = ["advisor", "director"];

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        element={
          <Guard>
            <AppLayout />
          </Guard>
        }
      >
        <Route path="/clients" element={<Guard roles={STAFF}><Clients /></Guard>} />
        <Route path="/clients/:id" element={<Guard roles={STAFF}><ClientDetail /></Guard>} />
        <Route path="/comptes" element={<Guard roles={STAFF}><Accounts /></Guard>} />
        <Route path="/transactions" element={<Guard roles={STAFF}><Transactions /></Guard>} />
        <Route path="/assistant" element={<Guard roles={STAFF}><Assistant /></Guard>} />
        <Route path="/operations/nouvelle" element={<Guard roles={["advisor"]}><NewTransaction /></Guard>} />
        <Route path="/dashboard" element={<Guard roles={["director"]}><Dashboard /></Guard>} />
        <Route path="/fraude" element={<Guard roles={["director"]}><Fraud /></Guard>} />
        <Route path="/rapports" element={<Guard roles={["director"]}><Reports /></Guard>} />
        <Route path="/users" element={<Guard roles={["admin"]}><Users /></Guard>} />
        <Route path="/audit" element={<Guard roles={["admin"]}><Audit /></Guard>} />
        <Route path="/parametres" element={<Settings />} />
      </Route>
      <Route path="*" element={<Home />} />
    </Routes>
  );
}
