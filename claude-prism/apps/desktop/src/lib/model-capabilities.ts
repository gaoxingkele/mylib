export interface OpenAiCompatibleModelInfo {
  id: string;
  metadata?: unknown;
}

interface ModelCapabilityInput {
  label?: string | null;
  baseUrl?: string | null;
  model?: string | null;
  metadata?: unknown;
}

export interface ModelCapabilities {
  chat: boolean;
  vision: boolean;
}

const modelMetadataCache = new Map<string, unknown>();

function normalizeText(value?: unknown) {
  return String(value ?? "")
    .trim()
    .toLowerCase();
}

function metadataKey(baseUrl?: string | null, model?: string | null) {
  return `${normalizeText(baseUrl)}::${normalizeText(model)}`;
}

export function rememberModelCapabilityMetadata(
  baseUrl: string | null | undefined,
  model: string | null | undefined,
  metadata: unknown,
) {
  if (!model?.trim()) return;
  modelMetadataCache.set(metadataKey(baseUrl, model), metadata);
}

export function rememberModelListCapabilityMetadata(
  baseUrl: string | null | undefined,
  models: Array<string | OpenAiCompatibleModelInfo>,
) {
  for (const model of models) {
    if (typeof model === "string") {
      rememberModelCapabilityMetadata(baseUrl, model, { id: model });
    } else {
      rememberModelCapabilityMetadata(
        baseUrl,
        model.id,
        model.metadata ?? model,
      );
    }
  }
}

export function modelInfoId(model: unknown) {
  if (typeof model === "string") return model;
  if (isPlainObject(model) && typeof model.id === "string") return model.id;
  return String(model ?? "");
}

function haystack(input: ModelCapabilityInput) {
  return [input.label, input.baseUrl, input.model]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();
}

function canonicalModelId(value?: string | null) {
  return normalizeText(value)
    .replace(/[._/]+/g, "-")
    .replace(/[^a-z0-9-]+/g, "-")
    .replace(/-+/g, "-")
    .replace(/^-|-$/g, "");
}

function isPlainObject(value: unknown): value is Record<string, unknown> {
  return !!value && typeof value === "object" && !Array.isArray(value);
}

function normalizeToken(value: unknown) {
  return String(value)
    .trim()
    .toLowerCase()
    .replace(/[_\s]+/g, "-");
}

function booleanValue(value: unknown): boolean | null {
  if (typeof value === "boolean") return value;
  if (typeof value !== "string") return null;
  const normalized = normalizeToken(value);
  if (["1", "true", "yes", "supported", "enabled"].includes(normalized)) {
    return true;
  }
  if (["0", "false", "no", "unsupported", "disabled"].includes(normalized)) {
    return false;
  }
  return null;
}

function valueTokens(value: unknown): string[] {
  if (Array.isArray(value)) {
    return value.flatMap(valueTokens);
  }
  if (isPlainObject(value)) {
    return Object.entries(value).flatMap(([key, child]) => [
      normalizeToken(key),
      ...valueTokens(child),
    ]);
  }
  if (typeof value === "string" || typeof value === "number") {
    return normalizeToken(value)
      .split(/[^a-z0-9]+/)
      .filter(Boolean);
  }
  return [];
}

const metadataVisionBooleanKeys = new Set([
  "supports-vision",
  "support-vision",
  "vision",
  "supports-image-input",
  "support-image-input",
  "image-input",
  "images-input",
  "supports-images",
  "multimodal",
  "multi-modal",
]);

const metadataFeatureKeys = new Set([
  "features",
  "capabilities",
  "modalities",
  "input-modalities",
  "supported-modalities",
  "supported-input-modalities",
  "model-features",
  "model-capabilities",
]);

const visionFeatureTokens = new Set([
  "vision",
  "visual",
  "image",
  "images",
  "image-input",
  "input-image",
  "multimodal",
  "multi-modal",
]);

const chatModeTokens = new Set([
  "chat",
  "completion",
  "completions",
  "messages",
  "text-generation",
  "text",
  "llm",
]);

const nonChatModeTokens = new Set([
  "embedding",
  "embeddings",
  "rerank",
  "reranking",
  "moderation",
  "whisper",
  "tts",
  "text-to-speech",
  "speech-to-text",
  "speech",
  "audio",
  "asr",
  "stt",
  "image-generation",
  "image-to-video",
  "video-generation",
  "text-embedding",
  "realtime",
]);

function metadataVisionCapability(
  value: unknown,
  depth = 0,
): boolean | undefined {
  if (depth > 5) return undefined;
  if (!isPlainObject(value)) return undefined;

  for (const [rawKey, child] of Object.entries(value)) {
    const key = normalizeToken(rawKey);
    if (metadataVisionBooleanKeys.has(key)) {
      const parsed = booleanValue(child);
      if (parsed !== null) return parsed;
    }

    if (metadataFeatureKeys.has(key)) {
      const tokens = valueTokens(child);
      if (tokens.some((token) => visionFeatureTokens.has(token))) return true;
    }

    const nested = metadataVisionCapability(child, depth + 1);
    if (nested !== undefined) return nested;
  }

  return undefined;
}

function metadataChatCapability(
  value: unknown,
  depth = 0,
): boolean | undefined {
  if (depth > 5) return undefined;
  if (!isPlainObject(value)) return undefined;

  for (const [rawKey, child] of Object.entries(value)) {
    const key = normalizeToken(rawKey);
    if (
      [
        "mode",
        "type",
        "task",
        "model-type",
        "endpoint-type",
        "category",
      ].includes(key)
    ) {
      const tokens = valueTokens(child);
      if (tokens.some((token) => nonChatModeTokens.has(token))) return false;
      if (tokens.some((token) => chatModeTokens.has(token))) return true;
    }

    if (metadataFeatureKeys.has(key)) {
      const tokens = valueTokens(child);
      if (tokens.some((token) => chatModeTokens.has(token))) return true;
    }

    const nested = metadataChatCapability(child, depth + 1);
    if (nested !== undefined) return nested;
  }

  return undefined;
}

function isNonChatModel(value: string) {
  return Array.from(nonChatModeTokens).some((marker) => value.includes(marker));
}

function isQwenProvider(value: string) {
  return [
    "qwen",
    "dashscope",
    "aliyuncs.com",
    "alibabacloud",
    "alibaba-cloud",
    "modelstudio",
    "bailian",
  ].some((marker) => value.includes(marker));
}

function isQwenVisionModel(model: string) {
  const id = canonicalModelId(model);

  if (
    [
      "qwen-vl",
      "qwen2-vl",
      "qwen2-5-vl",
      "qwen3-vl",
      "qwen-omni",
      "qwen2-5-omni",
      "qwen3-omni",
      "qvq",
    ].some((prefix) => id === prefix || id.startsWith(`${prefix}-`))
  ) {
    return true;
  }

  if (!id.startsWith("qwen")) return false;
  if (
    ["audio", "coder", "code", "embedding", "math", "rerank", "tts"].some(
      (token) => id.includes(token),
    )
  ) {
    return false;
  }

  const version = id.match(/^qwen-?(\d+)-(\d+)/);
  if (!version) return false;

  const major = Number(version[1]);
  const minor = Number(version[2]);
  return major > 3 || (major === 3 && minor >= 5);
}

function curatedVisionCapability(input: ModelCapabilityInput, value: string) {
  const model = input.model ?? "";

  if (isQwenProvider(value) && isQwenVisionModel(model)) {
    return true;
  }

  return undefined;
}

function hasExplicitVisionFamily(value: string) {
  const normalized = value.toLowerCase();
  const tokens = normalized.split(/[^a-z0-9]+/).filter(Boolean);

  if (tokens.includes("vl")) return true;

  return [
    "vision",
    "multimodal",
    "multi-modal",
    "omni",
    "qvq",
    "llava",
    "bakllava",
    "moondream",
    "minicpm-v",
    "glm-4v",
    "glm-4.5v",
    "internvl",
    "pixtral",
    "llama3.2-vision",
    "granite3.2-vision",
    "gpt-4o",
    "gpt-4.1",
    "gpt-4.5",
    "gpt-4-turbo",
    "gpt-4-vision",
    "o3",
    "o4",
    "gemini",
  ].some((marker) => normalized.includes(marker));
}

function modelMetadata(input: ModelCapabilityInput) {
  return (
    input.metadata ??
    modelMetadataCache.get(metadataKey(input.baseUrl, input.model)) ??
    modelMetadataCache.get(metadataKey(null, input.model))
  );
}

export function getModelCapabilities(
  input: ModelCapabilityInput,
): ModelCapabilities {
  const value = haystack(input);
  const model = normalizeText(input.model);

  if (!model) {
    return { chat: true, vision: false };
  }

  const metadata = modelMetadata(input);
  const metadataChat = metadataChatCapability(metadata);
  const metadataVision = metadataVisionCapability(metadata);

  const chat = metadataChat ?? !isNonChatModel(value);
  if (!chat) {
    return { chat: false, vision: false };
  }

  return {
    chat,
    vision:
      metadataVision ??
      curatedVisionCapability(input, value) ??
      hasExplicitVisionFamily(value),
  };
}

export function isChatModelOption(input: ModelCapabilityInput) {
  return getModelCapabilities(input).chat;
}
