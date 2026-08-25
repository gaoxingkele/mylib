import { useMemo } from "react";
import { Progress } from "@/components/ui/progress";

const PHASE_MAP: Record<string, number> = {
  "Preparing installer": 0,
  "Checking directory permissions...": 5,
  "Directory permissions OK": 10,
  "Git available": 15,
  "cloning repository": 20,
  "Downloading skills": 20,
  "downloading tarball": 20,
  "Download complete": 60,
  "Copying skills": 70,
  Copied: 90,
  "Cleanup complete": 95,
};

function pctFromLog(log: string): number | null {
  const downloadMatch = log.match(/^Download progress\s+(\d+)%/i);
  if (downloadMatch?.[1]) {
    const downloadPct = Math.max(0, Math.min(100, Number(downloadMatch[1])));
    return Math.round(20 + downloadPct * 0.4);
  }

  const downloadedMatch = log.match(/^Downloaded\s+(\d+)\s+MiB/i);
  if (downloadedMatch?.[1]) {
    const mib = Math.max(0, Number(downloadedMatch[1]));
    return Math.min(55, 20 + mib);
  }

  for (const [key, pct] of Object.entries(PHASE_MAP)) {
    if (log.toLowerCase().includes(key.toLowerCase())) return pct;
  }
  return null;
}

interface InstallProgressProps {
  isInstalling: boolean;
  isComplete: boolean;
  error: string | null;
  logs: string[];
}

export function InstallProgress({
  isComplete,
  error,
  logs,
}: InstallProgressProps) {
  const pct = useMemo(() => {
    if (isComplete) return 100;
    return logs.reduce((current, line) => {
      const next = pctFromLog(line);
      return next === null ? current : Math.max(current, next);
    }, 0);
  }, [isComplete, logs]);

  const label = isComplete
    ? "Done"
    : error
      ? "Error"
      : logs.length > 0
        ? logs[logs.length - 1]
        : "Starting...";

  return (
    <div className="space-y-2 py-1">
      <Progress value={pct} />
      <div className="flex items-center justify-between">
        <p className="max-w-[80%] truncate text-muted-foreground text-xs">
          {label}
        </p>
        <p className="font-mono text-muted-foreground text-xs tabular-nums">
          {pct}%
        </p>
      </div>
    </div>
  );
}
