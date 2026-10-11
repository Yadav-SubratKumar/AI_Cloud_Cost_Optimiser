import {
  useLocation
} from "react-router-dom";

import Navbar from "../components/Navbar";

export default function Report() {
  const location =
    useLocation();

  const report =
    location.state;

  if (!report) {
    return null;
  }

  async function downloadPdf() {
    const analysisId = report.analysis_id;
    if (!analysisId) return;
    const token = localStorage.getItem("token") || sessionStorage.getItem("token");
    const response = await fetch(`http://localhost:8000/api/reports/${analysisId}/pdf`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!response.ok) throw new Error("Unable to generate PDF");
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `cloud-cost-analysis-${analysisId}.pdf`;
    link.click();
    URL.revokeObjectURL(url);
  }

  function badge(
    severity: string
  ) {
    if (
      severity === "high"
    ) {
      return "bg-red-600";
    }

    if (
      severity === "medium"
    ) {
      return "bg-yellow-600";
    }

    return "bg-green-600";
  }

  return (
    <>
      <Navbar />

      <div className="p-8 text-white">

        <div className="bg-zinc-900 p-6 rounded-xl mb-8">

          <div className="flex justify-between items-center mb-4">
            <h1 className="text-2xl">Analysis Summary</h1>
            {report.analysis_id && (
              <button onClick={downloadPdf} className="bg-blue-600 px-4 py-2 rounded">Download PDF</button>
            )}
          </div>

          <p>
            Resources:
            {" "}
            {report.resource_count}
          </p>

          <p>
            Issues:
            {" "}
            {
              report.analysis
                .issues.length
            }
          </p>

          <p>
            Estimated Savings:
            {" "}
            $
            {
              report.analysis
                .estimated_monthly_savings_usd
            }
          </p>

        </div>

        {
          report.analysis.issues.map(
            (issue: any) => (
              <div
                key={issue.title}
                className="
                  bg-zinc-900
                  p-6
                  rounded-xl
                  mb-5
                "
              >
                <h2>
                  {issue.title}
                </h2>

                <p>
                  {
                    issue.resource_name
                  }
                </p>

                <span
                  className={`
                    px-2
                    py-1
                    rounded
                    ${badge(
                      issue.severity
                    )}
                  `}
                >
                  {issue.severity}
                </span>

                <p className="mt-3">
                  {
                    issue.description
                  }
                </p>

                <pre
                  className="
                    bg-black
                    p-4
                    mt-4
                    rounded
                  "
                >
                  {
                    issue.fix_command
                  }
                </pre>

                <button
                  className="mt-3 bg-blue-600 px-3 py-2 rounded"
                  onClick={() =>
                    navigator
                      .clipboard
                      .writeText(
                        issue.fix_command
                      )
                  }
                >
                  Copy Command
                </button>
              </div>
            )
          )
        }

      </div>
    </>
  );
}