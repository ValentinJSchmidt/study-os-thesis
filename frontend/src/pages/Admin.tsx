import { useEffect, useState } from "react";
import { api } from "../api/client";
import { useAuth } from "../auth/AuthContext";

type User = { id: number; email: string; role: string; created_at: string };

export default function Admin() {
  const { user } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (user?.role !== "admin") return;
    api<User[]>("/api/admin/users")
      .then(setUsers)
      .catch((err) => setError(err instanceof Error ? err.message : "Load failed"));
  }, [user]);

  if (user?.role !== "admin") return <div className="container">Admins only.</div>;

  return (
    <div className="container">
      <h1>Admin · Users</h1>
      {error && <div className="error">{error}</div>}
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr style={{ textAlign: "left", borderBottom: "1px solid #e5e7eb" }}>
            <th style={{ padding: "0.5rem" }}>ID</th>
            <th style={{ padding: "0.5rem" }}>Email</th>
            <th style={{ padding: "0.5rem" }}>Role</th>
            <th style={{ padding: "0.5rem" }}>Created</th>
          </tr>
        </thead>
        <tbody>
          {users.map((u) => (
            <tr key={u.id} style={{ borderBottom: "1px solid #f3f4f6" }}>
              <td style={{ padding: "0.5rem" }}>{u.id}</td>
              <td style={{ padding: "0.5rem" }}>{u.email}</td>
              <td style={{ padding: "0.5rem" }}>{u.role}</td>
              <td style={{ padding: "0.5rem" }}>{new Date(u.created_at).toLocaleString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
