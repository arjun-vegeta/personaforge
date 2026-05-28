"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
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
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  ChevronLeft,
  PlayCircle,
  AlertCircle,
  CheckCircle2,
  DollarSign,
} from "lucide-react";
import { Run, Conversation, getRunDetails } from "@/lib/api";

export default function RunDetailsPage() {
  const params = useParams();
  const runId = params.id as string;
  const [data, setData] = useState<{
    run: Run;
    conversations: Conversation[];
  } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const result = await getRunDetails(runId);
        setData(result);
      } catch (error) {
        console.error("Failed to fetch run details:", error);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, [runId]);

  if (loading)
    return (
      <div className="flex items-center justify-center h-[80vh]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );

  if (!data) return <div>Run not found.</div>;

  const { run, conversations } = data;

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/">
            <Button variant="outline" size="icon">
              <ChevronLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Run Details</h1>
            <p className="text-muted-foreground">
              {run.timestamp} — {run.id.slice(0, 8)}
            </p>
          </div>
        </div>
        <div className="flex gap-4">
          <Badge variant={run.status === "completed" ? "default" : "secondary"}>
            {run.status.toUpperCase()}
          </Badge>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pass Rate</CardTitle>
            <CheckCircle2 className="h-4 w-4 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {run.pass_rate.toFixed(1)}%
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Conversations</CardTitle>
            <PlayCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{run.total_conversations}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Failures</CardTitle>
            <AlertCircle className="h-4 w-4 text-destructive" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-destructive">
              {run.total_failures}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Cost</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${run.cost.toFixed(3)}</div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Conversations</CardTitle>
          <CardDescription>
            Individual test cases and their outcomes.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Persona</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Failures</TableHead>
                <TableHead>Cost</TableHead>
                <TableHead className="text-right">Action</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {conversations.map((conv) => (
                <TableRow key={conv.id}>
                  <TableCell className="font-medium">
                    {conv.persona_id || "Unknown"}
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant={
                        conv.status === "passed" ? "default" : "destructive"
                      }
                    >
                      {conv.status.toUpperCase()}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    {conv.failures && conv.failures.length > 0 ? (
                      <div className="flex gap-1">
                        {conv.failures.map(
                          (f: { category: string }, i: number) => (
                            <Badge
                              key={i}
                              variant="outline"
                              className="text-[10px]"
                            >
                              {f.category}
                            </Badge>
                          ),
                        )}
                      </div>
                    ) : (
                      <span className="text-muted-foreground text-xs">—</span>
                    )}
                  </TableCell>
                  <TableCell className="text-xs">
                    ${(conv.total_cost || 0).toFixed(4)}
                  </TableCell>
                  <TableCell className="text-right">
                    <Link href={`/replay/${conv.id}`}>
                      <Button variant="ghost" size="sm">
                        Replay
                      </Button>
                    </Link>
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
