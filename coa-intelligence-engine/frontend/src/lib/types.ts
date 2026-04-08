// ─── Validation status ────────────────────────────────────────────────────────

export type ValidationStatus = "PASS" | "WARNING" | "FAIL" | "REVIEW" | "ERROR";
export type SubmissionStatus = "pending" | "processing" | "completed" | "failed";

// ─── API response envelope ────────────────────────────────────────────────────

export interface ApiResponse<T> {
  data: T | null;
  error: { code: string; message: string } | null;
}

// ─── Upload ───────────────────────────────────────────────────────────────────

export interface UploadResponse {
  submission_id: string;
  filename: string;
  status: SubmissionStatus;
  file_size_bytes: number;
}

// ─── Status polling ───────────────────────────────────────────────────────────

export interface StatusResponse {
  submission_id: string;
  status: SubmissionStatus;
  page_count: number | null;
  pages_processed: number;
  error_message: string | null;
}

// ─── Result ───────────────────────────────────────────────────────────────────

export interface CoAHeader {
  product_name: string | null;
  product_grade: string | null;
  supplier_name: string | null;
  batch_number: string | null;
  manufacture_date: string | null;
  expiry_date: string | null;
  coa_number: string | null;
  header_confidence: number | null;
  extraction_notes: string | null;
}

export interface ParameterResult {
  id: string;
  submission_id: string;
  parameter_name: string;
  method_reference: string | null;
  result_value: string;
  result_unit: string | null;
  specification_limit: string | null;
  coa_pass_fail: string | null;
  extraction_confidence: number;
  validation_status: ValidationStatus;
  margin_from_boundary: number | null;
  spec_parameter_id: string | null;
  is_quantitative: boolean;
  validation_notes: string | null;
  created_at: string;
}

export interface CoAResult {
  submission: {
    id: string;
    original_filename: string;
    status: SubmissionStatus;
    page_count: number | null;
    created_at: string;
  };
  header: CoAHeader | null;
  parameters: ParameterResult[];
  overall_status: ValidationStatus;
  parameter_count: number;
  matched_product_id: string | null;
}

// ─── Sidebar ──────────────────────────────────────────────────────────────────

export interface SubmissionSummary {
  id: string;
  original_filename: string;
  status: SubmissionStatus;
  created_at: string;
  matched_product_id: string | null;
}
