"use client";

import React, { useState, useRef } from "react";
import { Upload, Download, CheckCircle2, AlertCircle, RefreshCw, Crop, Image as ImageIcon } from "lucide-react";
import { PhotoPreset, PresetInfo } from "../lib/types";
import { resizePhotoApi } from "../lib/api";

const PRESETS: PresetInfo[] = [
  {
    id: "tnpsc_upsc",
    title: "TNPSC / UPSC Govt Exams",
    badge: "Strict 20-50 KB",
    dimensions: "200 × 230 px",
    sizeLimit: "20 KB – 50 KB",
    description: "Strict official portal dimensions with dynamic stepped compression and padding.",
  },
  {
    id: "passport_standard",
    title: "Standard Passport (35×45mm)",
    badge: "300 DPI Contrast",
    dimensions: "413 × 531 px",
    sizeLimit: "High Quality Print",
    description: "Crisp 35x45 mm ratio with automatic contrast enhancement for counter printing.",
  },
  {
    id: "signature",
    title: "Exam Signature Spec",
    badge: "Under 20 KB",
    dimensions: "140 × 60 px",
    sizeLimit: "< 20 KB strictly",
    description: "Auto-contrast to clean up faint ink scans, compressed for instant portal upload.",
  },
];

export function PhotoSpecEngine({ onProcessed }: { onProcessed?: () => void }) {
  const [selectedPreset, setSelectedPreset] = useState<PhotoPreset>("tnpsc_upsc");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [originalPreviewUrl, setOriginalPreviewUrl] = useState<string | null>(null);
  const [processedUrl, setProcessedUrl] = useState<string | null>(null);
  const [processedSizeKb, setProcessedSizeKb] = useState<string | null>(null);
  const [processedDims, setProcessedDims] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (file: File) => {
    if (!file.type.startsWith("image/")) {
      setErrorMsg("Please upload a valid image file (JPEG, PNG, or WebP).");
      return;
    }
    setErrorMsg(null);
    setSelectedFile(file);
    setProcessedUrl(null);
    setProcessedSizeKb(null);
    setProcessedDims(null);

    const url = URL.createObjectURL(file);
    setOriginalPreviewUrl(url);

    // Auto-process on select
    processImage(file, selectedPreset);
  };

  const processImage = async (file: File, preset: PhotoPreset) => {
    setIsProcessing(true);
    setErrorMsg(null);
    try {
      const res = await resizePhotoApi(file, preset);
      const outputUrl = URL.createObjectURL(res.blob);
      setProcessedUrl(outputUrl);
      setProcessedSizeKb(res.sizeKb);
      setProcessedDims(res.dimensions);
      if (onProcessed) onProcessed();
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to process photo.");
    } finally {
      setIsProcessing(false);
    }
  };

  const handlePresetChange = (preset: PhotoPreset) => {
    setSelectedPreset(preset);
    if (selectedFile) {
      processImage(selectedFile, preset);
    }
  };

  const handleDownload = () => {
    if (!processedUrl) return;
    const a = document.createElement("a");
    a.href = processedUrl;
    a.download = `xeroxai_${selectedPreset}_${Date.now()}.jpg`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
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

  // Check if size satisfies preset bounds
  const isSizeCompliant = () => {
    if (!processedSizeKb) return false;
    const kb = parseFloat(processedSizeKb);
    if (selectedPreset === "tnpsc_upsc") return kb >= 20.0 && kb <= 50.0;
    if (selectedPreset === "signature") return kb < 20.0;
    return true;
  };

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-6 sm:p-8 shadow-sm flex flex-col gap-6">
      {/* Card Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div className="flex items-center gap-3.5">
          <div className="p-3 rounded-xl bg-rose-50 text-rose-600 border border-rose-100 shadow-2xs">
            <Crop className="h-6 w-6 stroke-[2.2]" />
          </div>
          <div>
            <div className="flex items-center gap-2.5">
              <h2 className="text-xl sm:text-2xl font-black text-slate-900 tracking-tight">
                Govt & Exam Photo Spec Engine
              </h2>
              <span className="px-2.5 py-1 text-xs font-mono font-bold bg-rose-50 text-rose-700 border border-rose-200 rounded-lg">
                Strict Byte Bounds
              </span>
            </div>
            <p className="text-sm text-slate-500 font-medium mt-0.5">
              Guaranteed strict byte limits & pixel dimensions via local PIL engine.
            </p>
          </div>
        </div>

        {/* Selected Preset indicator */}
        <div className="text-xs font-mono font-bold text-slate-700 bg-slate-100 px-3.5 py-1.5 rounded-xl border border-slate-200 self-start sm:self-auto shadow-2xs">
          Target: {PRESETS.find((p) => p.id === selectedPreset)?.dimensions}
        </div>
      </div>

      {/* Preset Selector Chips */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3.5">
        {PRESETS.map((p) => {
          const isSelected = selectedPreset === p.id;
          return (
            <button
              key={p.id}
              type="button"
              onClick={() => handlePresetChange(p.id)}
              className={`p-4 rounded-2xl border text-left transition-all flex flex-col justify-between gap-2.5 ${
                isSelected
                  ? "bg-indigo-50/90 border-indigo-500 text-slate-900 ring-2 ring-indigo-500/20 shadow-xs"
                  : "bg-slate-50 border-slate-200 hover:border-slate-300 text-slate-600 hover:text-slate-900"
              }`}
            >
              <div className="flex items-center justify-between w-full">
                <span className="font-bold text-sm tracking-tight text-slate-900">{p.title}</span>
                <span
                  className={`text-xs font-mono font-bold px-2 py-0.5 rounded-md ${
                    isSelected
                      ? "bg-indigo-600 text-white"
                      : "bg-slate-200 text-slate-700"
                  }`}
                >
                  {p.badge}
                </span>
              </div>
              <p className="text-xs text-slate-600 leading-relaxed font-medium">
                {p.description}
              </p>
            </button>
          );
        })}
      </div>

      {/* Drag & Drop Upload Zone */}
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
          accept="image/jpeg,image/png,image/webp"
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
            Drag & drop candidate photo, or <span className="text-indigo-600 underline underline-offset-4">browse</span>
          </p>
          <p className="text-xs text-slate-500">Supports JPEG, PNG, WebP (or paste from clipboard)</p>
        </div>
      </div>

      {errorMsg && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-sm font-medium flex items-center gap-2.5">
          <AlertCircle className="h-5 w-5 shrink-0 text-rose-600" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Before / After Preview Zone */}
      {(originalPreviewUrl || isProcessing) && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5 bg-slate-50 p-6 rounded-2xl border border-slate-200">
          {/* Original */}
          <div className="flex flex-col items-center gap-2.5">
            <span className="text-xs font-bold text-slate-600 uppercase tracking-wide">
              Original Upload
            </span>
            <div className="w-full h-64 rounded-xl bg-white border border-slate-200 flex items-center justify-center overflow-hidden p-3 shadow-2xs">
              {originalPreviewUrl ? (
                <img
                  src={originalPreviewUrl}
                  alt="Original"
                  className="max-h-full max-w-full object-contain rounded-lg"
                />
              ) : (
                <ImageIcon className="h-10 w-10 text-slate-300" />
              )}
            </div>
            {selectedFile && (
              <span className="text-xs font-mono text-slate-500 font-semibold">
                {(selectedFile.size / 1024).toFixed(1)} KB — Original
              </span>
            )}
          </div>

          {/* Processed Result */}
          <div className="flex flex-col items-center gap-2.5">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-slate-900 uppercase tracking-wide">
                Processed Spec Output
              </span>
              {isProcessing && <RefreshCw className="h-4 w-4 animate-spin text-indigo-600" />}
            </div>

            <div className="w-full h-64 rounded-xl bg-white border border-slate-200 flex items-center justify-center overflow-hidden p-3 relative shadow-2xs">
              {isProcessing ? (
                <div className="flex flex-col items-center gap-2.5 text-slate-600">
                  <RefreshCw className="h-7 w-7 animate-spin text-indigo-600" />
                  <span className="text-xs font-semibold">Compressing strictly to spec...</span>
                </div>
              ) : processedUrl ? (
                <img
                  src={processedUrl}
                  alt="Processed"
                  className="max-h-full max-w-full object-contain rounded-lg shadow-sm"
                />
              ) : (
                <span className="text-xs text-slate-400">Select an image to process</span>
              )}
            </div>

            {/* Compliance Badge & Download Action */}
            {processedSizeKb && (
              <div className="flex flex-col sm:flex-row items-center justify-between w-full gap-3 mt-1">
                <div className="flex items-center gap-2">
                  {isSizeCompliant() ? (
                    <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-mono font-bold shadow-2xs">
                      <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                      <span>{processedSizeKb} KB</span>
                      <span className="text-emerald-700 ml-0.5 font-normal">({processedDims})</span>
                    </div>
                  ) : (
                    <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-amber-50 border border-amber-200 text-amber-800 text-xs font-mono font-bold shadow-2xs">
                      <AlertCircle className="h-4 w-4 text-amber-600" />
                      <span>{processedSizeKb} KB</span>
                    </div>
                  )}
                </div>

                <button
                  type="button"
                  onClick={handleDownload}
                  className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold transition-all shadow-sm active:scale-95"
                >
                  <Download className="h-4 w-4" />
                  <span>Download Spec Photo</span>
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
