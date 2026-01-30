export interface Message {
  id: string;
  conversation_id: string;
  role: "user" | "model";
  content: string;
  data: DataBlock[] | null;
  usage: UsageBlock | null;
  created_at: string;
}

export interface Conversation {
  id: string;
  title: string;
  instrument: string;
  usage: UsageBlock & { message_count: number };
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

export interface UsageBlock {
  input_tokens: number;
  output_tokens: number;
  thinking_tokens: number;
  cached_tokens: number;
  input_cost: number;
  output_cost: number;
  thinking_cost: number;
  total_cost: number;
}

export interface ToolCall {
  tool_name: string;
  input: Record<string, unknown> | null;
  output: unknown;
  error: string | null;
  duration_ms: number | null;
}

export interface ChatResponse {
  message_id: string;
  conversation_id: string;
  answer: string;
  data: DataBlock[];
  usage: UsageBlock;
  tool_calls: ToolCall[];
  persisted: boolean;
}
