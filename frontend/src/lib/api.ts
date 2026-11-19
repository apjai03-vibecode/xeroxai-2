import {
  BillingCalculationResponse,
  BiodataResponse,
  BiodataSchema,
  Order,
  OrderItem,
  OrderParseResponse,
  PhotoPreset,
  PricingConfig,
  QueueEstimateRequest,
  QueueEstimateResponse,
  SmartDocResponse,
  TelemetryData,
} from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
const API_BASE = API_BASE_URL;

// -------------------------------------------------------------
// 1. Photo Spec Engine
// -------------------------------------------------------------
export async function resizePhotoApi(
  file: File,
  preset: PhotoPreset
): Promise<{ blob: Blob; dimensions: string; sizeKb: string; preset: string }> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("preset", preset);

  const res = await fetch(`${API_BASE}/api/resize-photo/`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const errorText = await res.text();
    throw new Error(errorText || `Resize failed with status ${res.status}`);
  }

  const dimensions = res.headers.get("x-dimensions") || "Unknown";
  const sizeKb = res.headers.get("x-file-size-kb") || "0";
  const appliedPreset = res.headers.get("x-preset-applied") || preset;
  const blob = await res.blob();

  return { blob, dimensions, sizeKb, preset: appliedPreset };
}

// -------------------------------------------------------------
// 2. Biodata & Form Extractor
// -------------------------------------------------------------
export async function generateBiodataApi(rawText: string): Promise<BiodataResponse> {
  const res = await fetch(`${API_BASE}/api/generate-biodata/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ raw_text: rawText }),
  });

  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || "Biodata extraction failed");
  }

  return res.json();
}

export async function downloadBiodataPdfApi(schema: BiodataSchema): Promise<Blob> {
  const res = await fetch(`${API_BASE}/api/download-biodata-pdf/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(schema),
  });

  if (!res.ok) {
    throw new Error("Failed to download PDF");
  }

  return res.blob();
}

// -------------------------------------------------------------
// 3. Queue Estimator
// -------------------------------------------------------------
export async function estimateJobApi(
  req: QueueEstimateRequest
): Promise<QueueEstimateResponse> {
  const res = await fetch(`${API_BASE}/api/estimate-job/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });

  if (!res.ok) {
    throw new Error("Queue estimation failed");
  }

  return res.json();
}

// -------------------------------------------------------------
// 4. Telemetry
// -------------------------------------------------------------
export async function getTelemetryApi(): Promise<TelemetryData> {
  const res = await fetch(`${API_BASE}/api/telemetry/`, {
    cache: "no-store",
  });

  if (!res.ok) {
    throw new Error("Failed to fetch telemetry");
  }

  return res.json();
}

// -------------------------------------------------------------
// 5. SmartDoc AI Engine
// -------------------------------------------------------------
export async function enhanceDocumentApi(
  file: File,
  outputMode: "enhanced_color" | "clean_bw" = "enhanced_color",
  autoDeskew: boolean = true,
  autoPerspective: boolean = true,
  removeShadows: boolean = true
): Promise<SmartDocResponse> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("output_mode", outputMode);
  formData.append("auto_deskew", String(autoDeskew));
  formData.append("auto_perspective", String(autoPerspective));
  formData.append("remove_shadows", String(removeShadows));

  const res = await fetch(`${API_BASE}/api/smartdoc/enhance/`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || "SmartDoc document enhancement failed");
  }

  return res.json();
}

// -------------------------------------------------------------
// 6. Smart Billing & Shop Pricing (SQLite)
// -------------------------------------------------------------
export async function getPricingApi(): Promise<PricingConfig> {
  const res = await fetch(`${API_BASE}/api/pricing/`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch shop pricing");
  return res.json();
}

export async function updatePricingApi(config: PricingConfig): Promise<PricingConfig> {
  const res = await fetch(`${API_BASE}/api/pricing/`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(config),
  });
  if (!res.ok) throw new Error("Failed to update shop pricing");
  return res.json();
}

export async function calculateBillingApi(items: OrderItem[]): Promise<BillingCalculationResponse> {
  const res = await fetch(`${API_BASE}/api/billing/calculate/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ items }),
  });
  if (!res.ok) throw new Error("Failed to calculate billing");
  return res.json();
}

// -------------------------------------------------------------
// 7. AI Order Assistant
// -------------------------------------------------------------
export async function parseOrderAiApi(naturalText: string): Promise<OrderParseResponse> {
  const res = await fetch(`${API_BASE}/api/orders/parse-ai/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ natural_text: naturalText }),
  });
  if (!res.ok) throw new Error("AI order parsing failed");
  return res.json();
}

// -------------------------------------------------------------
// 8. Order Management (Persistent SQLite)
// -------------------------------------------------------------
export async function createOrderApi(orderData: {
  customer_name: string;
  customer_phone?: string;
  items: OrderItem[];
  notes?: string;
}): Promise<Order> {
  const res = await fetch(`${API_BASE}/api/orders/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(orderData),
  });
  if (!res.ok) throw new Error("Failed to create order");
  return res.json();
}

export async function getOrdersApi(status?: string, search?: string): Promise<Order[]> {
  const params = new URLSearchParams();
  if (status && status !== "All") params.append("status", status);
  if (search) params.append("search", search);

  const res = await fetch(`${API_BASE}/api/orders/?${params.toString()}`, {
    cache: "no-store",
  });
  if (!res.ok) throw new Error("Failed to fetch orders");
  return res.json();
}

export async function updateOrderStatusApi(
  orderId: string,
  newStatus: "Pending" | "Processing" | "Completed"
): Promise<Order> {
  const res = await fetch(`${API_BASE}/api/orders/${orderId}/status`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status: newStatus }),
  });
  if (!res.ok) throw new Error("Failed to update order status");
  return res.json();
}
