import axios from "axios";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import Navbar from "../components/Navbar";

export default function History() {
  const [history, setHistory] = useState<any[]>([]);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    loadHistory();
  }, []);

  async function loadHistory() {
    // Fix 8: try/catch
    try {
      const token = localStorage.getItem("token");
      const res = await axios.get("http://localhost:8000/api/history", {
        headers: { Authorization: `Bearer ${token}` },
      });
      setHistory(res.data.history);
    } catch {
      setError("Failed to load history.");
    }
  }

  return (
    <>
      <Navbar />

      <div className="p-8 text-white">
        <h1 className="text-3xl mb-6">Analysis History</h1>

        {error && <p className="text-red-400 mb-4">{error}</p>}

        {history.length === 0 && !error && (
          <p className="text-zinc-400">No analyses yet.</p>
        )}

        {history.map((item) => {
          // Fix 6: defensively parse analysis_result if it's still a string
          const analysisResult =
            typeof item.analysis_result === "string"
              ? (() => {
                  try {
                    return JSON.parse(item.analysis_result);
                  } catch {
                    return null;
                  }
                })()
              : item.analysis_result;

          return (
            <div
              key={item.id}
              onClick={() =>
                navigate("/report", {
                  state: {
                    analysis: analysisResult,
                    resource_count: item.resources_scanned,
                  },
                })
              }
              className="bg-zinc-900 p-6 rounded-xl mb-4 cursor-pointer hover:bg-zinc-800 transition-colors"
            >
              <h2 className="font-semibold text-lg mb-1">
                {item.resource_group}
              </h2>
              <p className="text-zinc-400 text-sm">
                Issues: {item.issues_found}
              </p>
              <p className="text-zinc-400 text-sm">
                Estimated Savings: ${item.estimated_savings}
              </p>
              <p className="text-zinc-500 text-xs mt-2">{item.created_at}</p>
            </div>
          );
        })}
      </div>
    </>
  );
}
