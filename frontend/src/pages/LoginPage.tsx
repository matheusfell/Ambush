import { useState, type FormEvent } from "react";
import { Navigate } from "react-router-dom";
import { ApiError } from "@/api/client";
import { useAuth } from "@/auth/AuthContext";
import { Button, Card, FieldError, Input, Label } from "@/components/ui";

export function LoginPage() {
  const { token, loading, login } = useAuth();
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  if (!loading && token) return <Navigate to="/" replace />;

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setPending(true);
    try {
      await login(username, password);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Falha no login");
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="flex min-h-full items-center justify-center bg-[#0c0c0f] px-4">
      <Card className="w-full max-w-sm p-6">
        <div className="mb-6 flex items-center gap-3">
          <img src="/ambush.png" alt="AmbushSystem" className="size-12 rounded-xl object-contain" />
          <div>
            <h1 className="text-base font-semibold text-zinc-100">Ambush</h1>
            <p className="text-xs text-zinc-500">Acesso interno</p>
          </div>
        </div>

        <form className="space-y-3" onSubmit={onSubmit}>
          <div>
            <Label htmlFor="username">Usuário</Label>
            <Input
              id="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoComplete="username"
              required
            />
          </div>
          <div>
            <Label htmlFor="password">Senha</Label>
            <Input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              required
              aria-invalid={Boolean(error)}
            />
          </div>
          <FieldError>{error}</FieldError>
          <Button variant="primary" type="submit" className="w-full" disabled={pending}>
            {pending ? "Entrando…" : "Entrar"}
          </Button>
        </form>
      </Card>
    </div>
  );
}
