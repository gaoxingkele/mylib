import { beforeEach, describe, expect, it, vi } from "vitest";
import { invoke } from "@tauri-apps/api/core";
import { useClaudeSetupStore } from "@/stores/claude-setup-store";

// advanceSteps is module-private — replicate for testing
type StepStatus = "pending" | "active" | "complete" | "error";

interface StepInfo {
  id: string;
  label: string;
  status: StepStatus;
}

function advanceSteps(
  steps: StepInfo[],
  targetId: string,
  order: string[],
): StepInfo[] {
  const targetIdx = order.indexOf(targetId);
  return steps.map((s) => {
    const thisIdx = order.indexOf(s.id);
    if (thisIdx < targetIdx && s.status !== "error") {
      return { ...s, status: "complete" as const };
    }
    if (s.id === targetId) {
      return { ...s, status: "active" as const };
    }
    return s;
  });
}

const INSTALL_ORDER = ["downloading", "installing", "verifying", "complete"];

function makeSteps(statuses: StepStatus[]): StepInfo[] {
  return [
    { id: "downloading", label: "Downloading", status: statuses[0] },
    { id: "installing", label: "Installing", status: statuses[1] },
    { id: "verifying", label: "Verifying", status: statuses[2] },
    { id: "complete", label: "Complete", status: statuses[3] },
  ];
}

describe("advanceSteps", () => {
  it("sets target step to active", () => {
    const steps = makeSteps(["pending", "pending", "pending", "pending"]);
    const result = advanceSteps(steps, "downloading", INSTALL_ORDER);
    expect(result[0].status).toBe("active");
    expect(result[1].status).toBe("pending");
    expect(result[2].status).toBe("pending");
    expect(result[3].status).toBe("pending");
  });

  it("marks earlier steps as complete", () => {
    const steps = makeSteps(["active", "pending", "pending", "pending"]);
    const result = advanceSteps(steps, "installing", INSTALL_ORDER);
    expect(result[0].status).toBe("complete");
    expect(result[1].status).toBe("active");
    expect(result[2].status).toBe("pending");
    expect(result[3].status).toBe("pending");
  });

  it("marks all earlier steps complete when advancing to last", () => {
    const steps = makeSteps(["active", "pending", "pending", "pending"]);
    const result = advanceSteps(steps, "complete", INSTALL_ORDER);
    expect(result[0].status).toBe("complete");
    expect(result[1].status).toBe("complete");
    expect(result[2].status).toBe("complete");
    expect(result[3].status).toBe("active");
  });

  it("does not overwrite error status on earlier steps", () => {
    const steps = makeSteps(["error", "pending", "pending", "pending"]);
    const result = advanceSteps(steps, "verifying", INSTALL_ORDER);
    expect(result[0].status).toBe("error"); // preserved
    expect(result[1].status).toBe("complete");
    expect(result[2].status).toBe("active");
    expect(result[3].status).toBe("pending");
  });

  it("keeps later steps as pending", () => {
    const steps = makeSteps(["pending", "pending", "pending", "pending"]);
    const result = advanceSteps(steps, "installing", INSTALL_ORDER);
    expect(result[2].status).toBe("pending");
    expect(result[3].status).toBe("pending");
  });

  it("works with login steps", () => {
    const loginOrder = ["opening-browser", "waiting-auth", "complete"];
    const loginSteps: StepInfo[] = [
      { id: "opening-browser", label: "Opening browser", status: "active" },
      { id: "waiting-auth", label: "Waiting", status: "pending" },
      { id: "complete", label: "Done", status: "pending" },
    ];
    const result = advanceSteps(loginSteps, "waiting-auth", loginOrder);
    expect(result[0].status).toBe("complete");
    expect(result[1].status).toBe("active");
    expect(result[2].status).toBe("pending");
  });
});

describe("useClaudeSetupStore.saveApiKey", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useClaudeSetupStore.setState({
      status: "ready",
      isInstalling: false,
      isLoggingIn: false,
      isSavingApiKey: false,
      isClearingApiKey: false,
      error: null,
      version: "1.0.0",
      providerKind: "claude-code",
      accountEmail: null,
      providerModel: null,
      providerBaseUrl: null,
      openAiCredentials: [],
      activeOpenAiCredentialId: null,
      installSteps: [],
      installLogs: [],
      installLogsVisible: false,
      loginSteps: [],
    });
  });

  it("requires Claude Code before saving provider credentials", async () => {
    useClaudeSetupStore.setState({ status: "not-installed" });

    const success = await useClaudeSetupStore
      .getState()
      .saveApiKey(
        "sk-test",
        "https://api.deepseek.com/anthropic",
        "openai-compatible",
        "deepseek-v4-pro",
      );

    expect(success).toBe(false);
    expect(invoke).not.toHaveBeenCalled();
    expect(useClaudeSetupStore.getState().error).toBe(
      "Install Claude Code before configuring an AI provider.",
    );
  });

  it("verifies OpenAI-compatible credentials before saving them", async () => {
    vi.mocked(invoke).mockImplementation(async (command) => {
      if (command === "check_claude_status") {
        return {
          installed: true,
          authenticated: true,
          binary_path: null,
          version: "OpenAI-compatible provider",
          provider_kind: "openai-compatible",
          account_email: null,
          provider_model: "deepseek-v4-pro",
          provider_base_url: "https://api.deepseek.com/anthropic",
          missing_git: false,
        };
      }
      if (command === "list_openai_compatible_credentials") {
        return [
          {
            id: "cred-1",
            label: "DeepSeek",
            model: "deepseek-v4-pro",
            base_url: "https://api.deepseek.com/anthropic",
          },
        ];
      }
      return null;
    });

    const success = await useClaudeSetupStore
      .getState()
      .saveApiKey(
        "sk-test",
        "https://api.deepseek.com/anthropic",
        "openai-compatible",
        "deepseek-v4-pro",
      );

    expect(success).toBe(true);
    expect(invoke).toHaveBeenNthCalledWith(
      1,
      "verify_openai_compatible_api_key",
      {
        apiKey: "sk-test",
        baseUrl: "https://api.deepseek.com/anthropic",
        model: "deepseek-v4-pro",
      },
    );
    expect(invoke).toHaveBeenNthCalledWith(2, "save_anthropic_api_key", {
      apiKey: "sk-test",
      baseUrl: "https://api.deepseek.com/anthropic",
      provider: "openai-compatible",
      model: "deepseek-v4-pro",
      credentialLabel: null,
    });
  });

  it("normalizes legacy DeepSeek root URLs to the native Anthropic endpoint", async () => {
    vi.mocked(invoke).mockResolvedValue(null);

    const success = await useClaudeSetupStore
      .getState()
      .saveApiKey(
        "sk-test",
        "https://api.deepseek.com",
        "openai-compatible",
        "deepseek-v4-pro",
      );

    expect(success).toBe(true);
    expect(invoke).toHaveBeenNthCalledWith(
      1,
      "verify_openai_compatible_api_key",
      {
        apiKey: "sk-test",
        baseUrl: "https://api.deepseek.com/anthropic",
        model: "deepseek-v4-pro",
      },
    );
    expect(invoke).toHaveBeenNthCalledWith(2, "save_anthropic_api_key", {
      apiKey: "sk-test",
      baseUrl: "https://api.deepseek.com/anthropic",
      provider: "openai-compatible",
      model: "deepseek-v4-pro",
      credentialLabel: null,
    });
  });

  it("normalizes legacy Qwen compatible URLs to the native Anthropic endpoint", async () => {
    vi.mocked(invoke).mockResolvedValue(null);

    const success = await useClaudeSetupStore
      .getState()
      .saveApiKey(
        "sk-test",
        "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "openai-compatible",
        "qwen3-max-2026-01-23",
      );

    expect(success).toBe(true);
    expect(invoke).toHaveBeenNthCalledWith(
      1,
      "verify_openai_compatible_api_key",
      {
        apiKey: "sk-test",
        baseUrl: "https://dashscope.aliyuncs.com/apps/anthropic",
        model: "qwen3-max-2026-01-23",
      },
    );
    expect(invoke).toHaveBeenNthCalledWith(2, "save_anthropic_api_key", {
      apiKey: "sk-test",
      baseUrl: "https://dashscope.aliyuncs.com/apps/anthropic",
      provider: "openai-compatible",
      model: "qwen3-max-2026-01-23",
      credentialLabel: null,
    });
  });

  it("preserves Qwen native Anthropic URLs when saving credentials", async () => {
    vi.mocked(invoke).mockResolvedValue(null);

    const success = await useClaudeSetupStore
      .getState()
      .saveApiKey(
        "sk-test",
        "https://dashscope.aliyuncs.com/apps/anthropic/v1",
        "openai-compatible",
        "qwen3-max-2026-01-23",
      );

    expect(success).toBe(true);
    expect(invoke).toHaveBeenNthCalledWith(
      1,
      "verify_openai_compatible_api_key",
      {
        apiKey: "sk-test",
        baseUrl: "https://dashscope.aliyuncs.com/apps/anthropic",
        model: "qwen3-max-2026-01-23",
      },
    );
    expect(invoke).toHaveBeenNthCalledWith(2, "save_anthropic_api_key", {
      apiKey: "sk-test",
      baseUrl: "https://dashscope.aliyuncs.com/apps/anthropic",
      provider: "openai-compatible",
      model: "qwen3-max-2026-01-23",
      credentialLabel: null,
    });
  });

  it("normalizes Moonshot compatible URLs to the native Anthropic endpoint", async () => {
    vi.mocked(invoke).mockResolvedValue(null);

    const success = await useClaudeSetupStore
      .getState()
      .saveApiKey(
        "sk-test",
        "https://api.moonshot.cn/v1",
        "openai-compatible",
        "kimi-k2.5",
      );

    expect(success).toBe(true);
    expect(invoke).toHaveBeenNthCalledWith(
      1,
      "verify_openai_compatible_api_key",
      {
        apiKey: "sk-test",
        baseUrl: "https://api.moonshot.ai/anthropic",
        model: "kimi-k2.5",
      },
    );
    expect(invoke).toHaveBeenNthCalledWith(2, "save_anthropic_api_key", {
      apiKey: "sk-test",
      baseUrl: "https://api.moonshot.ai/anthropic",
      provider: "openai-compatible",
      model: "kimi-k2.5",
      credentialLabel: null,
    });
  });

  it("preserves Moonshot Anthropic-looking URLs when saving credentials", async () => {
    vi.mocked(invoke).mockResolvedValue(null);

    const success = await useClaudeSetupStore
      .getState()
      .saveApiKey(
        "sk-test",
        "https://api.moonshot.ai/anthropic/v1",
        "openai-compatible",
        "kimi-k2.5",
      );

    expect(success).toBe(true);
    expect(invoke).toHaveBeenNthCalledWith(
      1,
      "verify_openai_compatible_api_key",
      {
        apiKey: "sk-test",
        baseUrl: "https://api.moonshot.ai/anthropic",
        model: "kimi-k2.5",
      },
    );
    expect(invoke).toHaveBeenNthCalledWith(2, "save_anthropic_api_key", {
      apiKey: "sk-test",
      baseUrl: "https://api.moonshot.ai/anthropic",
      provider: "openai-compatible",
      model: "kimi-k2.5",
      credentialLabel: null,
    });
  });

  it("allows local OpenAI-compatible providers without an API key", async () => {
    vi.mocked(invoke).mockImplementation(async (command) => {
      if (command === "check_claude_status") {
        return {
          installed: true,
          authenticated: true,
          binary_path: null,
          version: "OpenAI-compatible provider",
          provider_kind: "openai-compatible",
          account_email: null,
          provider_model: "llama3.2",
          provider_base_url: "http://localhost:11434/v1",
          missing_git: false,
        };
      }
      if (command === "list_openai_compatible_credentials") {
        return [
          {
            id: "ollama-cred",
            label: "Ollama",
            model: "llama3.2",
            base_url: "http://localhost:11434/v1",
          },
        ];
      }
      return null;
    });

    const success = await useClaudeSetupStore
      .getState()
      .saveApiKey(
        "",
        "http://localhost:11434/v1",
        "openai-compatible",
        "llama3.2",
        "Ollama",
      );

    expect(success).toBe(true);
    expect(invoke).toHaveBeenNthCalledWith(
      1,
      "verify_openai_compatible_api_key",
      {
        apiKey: "",
        baseUrl: "http://localhost:11434/v1",
        model: "llama3.2",
      },
    );
    expect(invoke).toHaveBeenNthCalledWith(2, "save_anthropic_api_key", {
      apiKey: "",
      baseUrl: "http://localhost:11434/v1",
      provider: "openai-compatible",
      model: "llama3.2",
      credentialLabel: "Ollama",
    });
  });

  it("does not save OpenAI-compatible credentials when verification fails", async () => {
    vi.mocked(invoke).mockRejectedValueOnce(
      new Error("Invalid provider API key"),
    );

    const success = await useClaudeSetupStore
      .getState()
      .saveApiKey(
        "sk-test",
        "https://api.deepseek.com/anthropic",
        "openai-compatible",
        "deepseek-v4-pro",
      );

    expect(success).toBe(false);
    expect(invoke).toHaveBeenCalledTimes(1);
    expect(invoke).toHaveBeenCalledWith("verify_openai_compatible_api_key", {
      apiKey: "sk-test",
      baseUrl: "https://api.deepseek.com/anthropic",
      model: "deepseek-v4-pro",
    });
    expect(useClaudeSetupStore.getState().error).toBe(
      "Invalid provider API key",
    );
  });

  it("clears saved credentials and refreshes status", async () => {
    useClaudeSetupStore.setState({
      status: "ready",
      version: "OpenAI-compatible provider",
      providerKind: "openai-compatible",
      providerModel: "qwen3-coder-plus",
      providerBaseUrl: "https://dashscope.aliyuncs.com/compatible-mode/v1",
    });
    vi.mocked(invoke).mockImplementation(async (command) => {
      if (command === "check_claude_status") {
        return {
          installed: true,
          authenticated: false,
          binary_path: null,
          version: "1.0.0",
          provider_kind: "claude-code",
          account_email: null,
          provider_model: null,
          provider_base_url: null,
          missing_git: false,
        };
      }
      if (command === "list_openai_compatible_credentials") {
        return [];
      }
      return null;
    });

    const success = await useClaudeSetupStore.getState().clearApiKey();

    expect(success).toBe(true);
    expect(invoke).toHaveBeenNthCalledWith(1, "clear_anthropic_api_key");
    expect(invoke).toHaveBeenNthCalledWith(2, "check_claude_status");
    expect(invoke).toHaveBeenNthCalledWith(
      3,
      "list_openai_compatible_credentials",
    );
    expect(useClaudeSetupStore.getState().status).toBe("not-authenticated");
    expect(useClaudeSetupStore.getState().providerModel).toBeNull();
    expect(useClaudeSetupStore.getState().providerBaseUrl).toBeNull();
    expect(useClaudeSetupStore.getState().isClearingApiKey).toBe(false);
  });
});
