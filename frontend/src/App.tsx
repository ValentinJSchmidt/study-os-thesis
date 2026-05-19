import { Navigate, Route, Routes } from "react-router-dom";
import type { JSX } from "react";
import { useAuth } from "./auth/AuthContext";

import AppShell from "./components/AppShell";
import Dashboard from "./pages/Dashboard";
import Chat from "./pages/Chat";
import ChairExplorer from "./pages/ChairExplorer";
import Proposals from "./pages/Proposals";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Admin from "./pages/Admin";

/** Redirect to /login when unauthenticated; show spinner during hydration. */
function RequireAuth({ children }: { children: JSX.Element }) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-10 h-10 rounded-lg bg-primary flex items-center justify-center">
            <span
              className="material-symbols-outlined text-on-primary"
              style={{ fontVariationSettings: "'FILL' 1" }}
            >
              school
            </span>
          </div>
          <div className="w-6 h-6 border-2 border-outline-variant border-t-primary rounded-full animate-spin" />
        </div>
      </div>
    );
  }

  if (!user) return <Navigate to="/login" replace />;
  return children;
}

export default function App() {
  return (
    <Routes>
      {/* Public routes */}
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />

      {/* Root redirect */}
      <Route path="/" element={<Navigate to="/dashboard" replace />} />

      {/* Protected routes — all wrapped in AppShell (sidebar + topbar layout) */}
      <Route
        element={
          <RequireAuth>
            <AppShell />
          </RequireAuth>
        }
      >
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/chat" element={<Chat />} />
        <Route path="/chairs" element={<ChairExplorer />} />
        <Route path="/proposals" element={<Proposals />} />
        <Route path="/admin" element={<Admin />} />
      </Route>

      {/* Fallback */}
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}
