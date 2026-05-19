import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export default function Login() {
  const { login } = useAuth();
  const nav = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await login(email, password);
      nav("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="flex items-center justify-center gap-3 mb-8">
          <div className="w-10 h-10 rounded-lg bg-primary flex items-center justify-center">
            <span
              className="material-symbols-outlined text-on-primary"
              style={{ fontVariationSettings: "'FILL' 1" }}
            >
              school
            </span>
          </div>
          <div>
            <h1 className="text-headline-md font-headline-md font-bold text-primary tracking-tight">
              ScholarAI
            </h1>
            <p className="font-label-md text-label-md text-on-surface-variant uppercase tracking-widest">
              Academic Excellence
            </p>
          </div>
        </div>

        {/* Card */}
        <div className="bg-surface-container-lowest border border-outline-variant rounded-xl p-8 ambient-shadow">
          <h2 className="font-headline-md text-headline-md text-on-surface font-semibold mb-1">
            Willkommen zurück
          </h2>
          <p className="font-body-sm text-body-sm text-on-surface-variant mb-6">
            Melde dich an, um deine Forschungsreise fortzusetzen.
          </p>

          {error && (
            <div className="bg-error-container text-on-error-container border border-error/30 rounded-lg px-4 py-3 mb-4 font-body-sm text-body-sm">
              {error}
            </div>
          )}

          <form onSubmit={onSubmit} className="flex flex-col gap-4">
            <div>
              <label className="block font-label-md text-label-md text-on-surface-variant uppercase tracking-wider mb-2">
                E-Mail
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                placeholder="student@university.de"
                className="w-full border border-outline-variant rounded-lg py-3 px-4 font-body-md text-body-md text-on-surface bg-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all placeholder:text-on-surface-variant/60"
              />
            </div>

            <div>
              <label className="block font-label-md text-label-md text-on-surface-variant uppercase tracking-wider mb-2">
                Passwort
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                placeholder="••••••••"
                className="w-full border border-outline-variant rounded-lg py-3 px-4 font-body-md text-body-md text-on-surface bg-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all placeholder:text-on-surface-variant/60"
              />
            </div>

            <button
              type="submit"
              disabled={busy}
              className="w-full bg-primary text-on-primary font-label-md text-label-md py-3 rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50 mt-2 flex items-center justify-center gap-2"
            >
              {busy ? (
                <>
                  <span className="w-4 h-4 border-2 border-on-primary/30 border-t-on-primary rounded-full animate-spin" />
                  Anmelden…
                </>
              ) : (
                "Anmelden"
              )}
            </button>
          </form>

          <p className="text-center font-body-sm text-body-sm text-on-surface-variant mt-6">
            Noch kein Konto?{" "}
            <Link
              to="/register"
              className="text-primary font-semibold hover:underline"
            >
              Jetzt registrieren
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
