import axios from "axios";
import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";

export default function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function login(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await axios.post("http://localhost:8000/api/auth/login", {
        email: email.trim().toLowerCase(),
        password,
        remember_me: rememberMe,
      });
      localStorage.removeItem("token");
      sessionStorage.removeItem("token");
      const storage = rememberMe ? localStorage : sessionStorage;
      storage.setItem("token", res.data.token);
      localStorage.setItem("role", res.data.role);
      localStorage.setItem("role_name", res.data.role_name);
      navigate("/", { replace: true });
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Login failed. Check your email and password.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-zinc-950 text-white px-4">
      <form onSubmit={login} className="bg-zinc-900 p-8 rounded-xl w-full max-w-sm">
        <h1 className="text-2xl mb-6">Login</h1>
        <label className="block text-sm mb-1" htmlFor="login-email">Email</label>
        <input id="login-email" className="w-full p-3 mb-4 bg-zinc-800 rounded" placeholder="you@example.com" type="email" autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        <label className="block text-sm mb-1" htmlFor="login-password">Password</label>
        <input id="login-password" type="password" className="w-full p-3 mb-3 bg-zinc-800 rounded" placeholder="Password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} required />

        <label className="flex items-center gap-2 mb-4 text-sm text-zinc-300 cursor-pointer">
          <input type="checkbox" checked={rememberMe} onChange={(e) => setRememberMe(e.target.checked)} />
          Remember me
        </label>
        {error && <p role="alert" className="mb-3 text-sm text-red-400">{error}</p>}
        <button type="submit" disabled={loading} className="w-full p-3 rounded bg-blue-600 disabled:opacity-60">
          {loading ? "Logging in…" : "Login"}
        </button>
        <Link to="/forgot-password" className="block mt-4 text-center text-blue-400">Forgot password?</Link>
        <Link to="/signup" className="block mt-2 text-center text-blue-400">Create Account</Link>
      </form>
    </div>
  );
}
