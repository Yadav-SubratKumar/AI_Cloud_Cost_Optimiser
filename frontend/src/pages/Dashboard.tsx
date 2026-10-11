import axios from "axios";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import Navbar from "../components/Navbar";
import ProgressTracker from "../components/ProgressTracker";

export default function Dashboard() {
  const navigate = useNavigate();
  const [groups, setGroups] = useState<string[]>([]);
  const [selected, setSelected] = useState("");
  const [progress, setProgress] = useState<string[]>([]);
  const [done, setDone] = useState(false);
  // Fix 10: loading/disabled state
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const role = localStorage.getItem("role") || "finance_manager";
  const canScan = role === "cloud_admin" || role === "it_manager";

  useEffect(() => {
    if (canScan) loadGroups();
  }, [canScan]);

  async function loadGroups() {
    // Fix 8: try/catch on network call
    try {
      const token = localStorage.getItem("token") || sessionStorage.getItem("token");
      const res = await axios.get(
        "http://localhost:8000/api/resource-groups",
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setGroups(res.data.resource_groups);
    } catch {
      setError("Failed to load resource groups. Is the backend running?");
    }
  }

  async function runAnalysis() {
    if (!selected) {
      setError("Please select a resource group first.");
      return;
    }

    // Fix 10: disable button and show loading
    setLoading(true);
    setError("");
    setProgress([]);
    setDone(false);

    try {
      const token = localStorage.getItem("token") || sessionStorage.getItem("token");

      const start = await axios.post(
        "http://localhost:8000/api/analyze/start",
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );

      const analysisId = start.data.analysis_id;

      const ws = new WebSocket(
        `ws://localhost:8000/ws/progress/${analysisId}`
      );

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        setProgress((prev) => [...prev, data.message]);
      };

      const result = await axios.post(
        "http://localhost:8000/api/analyze",
        { analysis_id: analysisId, resource_group: selected },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      // Fix 7: mark progress as done before navigating
      setDone(true);
      ws.close();

      navigate("/report", { state: result.data });
    } catch (err: any) {
      // Fix 8: show error instead of white screen
      const msg =
        err?.response?.data?.detail ||
        err?.message ||
        "Analysis failed. Please try again.";
      setError(msg);
    } finally {
      // Fix 10: re-enable button
      setLoading(false);
    }
  }

  return (
    <>
      <Navbar />

      <div className="p-8 text-white">
        <h1 className="text-3xl mb-2">Dashboard</h1>
        <p className="text-zinc-400 mb-6">Welcome. Your role is {localStorage.getItem("role_name") || "User"}.</p>

        {!canScan ? (
          <div className="max-w-2xl bg-zinc-900 rounded-xl p-6">
            <h2 className="text-xl mb-2">Cost overview and reports</h2>
            <p className="text-zinc-300 mb-4">Your role can review saved analyses and reports. Resource scanning is available to Cloud Administrators and IT Managers.</p>
            <button onClick={() => navigate("/history")} className="bg-blue-600 px-4 py-2 rounded">View Analysis History</button>
          </div>
        ) : <>
        {/* Resource scanning controls are shown only to roles permitted to scan. */}
        <select
          className="bg-zinc-900 p-3 rounded"
          value={selected}
          onChange={(e) => setSelected(e.target.value)}
        >
          <option value="">Select Resource Group</option>
          {groups.map((g) => (
            <option key={g} value={g}>
              {g}
            </option>
          ))}
        </select>

        {/* Fix 10: disabled + visual feedback while loading */}
        <button
          onClick={runAnalysis}
          disabled={loading}
          className={`ml-4 p-3 rounded transition-opacity ${
            loading
              ? "bg-blue-400 opacity-60 cursor-not-allowed"
              : "bg-blue-600 hover:bg-blue-700"
          }`}
        >
          {loading ? "Analysing…" : "Run Analysis"}
        </button>

        {/* Fix 8: visible error message */}
        {error && (
          <p className="mt-4 text-red-400 text-sm">{error}</p>
        )}

        {progress.length > 0 && (
          <div className="mt-8">
            <ProgressTracker steps={progress} done={done} />
          </div>
        )}
        </>}
      </div>
    </>
  );
}
