"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import {
  AlertTriangle,
  Clock,
  DollarSign,
  Info,
  User,
  Bot,
  ChevronLeft,
} from "lucide-react";
import { Conversation, getConversation } from "@/lib/api";

export default function ConversationReplayPage() {
  const params = useParams();
  const router = useRouter();
  const conversationId = params.id as string;
  const [data, setData] = useState<Conversation | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const result = await getConversation(conversationId);
        setData(result);
      } catch (error) {
        console.error("Failed to fetch conversation:", error);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, [conversationId]);

  if (loading)
    return (
      <div className="flex items-center justify-center h-[80vh]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );

  if (!data) return <div>Conversation not found.</div>;

  const failures = data.evaluation?.failures || [];

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="outline" size="icon" onClick={() => router.back()}>
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <div>
            <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
              Conversation Replay
              <Badge
                variant={data.status === "passed" ? "default" : "destructive"}
                className="ml-2"
              >
                {data.status.toUpperCase()}
              </Badge>
            </h1>
            <p className="text-muted-foreground">
              {data.persona_name || "Unknown"} —{" "}
              {data.scenario_name || "Test Case"}
            </p>
          </div>
        </div>
        <div className="flex gap-4">
          <div className="flex items-center gap-2 px-3 py-1 bg-card border rounded-md">
            <DollarSign className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm font-medium">
              ${(data.cost || 0).toFixed(4)}
            </span>
          </div>
          <div className="flex items-center gap-2 px-3 py-1 bg-card border rounded-md">
            <Clock className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm font-medium">{data.latency || 0}s</span>
          </div>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-4">
          <Card className="min-h-[600px] flex flex-col">
            <CardHeader className="border-b bg-muted/30">
              <CardTitle className="text-sm flex items-center gap-2">
                <Info className="h-4 w-4" />
                Transcript
              </CardTitle>
            </CardHeader>
            <CardContent className="flex-1 overflow-y-auto p-6 space-y-6">
              {(data.turns || []).map((turn, i) => {
                const turnFailures = failures.filter(
                  (f) =>
                    f.turn_index === i ||
                    (f.evidence && f.evidence.includes(`Turn ${i + 1}`)),
                );
                const hasFailure = turnFailures.length > 0;

                return (
                  <div
                    key={i}
                    className={cn(
                      "flex flex-col gap-2 max-w-[80%]",
                      turn.role === "agent"
                        ? "ml-auto items-end"
                        : "items-start",
                    )}
                  >
                    <div className="flex items-center gap-2">
                      {turn.role === "customer" && (
                        <User className="h-3 w-3 text-muted-foreground" />
                      )}
                      <span className="text-[10px] uppercase font-bold tracking-wider text-muted-foreground">
                        {turn.role}
                      </span>
                      {turn.role === "agent" && (
                        <Bot className="h-3 w-3 text-muted-foreground" />
                      )}
                    </div>
                    <div
                      className={cn(
                        "rounded-2xl px-4 py-2 text-sm",
                        turn.role === "agent"
                          ? hasFailure
                            ? "bg-destructive/20 border border-destructive/50 text-foreground"
                            : "bg-primary text-primary-foreground"
                          : "bg-muted text-foreground",
                      )}
                    >
                      {turn.content}
                    </div>
                    <span className="text-[10px] text-muted-foreground">
                      {new Date(turn.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                );
              })}
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6">
          <Card
            className={cn(
              data.status === "failed"
                ? "border-destructive/50"
                : "border-primary/50",
            )}
          >
            <CardHeader
              className={cn(
                data.status === "failed"
                  ? "bg-destructive/10"
                  : "bg-primary/10",
              )}
            >
              <CardTitle
                className={cn(
                  "text-sm flex items-center gap-2",
                  data.status === "failed"
                    ? "text-destructive"
                    : "text-primary",
                )}
              >
                <AlertTriangle className="h-4 w-4" />
                Evaluation Result
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-4 space-y-4">
              <div>
                <div className="text-sm font-bold mb-1">Status</div>
                <div
                  className={cn(
                    "text-xl font-bold uppercase",
                    data.status === "failed"
                      ? "text-destructive"
                      : "text-primary",
                  )}
                >
                  {data.status}
                </div>
              </div>
              {data.evaluation?.reasoning && (
                <div>
                  <div className="text-sm font-bold mb-1">Reasoning</div>
                  <p className="text-xs text-muted-foreground leading-relaxed">
                    {data.evaluation.reasoning}
                  </p>
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-sm">
                Detected Failures ({failures.length})
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {failures.length > 0 ? (
                failures.map((failure, i) => (
                  <div
                    key={i}
                    className="p-3 rounded-md bg-muted/50 border space-y-2"
                  >
                    <div className="flex items-center justify-between">
                      <Badge variant="outline" className="text-[10px]">
                        {failure.category}
                      </Badge>
                      <Badge
                        variant={
                          failure.severity === "critical"
                            ? "destructive"
                            : "secondary"
                        }
                        className="text-[10px]"
                      >
                        {failure.severity}
                      </Badge>
                    </div>
                    {failure.turn_index !== undefined && (
                      <p className="text-xs font-medium">
                        Turn #{failure.turn_index + 1}
                      </p>
                    )}
                    <p className="text-[11px] text-muted-foreground italic">
                      &quot;{failure.evidence}&quot;
                    </p>
                  </div>
                ))
              ) : (
                <div className="text-xs text-muted-foreground text-center py-4">
                  No failures detected.
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
