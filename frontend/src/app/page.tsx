"use client";

import React, { useState, useEffect } from "react";
import { Header } from "../components/Header";
import { SmartDocEngine } from "../components/SmartDocEngine";
import { SmartBillingEngine } from "../components/SmartBillingEngine";
import { OrderManagement } from "../components/OrderManagement";
import { PhotoSpecEngine } from "../components/PhotoSpecEngine";
import { BiodataEngine } from "../components/BiodataEngine";
import { QueueEstimator } from "../components/QueueEstimator";
import { TelemetryDrawer } from "../components/TelemetryDrawer";
import { getTelemetryApi } from "../lib/api";
import { TelemetryData } from "../lib/types";
import {
  FileScan,
  Calculator,
  ShoppingBag,
  Crop,
  FileText,
  Clock,
  LayoutGrid,
  ShieldCheck,
  ArrowRight,
  ArrowLeft,
  Layers,
  Sparkles
} from "lucide-react";

type TabKey = "overview" | "smartdoc" | "billing" | "orders" | "photo" | "biodata" | "queue" | "all";

export default function Home() {
  const [telemetry, setTelemetry] = useState<TelemetryData | null>(null);
  const [activeTab, setActiveTab] = useState<TabKey>("overview");
  const [orderRefreshSignal, setOrderRefreshSignal] = useState<number>(0);

  const refreshTelemetry = async () => {
    try {
      const data = await getTelemetryApi();
      setTelemetry(data);
    } catch {
      // Backend may be starting or offline
    }
  };

  const triggerOrderRefresh = () => {
    setOrderRefreshSignal((prev) => prev + 1);
  };

  useEffect(() => {
    refreshTelemetry();
    const interval = setInterval(refreshTelemetry, 5000);
    return () => clearInterval(interval);
  }, []);

  const featureCards = [
    {
      id: "smartdoc" as TabKey,
      title: "SmartDoc AI",
      description: "Automatically corrects blur, paper skew, perspective distortion, and shadows in document scans.",
      icon: FileScan,
      iconColor: "text-cyan-600 bg-cyan-100/70 border-cyan-200",
    },
    {
      id: "billing" as TabKey,
      title: "AI Order Assistant & Smart Billing",
      description: "Converts customer requests into structured print orders with exact, transparent shop rate pricing.",
      icon: Calculator,
      iconColor: "text-indigo-600 bg-indigo-100/70 border-indigo-200",
    },
    {
      id: "orders" as TabKey,
      title: "Order Management",
      description: "Tracks counter print jobs with customer details, order totals, and live status progress.",
      icon: ShoppingBag,
      iconColor: "text-amber-600 bg-amber-100/70 border-amber-200",
    },
    {
      id: "photo" as TabKey,
      title: "Govt Photo Spec Engine",
      description: "Resizes candidate exam photos, passports, and signatures to strict portal dimensions and byte limits.",
      icon: Crop,
      iconColor: "text-rose-600 bg-rose-100/70 border-rose-200",
    },
    {
      id: "biodata" as TabKey,
      title: "A4 Biodata Maker",
      description: "Transforms rough customer notes or messages into structured biodata with instant print-ready PDF export.",
      icon: FileText,
      iconColor: "text-blue-600 bg-blue-100/70 border-blue-200",
    },
    {
      id: "queue" as TabKey,
      title: "Queue & Turnaround Estimator",
      description: "Predicts customer waiting times and fair service charges based on print queue volume.",
      icon: Clock,
      iconColor: "text-purple-600 bg-purple-100/70 border-purple-200",
    },
  ];

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col font-sans selection:bg-indigo-600 selection:text-white">
      {/* Top Header */}
      <Header telemetry={telemetry} />

      {/* Main Counter Workspace */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 py-8 flex flex-col gap-8">
        {/* Navigation Tab Bar */}
        <div className="bg-white p-2 rounded-2xl border border-slate-200 shadow-sm flex flex-col lg:flex-row items-center justify-between gap-3">
          <div className="flex items-center gap-1.5 w-full lg:w-auto overflow-x-auto pb-1 lg:pb-0 scrollbar-none">
            <button
              type="button"
              onClick={() => setActiveTab("overview")}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold transition-all whitespace-nowrap ${
                activeTab === "overview"
                  ? "bg-indigo-600 text-white shadow-sm font-bold"
                  : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
              }`}
            >
              <LayoutGrid className="h-4 w-4" />
              <span>Feature Guide</span>
            </button>

            <button
              type="button"
              onClick={() => setActiveTab("smartdoc")}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold transition-all whitespace-nowrap ${
                activeTab === "smartdoc"
                  ? "bg-indigo-600 text-white shadow-sm font-bold"
                  : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
              }`}
            >
              <FileScan className="h-4 w-4" />
              <span>1. SmartDoc AI</span>
            </button>

            <button
              type="button"
              onClick={() => setActiveTab("billing")}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold transition-all whitespace-nowrap ${
                activeTab === "billing"
                  ? "bg-indigo-600 text-white shadow-sm font-bold"
                  : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
              }`}
            >
              <Calculator className="h-4 w-4" />
              <span>2. AI Billing</span>
            </button>

            <button
              type="button"
              onClick={() => setActiveTab("orders")}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold transition-all whitespace-nowrap ${
                activeTab === "orders"
                  ? "bg-indigo-600 text-white shadow-sm font-bold"
                  : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
              }`}
            >
              <ShoppingBag className="h-4 w-4" />
              <span>3. Orders</span>
            </button>

            <button
              type="button"
              onClick={() => setActiveTab("photo")}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold transition-all whitespace-nowrap ${
                activeTab === "photo"
                  ? "bg-indigo-600 text-white shadow-sm font-bold"
                  : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
              }`}
            >
              <Crop className="h-4 w-4" />
              <span>4. Photo Spec</span>
            </button>

            <button
              type="button"
              onClick={() => setActiveTab("biodata")}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold transition-all whitespace-nowrap ${
                activeTab === "biodata"
                  ? "bg-indigo-600 text-white shadow-sm font-bold"
                  : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
              }`}
            >
              <FileText className="h-4 w-4" />
              <span>5. Biodata</span>
            </button>

            <button
              type="button"
              onClick={() => setActiveTab("queue")}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold transition-all whitespace-nowrap ${
                activeTab === "queue"
                  ? "bg-indigo-600 text-white shadow-sm font-bold"
                  : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
              }`}
            >
              <Clock className="h-4 w-4" />
              <span>6. Queue</span>
            </button>

            <button
              type="button"
              onClick={() => setActiveTab("all")}
              className={`flex items-center gap-2 px-3 py-2 rounded-xl text-xs font-semibold transition-all whitespace-nowrap ${
                activeTab === "all"
                  ? "bg-slate-900 text-white font-bold"
                  : "text-slate-500 hover:text-slate-800 hover:bg-slate-100"
              }`}
              title="Show all tools stacked in one page"
            >
              <Layers className="h-3.5 w-3.5" />
              <span>Full Counter</span>
            </button>
          </div>

          <div className="flex items-center gap-2 px-3 py-1 bg-slate-50 border border-slate-200 rounded-xl text-xs font-medium text-slate-600">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
            <span className="text-slate-700 font-semibold">Local Node Ready</span>
          </div>
        </div>

        {/* =========================================================================
            VIEW 1: ULTRA-MINIMALISTIC FEATURE GUIDE (DEFAULT)
            ========================================================================= */}
        {activeTab === "overview" && (
          <div className="flex flex-col gap-8">
            {/* Clean Hero Banner */}
            <div className="bg-gradient-to-br from-indigo-900 via-indigo-950 to-slate-950 text-white rounded-3xl p-8 sm:p-10 shadow-xl relative overflow-hidden">
              <div className="relative z-10 flex flex-col gap-4 max-w-3xl">
                <div className="flex items-center gap-2">
                  <span className="px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-xs font-bold tracking-wide uppercase flex items-center gap-1.5">
                    <ShieldCheck className="h-3.5 w-3.5" />
                    Local-First Privacy
                  </span>
                  <span className="px-3 py-1 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 text-xs font-bold tracking-wide uppercase">
                    Counter Workspace
                  </span>
                </div>

                <h2 className="text-3xl sm:text-4xl font-black tracking-tight text-white leading-tight">
                  Intelligent Print Shop & Document Automation System
                </h2>

                <p className="text-base sm:text-lg text-slate-300 leading-relaxed font-normal">
                  Built for independent print, stationery, and cyber-café operators handling customer records daily. Fast document cleanup, photo resizing, biodata formatting, and transparent counter billing with zero cloud data transfer.
                </p>

                <div className="flex flex-wrap items-center gap-3 pt-2">
                  <button
                    type="button"
                    onClick={() => setActiveTab("smartdoc")}
                    className="flex items-center gap-2 px-6 py-3 rounded-xl bg-indigo-500 hover:bg-indigo-400 text-white font-bold text-sm transition-all shadow-md shadow-indigo-500/30"
                  >
                    <span>Launch SmartDoc AI</span>
                    <ArrowRight className="h-4 w-4" />
                  </button>

                  <button
                    type="button"
                    onClick={() => setActiveTab("billing")}
                    className="flex items-center gap-2 px-6 py-3 rounded-xl bg-white/10 hover:bg-white/20 text-white border border-white/20 font-bold text-sm transition-all backdrop-blur-sm"
                  >
                    <span>Try AI Order Assistant</span>
                    <Sparkles className="h-4 w-4 text-amber-300" />
                  </button>
                </div>
              </div>
            </div>

            {/* Section Heading */}
            <div className="flex items-center justify-between border-b border-slate-200 pb-4">
              <div>
                <h3 className="text-2xl font-black text-slate-900 tracking-tight">
                  Feature Guide
                </h3>
                <p className="text-sm text-slate-600 mt-0.5">
                  Select a tool below to begin.
                </p>
              </div>

              <button
                type="button"
                onClick={() => setActiveTab("all")}
                className="text-xs font-semibold text-indigo-600 hover:text-indigo-800 flex items-center gap-1"
              >
                <span>View all tools stacked</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </button>
            </div>

            {/* Minimalistic 6 Feature Cards Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {featureCards.map((card) => {
                const IconComponent = card.icon;
                return (
                  <div
                    key={card.id}
                    className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm hover:shadow-md hover:border-indigo-300 transition-all flex flex-col justify-between gap-5 group"
                  >
                    <div className="flex flex-col gap-3.5">
                      <div className={`p-3 rounded-xl border w-fit ${card.iconColor} shadow-2xs`}>
                        <IconComponent className="h-6 w-6 stroke-[2.2]" />
                      </div>

                      <h4 className="text-lg font-bold text-slate-900 group-hover:text-indigo-600 transition-colors">
                        {card.title}
                      </h4>

                      <p className="text-sm text-slate-600 leading-relaxed">
                        {card.description}
                      </p>
                    </div>

                    <button
                      type="button"
                      onClick={() => setActiveTab(card.id)}
                      className="w-full flex items-center justify-between px-5 py-3 rounded-xl bg-slate-900 group-hover:bg-indigo-600 text-white font-semibold text-sm transition-all shadow-xs"
                    >
                      <span>Open →</span>
                      <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
                    </button>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* =========================================================================
            VIEW 2: INDIVIDUAL ENGINE VIEWS (WITH BACK NAVIGATION)
            ========================================================================= */}
        {activeTab !== "overview" && activeTab !== "all" && (
          <div className="flex flex-col gap-6">
            {/* Top Return Breadcrumb */}
            <div className="flex items-center justify-between bg-white px-5 py-3 rounded-xl border border-slate-200 shadow-2xs">
              <button
                type="button"
                onClick={() => setActiveTab("overview")}
                className="flex items-center gap-2 text-sm font-semibold text-slate-700 hover:text-indigo-600 transition-colors"
              >
                <ArrowLeft className="h-4 w-4" />
                <span>← Back to Feature Guide</span>
              </button>

              <div className="text-xs font-medium text-slate-500 hidden sm:block">
                Active tool: <span className="text-slate-900 font-semibold capitalize">{activeTab}</span>
              </div>
            </div>

            {/* Rendered Tool Component */}
            {activeTab === "smartdoc" && <SmartDocEngine onProcessed={refreshTelemetry} />}
            {activeTab === "billing" && <SmartBillingEngine onOrderCreated={triggerOrderRefresh} />}
            {activeTab === "orders" && <OrderManagement refreshSignal={orderRefreshSignal} />}
            {activeTab === "photo" && <PhotoSpecEngine onProcessed={refreshTelemetry} />}
            {activeTab === "biodata" && <BiodataEngine onProcessed={refreshTelemetry} />}
            {activeTab === "queue" && <QueueEstimator onProcessed={refreshTelemetry} />}
          </div>
        )}

        {/* =========================================================================
            VIEW 3: FULL COUNTER VIEW (ALL MODULES CONSECUTIVELY)
            ========================================================================= */}
        {activeTab === "all" && (
          <div className="flex flex-col gap-8">
            <div className="flex items-center justify-between bg-white px-5 py-3 rounded-xl border border-slate-200 shadow-2xs">
              <span className="text-sm font-bold text-slate-900">
                Full Counter Stack (All 6 Automation Engines Active)
              </span>
              <button
                type="button"
                onClick={() => setActiveTab("overview")}
                className="text-xs font-semibold text-indigo-600 hover:underline"
              >
                Switch to Feature Cards View
              </button>
            </div>

            <SmartDocEngine onProcessed={refreshTelemetry} />
            <SmartBillingEngine onOrderCreated={triggerOrderRefresh} />
            <OrderManagement refreshSignal={orderRefreshSignal} />
            <PhotoSpecEngine onProcessed={refreshTelemetry} />
            <BiodataEngine onProcessed={refreshTelemetry} />
            <QueueEstimator onProcessed={refreshTelemetry} />
          </div>
        )}

        {/* Bottom Sentry Telemetry Drawer */}
        <div className="mt-2">
          <TelemetryDrawer telemetry={telemetry} onRefresh={refreshTelemetry} />
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200 bg-white py-6 mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 flex flex-col sm:flex-row items-center justify-between gap-4 text-sm text-slate-500">
          <div className="flex items-center gap-2">
            <span className="font-bold text-slate-900">XeroxAI 2.0</span>
            <span>—</span>
            <span>Intelligent Print Shop & Document Automation System</span>
          </div>

          <div className="flex items-center gap-4 text-slate-600 flex-wrap text-xs sm:text-sm font-medium">
            <span>Local-First</span>
            <span>•</span>
            <span>Zero Cloud Leakage</span>
            <span>•</span>
            <span>Fast Counter Workflow</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
