"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { Card, CardContent } from "@/components/ui/card";
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
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Search, Eye } from "lucide-react";
import { getFailures } from "@/lib/api";

interface FailureInstance {
  id: string;
  type: string;
  severity: string;
  persona: string;
  scenario: string;
  evidence: string;
  timestamp: string;
}

export default function FailureExplorerPage() {
  const [filter, setFilter] = useState("all");
  const [failures, setFailures] = useState<FailureInstance[]>([]);
  const [search, setSearch] = useState("");

  useEffect(() => {
    async function fetchData() {
      try {
        const result = await getFailures(filter === "all" ? undefined : filter);
        setFailures(result as unknown as FailureInstance[]);
      } catch (error) {
        console.error("Failed to fetch failures:", error);
      }
    }
    fetchData();
  }, [filter]);

  const filteredFailures = failures.filter(
    (f) =>
      f.persona.toLowerCase().includes(search.toLowerCase()) ||
      f.evidence.toLowerCase().includes(search.toLowerCase()),
  );

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Failure Explorer</h1>
        <p className="text-muted-foreground">
          Investigate specific failure instances to improve agent prompts.
        </p>
      </div>

      <div className="flex items-center gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            type="search"
            placeholder="Search evidence or persona..."
            className="pl-8 w-full md:w-[300px]"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <Select
          defaultValue="all"
          onValueChange={(val) => setFilter(val || "all")}
        >
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Failure Type" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Types</SelectItem>
            <SelectItem value="hallucination">Hallucination</SelectItem>
            <SelectItem value="escalation">Escalation</SelectItem>
            <SelectItem value="looping">Looping</SelectItem>
            <SelectItem value="policy violation">Policy Violation</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Type</TableHead>
                <TableHead>Severity</TableHead>
                <TableHead>Persona / Scenario</TableHead>
                <TableHead className="w-[400px]">Evidence Summary</TableHead>
                <TableHead className="text-right">Action</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredFailures.map((failure, i) => (
                <TableRow key={`${failure.id}-${i}`}>
                  <TableCell>
                    <div className="font-medium uppercase text-[10px]">
                      {failure.type}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {new Date(failure.timestamp).toLocaleString()}
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant={
                        failure.severity === "critical"
                          ? "destructive"
                          : failure.severity === "high"
                            ? "destructive"
                            : "secondary"
                      }
                    >
                      {failure.severity.toUpperCase()}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <div className="text-sm font-medium">{failure.persona}</div>
                    <div className="text-xs text-muted-foreground">
                      {failure.scenario}
                    </div>
                  </TableCell>
                  <TableCell>
                    <p className="text-sm italic text-muted-foreground line-clamp-2">
                      &quot;{failure.evidence}&quot;
                    </p>
                  </TableCell>
                  <TableCell className="text-right">
                    <Link href={`/replay/${failure.id}`}>
                      <Button variant="ghost" size="icon">
                        <Eye className="h-4 w-4" />
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
