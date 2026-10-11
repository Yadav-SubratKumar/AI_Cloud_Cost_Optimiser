import axios from "axios";
import { useState } from "react";
import { Link } from "react-router-dom";

export default function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [devUrl, setDevUrl] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setMessage("");
    setDevUrl("");
    try {
      const res = await axios.post("http://localhost:8000/api/auth/forgot-password", { email });
      setMessage(res.data.message);
      if (res.data.dev_reset_url) setDevUrl(res.data.dev_reset_url);
    } catch (err: any) {
      setMessage(err?.response?.data?.detail || "Unable to process the request.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-zinc-950 text-white">
      <form onSubmit={submit} className="bg-zinc-900 p-8 rounded-xl w-96">
        <h1 className="text-2xl mb-3">Forgot Password</h1>
        <p className="text-sm text-zinc-400 mb-6">Enter your account email and we’ll generate a secure reset link.</p>
        <input className="w-full p-3 mb-4 bg-zinc-800 rounded" placeholder="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        <button disabled={loading} className="w-full p-3 rounded bg-blue-600 disabled:opacity-60">{loading ? "Sending…" : "Send Reset Link"}</button>
        {message && <p className="mt-4 text-sm text-zinc-300">{message}</p>}
        {devUrl && <a className="block mt-3 text-sm text-blue-400 break-all" href={devUrl}>Open development reset link</a>}
        <Link to="/login" className="block mt-5 text-center text-blue-400">Back to Login</Link>
      </form>
    </div>
  );
}
