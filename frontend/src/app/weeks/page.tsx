"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface WeekStatus {
  week_number: number;
  status: "not_generated" | "partial" | "complete" | "invalid";
  has_spec: boolean;
  has_days: number;
  last_modified?: string;
}

export default function WeeksPage() {
  const [weeks, setWeeks] = useState<WeekStatus[]>([]);
  const [filter, setFilter] = useState<string>("all");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchWeeks = async () => {
      try {
        const response = await fetch("http://localhost:8000/api/v1/weeks");
        if (!response.ok) throw new Error("Failed to fetch weeks");

        const data = await response.json();
        setWeeks(data.weeks);
      } catch (error) {
        console.error("Error fetching weeks:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchWeeks();
  }, []);

  const filteredWeeks = weeks.filter((week) => {
    if (filter === "all") return true;
    return week.status === filter;
  });

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

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-gray-500">Loading weeks...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">All Weeks</h1>
          <p className="mt-2 text-gray-600">
            Manage and view all 35 weeks of curriculum
          </p>
        </div>
        <Button asChild>
          <Link href="/">Back to Dashboard</Link>
        </Button>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Weeks List</CardTitle>
              <CardDescription>
                Showing {filteredWeeks.length} of {weeks.length} weeks
              </CardDescription>
            </div>
            <Select value={filter} onValueChange={setFilter}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Weeks</SelectItem>
                <SelectItem value="complete">Complete</SelectItem>
                <SelectItem value="partial">Partial</SelectItem>
                <SelectItem value="not_generated">Not Generated</SelectItem>
                <SelectItem value="invalid">Invalid</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Week</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Spec</TableHead>
                <TableHead>Days</TableHead>
                <TableHead>Last Modified</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredWeeks.map((week) => (
                <TableRow key={week.week_number}>
                  <TableCell className="font-medium">
                    Week {week.week_number}
                  </TableCell>
                  <TableCell>{getStatusBadge(week.status)}</TableCell>
                  <TableCell>
                    {week.has_spec ? (
                      <span className="text-green-600">✓</span>
                    ) : (
                      <span className="text-gray-400">✗</span>
                    )}
                  </TableCell>
                  <TableCell>{week.has_days}/4</TableCell>
                  <TableCell className="text-sm text-gray-500">
                    {week.last_modified
                      ? new Date(week.last_modified).toLocaleDateString()
                      : "—"}
                  </TableCell>
                  <TableCell className="text-right space-x-2">
                    <Button variant="outline" size="sm" asChild>
                      <Link href={`/weeks/${week.week_number}`}>View</Link>
                    </Button>
                    {week.status === "complete" && (
                      <Button variant="outline" size="sm" asChild>
                        <Link href={`/weeks/${week.week_number}/validate`}>
                          Validate
                        </Link>
                      </Button>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
