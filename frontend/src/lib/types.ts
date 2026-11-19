export type PhotoPreset = "tnpsc_upsc" | "passport_standard" | "signature";

export interface PresetInfo {
  id: PhotoPreset;
  title: string;
  badge: string;
  dimensions: string;
  sizeLimit: string;
  description: string;
}

export interface BiodataRequest {
  raw_text: string;
}

export interface BiodataSchema {
  full_name: string;
  dob: string;
  qualification: string;
  contact: string;
  email: string;
  address: string;
  skills: string[];
  languages: string[];
}

export interface BiodataResponse {
  extracted_data: BiodataSchema;
  is_fallback: boolean;
  model_used: string;
  pdf_base64?: string;
  processing_time_ms: number;
}

export interface QueueEstimateRequest {
  page_count: number;
  is_color: boolean;
  needs_lamination: boolean;
  current_queue_customers: number;
}

export interface QueuePriceBreakdown {
  printing_fee: number;
  lamination_fee: number;
  rush_buffer: number;
  total_fee: number;
  currency: string;
}

export interface QueueEstimateResponse {
  estimated_wait_minutes: number;
  price_breakdown: QueuePriceBreakdown;
  model_info: {
    engine: string;
    architecture: string;
    status: string;
  };
  processing_time_ms: number;
}

export interface TelemetrySpan {
  op: string;
  description: string;
  duration_ms: number;
  status: string;
  tags: Record<string, string>;
  data: Record<string, string>;
  timestamp: number;
}

export interface TelemetryData {
  recent_spans: TelemetrySpan[];
  tabpfn_status: {
    engine: string;
    is_native: boolean;
  };
  gemma_status: {
    model: string;
    ollama_endpoint: string;
  };
}

// ============================================================
// XeroxAI 2.0 Types: SmartDoc, Billing, Orders, AI Assistant
// ============================================================

export interface SmartDocResponse {
  filename: string;
  is_pdf: boolean;
  width: number;
  height: number;
  blur_score: number;
  is_blurry: boolean;
  detected_skew_deg: number;
  perspective_corrected: boolean;
  shadows_removed: boolean;
  output_mode: string;
  reliability_notes: string[];
  original_preview_base64: string;
  processed_preview_base64: string;
  processing_time_ms: number;
}

export interface PricingConfig {
  bw_single: number;
  bw_double: number;
  color_single: number;
  color_double: number;
  a3_multiplier: number;
  legal_multiplier: number;
  letter_multiplier: number;
  lamination_a4: number;
  lamination_a3: number;
  updated_at?: string;
}

export interface OrderItem {
  page_count: number;
  is_color: boolean;
  is_double_sided: boolean;
  paper_size: "A4" | "A3" | "Legal" | "Letter" | string;
  copies: number;
  needs_lamination: boolean;
  description?: string;
  unit_rate?: number;
  print_cost?: number;
  lamination_cost?: number;
  subtotal?: number;
}

export interface BillingCalculationResponse {
  items: OrderItem[];
  total_sheets: number;
  grand_total: number;
  currency: string;
}

export interface Order {
  id: number;
  order_id: string;
  customer_name: string;
  customer_phone: string;
  items: OrderItem[];
  total_amount: number;
  status: "Pending" | "Processing" | "Completed" | string;
  notes: string;
  created_at: string;
  updated_at: string;
}

export interface OrderParseResponse {
  parsed_order: {
    customer_name: string;
    customer_phone: string;
    page_count: number;
    is_color: boolean;
    is_double_sided: boolean;
    paper_size: string;
    copies: number;
    needs_lamination: boolean;
    notes: string;
  };
  is_fallback: boolean;
  model_used: string;
  calculated_billing: BillingCalculationResponse;
}
