import { useState, type ReactNode } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "@/auth/AuthContext";
import { NewMonitorModal } from "@/components/NewMonitorModal";
import { AppShell } from "@/layouts/AppShell";
import { DashboardPage } from "@/pages/DashboardPage";
import { EmailSettingsPage } from "@/pages/EmailSettingsPage";
import { IncidentsPage } from "@/pages/IncidentsPage";
import { LoginPage } from "@/pages/LoginPage";
import { MonitorDetailPage } from "@/pages/MonitorDetailPage";
import { MonitorsPage } from "@/pages/MonitorsPage";
import { Skeleton } from "@/components/ui";

function Protected({ children }: { children: ReactNode }) {
  const { token, loading } = useAuth();
  if (loading) {
    return (
      <div className="flex min-h-full items-center justify-center bg-[#0c0c0f]">
        <Skeleton className="h-8 w-40" />
      </div>
    );
  }
  if (!token) return <Navigate to="/login" replace />;
  return children;
}

function AuthenticatedLayout() {
  const [newOpen, setNewOpen] = useState(false);

  return (
    <AppShell onNewMonitor={() => setNewOpen(true)}>
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/monitors" element={<MonitorsPage />} />
        <Route path="/monitors/:id" element={<MonitorDetailPage />} />
        <Route path="/incidents" element={<IncidentsPage />} />
        <Route path="/email" element={<EmailSettingsPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      <NewMonitorModal open={newOpen} onClose={() => setNewOpen(false)} />
    </AppShell>
  );
}

export function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/*"
        element={
          <Protected>
            <AuthenticatedLayout />
          </Protected>
        }
      />
    </Routes>
  );
}
