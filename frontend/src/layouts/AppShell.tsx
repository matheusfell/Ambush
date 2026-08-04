import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  Activity,
  AlertTriangle,
  LogOut,
  Mail,
  PanelLeftClose,
  PanelLeftOpen,
  Plus,
} from "lucide-react";
import { useEffect, useState, type ReactNode } from "react";
import { useAuth } from "@/auth/AuthContext";
import { Button, IconButton } from "@/components/ui";
import { cn } from "@/lib/utils";

const nav = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/monitors", label: "Monitores", icon: Activity, end: false },
  { to: "/incidents", label: "Incidentes", icon: AlertTriangle, end: false },
  { to: "/email", label: "E-mail", icon: Mail, end: false },
];

export function AppShell({
  children,
  onNewMonitor,
}: {
  children: ReactNode;
  onNewMonitor?: () => void;
}) {
  const { user, logout, isAdmin } = useAuth();
  const [collapsed, setCollapsed] = useState(() => {
    return localStorage.getItem("ambush_sidebar_collapsed") === "true";
  });

  useEffect(() => {
    localStorage.setItem("ambush_sidebar_collapsed", String(collapsed));
  }, [collapsed]);

  return (
    <div
      className={cn(
        "grid min-h-full grid-cols-1 bg-[#0c0c0f] transition-[grid-template-columns]",
        collapsed ? "md:grid-cols-[72px_1fr]" : "md:grid-cols-[240px_1fr]",
      )}
    >
      <aside className="flex flex-col border-b border-zinc-800 bg-[#0c0c0f] md:border-b-0 md:border-r">
        <div
          className={cn(
            "flex items-center gap-3 border-b border-zinc-800 px-4 py-4",
            collapsed && "md:justify-center md:px-3",
          )}
        >
          <img
            src="/ambush.png"
            alt="Ambush"
            className="size-10 rounded-lg object-contain"
          />
          <div className={cn(collapsed && "md:hidden")}>
            <div className="text-sm font-semibold tracking-tight text-zinc-100">
              Ambush
            </div>
            <div className="text-xs text-zinc-500">Disponibilidade</div>
          </div>
          <IconButton
            className={cn("ml-auto hidden md:inline-flex", collapsed && "md:hidden")}
            aria-label="Recolher menu"
            onClick={() => setCollapsed(true)}
          >
            <PanelLeftClose className="size-4" />
          </IconButton>
        </div>

        {collapsed && (
          <div className="hidden border-b border-zinc-800 p-3 md:block">
            <IconButton
              className="w-full"
              aria-label="Expandir menu"
              onClick={() => setCollapsed(false)}
            >
              <PanelLeftOpen className="size-4" />
            </IconButton>
          </div>
        )}

        <nav className={cn("flex flex-1 flex-col gap-1 p-3", collapsed && "md:px-2")}>
          {nav.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                cn(
                  "inline-flex h-9 items-center gap-2 rounded-lg px-3 text-sm font-medium transition-colors",
                  collapsed && "md:justify-center md:px-0",
                  isActive
                    ? "bg-zinc-800 text-zinc-100"
                    : "text-zinc-500 hover:bg-zinc-900 hover:text-zinc-200",
                )
              }
            >
              <item.icon className="size-4 shrink-0" aria-hidden />
              <span className={cn(collapsed && "md:hidden")}>{item.label}</span>
            </NavLink>
          ))}

          {isAdmin && onNewMonitor && (
            <Button
              variant="primary"
              className={cn("mt-3 w-full", collapsed && "md:px-0")}
              onClick={onNewMonitor}
              aria-label="Novo monitor"
            >
              <Plus className="size-4" />
              <span className={cn(collapsed && "md:hidden")}>Novo monitor</span>
            </Button>
          )}
        </nav>

        <div className={cn("border-t border-zinc-800 p-3", collapsed && "md:px-2")}>
          <div
            className={cn(
              "mb-2 truncate px-1 text-xs text-zinc-500",
              collapsed && "md:hidden",
            )}
          >
            {user?.username}
            <span className="mx-1 text-zinc-700">·</span>
            <span className="text-zinc-400">{user?.role}</span>
          </div>
          <Button
            className={cn("w-full", collapsed && "md:px-0")}
            onClick={logout}
            aria-label="Sair"
          >
            <LogOut className="size-4" />
            <span className={cn(collapsed && "md:hidden")}>Sair</span>
          </Button>
        </div>
      </aside>

      <div className="flex min-h-0 flex-col">
        <header className="flex items-center justify-between border-b border-zinc-800 px-4 py-3 md:hidden">
          <div className="flex items-center gap-2">
            <img src="/ambush.png" alt="" className="size-10 rounded-md" />
            <span className="text-sm font-semibold">Ambush</span>
          </div>
          <IconButton aria-label="Sair" onClick={logout}>
            <LogOut className="size-4" />
          </IconButton>
        </header>
        <main className="flex-1 overflow-auto p-4 md:p-6">{children}</main>
      </div>
    </div>
  );
}
