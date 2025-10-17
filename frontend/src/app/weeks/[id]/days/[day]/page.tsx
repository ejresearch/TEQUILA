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
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Alert, AlertDescription } from "@/components/ui/alert";

interface DayData {
  week_number: number;
  day_number: number;
  class_name: string;
  summary: string;
  grade_level: string;
  role_context: any;
  guidelines_for_sparky: string;
  sparkys_greeting: string;
  documents: {
    vocabulary_key: string;
    chant_chart: string;
    spiral_review: string;
    teacher_voice_tips: string;
    virtue_and_faith: string;
    weekly_topics: string;
  };
}

export default function DayEditorPage() {
  const params = useParams();
  const router = useRouter();
  const weekId = parseInt(params.id as string);
  const dayNum = parseInt(params.day as string);

  const [day, setDay] = useState<DayData | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [edited, setEdited] = useState(false);

  useEffect(() => {
    const fetchDayData = async () => {
      try {
        const response = await fetch(
          `http://localhost:8000/api/v1/weeks/${weekId}/days/${dayNum}`
        );

        if (!response.ok) {
          console.error("Failed to fetch day data");
          setDay(null);
          setLoading(false);
          return;
        }

        const data = await response.json();

        // Map API response to DayData interface
        setDay({
          week_number: weekId,
          day_number: dayNum,
          class_name: data.class_name || "",
          summary: data.summary || "",
          grade_level: data.grade_level || "",
          role_context: data.role_context || null,
          guidelines_for_sparky: data.guidelines_for_sparky || "",
          sparkys_greeting: data.sparkys_greeting || "",
          documents: {
            vocabulary_key: data.documents?.vocabulary_key || "",
            chant_chart: data.documents?.chant_chart || "",
            spiral_review: data.documents?.spiral_review || "",
            teacher_voice_tips: data.documents?.teacher_voice_tips || "",
            virtue_and_faith: data.documents?.virtue_and_faith || "",
            weekly_topics: data.documents?.weekly_topics || "",
          },
        });
      } catch (error) {
        console.error("Error fetching day data:", error);
        setDay(null);
      } finally {
        setLoading(false);
      }
    };

    fetchDayData();
  }, [weekId, dayNum]);

  const handleSave = async () => {
    setSaving(true);
    // Simulate save
    await new Promise((resolve) => setTimeout(resolve, 1000));
    setSaving(false);
    setEdited(false);
  };

  const updateField = (field: keyof DayData, value: string) => {
    if (day) {
      setDay({ ...day, [field]: value });
      setEdited(true);
    }
  };

  const updateDocument = (field: keyof DayData["documents"], value: string) => {
    if (day) {
      setDay({
        ...day,
        documents: { ...day.documents, [field]: value },
      });
      setEdited(true);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-gray-500">Loading day...</p>
      </div>
    );
  }

  if (!day) {
    return (
      <div className="space-y-6">
        <Alert>
          <AlertDescription>
            Day not found. Please check the week and day numbers.
          </AlertDescription>
        </Alert>
        <Button onClick={() => router.push(`/weeks/${weekId}`)}>
          Back to Week
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">
            Week {weekId}, Day {dayNum}
          </h1>
          <p className="mt-2 text-gray-600">{day.class_name}</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" asChild>
            <Link href={`/weeks/${weekId}`}>Back to Week</Link>
          </Button>
          <Button
            onClick={handleSave}
            disabled={!edited || saving}
          >
            {saving ? "Saving..." : edited ? "Save Changes" : "Saved"}
          </Button>
        </div>
      </div>

      {edited && (
        <Alert>
          <AlertDescription>
            You have unsaved changes. Click "Save Changes" to persist them.
          </AlertDescription>
        </Alert>
      )}

      <Tabs defaultValue="field01" className="space-y-4">
        <TabsList>
          <TabsTrigger value="field01">01 - Class Name</TabsTrigger>
          <TabsTrigger value="field02">02 - Summary</TabsTrigger>
          <TabsTrigger value="field03">03 - Grade Level</TabsTrigger>
          <TabsTrigger value="field04">04 - Role Context</TabsTrigger>
          <TabsTrigger value="field05">05 - Guidelines</TabsTrigger>
          <TabsTrigger value="field06">06 - Documents</TabsTrigger>
          <TabsTrigger value="field07">07 - Greeting</TabsTrigger>
        </TabsList>

        <TabsContent value="field01">
          <Card>
            <CardHeader>
              <CardTitle>Field 01: Class Name</CardTitle>
              <CardDescription>
                The title of this lesson (from 01_class_name.txt)
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Input
                value={day.class_name}
                onChange={(e) => updateField("class_name", e.target.value)}
                placeholder="e.g., Latin A – Week 11 Day 1"
                className="text-base"
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="field02">
          <Card>
            <CardHeader>
              <CardTitle>Field 02: Summary</CardTitle>
              <CardDescription>
                Brief overview of the lesson content (from 02_summary.md)
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Textarea
                value={day.summary}
                onChange={(e) => updateField("summary", e.target.value)}
                placeholder="Brief summary of the day's lesson..."
                rows={10}
                className="text-sm"
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="field03">
          <Card>
            <CardHeader>
              <CardTitle>Field 03: Grade Level</CardTitle>
              <CardDescription>
                Target grade level (from 03_grade_level.txt)
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Input
                value={day.grade_level}
                onChange={(e) => updateField("grade_level", e.target.value)}
                placeholder="e.g., 3–5 (Grammar Stage)"
                className="text-base"
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="field04">
          <Card>
            <CardHeader>
              <CardTitle>Field 04: Role Context</CardTitle>
              <CardDescription>
                JSON configuration for Sparky's persona (from 04_role_context.json)
              </CardDescription>
            </CardHeader>
            <CardContent>
              <pre className="bg-gray-50 p-4 rounded overflow-x-auto text-sm font-mono max-h-96">
                {day.role_context
                  ? JSON.stringify(day.role_context, null, 2)
                  : "No role context available"}
              </pre>
              <p className="text-sm text-gray-500 mt-2">
                This JSON defines Sparky's character, voice, teaching style, virtue focus,
                and faith connections for this specific day.
              </p>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="field05">
          <Card>
            <CardHeader>
              <CardTitle>Field 05: Guidelines for Sparky</CardTitle>
              <CardDescription>
                Detailed teaching instructions (from 05_guidelines_for_sparky.md or .json)
              </CardDescription>
            </CardHeader>
            <CardContent>
              {typeof day.guidelines_for_sparky === "string" ? (
                <Textarea
                  value={day.guidelines_for_sparky}
                  onChange={(e) =>
                    updateField("guidelines_for_sparky", e.target.value)
                  }
                  rows={20}
                  className="font-mono text-sm"
                  placeholder="Markdown instructions for Sparky..."
                />
              ) : (
                <pre className="bg-gray-50 p-4 rounded overflow-x-auto text-sm font-mono max-h-96">
                  {day.guidelines_for_sparky
                    ? JSON.stringify(day.guidelines_for_sparky, null, 2)
                    : "No guidelines available"}
                </pre>
              )}
              <p className="text-sm text-gray-500 mt-2">
                Detailed teaching guidelines, pacing, emphasis points, and
                pedagogical notes for this lesson.
              </p>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="field06" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Field 06: Teacher Documents</CardTitle>
              <CardDescription>
                Six support documents from 06_document_for_sparky/ folder
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div>
                <label className="text-sm font-semibold mb-2 block">
                  Vocabulary Key
                </label>
                <Textarea
                  value={day.documents.vocabulary_key || ""}
                  onChange={(e) =>
                    updateDocument("vocabulary_key", e.target.value)
                  }
                  rows={6}
                  className="font-mono text-sm"
                  placeholder="vocabulary_key_document.txt content..."
                />
              </div>

              <div>
                <label className="text-sm font-semibold mb-2 block">
                  Chant Chart
                </label>
                <Textarea
                  value={day.documents.chant_chart || ""}
                  onChange={(e) => updateDocument("chant_chart", e.target.value)}
                  rows={6}
                  className="font-mono text-sm"
                  placeholder="chant_chart_document.txt content..."
                />
              </div>

              <div>
                <label className="text-sm font-semibold mb-2 block">
                  Spiral Review
                </label>
                <Textarea
                  value={day.documents.spiral_review || ""}
                  onChange={(e) =>
                    updateDocument("spiral_review", e.target.value)
                  }
                  rows={6}
                  className="font-mono text-sm"
                  placeholder="spiral_review_document.txt content..."
                />
              </div>

              <div>
                <label className="text-sm font-semibold mb-2 block">
                  Teacher Voice Tips
                </label>
                <Textarea
                  value={day.documents.teacher_voice_tips || ""}
                  onChange={(e) =>
                    updateDocument("teacher_voice_tips", e.target.value)
                  }
                  rows={6}
                  className="font-mono text-sm"
                  placeholder="teacher_voice_tips_document.txt content..."
                />
              </div>

              <div>
                <label className="text-sm font-semibold mb-2 block">
                  Virtue & Faith
                </label>
                <Textarea
                  value={day.documents.virtue_and_faith || ""}
                  onChange={(e) =>
                    updateDocument("virtue_and_faith", e.target.value)
                  }
                  rows={6}
                  className="font-mono text-sm"
                  placeholder="virtue_and_faith_document.txt content..."
                />
              </div>

              <div>
                <label className="text-sm font-semibold mb-2 block">
                  Weekly Topics
                </label>
                <Textarea
                  value={day.documents.weekly_topics || ""}
                  onChange={(e) =>
                    updateDocument("weekly_topics", e.target.value)
                  }
                  rows={6}
                  className="font-mono text-sm"
                  placeholder="weekly_topics_document.txt content..."
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="field07">
          <Card>
            <CardHeader>
              <CardTitle>Field 07: Sparky's Greeting</CardTitle>
              <CardDescription>
                The AI tutor's opening message to students (from 07_sparkys_greeting.txt)
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Textarea
                value={day.sparkys_greeting || ""}
                onChange={(e) =>
                  updateField("sparkys_greeting", e.target.value)
                }
                rows={8}
                className="text-sm"
                placeholder="Salve! Welcome to Latin A Week..."
              />
              <p className="text-sm text-gray-500 mt-2">
                This greeting sets the tone for the lesson and introduces
                the day's content in Sparky's voice.
              </p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
