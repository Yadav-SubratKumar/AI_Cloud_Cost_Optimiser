import axios from "axios";
import { useState } from "react";
import { Link, useSearchParams, useNavigate } from "react-router-dom";

export default function ResetPassword() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setMessage("");
    if (password.length < 8) return setError("Password must be at least 8 characters.");
    if (password !== confirm) return setError("Passwords do not match.");
    const token = params.get("token");
    if (!token) return setError("This reset link is missing its token.");
    try {
      const res = await axios.post("http://localhost:8000/api/auth/reset-password", { token, password });
      setMessage(res.data.message);
      setTimeout(() => navigate("/login"), 1200);
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Password reset failed.");
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-zinc-950 text-white">
      <form onSubmit={submit} className="bg-zinc-900 p-8 rounded-xl w-96">
        <h1 className="text-2xl mb-6">Reset Password</h1>
        <input className="w-full p-3 mb-3 bg-zinc-800 rounded" type="password" placeholder="New password" value={password} onChange={(e) => setPassword(e.target.value)} required />
        <input className="w-full p-3 mb-4 bg-zinc-800 rounded" type="password" placeholder="Confirm new password" value={confirm} onChange={(e) => setConfirm(e.target.value)} required />
        {error && <p className="mb-3 text-sm text-red-400">{error}</p>}
        {message && <p className="mb-3 text-sm text-green-400">{message}</p>}
        <button className="w-full p-3 rounded bg-blue-600">Update Password</button>
        <Link to="/login" className="block mt-4 text-center text-blue-400">Back to Login</Link>
      </form>
    </div>
  );
}
