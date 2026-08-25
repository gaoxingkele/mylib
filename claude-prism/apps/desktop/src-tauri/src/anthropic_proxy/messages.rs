use super::tools::{normalized_tool_call_id, repair_tool_arguments, repaired_tool_arguments_value};
use super::transformers::ProxyTransformerChain;
use super::OpenAiProxyCredential;
use serde_json::{json, Value};

const EXIT_TOOL_NAME: &str = "ExitTool";

pub(super) fn anthropic_to_openai_request(
    request: &Value,
    credential: &OpenAiProxyCredential,
    transformers: &ProxyTransformerChain,
) -> Result<Value, String> {
    let mut messages = Vec::new();
    if let Some(system) = request.get("system").and_then(flatten_anthropic_content) {
        if !system.trim().is_empty() {
            messages.push(json!({ "role": "system", "content": system }));
        }
    }

    for message in request
        .get("messages")
        .and_then(|value| value.as_array())
        .ok_or_else(|| "Anthropic request is missing messages[]".to_string())?
    {
        append_openai_messages_for_anthropic_message(&mut messages, message);
    }
    let messages = normalize_openai_tool_message_pairs(messages);

    let mut body = json!({
        "model": credential.model,
        "messages": messages,
        "stream": false,
    });
    copy_number_field(request, &mut body, "temperature");
    copy_number_field(request, &mut body, "top_p");
    copy_number_field(request, &mut body, "top_k");
    copy_number_field(request, &mut body, "max_tokens");
    if let Some(stop) = request.get("stop_sequences") {
        body["stop"] = stop.clone();
    }

    if let Some(tools) = request.get("tools").and_then(|value| value.as_array()) {
        let converted = tools
            .iter()
            .filter_map(anthropic_tool_to_openai_tool)
            .collect::<Vec<_>>();
        if !converted.is_empty() {
            let tool_choice = if transformers.has_tooluse() {
                Value::String("required".to_string())
            } else {
                openai_tool_choice(request.get("tool_choice"))
            };
            let mut converted = converted;
            if tool_choice == Value::String("required".to_string()) {
                append_exit_tool(&mut converted);
                append_exit_tool_reminder(&mut body);
            }
            body["tools"] = Value::Array(converted);
            body["tool_choice"] = tool_choice;
        }
    }

    Ok(body)
}

pub(super) fn openai_to_anthropic_message(
    anthropic_request: &Value,
    openai_response: &Value,
    credential: &OpenAiProxyCredential,
) -> Result<Value, String> {
    let message = openai_response
        .pointer("/choices/0/message")
        .ok_or_else(|| "Provider response is missing choices[0].message".to_string())?;
    let mut content = Vec::new();

    if let Some(reasoning) = openai_message_thinking(message) {
        content.push(json!({ "type": "thinking", "thinking": reasoning }));
    }

    if let Some(text) = openai_message_text(message).filter(|value| !value.trim().is_empty()) {
        content.push(json!({ "type": "text", "text": text }));
    }

    if let Some(tool_calls) = message.get("tool_calls").and_then(|value| value.as_array()) {
        for call in tool_calls {
            let function = call.get("function").unwrap_or(&Value::Null);
            let name = function
                .get("name")
                .and_then(|value| value.as_str())
                .unwrap_or("unknown");
            let arguments = function
                .get("arguments")
                .and_then(|value| value.as_str())
                .unwrap_or("{}");
            if name == EXIT_TOOL_NAME {
                if let Some(response) = exit_tool_response(arguments) {
                    content.push(json!({ "type": "text", "text": response }));
                }
                continue;
            }
            let input = repaired_tool_arguments_value(arguments);
            let id = normalized_tool_call_id(call.get("id").and_then(|value| value.as_str()));
            content.push(json!({
                "type": "tool_use",
                "id": id,
                "name": name,
                "input": input,
            }));
        }
    }

    if content.is_empty() {
        content.push(json!({ "type": "text", "text": "" }));
    }

    let finish_reason = openai_response
        .pointer("/choices/0/finish_reason")
        .and_then(|value| value.as_str());
    let stop_reason = if content
        .iter()
        .any(|block| block.get("type").and_then(|value| value.as_str()) == Some("tool_use"))
    {
        "tool_use"
    } else {
        match finish_reason {
            Some("length") => "max_tokens",
            Some("tool_calls") if !contains_only_exit_tool(message) => "tool_use",
            _ => "end_turn",
        }
    };

    let usage = openai_response.get("usage").unwrap_or(&Value::Null);
    Ok(json!({
        "id": openai_response
            .get("id")
            .and_then(|value| value.as_str())
            .map(str::to_string)
            .unwrap_or_else(|| format!("msg_{}", uuid::Uuid::new_v4().simple())),
        "type": "message",
        "role": "assistant",
        "model": anthropic_request
            .get("model")
            .and_then(|value| value.as_str())
            .unwrap_or(&credential.model),
        "content": content,
        "stop_reason": stop_reason,
        "stop_sequence": Value::Null,
        "usage": {
            "input_tokens": usage_token(usage, &["prompt_tokens", "input_tokens", "prompt_token_count"]),
            "output_tokens": usage_token(usage, &["completion_tokens", "output_tokens", "completion_token_count"]),
        },
    }))
}

fn append_openai_messages_for_anthropic_message(messages: &mut Vec<Value>, message: &Value) {
    let role = message
        .get("role")
        .and_then(|value| value.as_str())
        .unwrap_or("user");
    let content = message.get("content").unwrap_or(&Value::Null);

    if role == "assistant" {
        let (text, tool_calls, thinking) = assistant_content_to_openai(content);
        let mut openai_message = json!({
            "role": "assistant",
            "content": if text.trim().is_empty() { Value::Null } else { Value::String(text) },
        });
        if !tool_calls.is_empty() {
            openai_message["tool_calls"] = Value::Array(tool_calls);
        }
        if let Some(thinking) = thinking {
            openai_message["thinking"] = thinking;
        }
        messages.push(openai_message);
        return;
    }

    if let Some(blocks) = content.as_array() {
        let content_parts = user_content_blocks_to_openai_parts(blocks);
        if !content_parts.is_empty() {
            let content = if content_parts.len() == 1
                && content_parts[0]
                    .get("type")
                    .and_then(|value| value.as_str())
                    == Some("text")
            {
                content_parts[0]
                    .get("text")
                    .cloned()
                    .unwrap_or_else(|| json!(""))
            } else {
                Value::Array(content_parts)
            };
            messages.push(json!({ "role": role, "content": content }));
        }

        for block in blocks {
            if block.get("type").and_then(|value| value.as_str()) != Some("tool_result") {
                continue;
            }
            let tool_call_id = block
                .get("tool_use_id")
                .and_then(|value| value.as_str())
                .unwrap_or("toolu_unknown");
            let (content, image_parts) =
                tool_result_content_to_openai(block.get("content").unwrap_or(&Value::Null));
            let content = if content.trim().is_empty() && !image_parts.is_empty() {
                "Tool returned image content.".to_string()
            } else {
                content
            };
            messages.push(json!({
                "role": "tool",
                "tool_call_id": tool_call_id,
                "content": content,
            }));
            if !image_parts.is_empty() {
                let mut content_parts = vec![json!({
                    "type": "text",
                    "text": format!(
                        "Tool result for {} included image content. Use the attached image when answering.",
                        tool_call_id
                    ),
                })];
                content_parts.extend(image_parts);
                messages.push(json!({
                    "role": "user",
                    "content": content_parts,
                }));
            }
        }
        return;
    }

    let text = content
        .as_str()
        .map(str::to_string)
        .unwrap_or_else(|| content.to_string());
    messages.push(json!({ "role": role, "content": text }));
}

fn user_content_blocks_to_openai_parts(blocks: &[Value]) -> Vec<Value> {
    blocks
        .iter()
        .filter_map(
            |block| match block.get("type").and_then(|value| value.as_str()) {
                Some("text") => block
                    .get("text")
                    .and_then(|value| value.as_str())
                    .filter(|value| !value.is_empty())
                    .map(|text| json!({ "type": "text", "text": text })),
                Some("image") => anthropic_image_block_to_openai_part(block),
                _ => None,
            },
        )
        .collect()
}

fn anthropic_image_block_to_openai_part(block: &Value) -> Option<Value> {
    let source = block.get("source")?;
    let url = match source.get("type").and_then(|value| value.as_str()) {
        Some("base64") => {
            let media_type = source
                .get("media_type")
                .and_then(|value| value.as_str())
                .unwrap_or("image/png");
            let data = source.get("data").and_then(|value| value.as_str())?;
            format!("data:{};base64,{}", media_type, data)
        }
        Some("url") => source
            .get("url")
            .and_then(|value| value.as_str())?
            .to_string(),
        _ => return None,
    };
    Some(json!({
        "type": "image_url",
        "image_url": {
            "url": url,
            "detail": "high",
        },
    }))
}

fn normalize_openai_tool_message_pairs(messages: Vec<Value>) -> Vec<Value> {
    let mut normalized = Vec::with_capacity(messages.len());
    let mut consumed = vec![false; messages.len()];

    for index in 0..messages.len() {
        if consumed[index] {
            continue;
        }

        let message = &messages[index];
        let tool_call_ids = openai_assistant_tool_call_ids(message);
        if !tool_call_ids.is_empty() {
            consumed[index] = true;
            normalized.push(message.clone());

            for tool_call_id in tool_call_ids {
                if let Some(tool_index) =
                    find_following_tool_message(&messages, &consumed, index + 1, &tool_call_id)
                {
                    consumed[tool_index] = true;
                    normalized.push(messages[tool_index].clone());
                } else {
                    normalized.push(json!({
                        "role": "tool",
                        "tool_call_id": tool_call_id,
                        "content": "Tool result unavailable in the prior Claude Code transcript.",
                    }));
                }
            }
            continue;
        }

        consumed[index] = true;
        if openai_message_role(message) == Some("tool") {
            normalized.push(orphan_tool_message_to_user_message(message));
        } else {
            normalized.push(message.clone());
        }
    }

    normalized
}

fn openai_assistant_tool_call_ids(message: &Value) -> Vec<String> {
    if openai_message_role(message) != Some("assistant") {
        return Vec::new();
    }

    message
        .get("tool_calls")
        .and_then(|value| value.as_array())
        .map(|tool_calls| {
            tool_calls
                .iter()
                .filter_map(|tool_call| tool_call.get("id").and_then(|value| value.as_str()))
                .map(str::to_string)
                .collect()
        })
        .unwrap_or_default()
}

fn find_following_tool_message(
    messages: &[Value],
    consumed: &[bool],
    start: usize,
    tool_call_id: &str,
) -> Option<usize> {
    for index in start..messages.len() {
        if consumed[index] {
            continue;
        }
        let message = &messages[index];
        if openai_message_role(message) == Some("assistant") {
            break;
        }
        if openai_tool_message_id(message) == Some(tool_call_id) {
            return Some(index);
        }
    }
    None
}

fn orphan_tool_message_to_user_message(message: &Value) -> Value {
    let tool_call_id = openai_tool_message_id(message).unwrap_or("unknown");
    let content = message
        .get("content")
        .and_then(|value| value.as_str())
        .map(str::to_string)
        .unwrap_or_else(|| {
            message
                .get("content")
                .cloned()
                .unwrap_or(Value::Null)
                .to_string()
        });

    json!({
        "role": "user",
        "content": format!("Tool result for {}:\n{}", tool_call_id, content),
    })
}

fn openai_message_role(message: &Value) -> Option<&str> {
    message.get("role").and_then(|value| value.as_str())
}

fn openai_tool_message_id(message: &Value) -> Option<&str> {
    if openai_message_role(message) != Some("tool") {
        return None;
    }
    message.get("tool_call_id").and_then(|value| value.as_str())
}

fn flatten_anthropic_content(value: &Value) -> Option<String> {
    if let Some(text) = value.as_str() {
        return Some(text.to_string());
    }

    value.as_array().map(|blocks| {
        blocks
            .iter()
            .filter_map(|block| {
                block
                    .get("text")
                    .and_then(|value| value.as_str())
                    .or_else(|| block.get("content").and_then(|value| value.as_str()))
            })
            .collect::<Vec<_>>()
            .join("\n\n")
    })
}

fn assistant_content_to_openai(content: &Value) -> (String, Vec<Value>, Option<Value>) {
    let Some(blocks) = content.as_array() else {
        return (
            content
                .as_str()
                .map(str::to_string)
                .unwrap_or_else(|| content.to_string()),
            Vec::new(),
            None,
        );
    };

    let mut text = Vec::new();
    let mut tool_calls = Vec::new();
    let mut thinking = None;
    for block in blocks {
        match block.get("type").and_then(|value| value.as_str()) {
            Some("text") => {
                if let Some(value) = block.get("text").and_then(|value| value.as_str()) {
                    text.push(value);
                }
            }
            Some("tool_use") => {
                let id = block
                    .get("id")
                    .and_then(|value| value.as_str())
                    .unwrap_or("toolu_unknown");
                let name = block
                    .get("name")
                    .and_then(|value| value.as_str())
                    .unwrap_or("unknown");
                let input = block.get("input").cloned().unwrap_or_else(|| json!({}));
                tool_calls.push(json!({
                    "id": id,
                    "type": "function",
                    "function": {
                        "name": name,
                        "arguments": input.to_string(),
                    },
                }));
            }
            Some("thinking") => {
                if let Some(value) = block.get("thinking").and_then(|value| value.as_str()) {
                    let mut thinking_value = json!({ "content": value });
                    if let Some(signature) = block.get("signature").and_then(|value| value.as_str())
                    {
                        thinking_value["signature"] = Value::String(signature.to_string());
                    }
                    thinking = Some(thinking_value);
                }
            }
            _ => {}
        }
    }

    (text.join("\n\n"), tool_calls, thinking)
}

fn tool_result_content_to_openai(content: &Value) -> (String, Vec<Value>) {
    if let Some(text) = content.as_str() {
        return (text.to_string(), Vec::new());
    }
    if let Some(blocks) = content.as_array() {
        let mut text = Vec::new();
        let mut image_parts = Vec::new();
        for block in blocks {
            if let Some(value) = block
                .get("text")
                .and_then(|value| value.as_str())
                .or_else(|| block.get("content").and_then(|value| value.as_str()))
            {
                text.push(value);
                continue;
            }
            if block.get("type").and_then(|value| value.as_str()) == Some("image") {
                if let Some(part) = anthropic_image_block_to_openai_part(block) {
                    image_parts.push(part);
                }
            }
        }
        return (text.join("\n\n"), image_parts);
    }
    (content.to_string(), Vec::new())
}

fn anthropic_tool_to_openai_tool(tool: &Value) -> Option<Value> {
    let name = tool.get("name")?.as_str()?;
    let description = tool
        .get("description")
        .and_then(|value| value.as_str())
        .unwrap_or_default();
    let parameters = tool
        .get("input_schema")
        .cloned()
        .unwrap_or_else(|| json!({ "type": "object", "properties": {} }));

    Some(json!({
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": parameters,
        },
    }))
}

fn append_exit_tool(tools: &mut Vec<Value>) {
    if tools.iter().any(|tool| {
        tool.pointer("/function/name")
            .and_then(|value| value.as_str())
            == Some(EXIT_TOOL_NAME)
    }) {
        return;
    }
    tools.push(json!({
        "type": "function",
        "function": {
            "name": EXIT_TOOL_NAME,
            "description": "Use this when tool mode is active and no remaining tool call is needed. This is the valid way to exit tool mode with a final answer.",
            "parameters": {
                "type": "object",
                "properties": {
                    "response": {
                        "type": "string",
                        "description": "Final response to show the user exactly as written."
                    }
                },
                "required": ["response"]
            }
        }
    }));
}

fn append_exit_tool_reminder(body: &mut Value) {
    let Some(messages) = body
        .get_mut("messages")
        .and_then(|value| value.as_array_mut())
    else {
        return;
    };
    messages.push(json!({
        "role": "system",
        "content": "<system-reminder>Tool mode is active. The user expects you to proactively execute the most suitable tool to help complete the task. Before invoking a tool, carefully evaluate whether it matches the current task. If no available tool is appropriate, or the task is complete, call ExitTool with the final response instead of inventing another tool call.</system-reminder>",
    }));
}

fn openai_tool_choice(choice: Option<&Value>) -> Value {
    let Some(choice) = choice else {
        return Value::String("auto".to_string());
    };
    match choice.get("type").and_then(|value| value.as_str()) {
        Some("auto") => Value::String("auto".to_string()),
        Some("any") => Value::String("required".to_string()),
        Some("tool") => {
            let name = choice
                .get("name")
                .and_then(|value| value.as_str())
                .unwrap_or_default();
            json!({
                "type": "function",
                "function": { "name": name },
            })
        }
        _ => Value::String("auto".to_string()),
    }
}

fn copy_number_field(source: &Value, target: &mut Value, key: &str) {
    if let Some(value) = source.get(key).filter(|value| value.is_number()) {
        target[key] = value.clone();
    }
}

fn openai_message_text(message: &Value) -> Option<String> {
    let content = message.get("content")?;
    if let Some(text) = content.as_str() {
        return Some(text.to_string());
    }
    content.as_array().map(|parts| {
        parts
            .iter()
            .filter_map(|part| {
                part.get("text")
                    .and_then(|value| value.as_str())
                    .or_else(|| {
                        if part.get("type").and_then(|value| value.as_str()) == Some("text") {
                            part.get("content").and_then(|value| value.as_str())
                        } else {
                            None
                        }
                    })
            })
            .collect::<Vec<_>>()
            .join("\n")
    })
}

fn openai_message_thinking(message: &Value) -> Option<String> {
    message
        .get("reasoning_content")
        .or_else(|| message.get("reasoning"))
        .and_then(|value| value.as_str())
        .filter(|value| !value.trim().is_empty())
        .map(str::to_string)
        .or_else(|| {
            message
                .get("thinking")
                .and_then(|value| {
                    value
                        .get("content")
                        .and_then(|content| content.as_str())
                        .or_else(|| value.as_str())
                })
                .filter(|value| !value.trim().is_empty())
                .map(str::to_string)
        })
}

fn exit_tool_response(arguments: &str) -> Option<String> {
    let repaired = repair_tool_arguments(arguments);
    serde_json::from_str::<Value>(&repaired)
        .ok()
        .and_then(|value| {
            value
                .get("response")
                .and_then(|value| value.as_str())
                .map(str::to_string)
        })
        .filter(|value| !value.trim().is_empty())
}

fn contains_only_exit_tool(message: &Value) -> bool {
    let Some(tool_calls) = message.get("tool_calls").and_then(|value| value.as_array()) else {
        return false;
    };
    !tool_calls.is_empty()
        && tool_calls.iter().all(|call| {
            call.pointer("/function/name")
                .and_then(|value| value.as_str())
                == Some(EXIT_TOOL_NAME)
        })
}

fn usage_token(usage: &Value, keys: &[&str]) -> u64 {
    keys.iter()
        .find_map(|key| usage.get(*key).and_then(|value| value.as_u64()))
        .unwrap_or(0)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn credential() -> OpenAiProxyCredential {
        OpenAiProxyCredential {
            api_key: "sk-test".to_string(),
            base_url: "https://api.example.com/v1".to_string(),
            model: "qwen-test".to_string(),
            transformers: Vec::new(),
            model_transformers: Vec::new(),
        }
    }

    fn transformers(names: &[&str]) -> ProxyTransformerChain {
        ProxyTransformerChain::from_names(names)
    }

    #[test]
    fn preserves_anthropic_image_blocks_as_openai_image_url_parts() {
        let request = json!({
            "messages": [{
                "role": "user",
                "content": [
                    { "type": "text", "text": "what is this?" },
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": "abcd"
                        }
                    }
                ]
            }]
        });

        let converted =
            anthropic_to_openai_request(&request, &credential(), &transformers(&[])).unwrap();

        assert_eq!(converted["messages"][0]["content"][0]["type"], "text");
        assert_eq!(converted["messages"][0]["content"][1]["type"], "image_url");
        assert_eq!(
            converted["messages"][0]["content"][1]["image_url"]["url"],
            "data:image/png;base64,abcd"
        );
        assert_eq!(
            converted["messages"][0]["content"][1]["image_url"]["detail"],
            "high"
        );
    }

    #[test]
    fn preserves_tool_result_images_as_follow_up_user_image_parts() {
        let request = json!({
            "messages": [
                {
                    "role": "assistant",
                    "content": [{
                        "type": "tool_use",
                        "id": "toolu_read_image",
                        "name": "Read",
                        "input": { "file_path": "attachments/figure.png" }
                    }]
                },
                {
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": "toolu_read_image",
                        "content": [
                            { "type": "text", "text": "Image read successfully." },
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": "abcd"
                                }
                            }
                        ]
                    }]
                }
            ]
        });

        let converted =
            anthropic_to_openai_request(&request, &credential(), &transformers(&[])).unwrap();

        assert_eq!(converted["messages"][0]["role"], "assistant");
        assert_eq!(converted["messages"][1]["role"], "tool");
        assert_eq!(converted["messages"][1]["tool_call_id"], "toolu_read_image");
        assert_eq!(
            converted["messages"][1]["content"],
            "Image read successfully."
        );
        assert_eq!(converted["messages"][2]["role"], "user");
        assert_eq!(converted["messages"][2]["content"][0]["type"], "text");
        assert_eq!(converted["messages"][2]["content"][1]["type"], "image_url");
        assert_eq!(
            converted["messages"][2]["content"][1]["image_url"]["url"],
            "data:image/png;base64,abcd"
        );
        assert_eq!(
            converted["messages"][2]["content"][1]["image_url"]["detail"],
            "high"
        );
    }

    #[test]
    fn preserves_assistant_thinking_for_provider_context() {
        let request = json!({
            "messages": [{
                "role": "assistant",
                "content": [
                    {
                        "type": "thinking",
                        "thinking": "I inspected the files.",
                        "signature": "sig_1"
                    },
                    {
                        "type": "text",
                        "text": "Done."
                    }
                ]
            }]
        });

        let converted =
            anthropic_to_openai_request(&request, &credential(), &transformers(&[])).unwrap();

        assert_eq!(
            converted["messages"][0]["thinking"]["content"],
            "I inspected the files."
        );
        assert_eq!(converted["messages"][0]["thinking"]["signature"], "sig_1");
    }

    #[test]
    fn adds_exit_tool_when_tool_choice_requires_a_tool() {
        let request = json!({
            "messages": [{ "role": "user", "content": "finish" }],
            "tool_choice": { "type": "any" },
            "tools": [{
                "name": "Read",
                "description": "Read a file",
                "input_schema": { "type": "object" }
            }]
        });

        let converted =
            anthropic_to_openai_request(&request, &credential(), &transformers(&[])).unwrap();
        let tool_names = converted["tools"]
            .as_array()
            .unwrap()
            .iter()
            .filter_map(|tool| {
                tool.pointer("/function/name")
                    .and_then(|value| value.as_str())
            })
            .collect::<Vec<_>>();

        assert!(tool_names.contains(&"Read"));
        assert!(tool_names.contains(&EXIT_TOOL_NAME));
        assert_eq!(converted["tool_choice"], "required");
    }

    #[test]
    fn tooluse_transformer_forces_exit_tool_like_ccr() {
        let request = json!({
            "messages": [{ "role": "user", "content": "finish" }],
            "tools": [{
                "name": "Read",
                "description": "Read a file",
                "input_schema": { "type": "object" }
            }]
        });

        let converted =
            anthropic_to_openai_request(&request, &credential(), &transformers(&["tooluse"]))
                .unwrap();
        let tool_names = converted["tools"]
            .as_array()
            .unwrap()
            .iter()
            .filter_map(|tool| {
                tool.pointer("/function/name")
                    .and_then(|value| value.as_str())
            })
            .collect::<Vec<_>>();

        assert_eq!(converted["tool_choice"], "required");
        assert!(tool_names.contains(&"Read"));
        assert!(tool_names.contains(&EXIT_TOOL_NAME));
        assert!(converted["messages"]
            .as_array()
            .unwrap()
            .iter()
            .any(|message| message
                .get("content")
                .and_then(|value| value.as_str())
                .is_some_and(|content| content.contains("Tool mode is active"))));
    }

    #[test]
    fn converts_exit_tool_response_to_final_text() {
        let request = json!({ "model": "claude-sonnet-4" });
        let response = json!({
            "id": "chatcmpl_1",
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": null,
                    "tool_calls": [{
                        "id": "call_exit",
                        "type": "function",
                        "function": {
                            "name": "ExitTool",
                            "arguments": "{\"response\":\"done\"}"
                        }
                    }]
                },
                "finish_reason": "tool_calls"
            }],
            "usage": { "prompt_tokens": 5, "completion_tokens": 2 }
        });

        let converted = openai_to_anthropic_message(&request, &response, &credential()).unwrap();

        assert_eq!(converted["stop_reason"], "end_turn");
        assert_eq!(converted["content"][0]["type"], "text");
        assert_eq!(converted["content"][0]["text"], "done");
    }
}
