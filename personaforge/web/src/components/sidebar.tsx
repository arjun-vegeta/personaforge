import Link from "next/link";
import {
  LayoutDashboard,
  Activity,
  Users,
  AlertTriangle,
  Settings,
  ShieldCheck,
} from "lucide-react";
import { cn } from "@/lib/utils";

const navigation = [
  { name: "Overview", href: "/", icon: LayoutDashboard },
  { name: "Agent Health", href: "/health", icon: Activity },
  { name: "Persona Performance", href: "/personas", icon: Users },
  { name: "Failure Explorer", href: "/failures", icon: AlertTriangle },
];

export function Sidebar({ className }: { className?: string }) {
  return (
    <div className={cn("pb-12 border-r bg-card h-screen", className)}>
      <div className="space-y-4 py-4">
        <div className="px-6 py-2">
          <h2 className="mb-2 px-2 text-xl font-bold tracking-tight flex items-center gap-2">
            <ShieldCheck className="h-6 w-6 text-primary" />
            PersonaForge
          </h2>
        </div>
        <div className="px-3 py-2">
          <div className="space-y-1">
            {navigation.map((item) => (
              <Link
                key={item.name}
                href={item.href}
                className="group flex items-center rounded-md px-3 py-2 text-sm font-medium hover:bg-accent hover:text-accent-foreground"
              >
                <item.icon className="mr-3 h-4 w-4" />
                {item.name}
              </Link>
            ))}
          </div>
        </div>
      </div>
      <div className="absolute bottom-4 px-3 w-full">
        <Link
          href="/settings"
          className="group flex items-center rounded-md px-3 py-2 text-sm font-medium hover:bg-accent hover:text-accent-foreground"
        >
          <Settings className="mr-3 h-4 w-4" />
          Settings
        </Link>
      </div>
    </div>
  );
}
