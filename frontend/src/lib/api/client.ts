/**
 * API Client for TEQUILA Backend
 */

import type {
  WeekListResponse,
  WeekSpec,
  DayField,
  ValidationResult,
  ExportResponse,
  UsageStats,
  ApiResponse,
} from "./types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const API_KEY = process.env.NEXT_PUBLIC_API_KEY;

class TequilaApiClient {
  private baseUrl: string;
  private apiKey?: string;

  constructor(baseUrl: string = API_BASE_URL, apiKey?: string) {
    this.baseUrl = baseUrl;
    this.apiKey = apiKey || API_KEY;
  }

  private async request<T = any>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const headers: HeadersInit = {
      "Content-Type": "application/json",
      ...options.headers,
    };

    if (this.apiKey) {
      headers["X-API-Key"] = this.apiKey;
    }

    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({
        message: response.statusText,
      }));
      throw new Error(error.message || error.detail || "API request failed");
    }

    return response.json();
  }

  // ========================================================================
  // Week Operations
  // ========================================================================

  async getWeeks(): Promise<WeekListResponse> {
    return this.request<WeekListResponse>("/api/v1/weeks");
  }

  async getWeekSpec(week: number): Promise<WeekSpec> {
    const response = await this.request<{ spec: WeekSpec }>(
      `/api/v1/weeks/${week}/spec/compiled`
    );
    return response.spec;
  }

  async scaffoldWeek(week: number): Promise<ApiResponse> {
    return this.request(`/api/v1/weeks/${week}/scaffold`, {
      method: "POST",
    });
  }

  // ========================================================================
  // Day Operations
  // ========================================================================

  async getDayField(
    week: number,
    day: number,
    field: string
  ): Promise<{ field: string; content: any }> {
    return this.request(`/api/v1/weeks/${week}/days/${day}/fields/${field}`);
  }

  async updateDayField(
    week: number,
    day: number,
    field: string,
    content: any
  ): Promise<ApiResponse> {
    return this.request(`/api/v1/weeks/${week}/days/${day}/fields/${field}`, {
      method: "PUT",
      body: JSON.stringify({ content }),
    });
  }

  async getDayFlintBundle(
    week: number,
    day: number
  ): Promise<{ week: number; day: number; fields: Record<string, any> }> {
    return this.request(`/api/v1/weeks/${week}/days/${day}/flint-bundle`);
  }

  // ========================================================================
  // Validation & Export
  // ========================================================================

  async validateWeek(week: number): Promise<ValidationResult> {
    return this.request(`/api/v1/weeks/${week}/validate`, {
      method: "POST",
    });
  }

  async exportWeek(week: number): Promise<ExportResponse> {
    return this.request(`/api/v1/weeks/${week}/export`, {
      method: "POST",
    });
  }

  async downloadWeekExport(week: number): Promise<Blob> {
    const response = await fetch(
      `${this.baseUrl}/api/v1/weeks/${week}/export/download`,
      {
        headers: this.apiKey ? { "X-API-Key": this.apiKey } : {},
      }
    );

    if (!response.ok) {
      throw new Error("Download failed");
    }

    return response.blob();
  }

  // ========================================================================
  // Generation (Protected)
  // ========================================================================

  async generateWeekSpec(week: number): Promise<ApiResponse> {
    return this.request(`/api/v1/gen/weeks/${week}/spec`, {
      method: "POST",
    });
  }

  async generateRoleContext(week: number): Promise<ApiResponse> {
    return this.request(`/api/v1/gen/weeks/${week}/role-context`, {
      method: "POST",
    });
  }

  async generateAssets(week: number): Promise<ApiResponse> {
    return this.request(`/api/v1/gen/weeks/${week}/assets`, {
      method: "POST",
    });
  }

  async generateDayFields(week: number, day: number): Promise<ApiResponse> {
    return this.request(`/api/v1/gen/weeks/${week}/days/${day}/fields`, {
      method: "POST",
    });
  }

  async generateDayDocument(week: number, day: number): Promise<ApiResponse> {
    return this.request(`/api/v1/gen/weeks/${week}/days/${day}/document`, {
      method: "POST",
    });
  }

  async hydrateWeek(week: number): Promise<ApiResponse> {
    return this.request(`/api/v1/gen/weeks/${week}/hydrate`, {
      method: "POST",
    });
  }

  // ========================================================================
  // Usage & Analytics
  // ========================================================================

  async getUsage(): Promise<UsageStats> {
    return this.request("/api/v1/usage");
  }

  async resetUsage(): Promise<ApiResponse> {
    return this.request("/api/v1/usage/reset", {
      method: "POST",
    });
  }

  // ========================================================================
  // WebSocket
  // ========================================================================

  connectWebSocket(
    onMessage: (data: any) => void,
    onError?: (error: Event) => void
  ): WebSocket {
    const wsUrl = this.baseUrl.replace("http", "ws") + "/ws";
    const ws = new WebSocket(wsUrl);

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onMessage(data);
      } catch (e) {
        console.error("Failed to parse WebSocket message:", e);
      }
    };

    ws.onerror = (error) => {
      console.error("WebSocket error:", error);
      if (onError) onError(error);
    };

    // Send ping every 30 seconds to keep connection alive
    const pingInterval = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send("ping");
      } else {
        clearInterval(pingInterval);
      }
    }, 30000);

    return ws;
  }
}

// Export singleton instance
export const apiClient = new TequilaApiClient();

// Export class for custom instances
export default TequilaApiClient;
