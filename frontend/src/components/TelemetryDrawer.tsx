"use client";

import React, { useState } from "react";
import { Activity, ChevronDown, ChevronUp, Clock, ShieldCheck, Zap } from "lucide-react";
import { TelemetryData } from "../lib/types";

interface TelemetryDrawerProps {
  telemetry: TelemetryData | null;
  onRefresh: () => void;
}

export function TelemetryDrawer({ telemetry, onRefresh }: TelemetryDrawerProps) {
  const [isOpen, setIsOpen] = useState(false);

  const spans = telemetry?.recent_spans || [];

  return (
    <div className="bg-white border border-slate-200 rounded-2xl overflow-hidden shadow-xs transition-all">
      {/* Clickable Header Bar */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-5 py-3.5 flex items-center justify-between text-xs text-slate-700 hover:text-slate-900 hover:bg-slate-50 transition-colors"
      >
        <div className="flex items-center gap-2.5">
          <Activity className="h-4 w-4 text-rose-600" />
          <span className="font-bold text-slate-900 text-sm">Sentry Agent Tracing & Pipeline Observability</span>
          <span className="font-mono text-xs text-slate-600 bg-slate-100 px-2.5 py-0.5 rounded-lg border border-slate-200 font-semibold">
            {spans.length} recent spans
          </span>
        </div>

        <div className="flex items-center gap-2.5 text-slate-500">
          <span className="text-xs font-mono hidden sm:inline">
            {spans[0] ? `${spans[0].op} (${spans[0].duration_ms}ms)` : "No active spans"}
          </span>
          {isOpen ? <ChevronUp className="h-4 w-4 text-slate-700" /> : <ChevronDown className="h-4 w-4 text-slate-700" />}
        </div>
      </button>

      {/* Expanded Details */}
      {isOpen && (
        <div className="p-5 border-t border-slate-200 flex flex-col gap-3.5 bg-slate-50">
          <div className="flex items-center justify-between text-xs text-slate-600 font-medium">
            <span>Distributed Spans Log</span>
            <button
              type="button"
              onClick={onRefresh}
              className="text-xs text-indigo-600 hover:text-indigo-800 font-bold hover:underline"
            >
              Refresh Spans
            </button>
          </div>

          {spans.length > 0 ? (
            <div className="flex flex-col gap-2 max-h-60 overflow-y-auto pr-1">
              {spans.map((span, idx) => (
                <div
                  key={idx}
                  className="flex items-center justify-between px-4 py-2.5 rounded-xl bg-white border border-slate-200 text-xs shadow-2xs"
                >
                  <div className="flex items-center gap-2.5">
                    <span
                      className={`w-2.5 h-2.5 rounded-full ${
                        span.status === "ok" ? "bg-emerald-500" : "bg-rose-500"
                      }`}
                    />
                    <span className="font-mono font-bold text-slate-900">{span.op}</span>
                    <span className="text-xs text-slate-500 truncate max-w-[200px] sm:max-w-md font-medium">
                      {span.description}
                    </span>
                  </div>

                  <div className="flex items-center gap-4 font-mono text-xs">
                    <span className="text-slate-400">{new Date(span.timestamp * 1000).toLocaleTimeString()}</span>
                    <span className="text-indigo-700 font-bold bg-indigo-50 px-2 py-0.5 rounded border border-indigo-200">
                      {span.duration_ms} ms
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-6 text-center text-xs text-slate-500 font-medium">
              Run an image crop, biodata extraction, or queue estimate to view live distributed spans.
            </div>
          )}
        </div>
      )}
    </div>
  );
}
