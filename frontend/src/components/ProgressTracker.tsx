interface Props {
  steps: string[];
  // Fix 7: accept done flag so final step stops pulsing
  done?: boolean;
}

export default function ProgressTracker({ steps, done = false }: Props) {
  return (
    <div className="bg-zinc-900 p-5 rounded-xl">
      <h2 className="mb-4">Progress</h2>

      <div className="space-y-3">
        {steps.map((step, i) => {
          const isLast = i === steps.length - 1;
          // Fix 7: only pulse the latest step unless done
          const pulse = isLast && !done;

          return (
            <div
              key={i}
              className={`flex items-center gap-3 ${pulse ? "animate-pulse" : ""}`}
            >
              <div
                className={`w-3 h-3 rounded-full flex-shrink-0 ${
                  done || !isLast ? "bg-green-400" : "bg-blue-400"
                }`}
              />
              <span className={done || !isLast ? "text-zinc-300" : "text-white"}>
                {step}
              </span>
              {(done && isLast) && (
                <span className="text-green-400 text-xs ml-auto">✓ Done</span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
