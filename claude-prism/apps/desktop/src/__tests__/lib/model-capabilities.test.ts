import { describe, expect, it } from "vitest";
import {
  getModelCapabilities,
  isChatModelOption,
} from "@/lib/model-capabilities";

describe("model capabilities", () => {
  it("uses provider metadata for vision capability", () => {
    expect(
      getModelCapabilities({
        model: "custom-model",
        metadata: { model_info: { supports_vision: true } },
      }).vision,
    ).toBe(true);

    expect(
      getModelCapabilities({
        label: "Qwen",
        model: "qwen3.6-flash",
        metadata: { supports_vision: false },
      }).vision,
    ).toBe(false);
  });

  it("recognizes recent Qwen chat models as vision-capable when metadata is missing", () => {
    expect(
      getModelCapabilities({
        label: "Qwen",
        baseUrl: "https://dashscope.aliyuncs.com/compatible-mode/v1",
        model: "qwen3.5-flash",
      }).vision,
    ).toBe(true);

    expect(
      getModelCapabilities({
        label: "Qwen",
        baseUrl: "https://dashscope.aliyuncs.com/compatible-mode/v1",
        model: "qwen3.6-flash",
      }).vision,
    ).toBe(true);

    expect(
      getModelCapabilities({
        label: "Qwen",
        baseUrl: "https://dashscope.aliyuncs.com/compatible-mode/v1",
        model: "qwen3.6-plus",
      }).vision,
    ).toBe(true);

    expect(
      getModelCapabilities({
        label: "Qwen",
        baseUrl: "https://dashscope.aliyuncs.com/compatible-mode/v1",
        model: "qwen3.5-coder",
      }).vision,
    ).toBe(false);
  });

  it("filters non-chat model families", () => {
    expect(
      isChatModelOption({
        label: "Qwen",
        model: "text-embedding-v4",
      }),
    ).toBe(false);
  });
});
