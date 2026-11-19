"use client";

import React from "react";
import { Printer } from "lucide-react";
import { TelemetryData } from "../lib/types";

interface HeaderProps {
  telemetry: TelemetryData | null;
}

export function Header({ telemetry }: HeaderProps) {
  return (
    <header className="border-b border-slate-200 bg-white/95 backdrop-blur-md sticky top-0 z-50 shadow-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4 flex items-center justify-between gap-4">
        {/* Brand */}
        <div className="flex items-center gap-3.5">
          <div className="h-10 w-10 rounded-xl bg-indigo-600 flex items-center justify-center shadow-md shadow-indigo-600/20 text-white shrink-0">
            <Printer className="h-5 w-5 stroke-[2.2]" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl sm:text-2xl font-black tracking-tight text-slate-900 flex items-center gap-1">
                Xerox<span className="text-indigo-600">AI</span>
                <span className="text-xs px-2 py-0.5 rounded-md bg-indigo-50 text-indigo-700 border border-indigo-200 font-mono font-bold">
                  2.0
                </span>
              </h1>
              <span className="px-2.5 py-0.5 text-xs font-semibold tracking-wide uppercase bg-slate-100 text-slate-700 border border-slate-200 rounded-full hidden sm:inline-block">
                Counter Workspace
              </span>
            </div>
            <p className="text-xs text-slate-500 font-medium">
              Intelligent Print Shop & Document Automation System
            </p>
          </div>
        </div>

        {/* Minimal System Status */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-50 border border-emerald-200 text-xs font-semibold text-emerald-800 shadow-2xs">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          <span>System Ready</span>
        </div>
      </div>
    </header>
  );
}
