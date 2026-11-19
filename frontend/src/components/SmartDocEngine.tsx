"use client";

import React, { useState, useRef } from "react";
import {
  FileScan,
  Upload,
  Download,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Sparkles,
  Sliders,
  ShieldCheck,
  Eye,
  FileText,
  Compass,
  SunMedium,
  Maximize2
} from "lucide-react";
import { SmartDocResponse } from "../lib/types";
import { enhanceDocumentApi } from "../lib/api";

export function SmartDocEngine({ onProcessed }: { onProcessed?: () => void }) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [outputMode, setOutputMode] = useState<"enhanced_color" | "clean_bw">("enhanced_color");
  const [autoDeskew, setAutoDeskew] = useState(true);
  const [autoPerspective, setAutoPerspective] = useState(true);
  const [removeShadows, setRemoveShadows] = useState(true);

  const [isProcessing, setIsProcessing] = useState(false);
  const [result, setResult] = useState<SmartDocResponse | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (file: File) => {
    const validTypes = ["image/jpeg", "image/png", "image/webp", "application/pdf"];
    if (!validTypes.includes(file.type) && !file.name.toLowerCase().endsWith(".pdf")) {
      setErrorMsg("Please upload a valid document image (JPG, PNG, WebP) or PDF file.");
      return;
    }
    setErrorMsg(null);
    setSelectedFile(file);
    processDocumentFile(file, outputMode, autoDeskew, autoPerspective, removeShadows);
  };

  const processDocumentFile = async (
    file: File,
    mode: "enhanced_color" | "clean_bw",
    deskew: boolean,
    perspective: boolean,
    shadows: boolean
  ) => {
    setIsProcessing(true);
    setErrorMsg(null);
    try {
      const res = await enhanceDocumentApi(file, mode, deskew, perspective, shadows);
      setResult(res);
      if (onProcessed) onProcessed();
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to process document.");
    } finally {
      setIsProcessing(false);
    }
  };

  const handleDownload = () => {
    if (!result) return;
    const byteCharacters = atob(result.processed_preview_base64);
    const byteNumbers = new Array(byteCharacters.length);
    for (let i = 0; i < byteCharacters.length; i++) {
      byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    const byteArray = new Uint8Array(byteNumbers);
    const blob = new Blob([byteArray], { type: "image/jpeg" });
    const url = URL.createObjectURL(blob);

    const a = document.createElement("a");
    a.href = url;
    const baseName = result.filename.replace(/\.[^/.]+$/, "");
    a.download = `xeroxai_enhanced_${baseName}.jpg`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // Drag and drop handlers
  const onDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };
  const onDragLeave = () => setIsDragging(false);
  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-6 sm:p-8 shadow-sm flex flex-col gap-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div className="flex items-center gap-3.5">
          <div className="p-3 rounded-xl bg-cyan-50 text-cyan-600 border border-cyan-100 shadow-2xs">
            <FileScan className="h-6 w-6 stroke-[2.2]" />
          </div>
          <div>
            <div className="flex items-center gap-2.5">
              <h2 className="text-xl sm:text-2xl font-black text-slate-900 tracking-tight">
                SmartDoc AI — Document Correction
              </h2>
              <span className="px-2.5 py-1 text-xs font-mono font-bold bg-cyan-50 text-cyan-700 border border-cyan-200 rounded-lg">
                OpenCV Pipeline
              </span>
            </div>
            <p className="text-sm text-slate-500 font-medium mt-0.5">
              Auto-corrects blur, skew, perspective, shadows, and uneven counter lighting. Content preserved.
            </p>
          </div>
        </div>

        {/* Guaranteed Safety Badge */}
        <div className="flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-semibold self-start sm:self-auto shadow-2xs">
          <ShieldCheck className="h-4 w-4 shrink-0 text-emerald-600" />
          <span>Zero Text Alteration Guarantee</span>
        </div>
      </div>

      {/* Controls & Options Bar */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-3.5 bg-slate-50 p-4 rounded-2xl border border-slate-200 text-xs">
        {/* Output Mode Selector */}
        <div className="flex flex-col gap-1.5">
          <label className="text-xs font-bold text-slate-700 uppercase tracking-wide">
            Correction Mode
          </label>
          <div className="grid grid-cols-2 gap-1.5 bg-white p-1 rounded-xl border border-slate-200 shadow-2xs">
            <button
              type="button"
              onClick={() => {
                setOutputMode("enhanced_color");
                if (selectedFile) processDocumentFile(selectedFile, "enhanced_color", autoDeskew, autoPerspective, removeShadows);
              }}
              className={`py-1.5 px-2 rounded-lg font-bold text-xs transition-all ${
                outputMode === "enhanced_color"
                  ? "bg-indigo-600 text-white shadow-xs"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              Enhanced Color
            </button>
            <button
              type="button"
              onClick={() => {
                setOutputMode("clean_bw");
                if (selectedFile) processDocumentFile(selectedFile, "clean_bw", autoDeskew, autoPerspective, removeShadows);
              }}
              className={`py-1.5 px-2 rounded-lg font-bold text-xs transition-all ${
                outputMode === "clean_bw"
                  ? "bg-indigo-600 text-white shadow-xs"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              Clean B&W Scan
            </button>
          </div>
        </div>

        {/* Auto Deskew Toggle */}
        <div className="flex items-center justify-between p-3 rounded-xl bg-white border border-slate-200 shadow-2xs">
          <div className="flex items-center gap-2.5">
            <div className="p-1.5 rounded-lg bg-cyan-50 text-cyan-600">
              <Compass className="h-4 w-4" />
            </div>
            <div>
              <div className="font-bold text-slate-900 text-xs">Auto Deskew</div>
              <div className="text-[11px] text-slate-500">Corrects page tilt</div>
            </div>
          </div>
          <input
            type="checkbox"
            checked={autoDeskew}
            onChange={(e) => {
              setAutoDeskew(e.target.checked);
              if (selectedFile) processDocumentFile(selectedFile, outputMode, e.target.checked, autoPerspective, removeShadows);
            }}
            className="w-4 h-4 accent-indigo-600 rounded cursor-pointer"
          />
        </div>

        {/* Perspective Correction Toggle */}
        <div className="flex items-center justify-between p-3 rounded-xl bg-white border border-slate-200 shadow-2xs">
          <div className="flex items-center gap-2.5">
            <div className="p-1.5 rounded-lg bg-cyan-50 text-cyan-600">
              <Maximize2 className="h-4 w-4" />
            </div>
            <div>
              <div className="font-bold text-slate-900 text-xs">Perspective Warp</div>
              <div className="text-[11px] text-slate-500">4-corner desk quad</div>
            </div>
          </div>
          <input
            type="checkbox"
            checked={autoPerspective}
            onChange={(e) => {
              setAutoPerspective(e.target.checked);
              if (selectedFile) processDocumentFile(selectedFile, outputMode, autoDeskew, e.target.checked, removeShadows);
            }}
            className="w-4 h-4 accent-indigo-600 rounded cursor-pointer"
          />
        </div>

        {/* Shadow Removal Toggle */}
        <div className="flex items-center justify-between p-3 rounded-xl bg-white border border-slate-200 shadow-2xs">
          <div className="flex items-center gap-2.5">
            <div className="p-1.5 rounded-lg bg-cyan-50 text-cyan-600">
              <SunMedium className="h-4 w-4" />
            </div>
            <div>
              <div className="font-bold text-slate-900 text-xs">Shadow Removal</div>
              <div className="text-[11px] text-slate-500">Flatten lighting</div>
            </div>
          </div>
          <input
            type="checkbox"
            checked={removeShadows}
            onChange={(e) => {
              setRemoveShadows(e.target.checked);
              if (selectedFile) processDocumentFile(selectedFile, outputMode, autoDeskew, autoPerspective, e.target.checked);
            }}
            className="w-4 h-4 accent-indigo-600 rounded cursor-pointer"
          />
        </div>
      </div>

      {/* Upload Zone */}
      <div
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all ${
          isDragging
            ? "border-indigo-500 bg-indigo-50/50"
            : "border-slate-300 hover:border-indigo-400 bg-slate-50/60 hover:bg-indigo-50/20"
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept="image/jpeg,image/png,image/webp,application/pdf"
          className="hidden"
          onChange={(e) => {
            if (e.target.files && e.target.files[0]) {
              handleFileSelect(e.target.files[0]);
            }
          }}
        />
        <div className="flex flex-col items-center gap-2.5">
          <div className="p-3.5 rounded-2xl bg-white border border-slate-200 text-indigo-600 shadow-xs">
            <Upload className="h-6 w-6 stroke-[2.2]" />
          </div>
          <p className="text-base font-bold text-slate-900">
            Upload document (Govt form, certificate, receipt, or PDF)
          </p>
          <p className="text-xs text-slate-500">
            Supports JPG, PNG, WebP, and multi-page PDF documents. Drag and drop or click to browse.
          </p>
        </div>
      </div>

      {errorMsg && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-sm font-medium flex items-center gap-2.5">
          <AlertCircle className="h-5 w-5 shrink-0 text-rose-600" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Before / After Preview Zone */}
      {(result || isProcessing) && (
        <div className="flex flex-col gap-5 bg-slate-50 p-6 rounded-2xl border border-slate-200">
          {/* Quality Diagnostics Bar */}
          {result && (
            <div className="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-slate-200 text-xs font-mono">
              <div className="flex flex-wrap items-center gap-2">
                {/* Blur / Clarity Pill */}
                <div
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg border font-semibold ${
                    result.is_blurry
                      ? "bg-amber-50 border-amber-200 text-amber-800"
                      : "bg-emerald-50 border-emerald-200 text-emerald-800"
                  }`}
                >
                  <Eye className="h-4 w-4" />
                  <span>Clarity Score: {result.blur_score}</span>
                  <span className="text-[10px]">({result.is_blurry ? "Low Sharpness" : "Sharp"})</span>
                </div>

                {/* Skew Pill */}
                <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white border border-slate-200 text-slate-700 font-semibold shadow-2xs">
                  <Compass className="h-4 w-4 text-cyan-600" />
                  <span>Skew: {result.detected_skew_deg}°</span>
                </div>

                {/* Dimensions */}
                <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white border border-slate-200 text-slate-600 font-semibold shadow-2xs">
                  <span>{result.width} × {result.height} px</span>
                </div>
              </div>

              {/* Download Action */}
              <button
                type="button"
                onClick={handleDownload}
                className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold transition-all shadow-sm active:scale-95"
              >
                <Download className="h-4 w-4" />
                <span>Download Enhanced Document</span>
              </button>
            </div>
          )}

          {/* Side-by-Side Images */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {/* Original */}
            <div className="flex flex-col items-center gap-2.5">
              <span className="text-xs font-bold text-slate-600 uppercase tracking-wide">
                Original Upload (Preserved)
              </span>
              <div className="w-full h-88 rounded-xl bg-white border border-slate-200 flex items-center justify-center overflow-hidden p-3 shadow-2xs">
                {result?.original_preview_base64 ? (
                  <img
                    src={`data:image/jpeg;base64,${result.original_preview_base64}`}
                    alt="Original Document"
                    className="max-h-full max-w-full object-contain rounded-lg"
                  />
                ) : (
                  <FileText className="h-12 w-12 text-slate-300" />
                )}
              </div>
            </div>

            {/* Enhanced */}
            <div className="flex flex-col items-center gap-2.5">
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold text-slate-900 uppercase tracking-wide">
                  Corrected & Enhanced Document
                </span>
                {isProcessing && <RefreshCw className="h-4 w-4 animate-spin text-indigo-600" />}
              </div>

              <div className="w-full h-88 rounded-xl bg-white border border-slate-200 flex items-center justify-center overflow-hidden p-3 relative shadow-2xs">
                {isProcessing ? (
                  <div className="flex flex-col items-center gap-3 text-slate-600">
                    <RefreshCw className="h-8 w-8 animate-spin text-indigo-600" />
                    <span className="text-sm font-semibold">Running OpenCV document deskew & shadow cleanup...</span>
                  </div>
                ) : result?.processed_preview_base64 ? (
                  <img
                    src={`data:image/jpeg;base64,${result.processed_preview_base64}`}
                    alt="Enhanced Document"
                    className="max-h-full max-w-full object-contain rounded-lg shadow-sm"
                  />
                ) : null}
              </div>
            </div>
          </div>

          {/* Reliability Notes List */}
          {result?.reliability_notes && result.reliability_notes.length > 0 && (
            <div className="bg-white p-4 rounded-xl border border-slate-200 text-xs text-slate-700 flex flex-col gap-1.5 shadow-2xs">
              <span className="text-xs font-bold text-slate-900 uppercase tracking-wide">
                Processing Diagnostics & Integrity Verification:
              </span>
              <ul className="list-disc list-inside space-y-1 text-slate-600 font-medium">
                {result.reliability_notes.map((note, idx) => (
                  <li key={idx} className="text-slate-700">{note}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
