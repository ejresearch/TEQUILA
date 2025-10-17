"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Alert, AlertDescription } from "@/components/ui/alert";

interface LogEntry {
  timestamp: string;
  level: "info" | "success" | "warning" | "error";
  message: string;
}

export default function GenerateWeekPage() {
  const params = useParams();
  const router = useRouter();
  const weekId = parseInt(params.week as string);

  const [isGenerating, setIsGenerating] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState("");
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [completed, setCompleted] = useState(false);

  const addLog = (level: LogEntry["level"], message: string) => {
    const timestamp = new Date().toLocaleTimeString();
    setLogs((prev) => [...prev, { timestamp, level, message }]);
  };

  const startGeneration = async () => {
    setIsGenerating(true);
    setProgress(0);
    setLogs([]);
    setError(null);
    setCompleted(false);

    try {
      addLog("info", `Starting generation for Week ${weekId}`);
      setCurrentStep("Calling backend API...");
      setProgress(5);

      // Call the backend generation API
      const response = await fetch(
        `http://localhost:8000/api/v1/gen/weeks/${weekId}/generate`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
        }
      );

      if (!response.ok) {
        throw new Error(`API returned ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();

      // Parse stdout logs
      if (data.stdout) {
        const lines = data.stdout.split("\n");
        let progressValue = 10;

        for (const line of lines) {
          if (!line.trim()) continue;

          // Parse log level and message
          let level: LogEntry["level"] = "info";
          let message = line;

          if (line.includes("ERROR") || line.includes("Failed")) {
            level = "error";
          } else if (line.includes("SUCCESS") || line.includes("✓") || line.includes("completed")) {
            level = "success";
          } else if (line.includes("WARNING") || line.includes("⚠")) {
            level = "warning";
          }

          addLog(level, message);

          // Update progress based on content
          if (line.includes("Phase 1") || line.includes("week_spec")) {
            setCurrentStep("Phase 1: Generating week planning...");
            progressValue = Math.min(progressValue + 5, 40);
          } else if (line.includes("Day 1") || line.includes("Day1")) {
            setCurrentStep("Phase 2: Generating Day 1...");
            progressValue = 45;
          } else if (line.includes("Day 2") || line.includes("Day2")) {
            setCurrentStep("Phase 2: Generating Day 2...");
            progressValue = 60;
          } else if (line.includes("Day 3") || line.includes("Day3")) {
            setCurrentStep("Phase 2: Generating Day 3...");
            progressValue = 75;
          } else if (line.includes("Day 4") || line.includes("Day4")) {
            setCurrentStep("Phase 2: Generating Day 4...");
            progressValue = 90;
          }

          setProgress(progressValue);

          // Small delay to make logs readable
          await new Promise((resolve) => setTimeout(resolve, 50));
        }
      }

      // Parse stderr for errors
      if (data.stderr && data.stderr.trim()) {
        const errorLines = data.stderr.split("\n");
        for (const line of errorLines) {
          if (line.trim()) {
            addLog("error", line);
          }
        }
      }

      // Check final status
      if (data.success) {
        setProgress(100);
        setCurrentStep("Generation complete!");
        setCompleted(true);
        addLog("success", `Week ${weekId} generation completed successfully!`);
      } else {
        throw new Error(`Generation failed with return code ${data.return_code}`);
      }

      setIsGenerating(false);
    } catch (err: any) {
      setError(err.message || "Generation failed");
      addLog("error", err.message || "An error occurred during generation");
      setIsGenerating(false);
      setProgress(0);
    }
  };

  const getLogColor = (level: LogEntry["level"]) => {
    switch (level) {
      case "success":
        return "text-green-600";
      case "error":
        return "text-red-600";
      case "warning":
        return "text-yellow-600";
      default:
        return "text-gray-700";
    }
  };

  const getLogIcon = (level: LogEntry["level"]) => {
    switch (level) {
      case "success":
        return "✓";
      case "error":
        return "✗";
      case "warning":
        return "⚠";
      default:
        return "→";
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">
            Generate Week {weekId}
          </h1>
          <p className="mt-2 text-gray-600">
            Two-phase generation: Week planning → Day generation
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" asChild>
            <Link href={`/weeks/${weekId}`}>Back to Week</Link>
          </Button>
          {completed && (
            <Button asChild>
              <Link href={`/weeks/${weekId}`}>View Week</Link>
            </Button>
          )}
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <Alert className="border-red-500 bg-red-50">
          <AlertDescription className="text-red-700">
            {error}
          </AlertDescription>
        </Alert>
      )}

      {/* Progress Card */}
      <Card>
        <CardHeader>
          <CardTitle>Generation Progress</CardTitle>
          <CardDescription>{currentStep || "Ready to start"}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="font-medium">{progress}%</span>
              <span className="text-gray-500">
                {isGenerating
                  ? "Generating..."
                  : completed
                  ? "Completed"
                  : "Not started"}
              </span>
            </div>
            <Progress value={progress} className="h-4" />
          </div>

          {!isGenerating && !completed && (
            <Button onClick={startGeneration} className="w-full" size="lg">
              Start Generation
            </Button>
          )}

          {isGenerating && (
            <Button disabled className="w-full" size="lg">
              Generating...
            </Button>
          )}

          {completed && (
            <div className="flex gap-2">
              <Button
                variant="outline"
                onClick={() => {
                  setCompleted(false);
                  setProgress(0);
                  setLogs([]);
                  setIsGenerating(false);
                }}
                className="flex-1"
              >
                Generate Again
              </Button>
              <Button asChild className="flex-1">
                <Link href={`/weeks/${weekId}`}>View Week</Link>
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Log Viewer */}
      <Card>
        <CardHeader>
          <CardTitle>Generation Log</CardTitle>
          <CardDescription>
            Real-time updates from the generation process
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="bg-gray-900 rounded-lg p-4 h-96 overflow-y-auto font-mono text-sm">
            {logs.length === 0 ? (
              <p className="text-gray-500">
                No logs yet. Click "Start Generation" to begin.
              </p>
            ) : (
              <div className="space-y-1">
                {logs.map((log, index) => (
                  <div key={index} className="flex gap-2 text-white">
                    <span className="text-gray-500">{log.timestamp}</span>
                    <span className={getLogColor(log.level)}>
                      {getLogIcon(log.level)}
                    </span>
                    <span>{log.message}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Info Card */}
      <Card>
        <CardHeader>
          <CardTitle>What Gets Generated</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <h3 className="font-semibold mb-2">Phase 1: Week Planning</h3>
              <ul className="list-disc list-inside space-y-1 text-sm text-gray-700">
                <li>week_spec.json (grammar focus, objectives, vocabulary)</li>
                <li>role_context.json (Sparky's persona and behavior)</li>
                <li>week_summary.md (human-readable overview)</li>
                <li>generation_log.json (provenance tracking)</li>
              </ul>
            </div>

            <div>
              <h3 className="font-semibold mb-2">Phase 2: Day Generation</h3>
              <ul className="list-disc list-inside space-y-1 text-sm text-gray-700">
                <li>4 complete days (Discovery, Practice, Review, Quiz)</li>
                <li>7 fields per day: class_name, summary, grade_level, role_context, guidelines, documents, greeting</li>
                <li>6 teacher support documents per day in 06_document_for_sparky/</li>
              </ul>
            </div>

            <div>
              <h3 className="font-semibold mb-2">Validation</h3>
              <ul className="list-disc list-inside space-y-1 text-sm text-gray-700">
                <li>All 7 fields present for each day</li>
                <li>All 6 teacher documents generated</li>
                <li>Proper Latin macrons and grammar</li>
                <li>Virtue and faith integration verified</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
