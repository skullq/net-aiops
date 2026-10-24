export type NodeType = "Symptom" | "RootCause" | "Verification" | "Command";

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
}

export interface TraceEvent {
  step: string;
  title: string;
  status: "in_progress" | "success" | "error";
  message?: string;
  command?: string;
  host?: string;
  mock_mode?: boolean;
  raw_output?: string;
  parsed_output?: any;
  remediation_lines?: string[];
  remediation_text?: string;
  start_node?: string;
  paths?: Array<{ path: string[]; steps: Array<{ id: string; label: string; type: string }> }>;
  matched_subgraph?: GraphData;
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
  mock_mode: boolean;
}

export interface ManagedDevice {
  id: string;
  name: string;
  host: string;
  port?: number;
  username?: string;
  password?: string;
  enable_password?: string;
  mock_mode?: boolean;
  description?: string;
}

export interface AppConfig {
  llm: LLMConfig;
  device: DeviceConfig;
}
