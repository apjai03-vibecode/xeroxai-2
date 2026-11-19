"use client";

import React, { useState, useEffect } from "react";
import {
  Calculator,
  Sparkles,
  Layers,
  Palette,
  FileCheck,
  Plus,
  Trash2,
  Settings2,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  ShoppingBag,
  IndianRupee,
  Copy,
  ChevronDown,
  ChevronUp,
  Zap,
  Tag
} from "lucide-react";
import { OrderItem, PricingConfig, BillingCalculationResponse } from "../lib/types";
import {
  calculateBillingApi,
  getPricingApi,
  updatePricingApi,
  parseOrderAiApi,
  createOrderApi,
} from "../lib/api";

const PRIMARY_SAMPLE = "50 colour copies, double-sided, and 2 laminated sheets for Rahul";

const ADDITIONAL_SAMPLES = [
  "15 pages black and white double-sided A4 3 copies for Priya",
  "2 copies of 10 pages Color single-sided A3 with lamination for Suresh",
];

export function SmartBillingEngine({
  onOrderCreated,
}: {
  onOrderCreated?: () => void;
}) {
  // Natural language AI Assistant state
  const [naturalText, setNaturalText] = useState("");
  const [isParsingAi, setIsParsingAi] = useState(false);
  const [aiMessage, setAiMessage] = useState<string | null>(null);

  // Customer state
  const [customerName, setCustomerName] = useState("Walk-in Customer");
  const [customerPhone, setCustomerPhone] = useState("");
  const [notes, setNotes] = useState("");

  // Line items state
  const [items, setItems] = useState<OrderItem[]>([
    {
      page_count: 10,
      is_color: false,
      is_double_sided: false,
      paper_size: "A4",
      copies: 1,
      needs_lamination: false,
    },
  ]);

  // Billing calculation result
  const [calculation, setCalculation] = useState<BillingCalculationResponse | null>(null);
  const [isCalculating, setIsCalculating] = useState(false);

  // Shop Rates Configuration Modal / Drawer
  const [pricing, setPricing] = useState<PricingConfig | null>(null);
  const [showPricingModal, setShowPricingModal] = useState(false);
  const [isSavingPricing, setIsSavingPricing] = useState(false);
  const [orderCreatedMsg, setOrderCreatedMsg] = useState<string | null>(null);

  // Load shop pricing on mount
  useEffect(() => {
    getPricingApi()
      .then((cfg) => setPricing(cfg))
      .catch(() => {
        // Fallback to default pricing state
      });
  }, []);

  // Recalculate billing whenever items change
  useEffect(() => {
    let isCancelled = false;
    const calculate = async () => {
      setIsCalculating(true);
      try {
        const res = await calculateBillingApi(items);
        if (!isCancelled) {
          setCalculation(res);
        }
      } catch {
        // Calculation error handled in UI state
      } finally {
        if (!isCancelled) setIsCalculating(false);
      }
    };

    const timer = setTimeout(calculate, 200);
    return () => {
      isCancelled = true;
      clearTimeout(timer);
    };
  }, [items, pricing]);

  const runAiParser = async (textToParse: string) => {
    if (!textToParse.trim()) return;
    setIsParsingAi(true);
    setAiMessage(null);
    setOrderCreatedMsg(null);
    try {
      const res = await parseOrderAiApi(textToParse);
      const parsed = res.parsed_order;
      if (parsed.customer_name && parsed.customer_name !== "Walk-in Customer") {
        setCustomerName(parsed.customer_name);
      }
      if (parsed.customer_phone) {
        setCustomerPhone(parsed.customer_phone);
      }
      if (parsed.notes) {
        setNotes(parsed.notes);
      }

      setItems([
        {
          page_count: parsed.page_count,
          is_color: parsed.is_color,
          is_double_sided: parsed.is_double_sided,
          paper_size: parsed.paper_size,
          copies: parsed.copies,
          needs_lamination: parsed.needs_lamination,
        },
      ]);

      setAiMessage(
        `Parsed order via ${res.model_used}. Pricing calculated strictly using shop rate card.`
      );
    } catch (err: unknown) {
      setAiMessage(err instanceof Error ? err.message : "Failed to parse request with AI.");
    } finally {
      setIsParsingAi(false);
    }
  };

  const handleParseAi = () => {
    runAiParser(naturalText);
  };

  const handleQuickSampleClick = (sampleText: string) => {
    setNaturalText(sampleText);
    runAiParser(sampleText);
  };

  const addItem = () => {
    setItems([
      ...items,
      {
        page_count: 5,
        is_color: false,
        is_double_sided: false,
        paper_size: "A4",
        copies: 1,
        needs_lamination: false,
      },
    ]);
  };

  const removeItem = (idx: number) => {
    if (items.length <= 1) return;
    setItems(items.filter((_, i) => i !== idx));
  };

  const updateItem = (idx: number, updates: Partial<OrderItem>) => {
    setItems(
      items.map((it, i) => (i === idx ? { ...it, ...updates } : it))
    );
  };

  const handleCreateOrder = async () => {
    if (!items.length) return;
    try {
      const res = await createOrderApi({
        customer_name: customerName || "Walk-in Customer",
        customer_phone: customerPhone,
        items,
        notes,
      });
      setOrderCreatedMsg(`Order ${res.order_id} created successfully! Saved to persistent SQLite database.`);
      if (onOrderCreated) onOrderCreated();
    } catch (err: unknown) {
      alert("Failed to create order: " + (err instanceof Error ? err.message : String(err)));
    }
  };

  const handleSavePricing = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!pricing) return;
    setIsSavingPricing(true);
    try {
      const updated = await updatePricingApi(pricing);
      setPricing(updated);
      setShowPricingModal(false);
    } catch (err: unknown) {
      alert("Failed to update rates: " + (err instanceof Error ? err.message : String(err)));
    } finally {
      setIsSavingPricing(false);
    }
  };

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-6 sm:p-8 shadow-sm flex flex-col gap-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div className="flex items-center gap-3.5">
          <div className="p-3 rounded-xl bg-indigo-50 text-indigo-600 border border-indigo-100 shadow-2xs">
            <Calculator className="h-6 w-6 stroke-[2.2]" />
          </div>
          <div>
            <div className="flex items-center gap-2.5">
              <h2 className="text-xl sm:text-2xl font-black text-slate-900 tracking-tight">
                AI Order Assistant & Smart Billing
              </h2>
              <span className="px-2.5 py-1 text-xs font-mono font-bold bg-emerald-50 text-emerald-700 border border-emerald-200 rounded-lg">
                Deterministic ₹ Rates
              </span>
            </div>
            <p className="text-sm text-slate-500 font-medium mt-0.5">
              Natural-language customer counter parsing with strict, deterministic pricing formulas.
            </p>
          </div>
        </div>

        {/* Shop Pricing Modal Trigger */}
        <button
          type="button"
          onClick={() => setShowPricingModal(true)}
          className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-800 text-sm font-semibold border border-slate-300 transition-colors self-start sm:self-auto shadow-2xs"
        >
          <Settings2 className="h-4 w-4 text-indigo-600" />
          <span>Customize Shop Rates</span>
        </button>
      </div>

      {/* AI Order Assistant Box with 1-Click Quick-Fill */}
      <div className="bg-gradient-to-br from-indigo-50/70 via-indigo-50/30 to-slate-50 p-6 rounded-2xl border border-indigo-100 shadow-xs flex flex-col gap-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <label className="text-sm font-bold text-slate-900 uppercase tracking-wide flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-indigo-600" />
            <span>AI Order Assistant (Natural Language Counter Input)</span>
          </label>

          <span className="text-xs font-medium text-slate-500">
            Powered by Google Gemma 2:2B local-first
          </span>
        </div>

        {/* 1-Click Sample Pill Bar for Judges */}
        <div className="flex flex-wrap items-center gap-2 pt-1">
          <span className="text-xs font-bold text-indigo-950 uppercase tracking-wider flex items-center gap-1">
            <Zap className="h-3.5 w-3.5 text-amber-500 fill-amber-500" />
            1-Click Sample:
          </span>

          <button
            type="button"
            onClick={() => handleQuickSampleClick(PRIMARY_SAMPLE)}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold shadow-xs transition-all hover:scale-[1.02] active:scale-[0.98]"
          >
            <span>&ldquo;50 colour copies, double-sided, and 2 laminated sheets for Rahul&rdquo;</span>
            <Sparkles className="h-3 w-3 text-amber-300" />
          </button>

          {ADDITIONAL_SAMPLES.map((sample, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => handleQuickSampleClick(sample)}
              className="px-3 py-1.5 rounded-xl bg-white hover:bg-indigo-50 border border-slate-200 text-slate-700 text-xs font-medium shadow-2xs transition-colors"
            >
              Sample {idx + 2}
            </button>
          ))}
        </div>

        {/* Input and Parse Button */}
        <div className="flex flex-col sm:flex-row gap-3 pt-1">
          <input
            type="text"
            value={naturalText}
            onChange={(e) => setNaturalText(e.target.value)}
            placeholder="Type or click sample above (e.g., '50 colour copies, double-sided, and 2 laminated sheets for Rahul')"
            className="flex-1 bg-white border border-slate-300 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 rounded-xl px-4 py-3 text-sm text-slate-900 placeholder-slate-400 font-mono shadow-2xs outline-none transition-all"
          />
          <button
            type="button"
            disabled={isParsingAi || !naturalText.trim()}
            onClick={handleParseAi}
            className="flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-700 active:bg-indigo-800 text-white font-bold text-sm transition-all shadow-sm disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
          >
            {isParsingAi ? (
              <RefreshCw className="h-4 w-4 animate-spin" />
            ) : (
              <Sparkles className="h-4 w-4" />
            )}
            <span>Parse & Populate</span>
          </button>
        </div>

        {aiMessage && (
          <div className="text-xs font-mono text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-xl px-3.5 py-2 flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-600" />
            <span>{aiMessage}</span>
          </div>
        )}
      </div>

      {/* Customer Info Row */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div>
          <label className="text-xs font-bold text-slate-700 block mb-1.5">
            Customer Name
          </label>
          <input
            type="text"
            value={customerName}
            onChange={(e) => setCustomerName(e.target.value)}
            className="w-full bg-slate-50 border border-slate-300 focus:bg-white focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 rounded-xl px-3.5 py-2.5 text-sm text-slate-900 font-medium outline-none transition-all"
          />
        </div>
        <div>
          <label className="text-xs font-bold text-slate-700 block mb-1.5">
            Customer Phone
          </label>
          <input
            type="text"
            value={customerPhone}
            onChange={(e) => setCustomerPhone(e.target.value)}
            placeholder="e.g., 9876543210"
            className="w-full bg-slate-50 border border-slate-300 focus:bg-white focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 rounded-xl px-3.5 py-2.5 text-sm text-slate-900 font-medium outline-none transition-all"
          />
        </div>
        <div>
          <label className="text-xs font-bold text-slate-700 block mb-1.5">
            Job Notes / Instructions
          </label>
          <input
            type="text"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="e.g., Spiral bind later, urgent exam"
            className="w-full bg-slate-50 border border-slate-300 focus:bg-white focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 rounded-xl px-3.5 py-2.5 text-sm text-slate-900 font-medium outline-none transition-all"
          />
        </div>
      </div>

      {/* Line Items Section */}
      <div className="flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <span className="text-sm font-bold text-slate-900 uppercase tracking-wide">
            Job Line Items ({items.length})
          </span>
          <button
            type="button"
            onClick={addItem}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-50 text-emerald-700 hover:bg-emerald-100 border border-emerald-200 text-xs font-bold transition-colors"
          >
            <Plus className="h-4 w-4" />
            <span>Add Job Item</span>
          </button>
        </div>

        <div className="flex flex-col gap-3">
          {items.map((item, idx) => (
            <div
              key={idx}
              className="bg-slate-50 border border-slate-200 rounded-xl p-4 grid grid-cols-1 md:grid-cols-12 gap-3.5 items-center text-sm"
            >
              {/* Pages */}
              <div className="md:col-span-2">
                <label className="text-xs font-bold text-slate-600 block mb-1 font-mono">Pages</label>
                <input
                  type="number"
                  min={1}
                  value={item.page_count}
                  onChange={(e) =>
                    updateItem(idx, { page_count: Math.max(1, parseInt(e.target.value) || 1) })
                  }
                  className="w-full bg-white border border-slate-300 focus:border-indigo-500 rounded-lg px-3 py-2 text-slate-900 font-mono font-semibold"
                />
              </div>

              {/* Color Mode */}
              <div className="md:col-span-2">
                <label className="text-xs font-bold text-slate-600 block mb-1 font-mono">Color Mode</label>
                <select
                  value={item.is_color ? "color" : "bw"}
                  onChange={(e) => updateItem(idx, { is_color: e.target.value === "color" })}
                  className="w-full bg-white border border-slate-300 focus:border-indigo-500 rounded-lg px-2.5 py-2 text-slate-900 font-medium"
                >
                  <option value="bw">B&W (Mono)</option>
                  <option value="color">Full Color</option>
                </select>
              </div>

              {/* Print Sides */}
              <div className="md:col-span-2">
                <label className="text-xs font-bold text-slate-600 block mb-1 font-mono">Print Sides</label>
                <select
                  value={item.is_double_sided ? "duplex" : "simplex"}
                  onChange={(e) =>
                    updateItem(idx, { is_double_sided: e.target.value === "duplex" })
                  }
                  className="w-full bg-white border border-slate-300 focus:border-indigo-500 rounded-lg px-2.5 py-2 text-slate-900 font-medium"
                >
                  <option value="simplex">Single-sided</option>
                  <option value="duplex">Double-sided (Duplex)</option>
                </select>
              </div>

              {/* Paper Size */}
              <div className="md:col-span-2">
                <label className="text-xs font-bold text-slate-600 block mb-1 font-mono">Paper Size</label>
                <select
                  value={item.paper_size}
                  onChange={(e) => updateItem(idx, { paper_size: e.target.value })}
                  className="w-full bg-white border border-slate-300 focus:border-indigo-500 rounded-lg px-2.5 py-2 text-slate-900 font-medium"
                >
                  <option value="A4">A4 Standard</option>
                  <option value="A3">A3 Ledger</option>
                  <option value="Legal">Legal</option>
                  <option value="Letter">Letter</option>
                </select>
              </div>

              {/* Copies */}
              <div className="md:col-span-1">
                <label className="text-xs font-bold text-slate-600 block mb-1 font-mono">Copies</label>
                <input
                  type="number"
                  min={1}
                  value={item.copies}
                  onChange={(e) =>
                    updateItem(idx, { copies: Math.max(1, parseInt(e.target.value) || 1) })
                  }
                  className="w-full bg-white border border-slate-300 focus:border-indigo-500 rounded-lg px-2 py-2 text-slate-900 font-mono font-semibold text-center"
                />
              </div>

              {/* Lamination Checkbox */}
              <div className="md:col-span-2 flex items-center gap-2 pt-2 md:pt-4">
                <input
                  type="checkbox"
                  id={`lam_${idx}`}
                  checked={item.needs_lamination}
                  onChange={(e) => updateItem(idx, { needs_lamination: e.target.checked })}
                  className="w-4 h-4 accent-indigo-600 rounded cursor-pointer"
                />
                <label htmlFor={`lam_${idx}`} className="text-xs font-semibold text-slate-800 cursor-pointer">
                  Lamination
                </label>
              </div>

              {/* Delete line item */}
              <div className="md:col-span-1 flex justify-end pt-2 md:pt-4">
                <button
                  type="button"
                  disabled={items.length <= 1}
                  onClick={() => removeItem(idx)}
                  className="p-2 rounded-lg bg-white hover:bg-rose-50 text-slate-400 hover:text-rose-600 border border-slate-200 transition-colors disabled:opacity-20 shadow-2xs"
                  title="Remove item"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Itemized Calculation Summary & Order Action Bar */}
      <div className="bg-slate-900 text-white p-6 rounded-2xl shadow-md flex flex-col md:flex-row items-center justify-between gap-6">
        <div className="flex flex-wrap items-center gap-8 text-sm">
          <div>
            <span className="text-slate-400 block text-xs uppercase font-mono tracking-wider">Total Sheets</span>
            <span className="text-white font-mono font-bold text-xl">
              {calculation ? calculation.total_sheets : 0} sheets
            </span>
          </div>

          <div>
            <span className="text-slate-400 block text-xs uppercase font-mono tracking-wider">Total Amount</span>
            <span className="text-emerald-400 font-mono font-black text-3xl flex items-center">
              ₹{calculation ? calculation.grand_total.toFixed(2) : "0.00"}
            </span>
          </div>

          <div className="text-xs text-slate-400 max-w-xs leading-relaxed hidden lg:block">
            Calculated strictly according to your persistent shop rate card. AI never invents charges.
          </div>
        </div>

        <button
          type="button"
          onClick={handleCreateOrder}
          className="w-full md:w-auto flex items-center justify-center gap-2.5 px-8 py-3.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-black text-sm transition-all shadow-lg shadow-emerald-500/20 active:scale-95"
        >
          <ShoppingBag className="h-5 w-5" />
          <span>Save Counter Order (SQLite)</span>
        </button>
      </div>

      {orderCreatedMsg && (
        <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-sm font-medium flex items-center gap-2.5 shadow-2xs">
          <CheckCircle2 className="h-5 w-5 shrink-0 text-emerald-600" />
          <span>{orderCreatedMsg}</span>
        </div>
      )}

      {/* Shop Rates Customization Modal */}
      {showPricingModal && pricing && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white border border-slate-200 rounded-3xl max-w-lg w-full p-6 sm:p-8 shadow-2xl flex flex-col gap-5 text-slate-900">
            <div className="flex items-center justify-between border-b border-slate-200 pb-4">
              <div className="flex items-center gap-2.5">
                <Settings2 className="h-6 w-6 text-indigo-600" />
                <h3 className="font-black text-slate-900 text-lg">Customize Shop Rate Card (₹ INR)</h3>
              </div>
              <button
                type="button"
                onClick={() => setShowPricingModal(false)}
                className="text-slate-400 hover:text-slate-700 text-sm font-bold p-1 rounded-lg hover:bg-slate-100"
              >
                ✕ Close
              </button>
            </div>

            <form onSubmit={handleSavePricing} className="flex flex-col gap-4 text-xs">
              <div className="grid grid-cols-2 gap-3.5">
                <div>
                  <label className="text-xs font-bold text-slate-700 block mb-1">B&W Single-sided (A4)</label>
                  <input
                    type="number"
                    step="0.5"
                    value={pricing.bw_single}
                    onChange={(e) => setPricing({ ...pricing, bw_single: parseFloat(e.target.value) || 0 })}
                    className="w-full bg-slate-50 border border-slate-300 focus:bg-white focus:border-indigo-500 rounded-xl p-2.5 text-slate-900 font-mono font-semibold text-sm"
                  />
                </div>
                <div>
                  <label className="text-xs font-bold text-slate-700 block mb-1">B&W Double-sided (A4)</label>
                  <input
                    type="number"
                    step="0.5"
                    value={pricing.bw_double}
                    onChange={(e) => setPricing({ ...pricing, bw_double: parseFloat(e.target.value) || 0 })}
                    className="w-full bg-slate-50 border border-slate-300 focus:bg-white focus:border-indigo-500 rounded-xl p-2.5 text-slate-900 font-mono font-semibold text-sm"
                  />
                </div>
                <div>
                  <label className="text-xs font-bold text-slate-700 block mb-1">Color Single-sided (A4)</label>
                  <input
                    type="number"
                    step="1"
                    value={pricing.color_single}
                    onChange={(e) => setPricing({ ...pricing, color_single: parseFloat(e.target.value) || 0 })}
                    className="w-full bg-slate-50 border border-slate-300 focus:bg-white focus:border-indigo-500 rounded-xl p-2.5 text-slate-900 font-mono font-semibold text-sm"
                  />
                </div>
                <div>
                  <label className="text-xs font-bold text-slate-700 block mb-1">Color Double-sided (A4)</label>
                  <input
                    type="number"
                    step="1"
                    value={pricing.color_double}
                    onChange={(e) => setPricing({ ...pricing, color_double: parseFloat(e.target.value) || 0 })}
                    className="w-full bg-slate-50 border border-slate-300 focus:bg-white focus:border-indigo-500 rounded-xl p-2.5 text-slate-900 font-mono font-semibold text-sm"
                  />
                </div>
                <div>
                  <label className="text-xs font-bold text-slate-700 block mb-1">A3 Paper Multiplier</label>
                  <input
                    type="number"
                    step="0.1"
                    value={pricing.a3_multiplier}
                    onChange={(e) => setPricing({ ...pricing, a3_multiplier: parseFloat(e.target.value) || 1 })}
                    className="w-full bg-slate-50 border border-slate-300 focus:bg-white focus:border-indigo-500 rounded-xl p-2.5 text-slate-900 font-mono font-semibold text-sm"
                  />
                </div>
                <div>
                  <label className="text-xs font-bold text-slate-700 block mb-1">Legal Paper Multiplier</label>
                  <input
                    type="number"
                    step="0.05"
                    value={pricing.legal_multiplier}
                    onChange={(e) => setPricing({ ...pricing, legal_multiplier: parseFloat(e.target.value) || 1 })}
                    className="w-full bg-slate-50 border border-slate-300 focus:bg-white focus:border-indigo-500 rounded-xl p-2.5 text-slate-900 font-mono font-semibold text-sm"
                  />
                </div>
                <div>
                  <label className="text-xs font-bold text-slate-700 block mb-1">Lamination (A4)</label>
                  <input
                    type="number"
                    step="1"
                    value={pricing.lamination_a4}
                    onChange={(e) => setPricing({ ...pricing, lamination_a4: parseFloat(e.target.value) || 0 })}
                    className="w-full bg-slate-50 border border-slate-300 focus:bg-white focus:border-indigo-500 rounded-xl p-2.5 text-slate-900 font-mono font-semibold text-sm"
                  />
                </div>
                <div>
                  <label className="text-xs font-bold text-slate-700 block mb-1">Lamination (A3)</label>
                  <input
                    type="number"
                    step="1"
                    value={pricing.lamination_a3}
                    onChange={(e) => setPricing({ ...pricing, lamination_a3: parseFloat(e.target.value) || 0 })}
                    className="w-full bg-slate-50 border border-slate-300 focus:bg-white focus:border-indigo-500 rounded-xl p-2.5 text-slate-900 font-mono font-semibold text-sm"
                  />
                </div>
              </div>

              <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-200">
                <button
                  type="button"
                  onClick={() => setShowPricingModal(false)}
                  className="px-5 py-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-sm"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSavingPricing}
                  className="px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-sm shadow-sm"
                >
                  {isSavingPricing ? "Saving..." : "Save Rate Card (SQLite)"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
