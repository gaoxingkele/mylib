use super::transformers::ProxyTransformerChain;
use super::OpenAiProxyCredential;
use serde_json::{json, Value};

const DEEPSEEK_MAX_TOKENS: u64 = 8192;

pub(super) fn apply_provider_request_transforms(
    openai_request: &mut Value,
    anthropic_request: &Value,
    credential: &OpenAiProxyCredential,
    wants_stream: bool,
    transformers: &ProxyTransformerChain,
) {
    if transformers.has_cleancache() {
        clean_cache_control(openai_request);
    }

    if wants_stream && transformers.has_streamoptions() {
        openai_request["stream_options"] = json!({ "include_usage": true });
    }

    if transformers.has_deepseek() {
        cap_number_field(openai_request, "max_tokens", DEEPSEEK_MAX_TOKENS);
    }

    apply_reasoning_budget(openai_request, anthropic_request);
    apply_max_completion_tokens_compat(openai_request, credential);
    clean_null_optional_fields(openai_request);
}

fn cap_number_field(body: &mut Value, key: &str, max: u64) {
    let Some(value) = body.get(key).and_then(|value| value.as_u64()) else {
        return;
    };
    if value > max {
        body[key] = Value::Number(max.into());
    }
}

fn apply_reasoning_budget(openai_request: &mut Value, anthropic_request: &Value) {
    let Some(thinking) = anthropic_request.get("thinking") else {
        return;
    };
    if thinking.get("type").and_then(|value| value.as_str()) != Some("enabled") {
        return;
    }
    let Some(budget_tokens) = thinking
        .get("budget_tokens")
        .and_then(|value| value.as_u64())
    else {
        return;
    };
    if budget_tokens > 0 {
        openai_request["reasoning"] = json!({ "max_tokens": budget_tokens });
    }
}

fn apply_max_completion_tokens_compat(
    openai_request: &mut Value,
    credential: &OpenAiProxyCredential,
) {
    if !uses_max_completion_tokens(credential) {
        return;
    }
    let Some(max_tokens) = openai_request.get("max_tokens").cloned() else {
        return;
    };
    openai_request["max_completion_tokens"] = max_tokens;
    if let Some(object) = openai_request.as_object_mut() {
        object.remove("max_tokens");
    }
}

fn uses_max_completion_tokens(credential: &OpenAiProxyCredential) -> bool {
    let base_url = credential.base_url.to_ascii_lowercase();
    let model = credential.model.to_ascii_lowercase();
    let is_openai = base_url.contains("api.openai.com") || base_url.contains("openai.azure.com");
    is_openai
        && (model.starts_with("o1")
            || model.starts_with("o3")
            || model.starts_with("o4")
            || model.starts_with("gpt-5"))
}

fn clean_cache_control(value: &mut Value) {
    match value {
        Value::Array(values) => {
            for value in values {
                clean_cache_control(value);
            }
        }
        Value::Object(object) => {
            object.remove("cache_control");
            for value in object.values_mut() {
                clean_cache_control(value);
            }
        }
        _ => {}
    }
}

fn clean_null_optional_fields(value: &mut Value) {
    let Some(object) = value.as_object_mut() else {
        return;
    };
    for key in ["tool_choice", "stop", "stream_options", "reasoning"] {
        if object.get(key).is_some_and(Value::is_null) {
            object.remove(key);
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn credential(base_url: &str, model: &str) -> OpenAiProxyCredential {
        OpenAiProxyCredential {
            api_key: "sk-test".to_string(),
            base_url: base_url.to_string(),
            model: model.to_string(),
            transformers: Vec::new(),
            model_transformers: Vec::new(),
        }
    }

    #[test]
    fn adds_usage_stream_options_for_streaming_requests() {
        let mut body = json!({ "stream": true });
        apply_provider_request_transforms(
            &mut body,
            &json!({}),
            &credential("https://api.example.com/v1", "qwen-test"),
            true,
            &ProxyTransformerChain::from_names(&["streamoptions"]),
        );

        assert_eq!(body["stream_options"]["include_usage"], true);
    }

    #[test]
    fn caps_deepseek_max_tokens() {
        let mut body = json!({ "max_tokens": 20000 });
        apply_provider_request_transforms(
            &mut body,
            &json!({}),
            &credential("https://api.deepseek.com", "deepseek-chat"),
            false,
            &ProxyTransformerChain::from_names(&["deepseek"]),
        );

        assert_eq!(body["max_tokens"], DEEPSEEK_MAX_TOKENS);
    }

    #[test]
    fn copies_anthropic_thinking_budget_as_reasoning() {
        let mut body = json!({});
        apply_provider_request_transforms(
            &mut body,
            &json!({
                "thinking": {
                    "type": "enabled",
                    "budget_tokens": 4096
                }
            }),
            &credential("https://api.example.com/v1", "qwen-test"),
            false,
            &ProxyTransformerChain::from_names(&[]),
        );

        assert_eq!(body["reasoning"]["max_tokens"], 4096);
    }

    #[test]
    fn converts_openai_reasoning_models_to_max_completion_tokens() {
        let mut body = json!({ "max_tokens": 12000 });
        apply_provider_request_transforms(
            &mut body,
            &json!({}),
            &credential("https://api.openai.com/v1", "o3"),
            false,
            &ProxyTransformerChain::from_names(&[]),
        );

        assert!(body.get("max_tokens").is_none());
        assert_eq!(body["max_completion_tokens"], 12000);
    }

    #[test]
    fn strips_cache_control_from_openai_compatible_requests() {
        let mut body = json!({
            "messages": [{
                "role": "user",
                "content": [{
                    "type": "text",
                    "text": "hello",
                    "cache_control": { "type": "ephemeral" }
                }]
            }]
        });

        apply_provider_request_transforms(
            &mut body,
            &json!({}),
            &credential("https://api.example.com/v1", "qwen-test"),
            false,
            &ProxyTransformerChain::from_names(&["cleancache"]),
        );

        assert!(body["messages"][0]["content"][0]
            .get("cache_control")
            .is_none());
    }
}
