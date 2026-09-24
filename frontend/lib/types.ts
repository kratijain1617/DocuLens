export type AnswerStatus = "supported" | "partially_supported" | "conflicting_information" | "not_found";

export type User = {
  id: string;
  name: string;
  email: string;
  created_at: string;
  is_demo: boolean;
};

export type DocumentItem = {
  id: string;
  title: string;
  file_name: string;
  category: string;
  category_source: string;
  page_count: number;
  chunk_count: number;
  processing_status: string;
  error_message?: string | null;
  created_at: string;
  question_count: number;
  suggested_questions: string[];
  steps: { id: string; label: string }[];
};

export type Citation = {
  document_id: string;
  document_name: string;
  page_number: number;
  section: string;
  quoted_text: string;
  relevance_score: number;
};

export type RelatedSection = {
  document_id?: string;
  document_name: string;
  page_number: number;
  section: string;
};

export type AnswerRecord = {
  id?: string;
  question_id?: string;
  question: string;
  answer: string;
  explanation: string;
  confidence: number;
  answer_status: AnswerStatus;
  citations: Citation[];
  important_conditions: string[];
  related_sections: RelatedSection[];
  follow_up_questions: string[];
  created_at?: string;
};

export type SummaryPoint = { text: string; citation: Citation };

export type DocumentSummary = {
  document_id: string;
  document_name: string;
  title: string;
  category: string;
  one_sentence: string;
  detailed: string;
  topics: string[];
  important_dates: SummaryPoint[];
  important_numbers: SummaryPoint[];
  required_actions: SummaryPoint[];
  definitions: SummaryPoint[];
  risks_or_warnings: SummaryPoint[];
  missing_information: string[];
  suggested_questions: string[];
  citations: Citation[];
  answer_status: AnswerStatus;
};

export type CompareColumn = {
  document_id: string;
  document_name: string;
  title: string;
  category: string;
  summary: string;
  answer_status: AnswerStatus;
  confidence: number;
  citations: Citation[];
  important_conditions: string[];
};

export type EvidencePoint = {
  text: string;
  citations: Citation[];
  document_name?: string;
};

export type CompareResult = {
  question: string;
  answer: string;
  answer_status: AnswerStatus;
  confidence: number;
  summary: string;
  similarities: EvidencePoint[];
  differences: EvidencePoint[];
  conflicts: EvidencePoint[];
  documents: CompareColumn[];
  follow_up_questions: string[];
};

export type EvalItemResult = {
  question: string;
  expected_answer: string;
  expected_document: string;
  expected_page: number | null;
  expected_evidence: string;
  expected_status: string;
  answer?: string;
  answer_status?: string;
  confidence?: number;
  citations?: Citation[];
  answer_correct?: boolean;
  citation_correct?: boolean;
  page_correct?: boolean;
  grounded?: boolean;
  retrieval_hit?: boolean;
  unsupported?: boolean;
  response_time_ms?: number;
  error?: string;
};

export type EvalSummary = {
  answer_correctness: number;
  citation_correctness: number;
  correct_page_rate: number;
  citation_grounding_rate: number;
  retrieval_hit_rate: number;
  unsupported_answer_rate: number;
  average_response_time_ms: number;
  total: number;
};

export const DISCLAIMER =
  "DocuLens provides information based on uploaded documents. It is not legal, financial, medical, employment, or professional advice. Verify important decisions with the official source or a qualified professional.";

export const CATEGORIES = [
  "University document",
  "Research paper",
  "Rental agreement",
  "Policy or handbook",
  "Insurance document",
  "Technical manual",
  "Government form",
  "Business report",
  "Financial document",
  "Other",
];

export const STATUS_LABEL: Record<AnswerStatus, string> = {
  supported: "Supported",
  partially_supported: "Partially supported",
  conflicting_information: "Conflicting information",
  not_found: "Not found",
};
