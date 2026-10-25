export type NodeType = "Symptom" | "RootCause" | "Verification" | "Command" | "Remediation";

export interface GraphNode {
  id: string;
  label: string;
  type: NodeType;
  description?: string;
  details?: Record<string, any>;
  x?: number;
  y?: number;
  vx?: number;
  vy?: number;
  fx?: number;
  fy?: number;
}

export interface GraphLink {
  source: string | GraphNode;
  target: string | GraphNode;
  relationship?: string;
  description?: string;
}

export interface GraphData {
  nodes: GraphNode[];
  links: GraphLink[];
  layout?: string;
}

export interface TraceEvent {
  step: string;
  title: string;
  status: "in_progress" | "success" | "error";
  message?: string;
  command?: string;
  host?: string;
  raw_output?: string;
  parsed_output?: any;
  remediation_lines?: string[];
  remediation_text?: string;
  start_node?: string;
  paths?: Array<{ path: string[]; steps: Array<{ id: string; label: string; type: string }> }>;
  matched_subgraph?: GraphData;
  system_prompt?: string;
  dynamic_context?: any;
  llm_messages?: any[];
  session_id?: string;
  json_log_path?: string;
  text_log_path?: string;
  used_batfish_apis?: string[];
  timestamp: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: string;
  traceEvents?: TraceEvent[];
}

export interface LLMConfig {
  base_url: string;
  api_key: string;
  model: string;
}

export interface DeviceConfig {
  host: string;
  port: number;
  username: string;
  password?: string;
  enable_password?: string;
}

export interface ManagedDevice {
  id: string;
  name: string;
  host: string;
  port?: number;
  username?: string;
  password?: string;
  enable_password?: string;
  description?: string;
}

export interface AppConfig {
  llm: LLMConfig;
  device: DeviceConfig;
  debug_mode?: boolean;
}
