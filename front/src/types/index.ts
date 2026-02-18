export interface Instrument {
  symbol: string;
  name: string;
  exchange: string;
  category: string;
  image_url: string | null;
  notes: string | null;
}

export interface UserInstrument {
  instrument: string;
  name: string;
  exchange: string;
  image_url: string | null;
  added_at: string;
}

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

// --- Data blocks: typed content for panel rendering ---

export interface TableBlock {
  type: "table";
  columns: string[];
  rows: Record<string, unknown>[];
}

export interface BarChartBlock {
  type: "bar-chart";
  category_key: string;
  value_key: string;
  rows: Record<string, unknown>[];
}

export interface MetricsGridBlock {
  type: "metrics-grid";
  items: { label: string; value: string; color?: string }[];
}

export interface AreaChartBlock {
  type: "area-chart";
  x_key: string;
  series: { key: string; label: string; style: "line" | "area"; color?: string }[];
  data: Record<string, unknown>[];
}

export interface HorizontalBarBlock {
  type: "horizontal-bar";
  items: { label: string; value: number; detail?: string }[];
}

export type Block =
  | TableBlock
  | BarChartBlock
  | MetricsGridBlock
  | AreaChartBlock
  | HorizontalBarBlock;

export interface DataBlock {
  title: string;
  blocks: Block[];
  status?: "loading" | "success" | "error";
  error?: string;
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

// SSE streaming events from /api/chat/stream

export interface SSEToolStartEvent {
  tool_name: string;
  input: Record<string, unknown>;
}

export interface SSEToolEndEvent {
  tool_name: string;
  duration_ms: number;
  error: string | null;
}

export type SSEDataBlockEvent = DataBlock;

export interface SSETextDeltaEvent {
  delta: string;
}

export interface SSEDoneEvent {
  answer: string;
  usage: UsageBlock;
  tool_calls: ToolCall[];
  data: DataBlock[];
}

export interface SSEPersistEvent {
  message_id: string;
  persisted: boolean;
}

export interface SSETitleUpdateEvent {
  title: string;
}

export interface SSEErrorEvent {
  error: string;
}
