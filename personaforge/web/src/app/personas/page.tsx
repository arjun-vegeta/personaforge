"use client";

import { useEffect, useState } from "react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { PersonaMetric, getPersonaPerformance } from "@/lib/api";

export default function PersonaPerformancePage() {
  const [data, setData] = useState<PersonaMetric[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const result = await getPersonaPerformance();
        setData(result);
      } catch (error) {
        console.error("Failed to fetch persona performance:", error);
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

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">
          Persona Performance
        </h1>
        <p className="text-muted-foreground">
          Analyze how your agent handles different psychological profiles.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {data.map((persona) => (
          <Card key={persona.name}>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">
                {persona.name}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {persona.pass_rate.toFixed(1)}% Pass Rate
              </div>
              <div className="flex items-center gap-2 mt-1">
                <div className="h-2 flex-1 bg-secondary rounded-full overflow-hidden flex">
                  <div
                    className="bg-primary h-full"
                    style={{ width: `${persona.pass_rate}%` }}
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Pass Rate by Persona</CardTitle>
            <CardDescription>
              Comparison of success rates across profiles.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[400px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data} layout="vertical">
                  <CartesianGrid
                    strokeDasharray="3 3"
                    horizontal={true}
                    vertical={false}
                    stroke="#333"
                  />
                  <XAxis type="number" stroke="#888" domain={[0, 100]} />
                  <YAxis
                    dataKey="name"
                    type="category"
                    stroke="#888"
                    width={120}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#1f1f1f",
                      border: "1px solid #333",
                    }}
                  />
                  <Bar
                    dataKey="pass_rate"
                    fill="hsl(var(--primary))"
                    radius={[0, 4, 4, 0]}
                  >
                    {data.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={
                          entry.pass_rate < 80
                            ? "#ef4444"
                            : "hsl(var(--primary))"
                        }
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Detailed Metrics</CardTitle>
            <CardDescription>Volume and latency by persona.</CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Persona</TableHead>
                  <TableHead>Total Runs</TableHead>
                  <TableHead>Avg. Latency</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.map((persona) => (
                  <TableRow key={persona.name}>
                    <TableCell className="font-medium">
                      {persona.name}
                    </TableCell>
                    <TableCell>{persona.total_runs}</TableCell>
                    <TableCell>{persona.avg_latency.toFixed(2)}s</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
