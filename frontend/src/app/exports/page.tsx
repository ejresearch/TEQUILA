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
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";

interface ExportItem {
  week_number: number;
  filename: string;
  size_kb: number;
  created_at: string;
  status: "ready" | "generating" | "failed";
}

export default function ExportsPage() {
  const [exports, setExports] = useState<ExportItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState<number | null>(null);

  useEffect(() => {
    // Mock data - will be replaced with API call
    setExports([
      {
        week_number: 1,
        filename: "LatinA_Week01.zip",
        size_kb: 156.3,
        created_at: new Date().toISOString(),
        status: "ready",
      },
      {
        week_number: 11,
        filename: "LatinA_Week11.zip",
        size_kb: 142.8,
        created_at: new Date().toISOString(),
        status: "ready",
      },
      {
        week_number: 12,
        filename: "LatinA_Week12.zip",
        size_kb: 138.2,
        created_at: new Date().toISOString(),
        status: "ready",
      },
      {
        week_number: 13,
        filename: "LatinA_Week13.zip",
        size_kb: 145.9,
        created_at: new Date().toISOString(),
        status: "ready",
      },
      {
        week_number: 14,
        filename: "LatinA_Week14.zip",
        size_kb: 151.4,
        created_at: new Date().toISOString(),
        status: "ready",
      },
      {
        week_number: 15,
        filename: "LatinA_Week15.zip",
        size_kb: 148.7,
        created_at: new Date().toISOString(),
        status: "ready",
      },
    ]);
    setLoading(false);
  }, []);

  const handleExport = async (weekNumber: number) => {
    setGenerating(weekNumber);
    // Simulate export generation
    await new Promise((resolve) => setTimeout(resolve, 2000));
    setGenerating(null);
    // Refresh exports list
  };

  const handleDownload = async (weekNumber: number, filename: string) => {
    // Trigger download
    alert(`Downloading ${filename}...`);
  };

  const formatFileSize = (kb: number) => {
    if (kb < 1024) {
      return `${kb.toFixed(1)} KB`;
    }
    return `${(kb / 1024).toFixed(2)} MB`;
  };

  const totalSize = exports.reduce((sum, exp) => sum + exp.size_kb, 0);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-gray-500">Loading exports...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">
            Export Manager
          </h1>
          <p className="mt-2 text-gray-600">
            Download curriculum weeks as ZIP archives
          </p>
        </div>
        <Button variant="outline" asChild>
          <Link href="/">Back to Dashboard</Link>
        </Button>
      </div>

      {/* Export Info */}
      <Alert>
        <AlertDescription>
          ZIP exports include all day files, internal documents, assets, and a
          manifest.json with SHA-256 hashes for verification.
        </AlertDescription>
      </Alert>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-gray-600">
              Total Exports
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{exports.length}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-gray-600">
              Total Size
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{formatFileSize(totalSize)}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-gray-600">
              Avg Size/Week
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">
              {formatFileSize(totalSize / exports.length)}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Exports Table */}
      <Card>
        <CardHeader>
          <CardTitle>Available Exports</CardTitle>
          <CardDescription>
            Download or regenerate week exports
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Week</TableHead>
                <TableHead>Filename</TableHead>
                <TableHead>Size</TableHead>
                <TableHead>Created</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {exports.map((exp) => (
                <TableRow key={exp.week_number}>
                  <TableCell className="font-medium">
                    <Link
                      href={`/weeks/${exp.week_number}`}
                      className="hover:text-blue-600"
                    >
                      Week {exp.week_number}
                    </Link>
                  </TableCell>
                  <TableCell className="font-mono text-sm">
                    {exp.filename}
                  </TableCell>
                  <TableCell>{formatFileSize(exp.size_kb)}</TableCell>
                  <TableCell className="text-sm text-gray-500">
                    {new Date(exp.created_at).toLocaleDateString()}
                  </TableCell>
                  <TableCell>
                    {exp.status === "ready" && (
                      <Badge className="bg-green-500">Ready</Badge>
                    )}
                    {exp.status === "generating" && (
                      <Badge className="bg-yellow-500">Generating</Badge>
                    )}
                    {exp.status === "failed" && (
                      <Badge className="bg-red-500">Failed</Badge>
                    )}
                  </TableCell>
                  <TableCell className="text-right space-x-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() =>
                        handleDownload(exp.week_number, exp.filename)
                      }
                      disabled={exp.status !== "ready"}
                    >
                      Download
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleExport(exp.week_number)}
                      disabled={
                        generating === exp.week_number ||
                        exp.status === "generating"
                      }
                    >
                      {generating === exp.week_number
                        ? "Exporting..."
                        : "Re-export"}
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Export All Weeks */}
      <Card>
        <CardHeader>
          <CardTitle>Bulk Export</CardTitle>
          <CardDescription>
            Export multiple weeks at once
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-4">
            <Button onClick={() => alert("Exporting all complete weeks...")}>
              Export All Complete Weeks
            </Button>
            <Button
              variant="outline"
              onClick={() => alert("Exporting gold standards...")}
            >
              Export Gold Standards (1, 11-15)
            </Button>
          </div>
          <p className="text-sm text-gray-600">
            Bulk exports will be generated in the background. This may take
            several minutes.
          </p>
        </CardContent>
      </Card>

      {/* Export Settings */}
      <Card>
        <CardHeader>
          <CardTitle>Export Settings</CardTitle>
          <CardDescription>
            Configure export behavior
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded">
              <div>
                <p className="font-medium">Include Internal Documents</p>
                <p className="text-sm text-gray-600">
                  Week spec, summary, role context
                </p>
              </div>
              <Badge className="bg-green-500">Enabled</Badge>
            </div>

            <div className="flex items-center justify-between p-3 bg-gray-50 rounded">
              <div>
                <p className="font-medium">Include SHA-256 Hashes</p>
                <p className="text-sm text-gray-600">
                  Manifest with file verification
                </p>
              </div>
              <Badge className="bg-green-500">Enabled</Badge>
            </div>

            <div className="flex items-center justify-between p-3 bg-gray-50 rounded">
              <div>
                <p className="font-medium">Compress Assets</p>
                <p className="text-sm text-gray-600">
                  Reduce file size (slower)
                </p>
              </div>
              <Badge className="bg-green-500">Enabled</Badge>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
