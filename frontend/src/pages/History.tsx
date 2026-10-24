
import axios from "axios";
import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import Navbar from "../components/Navbar";

export default function History() {
  const [history, setHistory] = useState<any[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const navigate = useNavigate();

  const loadHistory = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const token =
        localStorage.getItem("token") ||
        sessionStorage.getItem("token");

      if (!token) {
        setError("Your session has expired. Please log in again.");
        setHistory([]);
        return;
      }

      const res = await axios.get(
        "http://localhost:8000/api/history",
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      setHistory(
        Array.isArray(res.data?.history)
          ? res.data.history
          : []
      );
    } catch (err) {
      console.error("Failed to load history:", err);

      setError(
        axios.isAxiosError(err) && err.response?.status === 401
          ? "Your session has expired. Please log in again."
          : axios.isAxiosError(err) && err.response?.status === 403
          ? "You don't have permission to view history."
          : "Failed to load history. Please try again."
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  return (
    <>
      <Navbar />

      <div className="p-8 text-white">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-3xl">Analysis History</h1>

          <button
            onClick={loadHistory}
            disabled={loading}
            className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 px-4 py-2 rounded-lg"
          >
            {loading ? "Loading..." : "Refresh"}
          </button>
        </div>

        {error && (
          <div className="text-red-400 mb-4">
            <p>{error}</p>
            <button
              onClick={loadHistory}
              className="underline mt-2"
            >
              Try again
            </button>
          </div>
        )}

        {loading && (
          <p className="text-zinc-400">
            Loading analysis history...
          </p>
        )}

        {!loading && !error && history.length === 0 && (
          <p className="text-zinc-400">No analyses yet.</p>
        )}

        {!loading &&
          history.map((item) => {
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
                      analysis_id: item.id,
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

                <p className="text-zinc-500 text-xs mt-2">
                  {item.created_at}
                </p>
              </div>
            );
          })}
      </div>
    </>
  );
}
