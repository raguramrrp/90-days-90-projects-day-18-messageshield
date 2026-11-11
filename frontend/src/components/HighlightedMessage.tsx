import React from "react";
import type { HighlightedSpan } from "../types/messageshield";

interface HighlightedMessageProps {
  message: string;
  spans: HighlightedSpan[];
}

export const HighlightedMessage: React.FC<HighlightedMessageProps> = ({
  message,
  spans,
}) => {
  if (!spans || spans.length === 0) {
    return (
      <p className="whitespace-pre-wrap break-words text-[13px] leading-relaxed text-zinc-800">
        {message}
      </p>
    );
  }

  const ordered = [...spans].sort((a, b) => a.start - b.start);
  const segments: React.ReactNode[] = [];
  let cursor = 0;

  ordered.forEach((span, idx) => {
    if (span.start < cursor || span.start >= message.length) return;
    if (span.start > cursor) {
      segments.push(
        <span key={`plain-${idx}`}>{message.slice(cursor, span.start)}</span>
      );
    }

    const highlightClass =
      span.severity === "critical" || span.severity === "high"
        ? "bg-red-100/90 text-red-950 underline decoration-red-500 decoration-2 underline-offset-2"
        : span.severity === "medium"
          ? "bg-amber-100/90 text-amber-950 underline decoration-amber-500 decoration-2 underline-offset-2"
          : "bg-zinc-200/80 text-zinc-900 underline decoration-zinc-500 underline-offset-2";

    const safeEnd = Math.min(span.end, message.length);
    segments.push(
      <mark
        key={`hl-${idx}`}
        title={span.reason}
        className={`rounded-xs px-0.5 font-medium ${highlightClass}`}
      >
        {message.slice(span.start, safeEnd)}
      </mark>
    );
    cursor = safeEnd;
  });

  if (cursor < message.length) {
    segments.push(<span key="tail">{message.slice(cursor)}</span>);
  }

  return (
    <p className="whitespace-pre-wrap break-words text-[13px] leading-relaxed text-zinc-800">
      {segments}
    </p>
  );
};
