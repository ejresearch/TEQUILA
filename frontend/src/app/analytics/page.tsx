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

interface UsageStats {
  total_requests: number;
  total_tokens: number;
  total_cost_usd: number;
  by_provider: {
    openai?: {
      requests: number;
      tokens: number;
      cost_usd: number;
    };
    anthropic?: {
      requests: number;
      tokens: number;
      cost_usd: number;
    };
  };
  by_week: Record<
    number,
    {
      requests: number;
      tokens: number;
      cost_usd: number;
    }
  >;
}

export default function AnalyticsPage() {
  const [stats, setStats] = useState<UsageStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Mock data - will be replaced with API call
    setStats({
      total_requests: 142,
      total_tokens: 1248690,
      total_cost_usd: 24.18,
      by_provider: {
        openai: {
          requests: 142,
          tokens: 1248690,
          cost_usd: 24.18,
        },
      },
      by_week: {
        1: { requests: 28, tokens: 245000, cost_usd: 4.75 },
        11: { requests: 26, tokens: 198000, cost_usd: 3.84 },
        12: { requests: 24, tokens: 189000, cost_usd: 3.66 },
        13: { requests: 22, tokens: 201000, cost_usd: 3.89 },
        14: { requests: 21, tokens: 210000, cost_usd: 4.07 },
        15: { requests: 21, tokens: 205690, cost_usd: 3.98 },
      },
    });
    setLoading(false);
  }, []);

  const formatCurrency = (amount: number) =>
    new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
    }).format(amount);

  const formatNumber = (num: number) =>
    new Intl.NumberFormat("en-US").format(num);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-gray-500">Loading analytics...</p>
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="space-y-6">
        <p>No usage data available.</p>
        <Button asChild>
          <Link href="/">Back to Dashboard</Link>
        </Button>
      </div>
    );
  }

  const weekStats = Object.entries(stats.by_week)
    .map(([week, data]) => ({
      week: parseInt(week),
      ...data,
    }))
    .sort((a, b) => b.cost_usd - a.cost_usd);

  const avgCostPerWeek =
    stats.total_cost_usd / Object.keys(stats.by_week).length;
  const avgTokensPerWeek =
    stats.total_tokens / Object.keys(stats.by_week).length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">
            Usage Analytics
          </h1>
          <p className="mt-2 text-gray-600">
            LLM usage statistics and cost tracking
          </p>
        </div>
        <Button variant="outline" asChild>
          <Link href="/">Back to Dashboard</Link>
        </Button>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-gray-600">
              Total Requests
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">
              {formatNumber(stats.total_requests)}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-gray-600">
              Total Tokens
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">
              {formatNumber(stats.total_tokens)}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-gray-600">
              Total Cost
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-blue-600">
              {formatCurrency(stats.total_cost_usd)}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-gray-600">
              Avg Cost/Week
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">
              {formatCurrency(avgCostPerWeek)}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Provider Breakdown */}
      <Card>
        <CardHeader>
          <CardTitle>Usage by Provider</CardTitle>
          <CardDescription>
            Breakdown of LLM usage across providers
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {stats.by_provider.openai && (
              <div className="p-4 border rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-semibold text-lg">OpenAI GPT-4o</h3>
                  <span className="text-2xl font-bold text-blue-600">
                    {formatCurrency(stats.by_provider.openai.cost_usd)}
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-gray-600">Requests</p>
                    <p className="font-semibold">
                      {formatNumber(stats.by_provider.openai.requests)}
                    </p>
                  </div>
                  <div>
                    <p className="text-gray-600">Tokens</p>
                    <p className="font-semibold">
                      {formatNumber(stats.by_provider.openai.tokens)}
                    </p>
                  </div>
                </div>
              </div>
            )}

            {stats.by_provider.anthropic && (
              <div className="p-4 border rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-semibold text-lg">Anthropic Claude</h3>
                  <span className="text-2xl font-bold text-purple-600">
                    {formatCurrency(stats.by_provider.anthropic.cost_usd)}
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-gray-600">Requests</p>
                    <p className="font-semibold">
                      {formatNumber(stats.by_provider.anthropic.requests)}
                    </p>
                  </div>
                  <div>
                    <p className="text-gray-600">Tokens</p>
                    <p className="font-semibold">
                      {formatNumber(stats.by_provider.anthropic.tokens)}
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Per-Week Stats */}
      <Card>
        <CardHeader>
          <CardTitle>Cost by Week</CardTitle>
          <CardDescription>
            Detailed usage breakdown for each generated week
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Week</TableHead>
                <TableHead className="text-right">Requests</TableHead>
                <TableHead className="text-right">Tokens</TableHead>
                <TableHead className="text-right">Cost</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {weekStats.map((week) => (
                <TableRow key={week.week}>
                  <TableCell className="font-medium">
                    <Link
                      href={`/weeks/${week.week}`}
                      className="hover:text-blue-600"
                    >
                      Week {week.week}
                    </Link>
                  </TableCell>
                  <TableCell className="text-right">
                    {formatNumber(week.requests)}
                  </TableCell>
                  <TableCell className="text-right">
                    {formatNumber(week.tokens)}
                  </TableCell>
                  <TableCell className="text-right font-semibold">
                    {formatCurrency(week.cost_usd)}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Cost Projections */}
      <Card>
        <CardHeader>
          <CardTitle>Cost Projections</CardTitle>
          <CardDescription>
            Estimated costs for generating remaining weeks
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex justify-between items-center p-4 bg-gray-50 rounded">
              <div>
                <p className="font-medium">Cost for 10 more weeks</p>
                <p className="text-sm text-gray-600">
                  At {formatCurrency(avgCostPerWeek)}/week average
                </p>
              </div>
              <p className="text-2xl font-bold">
                {formatCurrency(avgCostPerWeek * 10)}
              </p>
            </div>

            <div className="flex justify-between items-center p-4 bg-gray-50 rounded">
              <div>
                <p className="font-medium">Complete curriculum (35 weeks)</p>
                <p className="text-sm text-gray-600">
                  Estimated total cost
                </p>
              </div>
              <p className="text-2xl font-bold">
                {formatCurrency(avgCostPerWeek * 35)}
              </p>
            </div>

            <div className="flex justify-between items-center p-4 bg-blue-50 rounded border-2 border-blue-200">
              <div>
                <p className="font-medium">Remaining weeks (29)</p>
                <p className="text-sm text-gray-600">
                  Cost to complete curriculum
                </p>
              </div>
              <p className="text-2xl font-bold text-blue-600">
                {formatCurrency(avgCostPerWeek * 29)}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Efficiency Metrics */}
      <Card>
        <CardHeader>
          <CardTitle>Efficiency Metrics</CardTitle>
          <CardDescription>
            Average metrics per generated week
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <div className="p-4 bg-gray-50 rounded">
              <p className="text-sm text-gray-600 mb-1">Avg Requests/Week</p>
              <p className="text-2xl font-bold">
                {formatNumber(
                  Math.round(
                    stats.total_requests / Object.keys(stats.by_week).length
                  )
                )}
              </p>
            </div>
            <div className="p-4 bg-gray-50 rounded">
              <p className="text-sm text-gray-600 mb-1">Avg Tokens/Week</p>
              <p className="text-2xl font-bold">
                {formatNumber(Math.round(avgTokensPerWeek))}
              </p>
            </div>
            <div className="p-4 bg-gray-50 rounded">
              <p className="text-sm text-gray-600 mb-1">Avg Cost/Request</p>
              <p className="text-2xl font-bold">
                {formatCurrency(stats.total_cost_usd / stats.total_requests)}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
