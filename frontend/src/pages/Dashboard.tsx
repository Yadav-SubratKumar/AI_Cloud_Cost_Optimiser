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

  useEffect(() => {
    loadGroups();
  }, []);

  async function loadGroups() {
    // Fix 8: try/catch on network call
    try {
      const token = localStorage.getItem("token");
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
      const token = localStorage.getItem("token");

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

        {/* Fix 5: value={g} on every option */}
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

      </div>
    </>
  );
}
