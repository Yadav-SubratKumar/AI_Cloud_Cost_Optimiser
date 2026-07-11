import axios from "axios";
import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";

export default function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  // Fix 8: error state instead of unhandled crash
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function login() {
    setError("");
    setLoading(true);
    try {
      const res = await axios.post(
        "http://localhost:8000/api/auth/login",
        { email, password }
      );
      localStorage.setItem("token", res.data.token);
      navigate("/");
    } catch (err: any) {
      const msg =
        err?.response?.data?.detail ||
        "Login failed. Check your email and password.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-zinc-950 text-white">
      <div className="bg-zinc-900 p-8 rounded-xl w-96">

        <h1 className="text-2xl mb-6">Login</h1>

        <input
          className="w-full p-3 mb-3 bg-zinc-800 rounded"
          placeholder="Email"
          type="email"
          onChange={(e) => setEmail(e.target.value)}
        />

        <input
          type="password"
          className="w-full p-3 mb-4 bg-zinc-800 rounded"
          placeholder="Password"
          onChange={(e) => setPassword(e.target.value)}
        />

        {/* Fix 8: show error message */}
        {error && (
          <p className="mb-3 text-sm text-red-400">{error}</p>
        )}

        <button
          onClick={login}
          disabled={loading}
          className={`w-full p-3 rounded ${
            loading ? "bg-blue-400 opacity-60 cursor-not-allowed" : "bg-blue-600"
          }`}
        >
          {loading ? "Logging in…" : "Login"}
        </button>

        <Link
          to="/signup"
          className="block mt-4 text-center text-blue-400"
        >
          Create Account
        </Link>

      </div>
    </div>
  );
}
