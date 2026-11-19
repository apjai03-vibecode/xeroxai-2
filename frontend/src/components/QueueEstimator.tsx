"use client";

import React, { useState, useEffect } from "react";
import {
  Clock,
  Layers,
  Palette,
  Users,
  IndianRupee,
  Cpu,
  Sparkles,
  ShieldAlert,
  ArrowRight,
} from "lucide-react";
import { QueueEstimateResponse } from "../lib/types";
import { estimateJobApi } from "../lib/api";

export function QueueEstimator({ onProcessed }: { onProcessed?: () => void }) {
  const [pageCount, setPageCount] = useState<number>(15);
  const [isColor, setIsColor] = useState<boolean>(false);
  const [needsLamination, setNeedsLamination] = useState<boolean>(false);
  const [currentQueue, setCurrentQueue] = useState<number>(1);
  const [estimate, setEstimate] = useState<QueueEstimateResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  useEffect(() => {
    let isCancelled = false;
    const fetchEstimate = async () => {
      setIsLoading(true);
      try {
        const res = await estimateJobApi({
          page_count: pageCount,
          is_color: isColor,
          needs_lamination: needsLamination,
          current_queue_customers: currentQueue,
        });
        if (!isCancelled) {
          setEstimate(res);
          if (onProcessed) onProcessed();
        }
      } catch {
        // Queue estimation fallback handled by loading/empty state
      } finally {
        if (!isCancelled) setIsLoading(false);
      }
    };

    const timer = setTimeout(fetchEstimate, 250);
    return () => {
      isCancelled = true;
      clearTimeout(timer);
    };
  }, [pageCount, isColor, needsLamination, currentQueue]);

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-6 sm:p-8 shadow-sm flex flex-col gap-6">
      {/* Card Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div className="flex items-center gap-3.5">
          <div className="p-3 rounded-xl bg-purple-50 text-purple-600 border border-purple-100 shadow-2xs">
            <Clock className="h-6 w-6 stroke-[2.2]" />
          </div>
          <div>
            <div className="flex items-center gap-2.5">
              <h2 className="text-xl sm:text-2xl font-black text-slate-900 tracking-tight">
                Queue & Job Cost Estimator
              </h2>
              <span className="px-2.5 py-1 text-xs font-mono font-bold bg-purple-50 text-purple-700 border border-purple-200 rounded-lg">
                Prior Labs TabPFN-3.5
              </span>
            </div>
            <p className="text-sm text-slate-500 font-medium mt-0.5">
              Wait-time prediction by Prior Labs TabPFN tabular foundation model.
            </p>
          </div>
        </div>

        {/* TabPFN Engine Tag */}
        <div className="flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-slate-50 border border-slate-200 text-xs font-mono font-bold text-purple-700 shadow-2xs">
          <Cpu className="h-4 w-4 text-purple-600" />
          <span>TabPFN-3.5 Regressor</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Controls Column (7 cols) */}
        <div className="lg:col-span-7 flex flex-col gap-4">
          {/* Page Count Slider & Input */}
          <div className="bg-slate-50 p-5 rounded-2xl border border-slate-200 flex flex-col gap-3">
            <div className="flex items-center justify-between">
              <label className="text-xs font-bold text-slate-700 flex items-center gap-2 uppercase tracking-wide">
                <Layers className="h-4 w-4 text-indigo-600" />
                <span>Page Count</span>
              </label>
              <div className="flex items-center gap-2">
                <input
                  type="number"
                  min={1}
                  max={500}
                  value={pageCount}
                  onChange={(e) => setPageCount(Math.max(1, parseInt(e.target.value) || 1))}
                  className="w-24 bg-white border border-slate-300 focus:border-indigo-500 rounded-xl px-3 py-1.5 text-center font-mono text-base text-slate-900 font-bold outline-none shadow-2xs"
                />
                <span className="text-sm text-slate-600 font-semibold">pages</span>
              </div>
            </div>

            <input
              type="range"
              min={1}
              max={100}
              value={pageCount}
              onChange={(e) => setPageCount(parseInt(e.target.value))}
              className="w-full h-2.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-indigo-600"
            />

            <div className="flex justify-between text-xs text-slate-400 font-mono font-medium">
              <span>1 page</span>
              <span>25</span>
              <span>50</span>
              <span>100+ pages</span>
            </div>
          </div>

          {/* Toggle Chips: Color & Lamination */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Color Mode Toggle */}
            <button
              type="button"
              onClick={() => setIsColor(!isColor)}
              className={`p-4 rounded-2xl border text-left transition-all flex items-center justify-between ${
                isColor
                  ? "bg-purple-50/90 border-purple-400 text-slate-900 ring-2 ring-purple-400/20 shadow-xs"
                  : "bg-slate-50 border-slate-200 text-slate-700 hover:border-slate-300"
              }`}
            >
              <div className="flex items-center gap-3">
                <Palette className={`h-5 w-5 ${isColor ? "text-purple-600" : "text-slate-400"}`} />
                <div>
                  <div className="text-sm font-bold text-slate-900">Full Color Mode</div>
                  <div className="text-xs text-slate-500 font-mono mt-0.5">
                    {isColor ? "₹10 / page" : "B&W (₹2 / page)"}
                  </div>
                </div>
              </div>
              <div
                className={`w-5 h-5 rounded-full border flex items-center justify-center ${
                  isColor ? "border-purple-600 bg-purple-600" : "border-slate-300 bg-white"
                }`}
              >
                {isColor && <div className="w-2 h-2 bg-white rounded-full" />}
              </div>
            </button>

            {/* Lamination Toggle */}
            <button
              type="button"
              onClick={() => setNeedsLamination(!needsLamination)}
              className={`p-4 rounded-2xl border text-left transition-all flex items-center justify-between ${
                needsLamination
                  ? "bg-indigo-50/90 border-indigo-400 text-slate-900 ring-2 ring-indigo-400/20 shadow-xs"
                  : "bg-slate-50 border-slate-200 text-slate-700 hover:border-slate-300"
              }`}
            >
              <div className="flex items-center gap-3">
                <Sparkles
                  className={`h-5 w-5 ${needsLamination ? "text-indigo-600" : "text-slate-400"}`}
                />
                <div>
                  <div className="text-sm font-bold text-slate-900">Thermal Lamination</div>
                  <div className="text-xs text-slate-500 font-mono mt-0.5">+₹20 finishing</div>
                </div>
              </div>
              <div
                className={`w-5 h-5 rounded-full border flex items-center justify-center ${
                  needsLamination ? "border-indigo-600 bg-indigo-600" : "border-slate-300 bg-white"
                }`}
              >
                {needsLamination && <div className="w-2 h-2 bg-white rounded-full" />}
              </div>
            </button>
          </div>

          {/* Current Queue Stepper */}
          <div className="bg-slate-50 p-4 rounded-2xl border border-slate-200 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Users className="h-5 w-5 text-slate-500" />
              <div>
                <div className="text-sm font-bold text-slate-900">Customers Ahead in Queue</div>
                <div className="text-xs text-slate-500">
                  Affects rush queue buffer and TabPFN turnaround delay
                </div>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => setCurrentQueue(Math.max(0, currentQueue - 1))}
                className="w-9 h-9 rounded-xl bg-white hover:bg-slate-100 text-slate-800 font-bold flex items-center justify-center text-sm border border-slate-300 shadow-2xs transition-colors"
              >
                -
              </button>
              <span className="w-9 text-center font-mono font-black text-slate-900 text-base">
                {currentQueue}
              </span>
              <button
                type="button"
                onClick={() => setCurrentQueue(currentQueue + 1)}
                className="w-9 h-9 rounded-xl bg-white hover:bg-slate-100 text-slate-800 font-bold flex items-center justify-center text-sm border border-slate-300 shadow-2xs transition-colors"
              >
                +
              </button>
            </div>
          </div>
        </div>

        {/* Right Output Column: Readout Cards (5 cols) */}
        <div className="lg:col-span-5 flex flex-col gap-4">
          {/* Predicted Turnaround Big Card */}
          <div className="bg-gradient-to-br from-purple-50 via-indigo-50/50 to-slate-50 p-6 rounded-2xl border border-purple-200/70 shadow-xs flex flex-col justify-between">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-purple-900 uppercase tracking-wide flex items-center gap-2">
                <Clock className="h-4 w-4 text-purple-600" />
                <span>Estimated Wait Time</span>
              </span>
              {isLoading && <span className="text-xs font-mono font-semibold text-purple-600 animate-pulse">Computing...</span>}
            </div>

            <div className="my-4 flex items-baseline gap-2.5">
              <span className="text-4xl sm:text-5xl font-black text-slate-900 tracking-tight font-mono">
                {estimate ? `~${estimate.estimated_wait_minutes}` : "..."}
              </span>
              <span className="text-base font-bold text-purple-700">minutes</span>
            </div>

            <p className="text-xs text-slate-600 leading-relaxed font-medium">
              Calculated across small-sample queue history with spooling & handling factors.
            </p>
          </div>

          {/* Fair Pricing Breakdown Card */}
          <div className="bg-slate-50 p-6 rounded-2xl border border-slate-200 flex flex-col gap-3.5">
            <span className="text-xs font-bold text-slate-700 uppercase tracking-wide flex items-center justify-between">
              <span>Recommended Counter Charge</span>
              <span className="text-emerald-700 text-lg font-black font-mono">
                ₹{estimate ? estimate.price_breakdown.total_fee.toFixed(2) : "0.00"}
              </span>
            </span>

            {/* Breakdown rows */}
            <div className="flex flex-col gap-2 pt-3 border-t border-slate-200 text-xs">
              <div className="flex justify-between text-slate-600 font-medium">
                <span>
                  Printing ({pageCount} {isColor ? "Color" : "B&W"} pages)
                </span>
                <span className="font-mono text-slate-900 font-semibold">
                  ₹{estimate ? estimate.price_breakdown.printing_fee.toFixed(2) : "0.00"}
                </span>
              </div>

              {needsLamination && (
                <div className="flex justify-between text-slate-600 font-medium">
                  <span>Thermal Lamination</span>
                  <span className="font-mono text-slate-900 font-semibold">
                    ₹{estimate ? estimate.price_breakdown.lamination_fee.toFixed(2) : "0.00"}
                  </span>
                </div>
              )}

              {estimate && estimate.price_breakdown.rush_buffer > 0 && (
                <div className="flex justify-between text-amber-700 font-semibold">
                  <span>Rush Queue Buffer</span>
                  <span className="font-mono">
                    +₹{estimate.price_breakdown.rush_buffer.toFixed(2)}
                  </span>
                </div>
              )}

              <div className="flex justify-between text-slate-900 font-bold pt-3 border-t border-slate-200 text-sm">
                <span>Total Suggested Billing</span>
                <span className="text-emerald-600 font-mono font-black text-base">
                  ₹{estimate ? estimate.price_breakdown.total_fee.toFixed(2) : "0.00"}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
