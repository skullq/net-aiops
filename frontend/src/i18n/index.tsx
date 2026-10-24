"use client";

import React, { createContext, useContext, useState, useEffect } from "react";

export type Language = "ko" | "en";

export const translations = {
  ko: {
    common: {
      cancel: "취소",
      confirm: "확인",
      save: "저장",
      saved: "저장 완료!",
      delete: "삭제",
      edit: "수정",
      close: "닫기",
      clear: "지우기",
      reset: "초기화",
      loading: "로딩 중...",
      error: "오류",
      success: "성공",
      live: "LIVE",
      mock: "MOCK",
      all: "전체",
    },
    header: {
      title: "Net-AIOps Studio",
      subtitle: "Causal GraphDB & Cisco IOS-XE MCP Operations",
      tabDiagnostics: "AIOps 통합 진단 워크스페이스",
      tabGraphStudio: "Graph Causal Studio",
      fastapiLive: "FastAPI 연결됨",
      fastapiOffline: "FastAPI 오프라인",
      networkDevices: "네트워크 장비",
      alwaysConnected: "상시 접속",
      deviceCountUnit: "대",
      resetGraph: "초기화",
      resetTitle: "인과 그래프 기본 시나리오로 초기화",
      llmSettings: "LLM 설정",
      deviceManagerTooltip: "네트워크 장비 관리 (devices.env & devices.json)",
      langKo: "한국어",
      langEn: "English",
    },
    chat: {
      title: "통합 AI 진단 채팅 (Net-AIOps Agent)",
      clearHistory: "대화 내역 초기화",
      emptyTitle: "Net-AIOps 지능형 네트워크 진단",
      emptyDesc:
        "NetworkX Causal Graph와 Cisco IOS-XE Scrapli/hier-config MCP 도구를 기반으로 자율적인 근본 원인 분석과 교정 CLI를 제공합니다.",
      quickScenarios: "추천 진단 시나리오:",
      quick1Title: "BGP Neighbor Down 진단",
      quick1Prompt:
        "BGP 피어 192.168.10.2가 Down 상태입니다. 인과 그래프와 show 명령어로 원인을 분석하고 복구 명령을 생성해줘.",
      quick2Title: "OSPF Stuck in ExStart 점검",
      quick2Prompt:
        "OSPF 네이버가 EXSTART 단계에서 멈춰있습니다. MTU 및 인접 상태를 점검하고 해결책을 제시해줘.",
      quick3Title: "인터페이스 CRC Drop 분석",
      quick3Prompt:
        "GigabitEthernet1 인터페이스에 패킷 드롭 및 Input Error가 발생합니다. 원인 분석과 Remediation을 작성해줘.",
      runDiagnostic: "진단 실행 →",
      inputPlaceholder:
        "네트워크 장애 증상이나 명령어를 입력하세요... (예: OSPF 인접관계 불일치 진단)",
      send: "전송",
      streaming: "분석 중...",
      copy: "복사",
      copied: "복사됨",
      apiFailError:
        "⚠️ 백엔드 API 연결에 실패하였습니다. 백엔드 서버(FastAPI)가 실행 중인지 확인해 주세요.",
    },
    trace: {
      title: "실시간 진단 Trace & MCP 뷰어",
      liveBadge: "LIVE",
      clear: "지우기",
      emptyTitle: "실시간 Trace 대기 중",
      emptyDesc:
        "AI 채팅창에 진단 질문을 전송하면 GraphDB 탐색, Scrapli 실행 상태 및 원시 JSON 파싱 결과가 타임라인으로 스트리밍됩니다.",
      successBadge: "성공",
      failedBadge: "실패",
      parsedOutput: "TextFSM 구조화 파싱 데이터 (JSON):",
      rawCliOutput: "Cisco CLI 원시 터미널 출력:",
      remediationScript: "hier-config 도출 복구 설정 스크립트:",
      graphPaths: "탐색된 인과 관계 경로 (Causal Path):",
      collapse: "접기",
      expand: "상세 보기",
    },
    graph: {
      canvasLoading: "Causal Graph Studio 캔버스 로딩 중...",
      searchPlaceholder: "노드 ID, 라벨, 설명 검색...",
      filterAll: "모든 노드 타입",
      symptom: "증상 (Symptom)",
      rootCause: "근본 원인 (RootCause)",
      verification: "검증 단계 (Verification)",
      command: "실행 명령어 (Command)",
      nodesCount: "개 노드",
      edgesCount: "개 엣지",
      addNode: "노드 추가",
      addEdge: "엣지 연결",
      resetGraph: "기본값 초기화",
      fitView: "화면 맞춤",
      nodeDetails: "노드 상세 정보",
      selectNodeGuide:
        "캔버스의 노드를 클릭하면 인과 관계 및 상세 속성을 확인할 수 있습니다.",
      nodeType: "타입",
      nodeLabel: "라벨",
      nodeDesc: "설명",
      causeNodes: "선행 유발 요인 (Incoming Causes)",
      effectNodes: "후속 전파 영향 (Outgoing Effects)",
      noIncoming: "선행 유발 요인 없음 (최상위 증상/원인)",
      noOutgoing: "후속 전파 영향 없음 (최종 조치/명령어)",
      deleteNode: "노드 삭제",
      modalAddNodeTitle: "새 인과 노드 등록",
      modalAddEdgeTitle: "새 인과 관계 엣지 추가",
      nodeId: "노드 ID (고유 식별자)",
      nodeLabelLabel: "노드 라벨 (표시명)",
      nodeDescLabel: "설명 (선택)",
      sourceNode: "출발 노드 (Source)",
      targetNode: "도착 노드 (Target)",
      relationshipType: "관계 유형",
      relLeadsTo: "leads_to (유발함)",
      relVerifiedBy: "verified_by (검증됨)",
      relFixedBy: "fixed_by (해결됨)",
      relExecutes: "executes (실행함)",
      legend: "범례 (Legend):",
    },
    deviceManager: {
      modalTitle: "네트워크 장비 관리",
      registeredCount: "대 등록됨",
      guideBanner:
        "접속정보는 기본설정(admin / admin, 포트 22)을 따르며, 개별 장비에 별도 설정이 있으면 개별 설정이 우선 적용됩니다.",
      inventoryTitle: "상시 접근 가능 장비 목록",
      addDevice: "장비 추가",
      closeForm: "닫기",
      newDeviceTitle: "새 장비 추가 등록",
      editDeviceTitle: "설정 변경",
      deviceName: "장비명",
      deviceHost: "IP 주소",
      username: "계정명",
      usernameHint: "비워둘 시 admin",
      password: "비밀번호",
      passwordHint: "비워둘 시 admin",
      port: "SSH 포트",
      mockModeLabel: "Mock 시뮬레이션 모드로 등록",
      mockModeEdit: "Mock 모드",
      register: "등록",
      save: "저장",
      cancel: "취소",
      close: "닫기",
      liveBadge: "LIVE SSH",
      mockBadge: "MOCK",
      editTooltip: "설정 변경",
      deleteTooltip: "장비 삭제",
      userLabel: "계정",
    },
    settings: {
      modalTitle: "연결 환경 설정 (Settings)",
      modalDesc: "LLM Provider 및 Cisco IOS-XE 장비 연결 정보를 구성합니다.",
      llmSectionTitle: "LLM Provider 설정 (OpenAI 호환)",
      baseUrl: "Base URL",
      apiKey: "API Key",
      apiKeyHint: "* 비워둘 경우 내장 지능형 분석 엔진이 자동 가동됩니다.",
      modelName: "Model 명",
      geminiGuideTitle: "Google Gemini OpenAI 호환 엔드포인트 안내",
      geminiGuideDesc:
        "Gemini 2.5 Flash를 사용할 경우 Base URL을 https://generativelanguage.googleapis.com/v1beta/openai 로 지정하고 Gemini API Key를 입력하세요.",
      deviceSectionTitle: "Cisco IOS-XE 기본 장비 설정 (devices.env)",
      deviceHost: "호스트 IP",
      devicePort: "SSH 포트",
      deviceUser: "SSH 계정",
      devicePass: "SSH 비밀번호",
      enablePass: "Enable 비밀번호",
      enablePassHint: "* 필요 시 입력",
      mockModeToggle: "Cisco 장비 Mock 시뮬레이션 모드 사용",
      mockModeDesc:
        "활성화 시 실제 SSH 장비 연결 없이 가상 Cisco IOS-XE 응답 데이터셋으로 동작합니다.",
      saveSettings: "설정 저장하기",
      saved: "저장 완료!",
      cancel: "취소",
    },
  },
  en: {
    common: {
      cancel: "Cancel",
      confirm: "Confirm",
      save: "Save",
      saved: "Saved!",
      delete: "Delete",
      edit: "Edit",
      close: "Close",
      clear: "Clear",
      reset: "Reset",
      loading: "Loading...",
      error: "Error",
      success: "Success",
      live: "LIVE",
      mock: "MOCK",
      all: "All",
    },
    header: {
      title: "Net-AIOps Studio",
      subtitle: "Causal GraphDB & Cisco IOS-XE MCP Operations",
      tabDiagnostics: "AIOps Unified Diagnostics Workspace",
      tabGraphStudio: "Graph Causal Studio",
      fastapiLive: "FastAPI Live",
      fastapiOffline: "FastAPI Offline",
      networkDevices: "Network Devices",
      alwaysConnected: "Online",
      deviceCountUnit: "devs",
      resetGraph: "Reset",
      resetTitle: "Reset Causal Graph to default scenarios",
      llmSettings: "LLM Settings",
      deviceManagerTooltip: "Manage Network Devices (devices.env & devices.json)",
      langKo: "한국어",
      langEn: "English",
    },
    chat: {
      title: "Unified AI Diagnostic Chat (Net-AIOps Agent)",
      clearHistory: "Clear chat history",
      emptyTitle: "Net-AIOps Intelligent Network Diagnostics",
      emptyDesc:
        "Provides autonomous root-cause analysis and remediation CLI based on NetworkX Causal Graph and Cisco IOS-XE Scrapli/hier-config MCP tools.",
      quickScenarios: "Recommended Diagnostic Scenarios:",
      quick1Title: "BGP Neighbor Down Diagnostics",
      quick1Prompt:
        "BGP peer 192.168.10.2 is Down. Analyze the root cause using the causal graph and show commands, and generate recovery commands.",
      quick2Title: "OSPF Stuck in ExStart Check",
      quick2Prompt:
        "OSPF neighbor is stuck in EXSTART state. Check MTU and adjacency status, and provide a resolution.",
      quick3Title: "Interface CRC Drop Analysis",
      quick3Prompt:
        "Packet drops and input errors are occurring on GigabitEthernet1. Provide root-cause analysis and remediation CLI.",
      runDiagnostic: "Run Diagnostic →",
      inputPlaceholder:
        "Enter network symptom or command... (e.g. Diagnose OSPF adjacency mismatch)",
      send: "Send",
      streaming: "Analyzing...",
      copy: "Copy",
      copied: "Copied",
      apiFailError:
        "⚠️ Failed to connect to backend API. Please make sure the FastAPI backend is running.",
    },
    trace: {
      title: "Real-time Diagnostic Trace & MCP Viewer",
      liveBadge: "LIVE",
      clear: "Clear",
      emptyTitle: "Awaiting Real-time Trace",
      emptyDesc:
        "When you send a diagnostic query in chat, GraphDB traversal, Scrapli CLI execution, and raw JSON parsing stream here in real time.",
      successBadge: "Success",
      failedBadge: "Failed",
      parsedOutput: "TextFSM Structured Parsing Data (JSON):",
      rawCliOutput: "Cisco CLI Raw Terminal Output:",
      remediationScript: "hier-config Derived Remediation Script:",
      graphPaths: "Traversed Causal Path:",
      collapse: "Collapse",
      expand: "Expand",
    },
    graph: {
      canvasLoading: "Loading Causal Graph Studio Canvas...",
      searchPlaceholder: "Search node ID, label, description...",
      filterAll: "All Node Types",
      symptom: "Symptom",
      rootCause: "RootCause",
      verification: "Verification",
      command: "Command",
      nodesCount: "nodes",
      edgesCount: "edges",
      addNode: "Add Node",
      addEdge: "Add Edge",
      resetGraph: "Reset Graph",
      fitView: "Fit View",
      nodeDetails: "Node Details",
      selectNodeGuide:
        "Click any node on the canvas to inspect its causal relations and properties.",
      nodeType: "Type",
      nodeLabel: "Label",
      nodeDesc: "Description",
      causeNodes: "Incoming Causes",
      effectNodes: "Outgoing Effects",
      noIncoming: "No incoming causes (Root symptom/cause)",
      noOutgoing: "No outgoing effects (Leaf action/command)",
      deleteNode: "Delete Node",
      modalAddNodeTitle: "Add New Causal Node",
      modalAddEdgeTitle: "Add New Causal Edge",
      nodeId: "Node ID (Unique Identifier)",
      nodeLabelLabel: "Node Label (Display Name)",
      nodeDescLabel: "Description (Optional)",
      sourceNode: "Source Node",
      targetNode: "Target Node",
      relationshipType: "Relationship Type",
      relLeadsTo: "leads_to",
      relVerifiedBy: "verified_by",
      relFixedBy: "fixed_by",
      relExecutes: "executes",
      legend: "Legend:",
    },
    deviceManager: {
      modalTitle: "Network Device Management",
      registeredCount: "registered",
      guideBanner:
        "Connection details follow global defaults (admin / admin, port 22), but individual credentials on specific devices take precedence.",
      inventoryTitle: "Accessible Device Inventory",
      addDevice: "Add Device",
      closeForm: "Close",
      newDeviceTitle: "Register New Device",
      editDeviceTitle: "Edit Settings",
      deviceName: "Device Name",
      deviceHost: "IP Address",
      username: "Username",
      usernameHint: "admin if blank",
      password: "Password",
      passwordHint: "admin if blank",
      port: "SSH Port",
      mockModeLabel: "Register in Mock simulation mode",
      mockModeEdit: "Mock Mode",
      register: "Register",
      save: "Save",
      cancel: "Cancel",
      close: "Close",
      liveBadge: "LIVE SSH",
      mockBadge: "MOCK",
      editTooltip: "Edit Settings",
      deleteTooltip: "Delete Device",
      userLabel: "User",
    },
    settings: {
      modalTitle: "Connection Environment Settings",
      modalDesc: "Configure LLM Provider and Cisco IOS-XE connection settings.",
      llmSectionTitle: "LLM Provider Settings (OpenAI Compatible)",
      baseUrl: "Base URL",
      apiKey: "API Key",
      apiKeyHint: "* If blank, built-in intelligent engine runs automatically.",
      modelName: "Model Name",
      geminiGuideTitle: "Google Gemini OpenAI Compatible Endpoint Guide",
      geminiGuideDesc:
        "For Gemini 2.5 Flash, set Base URL to https://generativelanguage.googleapis.com/v1beta/openai and enter your Gemini API Key.",
      deviceSectionTitle: "Cisco IOS-XE Default Settings (devices.env)",
      deviceHost: "Host IP",
      devicePort: "SSH Port",
      deviceUser: "SSH Username",
      devicePass: "SSH Password",
      enablePass: "Enable Password",
      enablePassHint: "* Optional",
      mockModeToggle: "Use Cisco Device Mock Simulation Mode",
      mockModeDesc:
        "When enabled, operates with simulated Cisco IOS-XE dataset without real SSH connection.",
      saveSettings: "Save Settings",
      saved: "Saved!",
      cancel: "Cancel",
    },
  },
};

export type Translations = typeof translations.ko;

interface I18nContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: Translations;
}

const I18nContext = createContext<I18nContextType>({
  language: "ko",
  setLanguage: () => {},
  t: translations.ko,
});

export const I18nProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [language, setLanguageState] = useState<Language>("ko");

  useEffect(() => {
    try {
      const saved = localStorage.getItem("net_aiops_lang") as Language | null;
      if (saved === "ko" || saved === "en") {
        setLanguageState(saved);
      }
    } catch {
      // ignore
    }
  }, []);

  const setLanguage = (lang: Language) => {
    setLanguageState(lang);
    try {
      localStorage.setItem("net_aiops_lang", lang);
    } catch {
      // ignore
    }
  };

  const t = translations[language] || translations.ko;

  return (
    <I18nContext.Provider value={{ language, setLanguage, t }}>
      {children}
    </I18nContext.Provider>
  );
};

export const useI18n = () => useContext(I18nContext);
