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

          <h1 className="text-2xl mb-4">
            Analysis Summary
          </h1>

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