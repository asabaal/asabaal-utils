export interface MemoryItem {
  id: string;
  title: string;
  content: string;
  tags: string[];
  status: "active" | "archived";
  created_at: string;
  updated_at: string;
  provenance?: Record<string, any>;
}

export interface MemoryCreate {
  title: string;
  content: string;
  tags: string[];
}

export interface MemoryUpdate {
  title?: string;
  content?: string;
  tags?: string[];
  status?: "active" | "archived";
}

export interface UsedMemory {
  id: string;
  title: string;
  score: number;
  source_type?: "user_provided" | "chatbot_response" | "system_knowledge";
  tags: string[];
}

export interface ChatRequest {
  message: string;
  max_tokens?: number;
  model?: string;
  temperature?: number;
}

export interface ChatResponse {
  text: string;
  used_memory: UsedMemory[];
}

export interface ChatTurn {
  id: string;
  ts: string;
  user_text: string;
  model_text: string;
  memory_hits: UsedMemory[];
  prompt_meta: Record<string, any>;
}