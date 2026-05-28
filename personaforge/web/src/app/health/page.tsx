"use client";

import { useState, useEffect } from "react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { cn } from "@/lib/utils";
import { getAgentHealth } from "@/lib/api";

interface HealthMetric {
  version: string;
  completion_rate: number;
  hallucination_rate: number;
  escalation_rate: number;
  avg_latency: number;
}

export default function AgentHealthPage() {
  const [data, setData] = useState<HealthMetric[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const result = await getAgentHealth();
        setData(result as HealthMetric[]);
      } catch (error) {
        console.error("Failed to fetch agent health:", error);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  if (loading)
    return (
      <div className="flex items-center justify-center h-[80vh]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );

  const latest = data[data.length - 1] || {};
  const previous = data[data.length - 2] || {};

  const getDiff = (curr: number, prev: number) => {
    if (prev === undefined) return null;
    const diff = curr - prev;
    return diff > 0 ? `+${diff.toFixed(1)}%` : `${diff.toFixed(1)}%`;
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Agent Health</h1>
        <p className="text-muted-foreground">
          Monitor core reliability metrics across agent versions.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">
              Avg. Completion Rate
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {latest.completion_rate?.toFixed(1)}%
            </div>
            {previous.completion_rate && (
              <p
                className={cn(
                  "text-xs",
                  latest.completion_rate >= previous.completion_rate
                    ? "text-primary"
                    : "text-destructive",
                )}
              >
                {getDiff(latest.completion_rate, previous.completion_rate)} from
                last version
              </p>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">
              Hallucination Rate
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {latest.hallucination_rate?.toFixed(1)}%
            </div>
            <p className="text-xs text-muted-foreground">Target: &lt;5%</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">
              Escalation Rate
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {latest.escalation_rate?.toFixed(1)}%
            </div>
            <p className="text-xs text-muted-foreground">Target: &gt;90%</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Avg. Latency</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {latest.avg_latency?.toFixed(2)}s
            </div>
            <p className="text-xs text-muted-foreground">Target: &lt;2s</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Reliability Trends</CardTitle>
            <CardDescription>
              Completion vs Hallucination vs Escalation
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[400px]">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={data}>
                  <CartesianGrid
                    strokeDasharray="3 3"
                    vertical={false}
                    stroke="#333"
                  />
                  <XAxis dataKey="version" stroke="#888" />
                  <YAxis stroke="#888" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#1f1f1f",
                      border: "1px solid #333",
                    }}
                  />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="completion_rate"
                    stroke="#10b981"
                    name="Completion %"
                    strokeWidth={2}
                  />
                  <Line
                    type="monotone"
                    dataKey="hallucination_rate"
                    stroke="#ef4444"
                    name="Hallucinations %"
                    strokeWidth={2}
                  />
                  <Line
                    type="monotone"
                    dataKey="escalation_rate"
                    stroke="#f59e0b"
                    name="Escalations %"
                    strokeWidth={2}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Latency Trend</CardTitle>
            <CardDescription>Response time in seconds</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[400px]">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={data}>
                  <CartesianGrid
                    strokeDasharray="3 3"
                    vertical={false}
                    stroke="#333"
                  />
                  <XAxis dataKey="version" stroke="#888" />
                  <YAxis stroke="#888" unit="s" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#1f1f1f",
                      border: "1px solid #333",
                    }}
                  />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="avg_latency"
                    stroke="#3b82f6"
                    name="Latency (s)"
                    strokeWidth={2}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
