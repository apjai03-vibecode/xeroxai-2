"use client";

import React, { useState } from "react";
import {
  FileText,
  Sparkles,
  Download,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Edit3,
  User,
  Calendar,
  GraduationCap,
  Phone,
  Mail,
  MapPin,
  Languages,
  CheckSquare,
} from "lucide-react";
import { BiodataSchema, BiodataResponse } from "../lib/types";
import { generateBiodataApi, downloadBiodataPdfApi } from "../lib/api";

const SAMPLE_WHATSAPP_NOTES = `Name: Karthikeyan M
DOB: 18/06/1999
Completed B.E Mechanical Engineering from PSG Tech (8.2 CGPA)
Mobile: 9443219870
Email: karthi.mech99@gmail.com
Address: 45 Bharathiyar Street, Gandhipuram, Coimbatore - 641012
Skills: AutoCAD, SolidWorks, CNC Programming, MS Excel, Industrial Safety
Languages: Tamil, English, Malayalam`;

const SAMPLE_SCRAWLED_NOTES = `Candidate: Priya Sundaram
Born: 14-03-2001
B.Com Computer Applications first class
Ph 9841029384
Email: priya.sundar2001@outlook.com
Residing at No 8, North Usman Road, T Nagar Chennai 600017
Skills known: Tally ERP 9, GST Billing, Fast English Typing 40wpm, Office tools
Can speak: English, Tamil, Telugu`;

export function BiodataEngine({ onProcessed }: { onProcessed?: () => void }) {
  const [rawText, setRawText] = useState("");
  const [isExtracting, setIsExtracting] = useState(false);
  const [extractedData, setExtractedData] = useState<BiodataSchema | null>(null);
  const [isFallback, setIsFallback] = useState(false);
  const [modelUsed, setModelUsed] = useState<string | null>(null);
  const [pdfBase64, setPdfBase64] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isDownloadingPdf, setIsDownloadingPdf] = useState(false);

  const handleExtract = async () => {
    if (!rawText.trim()) {
      setErrorMsg("Please enter or paste raw customer notes first.");
      return;
    }
    setErrorMsg(null);
    setIsExtracting(true);
    try {
      const res: BiodataResponse = await generateBiodataApi(rawText);
      setExtractedData(res.extracted_data);
      setIsFallback(res.is_fallback);
      setModelUsed(res.model_used);
      if (res.pdf_base64) {
        setPdfBase64(res.pdf_base64);
      }
      if (onProcessed) onProcessed();
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to extract biodata.");
    } finally {
      setIsExtracting(false);
    }
  };

  const handleFieldChange = (field: keyof BiodataSchema, value: any) => {
    if (!extractedData) return;
    setExtractedData({
      ...extractedData,
      [field]: value,
    });
  };

  const handleDownloadPdf = async () => {
    if (!extractedData) return;
    setIsDownloadingPdf(true);
    try {
      const blob = await downloadBiodataPdfApi(extractedData);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${(extractedData.full_name || "Biodata").replace(/\s+/g, "_")}_A4.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err: any) {
      setErrorMsg("Failed to download PDF.");
    } finally {
      setIsDownloadingPdf(false);
    }
  };

  const loadSample = (sample: string) => {
    setRawText(sample);
    setErrorMsg(null);
  };

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-6 sm:p-8 shadow-sm flex flex-col gap-6">
      {/* Card Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div className="flex items-center gap-3.5">
          <div className="p-3 rounded-xl bg-blue-50 text-blue-600 border border-blue-100 shadow-2xs">
            <FileText className="h-6 w-6 stroke-[2.2]" />
          </div>
          <div>
            <div className="flex items-center gap-2.5">
              <h2 className="text-xl sm:text-2xl font-black text-slate-900 tracking-tight">
                Instant A4 Biodata Maker
              </h2>
              <span className="px-2.5 py-1 text-xs font-mono font-bold bg-blue-50 text-blue-700 border border-blue-200 rounded-lg">
                Gemma 2:2B + ReportLab
              </span>
            </div>
            <p className="text-sm text-slate-500 font-medium mt-0.5">
              Structured field extraction via Google Gemma 2:2B & ReportLab print-ready PDF generator.
            </p>
          </div>
        </div>

        {/* Quick Sample Buttons */}
        <div className="flex items-center gap-2 self-start sm:self-auto">
          <button
            type="button"
            onClick={() => loadSample(SAMPLE_WHATSAPP_NOTES)}
            className="text-xs px-3.5 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-800 font-semibold border border-slate-300 transition-colors shadow-2xs"
          >
            Load WhatsApp Paste
          </button>
          <button
            type="button"
            onClick={() => loadSample(SAMPLE_SCRAWLED_NOTES)}
            className="text-xs px-3.5 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-800 font-semibold border border-slate-300 transition-colors shadow-2xs"
          >
            Load Scrawled Notes
          </button>
        </div>
      </div>

      {/* Main Grid: Input & Output */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column: Raw Input */}
        <div className="flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <label className="text-xs font-bold text-slate-700 uppercase tracking-wide flex items-center gap-2">
              <span>Customer Raw Notes / Text Paste</span>
            </label>
            <span className="text-xs text-slate-500 font-mono font-semibold">
              {rawText.length} characters
            </span>
          </div>

          <textarea
            rows={10}
            value={rawText}
            onChange={(e) => setRawText(e.target.value)}
            placeholder="Paste rough customer WhatsApp message, scrawled resume points, or candidate notes here..."
            className="w-full rounded-2xl bg-slate-50 border border-slate-300 focus:bg-white focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 p-4 text-sm text-slate-900 placeholder-slate-400 font-mono transition-all resize-y outline-none shadow-2xs"
          />

          <button
            type="button"
            disabled={isExtracting || !rawText.trim()}
            onClick={handleExtract}
            className="w-full flex items-center justify-center gap-2.5 py-3.5 px-6 rounded-xl bg-indigo-600 hover:bg-indigo-700 active:bg-indigo-800 text-white font-bold text-sm transition-all shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isExtracting ? (
              <>
                <RefreshCw className="h-4 w-4 animate-spin" />
                <span>Extracting with Local Gemma 2:2B...</span>
              </>
            ) : (
              <>
                <Sparkles className="h-4 w-4" />
                <span>Extract & Preview Biodata</span>
              </>
            )}
          </button>

          {errorMsg && (
            <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-sm font-medium flex items-center gap-2.5">
              <AlertCircle className="h-5 w-5 shrink-0 text-rose-600" />
              <span>{errorMsg}</span>
            </div>
          )}
        </div>

        {/* Right Column: Structured Live Preview */}
        <div className="flex flex-col gap-4 bg-slate-50 p-5 rounded-2xl border border-slate-200">
          <div className="flex items-center justify-between border-b border-slate-200 pb-3">
            <span className="text-xs font-bold text-slate-900 uppercase tracking-wide flex items-center gap-2">
              <Edit3 className="h-4 w-4 text-indigo-600" />
              <span>Structured Field Review</span>
            </span>

            {modelUsed && (
              <span
                className={`text-xs font-mono font-bold px-2.5 py-0.5 rounded-full border ${
                  isFallback
                    ? "bg-amber-50 text-amber-800 border-amber-300"
                    : "bg-blue-50 text-blue-800 border-blue-300"
                }`}
              >
                {modelUsed}
              </span>
            )}
          </div>

          {extractedData ? (
            <div className="flex flex-col gap-3 text-xs">
              {/* Name & DOB */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-bold text-slate-700 flex items-center gap-1.5 mb-1">
                    <User className="h-3.5 w-3.5 text-slate-500" /> Full Name
                  </label>
                  <input
                    type="text"
                    value={extractedData.full_name}
                    onChange={(e) => handleFieldChange("full_name", e.target.value)}
                    className="w-full bg-white border border-slate-300 focus:border-indigo-500 rounded-lg px-3 py-2 text-slate-900 font-medium text-xs"
                  />
                </div>
                <div>
                  <label className="text-xs font-bold text-slate-700 flex items-center gap-1.5 mb-1">
                    <Calendar className="h-3.5 w-3.5 text-slate-500" /> Date of Birth
                  </label>
                  <input
                    type="text"
                    value={extractedData.dob}
                    onChange={(e) => handleFieldChange("dob", e.target.value)}
                    className="w-full bg-white border border-slate-300 focus:border-indigo-500 rounded-lg px-3 py-2 text-slate-900 font-medium text-xs"
                  />
                </div>
              </div>

              {/* Qualification */}
              <div>
                <label className="text-xs font-bold text-slate-700 flex items-center gap-1.5 mb-1">
                  <GraduationCap className="h-3.5 w-3.5 text-slate-500" /> Highest Qualification
                </label>
                <input
                  type="text"
                  value={extractedData.qualification}
                  onChange={(e) => handleFieldChange("qualification", e.target.value)}
                  className="w-full bg-white border border-slate-300 focus:border-indigo-500 rounded-lg px-3 py-2 text-slate-900 font-medium text-xs"
                />
              </div>

              {/* Contact & Email */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-bold text-slate-700 flex items-center gap-1.5 mb-1">
                    <Phone className="h-3.5 w-3.5 text-slate-500" /> Phone Number
                  </label>
                  <input
                    type="text"
                    value={extractedData.contact}
                    onChange={(e) => handleFieldChange("contact", e.target.value)}
                    className="w-full bg-white border border-slate-300 focus:border-indigo-500 rounded-lg px-3 py-2 text-slate-900 font-medium text-xs"
                  />
                </div>
                <div>
                  <label className="text-xs font-bold text-slate-700 flex items-center gap-1.5 mb-1">
                    <Mail className="h-3.5 w-3.5 text-slate-500" /> Email Address
                  </label>
                  <input
                    type="text"
                    value={extractedData.email}
                    onChange={(e) => handleFieldChange("email", e.target.value)}
                    className="w-full bg-white border border-slate-300 focus:border-indigo-500 rounded-lg px-3 py-2 text-slate-900 font-medium text-xs"
                  />
                </div>
              </div>

              {/* Address */}
              <div>
                <label className="text-xs font-bold text-slate-700 flex items-center gap-1.5 mb-1">
                  <MapPin className="h-3.5 w-3.5 text-slate-500" /> Address
                </label>
                <input
                  type="text"
                  value={extractedData.address}
                  onChange={(e) => handleFieldChange("address", e.target.value)}
                  className="w-full bg-white border border-slate-300 focus:border-indigo-500 rounded-lg px-3 py-2 text-slate-900 font-medium text-xs"
                />
              </div>

              {/* Skills Tags */}
              <div>
                <label className="text-xs font-bold text-slate-700 flex items-center gap-1.5 mb-1">
                  <CheckSquare className="h-3.5 w-3.5 text-slate-500" /> Skills (comma separated)
                </label>
                <input
                  type="text"
                  value={extractedData.skills.join(", ")}
                  onChange={(e) =>
                    handleFieldChange(
                      "skills",
                      e.target.value.split(",").map((s) => s.trim()).filter(Boolean)
                    )
                  }
                  className="w-full bg-white border border-slate-300 focus:border-indigo-500 rounded-lg px-3 py-2 text-slate-900 font-medium text-xs"
                />
              </div>

              {/* Languages */}
              <div>
                <label className="text-xs font-bold text-slate-700 flex items-center gap-1.5 mb-1">
                  <Languages className="h-3.5 w-3.5 text-slate-500" /> Languages (comma separated)
                </label>
                <input
                  type="text"
                  value={extractedData.languages.join(", ")}
                  onChange={(e) =>
                    handleFieldChange(
                      "languages",
                      e.target.value.split(",").map((s) => s.trim()).filter(Boolean)
                    )
                  }
                  className="w-full bg-white border border-slate-300 focus:border-indigo-500 rounded-lg px-3 py-2 text-slate-900 font-medium text-xs"
                />
              </div>

              {/* Download Ready-to-Print PDF Button */}
              <div className="pt-2">
                <button
                  type="button"
                  disabled={isDownloadingPdf}
                  onClick={handleDownloadPdf}
                  className="w-full flex items-center justify-center gap-2.5 py-3 px-6 rounded-xl bg-emerald-600 hover:bg-emerald-700 active:bg-emerald-800 text-white font-bold text-xs transition-all shadow-sm"
                >
                  {isDownloadingPdf ? (
                    <RefreshCw className="h-4 w-4 animate-spin" />
                  ) : (
                    <Download className="h-4 w-4" />
                  )}
                  <span>Generate & Download Print-Ready A4 PDF</span>
                </button>
              </div>
            </div>
          ) : (
            <div className="h-72 flex flex-col items-center justify-center text-slate-400 gap-3">
              <FileText className="h-12 w-12 stroke-[1.5] text-slate-300" />
              <p className="text-sm font-medium">Paste customer notes and click Extract</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
