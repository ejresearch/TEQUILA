"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";

interface WeekStatus {
  week_number: number;
  status: "not_generated" | "partial" | "complete" | "invalid";
  has_spec: boolean;
  has_days: number;
  last_modified?: string;
}

export default function Dashboard() {
  const [weeks, setWeeks] = useState<WeekStatus[]>([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    total: 35,
    complete: 0,
    partial: 0,
    not_generated: 0,
  });

  useEffect(() => {
    const fetchWeeks = async () => {
      try {
        const response = await fetch("http://localhost:8000/api/v1/weeks");
        if (!response.ok) throw new Error("Failed to fetch weeks");

        const data = await response.json();
        setWeeks(data.weeks);

        // Calculate stats
        const complete = data.weeks.filter((w: WeekStatus) => w.status === "complete").length;
        const partial = data.weeks.filter((w: WeekStatus) => w.status === "partial").length;
        const not_generated = data.weeks.filter(
          (w: WeekStatus) => w.status === "not_generated"
        ).length;

        setStats({
          total: 35,
          complete,
          partial,
          not_generated,
        });
      } catch (error) {
        console.error("Error fetching weeks:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchWeeks();
  }, []);

  const getStatusBadge = (status: WeekStatus["status"]) => {
    switch (status) {
      case "complete":
        return <Badge className="bg-green-500">Complete</Badge>;
      case "partial":
        return <Badge className="bg-yellow-500">Partial</Badge>;
      case "invalid":
        return <Badge className="bg-red-500">Invalid</Badge>;
      default:
        return <Badge variant="outline">Not Generated</Badge>;
    }
  };

  const progressPercent = Math.round((stats.complete / stats.total) * 100);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-gray-500">Loading curriculum...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">
          Curriculum Dashboard
        </h1>
        <p className="mt-2 text-gray-600">
          Overview of all 35 weeks in the Latin A curriculum
        </p>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-gray-600">
              Total Weeks
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{stats.total}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-gray-600">
              Complete
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-green-600">
              {stats.complete}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-gray-600">
              In Progress
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-yellow-600">
              {stats.partial}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-gray-600">
              Not Generated
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-gray-400">
              {stats.not_generated}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Progress Bar */}
      <Card>
        <CardHeader>
          <CardTitle>Overall Progress</CardTitle>
          <CardDescription>
            {stats.complete} of {stats.total} weeks completed ({progressPercent}
            %)
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Progress value={progressPercent} className="h-4" />
        </CardContent>
      </Card>

      {/* Weeks Grid */}
      <Card>
        <CardHeader>
          <CardTitle>All Weeks</CardTitle>
          <CardDescription>
            Click on a week to view or edit its content
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
            {weeks.map((week) => (
              <Link
                key={week.week_number}
                href={`/weeks/${week.week_number}`}
                className="block h-full"
              >
                <Card className="hover:border-blue-500 transition-colors cursor-pointer h-full flex flex-col">
                  <CardHeader className="pb-3">
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-lg">
                        Week {week.week_number}
                      </CardTitle>
                      {getStatusBadge(week.status)}
                    </div>
                  </CardHeader>
                  <CardContent className="flex-1">
                    <div className="space-y-1 text-sm">
                      <p className="text-gray-600">
                        Days: {week.has_days}/4
                      </p>
                      <p className="text-gray-600">
                        Spec: {week.has_spec ? "✓" : "✗"}
                      </p>
                      {week.last_modified && (
                        <p className="text-xs text-gray-400">
                          Modified: {new Date(week.last_modified).toLocaleDateString()}
                        </p>
                      )}
                    </div>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
        </CardHeader>
        <CardContent className="flex gap-4">
          <Button asChild>
            <Link href="/weeks">View All Weeks</Link>
          </Button>
          <Button variant="outline" asChild>
            <Link href="/analytics">View Analytics</Link>
          </Button>
          <Button variant="outline" asChild>
            <Link href="/exports">Manage Exports</Link>
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
