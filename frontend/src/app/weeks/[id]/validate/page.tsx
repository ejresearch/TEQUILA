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
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

interface ValidationError {
  location: string;
  message: string;
}

interface ValidationWarning {
  location: string;
  message: string;
}

interface ValidationInfo {
  location: string;
  message: string;
}

interface ValidationResult {
  week: number;
  is_valid: boolean;
  summary: string;
  errors: ValidationError[];
  warnings: ValidationWarning[];
  info: ValidationInfo[];
}

export default function ValidatePage() {
  const params = useParams();
  const router = useRouter();
  const weekId = parseInt(params.id as string);

  const [result, setResult] = useState<ValidationResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [validating, setValidating] = useState(false);

  useEffect(() => {
    loadValidation();
  }, [weekId]);

  const loadValidation = async () => {
    setLoading(true);
    // Mock data - will be replaced with API call
    await new Promise((resolve) => setTimeout(resolve, 500));

    setResult({
      week: weekId,
      is_valid: weekId === 1 || weekId >= 11,
      summary:
        weekId === 1 || weekId >= 11
          ? "✓ Week validation passed"
          : "✗ Week validation failed",
      errors:
        weekId === 1 || weekId >= 11
          ? []
          : [
              {
                location: "Day 2: 06_document_for_sparky",
                message: "Missing vocabulary_key_document.txt",
              },
              {
                location: "Day 3: 02_summary.md",
                message: "Summary exceeds maximum length (500 chars)",
              },
            ],
      warnings:
        weekId === 1
          ? []
          : [
              {
                location: "Day 4",
                message:
                  "Spiral review content is only 18% (recommended: ≥25%)",
              },
            ],
      info: [
        {
          location: "Week Spec",
          message: "Grammar focus: First Declension Nouns",
        },
        {
          location: "Days",
          message: "4 days present and complete",
        },
        {
          location: "Assets",
          message: "Quiz packet and teacher key present",
        },
      ],
    });

    setLoading(false);
  };

  const handleRevalidate = async () => {
    setValidating(true);
    await loadValidation();
    setValidating(false);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-gray-500">Running validation...</p>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="space-y-6">
        <Alert>
          <AlertDescription>
            Validation results not available. Please try again.
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
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-bold text-gray-900">
              Week {weekId} Validation
            </h1>
            {result.is_valid ? (
              <Badge className="bg-green-500">Valid</Badge>
            ) : (
              <Badge className="bg-red-500">Invalid</Badge>
            )}
          </div>
          <p className="mt-2 text-gray-600">{result.summary}</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" asChild>
            <Link href={`/weeks/${weekId}`}>Back to Week</Link>
          </Button>
          <Button onClick={handleRevalidate} disabled={validating}>
            {validating ? "Validating..." : "Re-validate"}
          </Button>
        </div>
      </div>

      {/* Overall Status */}
      <Alert className={result.is_valid ? "border-green-500" : "border-red-500"}>
        <AlertTitle className={result.is_valid ? "text-green-700" : "text-red-700"}>
          {result.is_valid ? "✓ Validation Passed" : "✗ Validation Failed"}
        </AlertTitle>
        <AlertDescription>
          {result.is_valid
            ? "This week meets all validation criteria and is ready for export."
            : `This week has ${result.errors.length} error(s) that must be fixed before export.`}
        </AlertDescription>
      </Alert>

      {/* Errors */}
      {result.errors.length > 0 && (
        <Card className="border-red-200">
          <CardHeader>
            <CardTitle className="text-red-700">
              Errors ({result.errors.length})
            </CardTitle>
            <CardDescription>
              Critical issues that must be resolved
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {result.errors.map((error, i) => (
                <div key={i} className="p-4 bg-red-50 rounded border border-red-200">
                  <div className="flex items-start gap-3">
                    <span className="text-red-600 font-bold">✗</span>
                    <div className="flex-1">
                      <p className="font-medium text-red-900">{error.location}</p>
                      <p className="text-sm text-red-700 mt-1">{error.message}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Warnings */}
      {result.warnings.length > 0 && (
        <Card className="border-yellow-200">
          <CardHeader>
            <CardTitle className="text-yellow-700">
              Warnings ({result.warnings.length})
            </CardTitle>
            <CardDescription>
              Non-critical issues that should be addressed
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {result.warnings.map((warning, i) => (
                <div key={i} className="p-4 bg-yellow-50 rounded border border-yellow-200">
                  <div className="flex items-start gap-3">
                    <span className="text-yellow-600 font-bold">⚠</span>
                    <div className="flex-1">
                      <p className="font-medium text-yellow-900">
                        {warning.location}
                      </p>
                      <p className="text-sm text-yellow-700 mt-1">
                        {warning.message}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Info/Success Items */}
      <Card className="border-blue-200">
        <CardHeader>
          <CardTitle className="text-blue-700">
            Validation Details ({result.info.length})
          </CardTitle>
          <CardDescription>
            Items that passed validation
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {result.info.map((info, i) => (
              <div key={i} className="p-4 bg-blue-50 rounded border border-blue-200">
                <div className="flex items-start gap-3">
                  <span className="text-blue-600 font-bold">ℹ</span>
                  <div className="flex-1">
                    <p className="font-medium text-blue-900">{info.location}</p>
                    <p className="text-sm text-blue-700 mt-1">{info.message}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Validation Rules */}
      <Card>
        <CardHeader>
          <CardTitle>Validation Rules</CardTitle>
          <CardDescription>
            Criteria checked during validation
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="flex items-center gap-2 p-2 bg-gray-50 rounded">
              <span className="text-green-600">✓</span>
              <span className="text-sm">Schema validation (Pydantic models)</span>
            </div>
            <div className="flex items-center gap-2 p-2 bg-gray-50 rounded">
              <span className="text-green-600">✓</span>
              <span className="text-sm">
                All 7 fields present per day (01-07)
              </span>
            </div>
            <div className="flex items-center gap-2 p-2 bg-gray-50 rounded">
              <span className="text-green-600">✓</span>
              <span className="text-sm">
                6 teacher support documents in 06_document_for_sparky/
              </span>
            </div>
            <div className="flex items-center gap-2 p-2 bg-gray-50 rounded">
              <span className="text-green-600">✓</span>
              <span className="text-sm">
                Day 4 includes ≥25% spiral review content
              </span>
            </div>
            <div className="flex items-center gap-2 p-2 bg-gray-50 rounded">
              <span className="text-green-600">✓</span>
              <span className="text-sm">
                Grammar focus consistency across all 4 days
              </span>
            </div>
            <div className="flex items-center gap-2 p-2 bg-gray-50 rounded">
              <span className="text-green-600">✓</span>
              <span className="text-sm">Quiz packet and teacher key present</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Actions */}
      {result.is_valid && (
        <Card>
          <CardHeader>
            <CardTitle>Next Steps</CardTitle>
            <CardDescription>
              This week is ready for use
            </CardDescription>
          </CardHeader>
          <CardContent className="flex gap-4">
            <Button asChild>
              <Link href={`/weeks/${weekId}`}>Edit Week</Link>
            </Button>
            <Button variant="outline" asChild>
              <Link href={`/weeks/${weekId}/export`}>Export to ZIP</Link>
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
