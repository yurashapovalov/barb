export interface Message {
  id: string;
  conversation_id: string;
  role: "user" | "model";
  content: string;
  data: DataBlock[] | null;
  cost: CostBlock | null;
  created_at: string;
}

export interface Conversation {
  id: string;
  title: string;
  instrument: string;
  created_at: string;
  updated_at: string;
}

export interface DataBlock {
  query: Record<string, unknown>;
  result: unknown;
  rows: number | null;
  session: string | null;
  timeframe: string | null;
}

export interface CostBlock {
  input_tokens: number;
  output_tokens: number;
  thinking_tokens: number;
  cached_tokens: number;
  input_cost: number;
  output_cost: number;
  thinking_cost: number;
  total_cost: number;
}

export interface ChatResponse {
  answer: string;
  data: DataBlock[];
  cost: CostBlock;
}
