import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import type { Role } from "../auth/AuthContext";

export default function Register() {
  const { register } = useAuth();
  const nav = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<Role>("student");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await register(email, password, role);
      nav("/chat");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="container">
      <h1>Register</h1>
      {error && <div className="error">{error}</div>}
      <form onSubmit={onSubmit}>
        <div className="form-row">
          <label>Email</label>
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        </div>
        <div className="form-row">
          <label>Password (min 8 chars)</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={8}
          />
        </div>
        <div className="form-row">
          <label>Role</label>
          <select value={role} onChange={(e) => setRole(e.target.value as Role)}>
            <option value="student">Student</option>
            <option value="professor">Professor</option>
          </select>
        </div>
        <button type="submit" disabled={busy}>{busy ? "…" : "Create account"}</button>
      </form>
    </div>
  );
}
