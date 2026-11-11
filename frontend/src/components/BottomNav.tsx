import React from "react";
import { BarChart3, Clock, Home, ScanSearch, Settings } from "lucide-react";
import type { NavTab } from "../types/messageshield";

interface BottomNavProps {
  activeTab: NavTab;
  onSelectTab: (tab: NavTab) => void;
}

const NAV_ITEMS: {
  id: NavTab;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
}[] = [
  { id: "home", label: "Home", icon: Home },
  { id: "scan", label: "Scan", icon: ScanSearch },
  { id: "history", label: "History", icon: Clock },
  { id: "insights", label: "Insights", icon: BarChart3 },
  { id: "settings", label: "Settings", icon: Settings },
];

export const BottomNav: React.FC<BottomNavProps> = ({ activeTab, onSelectTab }) => {
  return (
    <nav
      aria-label="Primary mobile navigation"
      className="grid shrink-0 grid-cols-5 border-t border-zinc-200 bg-white px-1 pb-1.5 pt-1.5"
    >
      {NAV_ITEMS.map(({ id, label, icon: Icon }) => {
        const isActive = activeTab === id;
        return (
          <button
            key={id}
            type="button"
            onClick={() => onSelectTab(id)}
            data-testid={`nav-${id}`}
            aria-current={isActive ? "page" : undefined}
            className={`flex flex-col items-center justify-center gap-0.5 py-1 transition ${
              isActive
                ? "text-zinc-900"
                : "text-zinc-400 hover:text-zinc-700"
            }`}
          >
            <Icon
              className={`h-[19px] w-[19px] ${
                isActive ? "stroke-[2.2]" : "stroke-[1.75]"
              }`}
            />
            <span
              className={`text-[10px] leading-tight ${
                isActive ? "font-semibold text-zinc-900" : "font-medium"
              }`}
            >
              {label}
            </span>
          </button>
        );
      })}
    </nav>
  );
};
