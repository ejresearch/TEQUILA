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
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Progress } from "@/components/ui/progress";

interface WeekData {
  week_number: number;
  status: "not_generated" | "partial" | "complete" | "invalid";
  spec?: {
    grammar_focus: string;
    objectives: string[];
    vocabulary: Array<{ latin: string; english: string }>;
  };
  days: Array<{
    day_number: number;
    class_name: string;
    summary: string;
    grade_level: string;
  }>;
}

export default function WeekDetailPage() {
  const params = useParams();
  const router = useRouter();
  const weekId = parseInt(params.id as string);

  const [week, setWeek] = useState<WeekData | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [generateProgress, setGenerateProgress] = useState(0);

  useEffect(() => {
    const fetchWeekData = async () => {
      try {
        // First, get the week status from the list endpoint
        const weeksResponse = await fetch("http://localhost:8000/api/v1/weeks");
        if (!weeksResponse.ok) throw new Error("Failed to fetch weeks");

        const weeksData = await weeksResponse.json();
        const weekInfo = weeksData.weeks.find((w: any) => w.week_number === weekId);

        if (!weekInfo) {
          setWeek(null);
          setLoading(false);
          return;
        }

        // If the week is complete or partial, load actual day data
        if (weekInfo.status === "complete" || weekInfo.status === "partial") {
          // Fetch real day data for each day
          const dayPromises = Array.from({ length: weekInfo.has_days }, async (_, i) => {
            try {
              const dayResponse = await fetch(`http://localhost:8000/api/v1/weeks/${weekId}/days/${i + 1}`);
              if (dayResponse.ok) {
                return await dayResponse.json();
              }
              return {
                day_number: i + 1,
                class_name: `Day ${i + 1}`,
                summary: `Day ${i + 1} content`,
                grade_level: "7-8",
              };
            } catch (error) {
              console.error(`Error fetching day ${i + 1}:`, error);
              return {
                day_number: i + 1,
                class_name: `Day ${i + 1}`,
                summary: `Day ${i + 1} content`,
                grade_level: "7-8",
              };
            }
          });

          const daysData = await Promise.all(dayPromises);

          setWeek({
            week_number: weekId,
            status: weekInfo.status,
            spec: {
              grammar_focus: `Week ${weekId}`,
              objectives: [],
              vocabulary: [],
            },
            days: daysData.map((day: any) => ({
              day_number: day.day,
              class_name: day.class_name || `Day ${day.day}`,
              summary: day.summary || `Day ${day.day} content`,
              grade_level: day.grade_level || "7-8",
            })),
          });
        } else {
          setWeek({
            week_number: weekId,
            status: weekInfo.status,
            days: [],
          });
        }
      } catch (error) {
        console.error("Error fetching week data:", error);
        setWeek(null);
      } finally {
        setLoading(false);
      }
    };

    fetchWeekData();
  }, [weekId]);

  const handleGenerate = async () => {
    setGenerating(true);
    setGenerateProgress(0);

    // Simulate generation progress
    const interval = setInterval(() => {
      setGenerateProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval);
          setGenerating(false);
          return 100;
        }
        return prev + 10;
      });
    }, 500);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-gray-500">Loading week...</p>
      </div>
    );
  }

  if (!week) {
    return (
      <div className="space-y-6">
        <Alert>
          <AlertTitle>Week Not Found</AlertTitle>
          <AlertDescription>
            Week {weekId} could not be found. Please check the week number.
          </AlertDescription>
        </Alert>
        <Button onClick={() => router.push("/weeks")}>Back to Weeks</Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-bold text-gray-900">
              Week {week.week_number}
            </h1>
            {week.status === "complete" && (
              <Badge className="bg-green-500">Complete</Badge>
            )}
            {week.status === "partial" && (
              <Badge className="bg-yellow-500">Partial</Badge>
            )}
            {week.status === "not_generated" && (
              <Badge variant="outline">Not Generated</Badge>
            )}
          </div>
          {week.spec && (
            <p className="mt-2 text-gray-600">{week.spec.grammar_focus}</p>
          )}
        </div>
        <div className="flex gap-2">
          <Button variant="outline" asChild>
            <Link href="/weeks">Back to List</Link>
          </Button>
          {week.status === "not_generated" && (
            <Button asChild>
              <Link href={`/generate/${weekId}`}>Generate Week</Link>
            </Button>
          )}
          {week.status === "complete" && (
            <>
              <Button variant="outline" asChild>
                <Link href={`/weeks/${weekId}/validate`}>Validate</Link>
              </Button>
              <Button asChild>
                <Link href={`/weeks/${weekId}/export`}>Export</Link>
              </Button>
            </>
          )}
        </div>
      </div>

      {/* Generation Progress */}
      {generating && (
        <Card>
          <CardHeader>
            <CardTitle>Generating Week {week.week_number}</CardTitle>
            <CardDescription>
              This may take a few minutes. Progress: {generateProgress}%
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Progress value={generateProgress} className="h-4" />
          </CardContent>
        </Card>
      )}

      {/* Content Tabs */}
      {week.status !== "not_generated" && (
        <Tabs defaultValue="overview" className="space-y-4">
          <TabsList>
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="spec">Week Spec</TabsTrigger>
            <TabsTrigger value="days">Days</TabsTrigger>
            <TabsTrigger value="internal">Internal Docs</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Week Overview</CardTitle>
                <CardDescription>
                  Summary of Week {week.week_number} content
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {week.spec && (
                  <>
                    <div>
                      <h3 className="font-semibold mb-2">Grammar Focus</h3>
                      <p className="text-gray-700">{week.spec.grammar_focus}</p>
                    </div>

                    <div>
                      <h3 className="font-semibold mb-2">Learning Objectives</h3>
                      <ul className="list-disc list-inside space-y-1">
                        {week.spec.objectives.map((obj, i) => (
                          <li key={i} className="text-gray-700">
                            {obj}
                          </li>
                        ))}
                      </ul>
                    </div>

                    <div>
                      <h3 className="font-semibold mb-2">
                        Vocabulary ({week.spec.vocabulary.length} words)
                      </h3>
                      <div className="grid grid-cols-2 gap-2">
                        {week.spec.vocabulary.map((word, i) => (
                          <div
                            key={i}
                            className="p-2 bg-gray-50 rounded border"
                          >
                            <span className="font-medium">{word.latin}</span> —{" "}
                            {word.english}
                          </div>
                        ))}
                      </div>
                    </div>
                  </>
                )}

                <div>
                  <h3 className="font-semibold mb-2">Days</h3>
                  <div className="grid grid-cols-1 gap-3">
                    {week.days.map((day) => (
                      <Link
                        key={day.day_number}
                        href={`/weeks/${weekId}/days/${day.day_number}`}
                      >
                        <Card className="hover:border-blue-500 transition-colors cursor-pointer">
                          <CardHeader>
                            <CardTitle className="text-lg">
                              Day {day.day_number}: {day.class_name}
                            </CardTitle>
                            <CardDescription>{day.summary}</CardDescription>
                          </CardHeader>
                        </Card>
                      </Link>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="spec">
            <Card>
              <CardHeader>
                <CardTitle>Week Specification</CardTitle>
                <CardDescription>
                  Complete week spec from internal_documents/
                </CardDescription>
              </CardHeader>
              <CardContent>
                <pre className="bg-gray-50 p-4 rounded overflow-x-auto text-sm">
                  {JSON.stringify(week.spec, null, 2)}
                </pre>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="days" className="space-y-4">
            {week.days.map((day) => (
              <Card key={day.day_number}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle>Day {day.day_number}</CardTitle>
                      <CardDescription>{day.class_name}</CardDescription>
                    </div>
                    <Button variant="outline" size="sm" asChild>
                      <Link href={`/weeks/${weekId}/days/${day.day_number}`}>
                        Edit Day
                      </Link>
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-gray-700">{day.summary}</p>
                  <p className="text-sm text-gray-500 mt-2">
                    Grade Level: {day.grade_level}
                  </p>
                </CardContent>
              </Card>
            ))}
          </TabsContent>

          <TabsContent value="internal">
            <Card>
              <CardHeader>
                <CardTitle>Internal Documents</CardTitle>
                <CardDescription>
                  Planning documents from internal_documents/ folder
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="p-3 bg-gray-50 rounded border">
                    <span className="font-medium">week_spec.json</span>
                    <p className="text-sm text-gray-600">
                      Complete week specification
                    </p>
                  </div>
                  <div className="p-3 bg-gray-50 rounded border">
                    <span className="font-medium">week_summary.md</span>
                    <p className="text-sm text-gray-600">
                      Human-readable overview
                    </p>
                  </div>
                  <div className="p-3 bg-gray-50 rounded border">
                    <span className="font-medium">role_context.json</span>
                    <p className="text-sm text-gray-600">
                      AI tutor persona for the week
                    </p>
                  </div>
                  <div className="p-3 bg-gray-50 rounded border">
                    <span className="font-medium">generation_log.json</span>
                    <p className="text-sm text-gray-600">
                      Provenance tracking
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      )}

      {/* Not Generated State */}
      {week.status === "not_generated" && !generating && (
        <Card>
          <CardHeader>
            <CardTitle>Week Not Generated</CardTitle>
            <CardDescription>
              This week has not been generated yet. Click the button above to
              generate it.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Alert>
              <AlertTitle>Generation Process</AlertTitle>
              <AlertDescription>
                Generation creates:
                <ul className="list-disc list-inside mt-2 space-y-1">
                  <li>Week specification (grammar focus, objectives, vocab)</li>
                  <li>Role context for Sparky (AI tutor)</li>
                  <li>4 complete days (Discovery, Practice, Review, Quiz)</li>
                  <li>Quiz packet and teacher key</li>
                </ul>
              </AlertDescription>
            </Alert>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
