import axios from "axios";
import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";

const roles = [
  { value: "cloud_admin", label: "Cloud Administrator" },
  { value: "finance_manager", label: "Finance Manager" },
  { value: "it_manager", label: "IT Manager" },
  { value: "executive", label: "CTO/CIO" },
];

export default function Signup() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("finance_manager");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function signup(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    if (password.length < 8) {
      setError("Password must be at least 8 characters long.");
      return;
    }
    setLoading(true);
    try {
      const res = await axios.post("http://localhost:8000/api/auth/signup", {
        email: email.trim().toLowerCase(),
        password,
        role,
      });
      localStorage.removeItem("token");
      sessionStorage.removeItem("token");
      // Signup logs the new user in and sends them to the dashboard.
      localStorage.setItem("token", res.data.token);
      localStorage.setItem("role", res.data.role);
      localStorage.setItem("role_name", res.data.role_name);
      navigate("/", { replace: true });
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Sign up failed. Please check your details and try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-zinc-950 text-white px-4">
      <form onSubmit={signup} className="bg-zinc-900 p-8 rounded-xl w-full max-w-sm">
        <h1 className="text-2xl mb-2">Create Account</h1>
        <p className="text-sm text-zinc-400 mb-6">Enter your details and choose the role you need for this project.</p>

        <label className="block text-sm mb-1" htmlFor="signup-email">Email</label>
        <input id="signup-email" className="w-full p-3 mb-4 bg-zinc-800 rounded" placeholder="you@example.com" type="email" autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} required />

        <label className="block text-sm mb-1" htmlFor="signup-password">Password</label>
        <input id="signup-password" type="password" className="w-full p-3 mb-4 bg-zinc-800 rounded" placeholder="At least 8 characters" autoComplete="new-password" minLength={8} value={password} onChange={(e) => setPassword(e.target.value)} required />

        <label className="block text-sm mb-1" htmlFor="signup-role">Select Role</label>
        <select id="signup-role" className="w-full p-3 mb-4 bg-zinc-800 rounded" value={role} onChange={(e) => setRole(e.target.value)} required>
          {roles.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
        </select>

        {error && <p role="alert" className="mb-3 text-sm text-red-400">{error}</p>}
        <button type="submit" disabled={loading} className="w-full p-3 rounded bg-green-600 disabled:opacity-60">
          {loading ? "Creating account…" : "Sign Up"}
        </button>
        <Link to="/login" className="block mt-4 text-center text-blue-400">Already have an account? Login</Link>
      </form>
    </div>
  );
}
