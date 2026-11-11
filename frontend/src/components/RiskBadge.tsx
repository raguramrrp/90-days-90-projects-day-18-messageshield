import React from "react";
import { AlertOctagon, AlertTriangle, CheckCircle2, HelpCircle, Tag } from "lucide-react";
import type { RiskLevel, ThreatCategory } from "../types/messageshield";

export function getRiskColors(
  risk: RiskLevel | string,
  category?: ThreatCategory | string
) {
  if (category === "Promotional") {
    return {
      bg: "bg-white",
      accentBorder: "border-l-4 border-l-amber-500",
      border: "border-zinc-200",
      text: "text-amber-800",
      pill: "bg-amber-50 text-amber-800 border-amber-200",
      Icon: Tag,
    };
  }
  switch (risk) {
    case "Critical":
      return {
        bg: "bg-white",
        accentBorder: "border-l-4 border-l-red-600",
        border: "border-zinc-200",
        text: "text-red-700",
        pill: "bg-red-50 text-red-700 border-red-200",
        Icon: AlertOctagon,
      };
    case "High":
      return {
        bg: "bg-white",
        accentBorder: "border-l-4 border-l-orange-600",
        border: "border-zinc-200",
        text: "text-orange-700",
        pill: "bg-orange-50 text-orange-800 border-orange-200",
        Icon: AlertTriangle,
      };
    case "Medium":
    case "Needs Review":
      return {
        bg: "bg-white",
        accentBorder: "border-l-4 border-l-amber-500",
        border: "border-zinc-200",
        text: "text-amber-800",
        pill: "bg-amber-50 text-amber-800 border-amber-200",
        Icon: HelpCircle,
      };
    default:
      return {
        bg: "bg-white",
        accentBorder: "border-l-4 border-l-emerald-600",
        border: "border-zinc-200",
        text: "text-emerald-800",
        pill: "bg-emerald-50 text-emerald-800 border-emerald-200",
        Icon: CheckCircle2,
      };
  }
}

export const RiskBadge: React.FC<{
  risk: RiskLevel | string;
  category?: ThreatCategory | string;
  compact?: boolean;
}> = ({ risk, category, compact = false }) => {
  const style = getRiskColors(risk, category);
  const Icon = style.Icon;
  return (
    <span
      className={`inline-flex items-center gap-1 rounded border font-medium ${style.pill} ${
        compact ? "px-1.5 py-0.5 text-[10px]" : "px-2 py-0.5 text-[11px]"
      }`}
    >
      <Icon className={compact ? "h-3 w-3" : "h-3.5 w-3.5"} />
      <span>{risk === "Needs Review" ? "Needs Review" : `${risk} Risk`}</span>
    </span>
  );
};
