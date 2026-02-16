/** API configuration — switches between local and deployed backends */
export const API_CONFIG = {
  backendUrl:
    process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:10000",
  endpoints: {
    generate: "/generate",
    health: "/health",
  },
} as const;

export type GenerateRequest = {
  prefix: string;
  max_length: number;
};

export type StreamToken = {
  token: string;
  full_text: string;
  is_finished: boolean;
  error?: string;
};

/**
 * Calls the backend /generate endpoint and streams tokens via SSE.
 * Returns an async generator that yields each token as it arrives.
 */
export async function* streamGenerate(
  request: GenerateRequest
): AsyncGenerator<StreamToken> {
  const url = `${API_CONFIG.backendUrl}${API_CONFIG.endpoints.generate}`;

  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error(`Backend error: ${response.status} ${response.statusText}`);
  }

  const reader = response.body?.getReader();
  if (!reader) throw new Error("No response body");

  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    // Parse SSE lines from buffer
    const lines = buffer.split("\n");
    buffer = lines.pop() || ""; // keep incomplete line in buffer

    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed || !trimmed.startsWith("data: ")) continue;

      const jsonStr = trimmed.slice(6); // remove "data: " prefix
      try {
        const token: StreamToken = JSON.parse(jsonStr);
        yield token;

        if (token.is_finished || token.error) return;
      } catch {
        // Ignore malformed JSON lines
      }
    }
  }
}

/** Health check */
export async function checkHealth(): Promise<{
  status: string;
  model_loaded: boolean;
  tokenizer_loaded: boolean;
}> {
  const url = `${API_CONFIG.backendUrl}${API_CONFIG.endpoints.health}`;
  const response = await fetch(url);
  if (!response.ok) throw new Error(`Health check failed: ${response.status}`);
  return response.json();
}
