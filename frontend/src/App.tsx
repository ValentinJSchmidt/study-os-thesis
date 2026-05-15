import { Link, Navigate, Route, Routes, useNavigate } from "react-router-dom";
import { useAuth } from "./auth/AuthContext";
import Login from "./pages/Login";
import Register from "./pages/Register";
import SubmitThesis from "./pages/SubmitThesis";
import Chat from "./pages/Chat";
import Admin from "./pages/Admin";
import type { JSX } from "react";

function Nav() {
  const { user, logout } = useAuth();
  const nav = useNavigate();
  return (
    <div className="nav">
      <Link to="/">study-os-thesis</Link>
      {user && <Link to="/chat">Chat</Link>}
      {user && <Link to="/submit">Submit thesis</Link>}
      {user?.role === "admin" && <Link to="/admin">Admin</Link>}
      <div className="spacer" />
      {user ? (
        <>
          <span style={{ color: "#6b7280" }}>{user.email} ({user.role})</span>
          <button onClick={() => { logout(); nav("/login"); }}>Log out</button>
        </>
      ) : (
        <>
          <Link to="/login">Log in</Link>
          <Link to="/register">Register</Link>
        </>
      )}
    </div>
  );
}

function RequireAuth({ children }: { children: JSX.Element }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="container">Loading…</div>;
  if (!user) return <Navigate to="/login" replace />;
  return children;
}

function Home() {
  const { user } = useAuth();
  return (
    <div className="container">
      <h1>Find a thesis topic</h1>
      <p>Chat with an LLM that searches a database of professor- and student-submitted theses.</p>
      {user ? (
        <p>
          <Link to="/chat">Start a chat</Link> ·{" "}
          <Link to="/submit">Submit a thesis</Link>
        </p>
      ) : (
        <p>
          <Link to="/register">Register</Link> or <Link to="/login">log in</Link> to begin.
        </p>
      )}
    </div>
  );
}

export default function App() {
  return (
    <>
      <Nav />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/submit" element={<RequireAuth><SubmitThesis /></RequireAuth>} />
        <Route path="/chat" element={<RequireAuth><Chat /></RequireAuth>} />
        <Route path="/admin" element={<RequireAuth><Admin /></RequireAuth>} />
      </Routes>
    </>
  );
}
