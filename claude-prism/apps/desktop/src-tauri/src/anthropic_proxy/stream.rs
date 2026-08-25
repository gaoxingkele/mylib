use super::tools::{normalized_tool_call_id, repair_tool_arguments};
use super::{http_response, OpenAiProxyCredential};
use serde_json::{json, Value};
use std::collections::HashMap;
use tokio::io::AsyncWriteExt;
use tokio::net::TcpStream;

#[derive(Default)]
struct OpenAiStreamState {
    message_started: bool,
    completed: bool,
    message_id: Option<String>,
    model: Option<String>,
    next_block_index: usize,
    text_block_index: Option<usize>,
    thinking_block_index: Option<usize>,
    tool_blocks: HashMap<i64, StreamToolBlock>,
    stop_reason: Option<String>,
    output_tokens: u64,
}

#[derive(Default)]
struct StreamToolBlock {
    id: Option<String>,
    name: Option<String>,
    buffered_arguments: String,
}

pub(super) async fn stream_openai_sse_to_anthropic(
    stream: &mut TcpStream,
    mut response: reqwest::Response,
    anthropic_request: &Value,
    credential: &OpenAiProxyCredential,
) -> Result<(), String> {
    stream
        .write_all(streaming_http_headers().as_bytes())
        .await
        .map_err(|err| format!("Failed to write proxy stream headers: {}", err))?;

    let mut state = OpenAiStreamState::default();
    let mut buffer = String::new();
    while let Some(chunk) = match response.chunk().await {
        Ok(chunk) => chunk,
        Err(err) => {
            let rendered =
                anthropic_stream_error_sse(&format!("Provider stream ended unexpectedly: {}", err));
            let _ = write_stream_body(stream, &rendered, "provider stream error").await;
            return Ok(());
        }
    } {
        buffer.push_str(&String::from_utf8_lossy(&chunk));
        while let Some((event, rest)) = take_next_sse_event(&buffer) {
            buffer = rest;
            let rendered =
                openai_sse_event_to_anthropic(&mut state, &event, anthropic_request, credential);
            if !write_stream_body(stream, &rendered, "proxy stream event").await {
                return Ok(());
            }
        }
    }

    if !buffer.trim().is_empty() {
        let rendered =
            openai_sse_event_to_anthropic(&mut state, &buffer, anthropic_request, credential);
        if !write_stream_body(stream, &rendered, "final proxy stream event").await {
            return Ok(());
        }
    }

    let rendered = finish_anthropic_stream(&mut state);
    let _ = write_stream_body(stream, &rendered, "proxy stream completion").await;
    Ok(())
}

fn streaming_http_headers() -> String {
    "HTTP/1.1 200 OK\r\nContent-Type: text/event-stream; charset=utf-8\r\nCache-Control: no-cache\r\nConnection: close\r\n\r\n"
        .to_string()
}

async fn write_stream_body(stream: &mut TcpStream, body: &str, context: &str) -> bool {
    if body.is_empty() {
        return true;
    }
    match stream.write_all(body.as_bytes()).await {
        Ok(()) => true,
        Err(err) => {
            eprintln!("[anthropic-proxy] failed to write {}: {}", context, err);
            false
        }
    }
}

fn anthropic_stream_error_sse(message: &str) -> String {
    let mut body = String::new();
    push_sse(
        &mut body,
        "error",
        &json!({
            "type": "error",
            "error": {
                "type": "api_error",
                "message": message,
            },
        }),
    );
    body
}

fn take_next_sse_event(buffer: &str) -> Option<(String, String)> {
    if let Some(index) = buffer.find("\n\n") {
        let event = buffer[..index].to_string();
        let rest = buffer[index + 2..].to_string();
        return Some((event, rest));
    }
    if let Some(index) = buffer.find("\r\n\r\n") {
        let event = buffer[..index].to_string();
        let rest = buffer[index + 4..].to_string();
        return Some((event, rest));
    }
    None
}

fn openai_sse_event_to_anthropic(
    state: &mut OpenAiStreamState,
    event: &str,
    anthropic_request: &Value,
    credential: &OpenAiProxyCredential,
) -> String {
    let Some(data) = sse_event_data(event) else {
        return String::new();
    };
    if data.trim() == "[DONE]" {
        return finish_anthropic_stream(state);
    }
    let Ok(chunk) = serde_json::from_str::<Value>(&data) else {
        return String::new();
    };
    openai_stream_chunk_to_anthropic(state, &chunk, anthropic_request, credential)
}

fn sse_event_data(event: &str) -> Option<String> {
    let mut parts = Vec::new();
    for line in event.lines() {
        let line = line.trim_end_matches('\r');
        if let Some(data) = line.strip_prefix("data:") {
            parts.push(data.trim_start());
        }
    }
    if parts.is_empty() {
        None
    } else {
        Some(parts.join("\n"))
    }
}

fn openai_stream_chunk_to_anthropic(
    state: &mut OpenAiStreamState,
    chunk: &Value,
    anthropic_request: &Value,
    credential: &OpenAiProxyCredential,
) -> String {
    let mut body = String::new();
    ensure_stream_message_started(state, &mut body, chunk, anthropic_request, credential);

    if let Some(usage) = chunk.get("usage") {
        state.output_tokens = usage_token(
            usage,
            &[
                "completion_tokens",
                "output_tokens",
                "completion_token_count",
            ],
        );
    }

    let Some(choice) = chunk
        .get("choices")
        .and_then(|value| value.as_array())
        .and_then(|choices| choices.first())
    else {
        return body;
    };
    let delta = choice.get("delta").unwrap_or(&Value::Null);

    if let Some(reasoning) = delta_text(delta, &["reasoning_content", "reasoning"]) {
        push_stream_text_delta(state, &mut body, "thinking", &reasoning);
    }
    if let Some(thinking) = delta
        .get("thinking")
        .and_then(|value| {
            value
                .get("content")
                .and_then(|content| content.as_str())
                .or_else(|| value.as_str())
        })
        .filter(|value| !value.is_empty())
    {
        push_stream_text_delta(state, &mut body, "thinking", thinking);
    }
    if let Some(content) = delta_text(delta, &["content"]) {
        push_stream_text_delta(state, &mut body, "text", &content);
    }
    if let Some(tool_calls) = delta.get("tool_calls").and_then(|value| value.as_array()) {
        for call in tool_calls {
            push_stream_tool_delta(state, call);
        }
    }

    if let Some(finish_reason) = choice.get("finish_reason").and_then(|value| value.as_str()) {
        if !finish_reason.is_empty() {
            state.stop_reason = Some(map_openai_finish_reason(finish_reason).to_string());
        }
    }

    body
}

fn ensure_stream_message_started(
    state: &mut OpenAiStreamState,
    body: &mut String,
    chunk: &Value,
    anthropic_request: &Value,
    credential: &OpenAiProxyCredential,
) {
    if state.message_started {
        return;
    }
    state.message_started = true;
    state.message_id = chunk
        .get("id")
        .and_then(|value| value.as_str())
        .map(str::to_string)
        .or_else(|| Some(format!("msg_{}", uuid::Uuid::new_v4().simple())));
    state.model = anthropic_request
        .get("model")
        .and_then(|value| value.as_str())
        .map(str::to_string)
        .or_else(|| {
            chunk
                .get("model")
                .and_then(|value| value.as_str())
                .map(str::to_string)
        })
        .or_else(|| Some(credential.model.clone()));

    push_sse(
        body,
        "message_start",
        &json!({
            "type": "message_start",
            "message": {
                "id": state.message_id.clone().unwrap_or_else(|| format!("msg_{}", uuid::Uuid::new_v4().simple())),
                "type": "message",
                "role": "assistant",
                "model": state.model.clone().unwrap_or_else(|| credential.model.clone()),
                "content": [],
                "stop_reason": Value::Null,
                "stop_sequence": Value::Null,
                "usage": {
                    "input_tokens": 0,
                    "output_tokens": 0,
                },
            },
        }),
    );
}

fn delta_text(delta: &Value, keys: &[&str]) -> Option<String> {
    keys.iter()
        .find_map(|key| delta.get(*key).and_then(|value| value.as_str()))
        .filter(|value| !value.is_empty())
        .map(str::to_string)
}

fn push_stream_text_delta(
    state: &mut OpenAiStreamState,
    body: &mut String,
    block_type: &str,
    text: &str,
) {
    if block_type != "thinking" {
        close_thinking_block_if_open(state, body);
    }

    let block_index = if block_type == "thinking" {
        if let Some(index) = state.thinking_block_index {
            index
        } else {
            let index = state.next_block_index;
            state.next_block_index += 1;
            state.thinking_block_index = Some(index);
            push_sse(
                body,
                "content_block_start",
                &json!({
                    "type": "content_block_start",
                    "index": index,
                    "content_block": {
                        "type": "thinking",
                        "thinking": "",
                    },
                }),
            );
            index
        }
    } else if let Some(index) = state.text_block_index {
        index
    } else {
        let index = state.next_block_index;
        state.next_block_index += 1;
        state.text_block_index = Some(index);
        push_sse(
            body,
            "content_block_start",
            &json!({
                "type": "content_block_start",
                "index": index,
                "content_block": {
                    "type": "text",
                    "text": "",
                },
            }),
        );
        index
    };

    let (delta_type, key) = if block_type == "thinking" {
        ("thinking_delta", "thinking")
    } else {
        ("text_delta", "text")
    };
    push_sse(
        body,
        "content_block_delta",
        &json!({
            "type": "content_block_delta",
            "index": block_index,
            "delta": {
                "type": delta_type,
                key: text,
            },
        }),
    );
}

fn push_stream_tool_delta(state: &mut OpenAiStreamState, call: &Value) {
    let openai_index = call
        .get("index")
        .and_then(|value| value.as_i64())
        .unwrap_or(0);
    let block = state.tool_blocks.entry(openai_index).or_default();
    if let Some(id) = call.get("id").and_then(|value| value.as_str()) {
        block.id = Some(normalized_tool_call_id(Some(id)));
    }
    let function = call.get("function").unwrap_or(&Value::Null);
    if let Some(name) = function.get("name").and_then(|value| value.as_str()) {
        if !name.is_empty() {
            block.name = Some(name.to_string());
        }
    }
    if let Some(arguments) = function.get("arguments").and_then(|value| value.as_str()) {
        block.buffered_arguments.push_str(arguments);
    }
}

fn close_thinking_block_if_open(state: &mut OpenAiStreamState, body: &mut String) {
    if let Some(index) = state.thinking_block_index.take() {
        push_sse(
            body,
            "content_block_delta",
            &json!({
                "type": "content_block_delta",
                "index": index,
                "delta": {
                    "type": "signature_delta",
                    "signature": format!("ccr_{}", uuid::Uuid::new_v4().simple()),
                },
            }),
        );
        push_content_block_stop(body, index);
    }
}

fn finish_anthropic_stream(state: &mut OpenAiStreamState) -> String {
    if state.completed {
        return String::new();
    }
    state.completed = true;
    let mut body = String::new();
    if !state.message_started {
        state.message_started = true;
        let message_id = format!("msg_{}", uuid::Uuid::new_v4().simple());
        state.message_id = Some(message_id.clone());
        push_sse(
            &mut body,
            "message_start",
            &json!({
                "type": "message_start",
                "message": {
                    "id": message_id,
                    "type": "message",
                    "role": "assistant",
                    "model": state.model.clone().unwrap_or_else(|| "claude-prism-proxy".to_string()),
                    "content": [],
                    "stop_reason": Value::Null,
                    "stop_sequence": Value::Null,
                    "usage": {
                        "input_tokens": 0,
                        "output_tokens": 0,
                    },
                },
            }),
        );
    }
    close_thinking_block_if_open(state, &mut body);
    if let Some(index) = state.text_block_index.take() {
        push_content_block_stop(&mut body, index);
    }

    let mut tool_blocks = state
        .tool_blocks
        .iter()
        .map(|(openai_index, block)| (*openai_index, block))
        .collect::<Vec<_>>();
    tool_blocks.sort_by_key(|(openai_index, _)| *openai_index);
    let exit_tool_response = if tool_blocks
        .iter()
        .all(|(_, block)| block.name.as_deref() == Some("ExitTool"))
    {
        tool_blocks
            .iter()
            .find_map(|(_, block)| exit_tool_response(&block.buffered_arguments))
    } else {
        None
    };
    if let Some(response) = exit_tool_response {
        push_stream_text_delta(state, &mut body, "text", &response);
        if let Some(index) = state.text_block_index.take() {
            push_content_block_stop(&mut body, index);
        }
        state.tool_blocks.clear();
        state.stop_reason = Some("end_turn".to_string());
    }
    let mut tool_blocks = state
        .tool_blocks
        .iter()
        .map(|(openai_index, block)| (*openai_index, block))
        .collect::<Vec<_>>();
    tool_blocks.sort_by_key(|(openai_index, _)| *openai_index);
    for (_, block) in tool_blocks {
        let index = state.next_block_index;
        state.next_block_index += 1;
        push_sse(
            &mut body,
            "content_block_start",
            &json!({
                "type": "content_block_start",
                "index": index,
                "content_block": {
                    "type": "tool_use",
                    "id": block.id.clone().unwrap_or_else(|| normalized_tool_call_id(None)),
                    "name": block.name.clone().unwrap_or_else(|| "unknown".to_string()),
                    "input": {},
                },
            }),
        );
        let repaired_arguments = repair_tool_arguments(&block.buffered_arguments);
        if repaired_arguments != "{}" || !block.buffered_arguments.trim().is_empty() {
            push_sse(
                &mut body,
                "content_block_delta",
                &json!({
                    "type": "content_block_delta",
                    "index": index,
                    "delta": {
                        "type": "input_json_delta",
                        "partial_json": repaired_arguments,
                    },
                }),
            );
        }
        push_content_block_stop(&mut body, index);
    }
    let stop_reason = if state.tool_blocks.is_empty() {
        state
            .stop_reason
            .clone()
            .unwrap_or_else(|| "end_turn".to_string())
    } else {
        "tool_use".to_string()
    };
    push_sse(
        &mut body,
        "message_delta",
        &json!({
            "type": "message_delta",
            "delta": {
                "stop_reason": stop_reason,
                "stop_sequence": Value::Null,
            },
            "usage": {
                "output_tokens": state.output_tokens,
            },
        }),
    );
    push_sse(
        &mut body,
        "message_stop",
        &json!({ "type": "message_stop" }),
    );
    body
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

fn push_content_block_stop(body: &mut String, index: usize) {
    push_sse(
        body,
        "content_block_stop",
        &json!({
            "type": "content_block_stop",
            "index": index,
        }),
    );
}

fn map_openai_finish_reason(reason: &str) -> &str {
    match reason {
        "length" => "max_tokens",
        "tool_calls" => "tool_use",
        _ => "end_turn",
    }
}

pub(super) fn sse_response(message: &Value) -> String {
    let content = message
        .get("content")
        .and_then(|value| value.as_array())
        .cloned()
        .unwrap_or_default();
    let input_tokens = message
        .pointer("/usage/input_tokens")
        .and_then(|value| value.as_u64())
        .unwrap_or(0);
    let output_tokens = message
        .pointer("/usage/output_tokens")
        .and_then(|value| value.as_u64())
        .unwrap_or(0);

    let start = json!({
        "type": "message_start",
        "message": {
            "id": message.get("id").cloned().unwrap_or_else(|| json!(format!("msg_{}", uuid::Uuid::new_v4().simple()))),
            "type": "message",
            "role": "assistant",
            "model": message.get("model").cloned().unwrap_or_else(|| json!("claude-prism-proxy")),
            "content": [],
            "stop_reason": Value::Null,
            "stop_sequence": Value::Null,
            "usage": {
                "input_tokens": input_tokens,
                "output_tokens": 0,
            },
        },
    });

    let mut body = String::new();
    push_sse(&mut body, "message_start", &start);
    for (index, block) in content.iter().enumerate() {
        let block_type = block
            .get("type")
            .and_then(|value| value.as_str())
            .unwrap_or("text");
        match block_type {
            "tool_use" => {
                let content_block = json!({
                    "type": "tool_use",
                    "id": block.get("id").cloned().unwrap_or_else(|| json!(format!("toolu_{}", uuid::Uuid::new_v4().simple()))),
                    "name": block.get("name").cloned().unwrap_or_else(|| json!("unknown")),
                    "input": {},
                });
                push_sse(
                    &mut body,
                    "content_block_start",
                    &json!({
                        "type": "content_block_start",
                        "index": index,
                        "content_block": content_block,
                    }),
                );
                let input = block.get("input").cloned().unwrap_or_else(|| json!({}));
                push_sse(
                    &mut body,
                    "content_block_delta",
                    &json!({
                        "type": "content_block_delta",
                        "index": index,
                        "delta": {
                            "type": "input_json_delta",
                            "partial_json": input.to_string(),
                        },
                    }),
                );
            }
            "thinking" => {
                push_text_like_sse_block(
                    &mut body,
                    index,
                    "thinking",
                    block
                        .get("thinking")
                        .and_then(|value| value.as_str())
                        .unwrap_or_default(),
                );
            }
            _ => {
                push_text_like_sse_block(
                    &mut body,
                    index,
                    "text",
                    block
                        .get("text")
                        .and_then(|value| value.as_str())
                        .unwrap_or_default(),
                );
            }
        }
        push_content_block_stop(&mut body, index);
    }
    push_sse(
        &mut body,
        "message_delta",
        &json!({
            "type": "message_delta",
            "delta": {
                "stop_reason": message.get("stop_reason").cloned().unwrap_or_else(|| json!("end_turn")),
                "stop_sequence": Value::Null,
            },
            "usage": {
                "output_tokens": output_tokens,
            },
        }),
    );
    push_sse(
        &mut body,
        "message_stop",
        &json!({ "type": "message_stop" }),
    );

    http_response(
        200,
        "text/event-stream; charset=utf-8",
        &format!("{}{}", body, "\n"),
    )
}

fn push_text_like_sse_block(body: &mut String, index: usize, block_type: &str, text: &str) {
    let content_block = if block_type == "thinking" {
        json!({
            "type": "thinking",
            "thinking": "",
        })
    } else {
        json!({
            "type": "text",
            "text": "",
        })
    };
    push_sse(
        body,
        "content_block_start",
        &json!({
            "type": "content_block_start",
            "index": index,
            "content_block": content_block,
        }),
    );
    if !text.is_empty() {
        let delta_type = if block_type == "thinking" {
            "thinking_delta"
        } else {
            "text_delta"
        };
        let delta_key = if block_type == "thinking" {
            "thinking"
        } else {
            "text"
        };
        push_sse(
            body,
            "content_block_delta",
            &json!({
                "type": "content_block_delta",
                "index": index,
                "delta": {
                    "type": delta_type,
                    delta_key: text,
                },
            }),
        );
    }
    if block_type == "thinking" {
        push_sse(
            body,
            "content_block_delta",
            &json!({
                "type": "content_block_delta",
                "index": index,
                "delta": {
                    "type": "signature_delta",
                    "signature": format!("ccr_{}", uuid::Uuid::new_v4().simple()),
                },
            }),
        );
    }
}

fn push_sse(body: &mut String, event: &str, data: &Value) {
    body.push_str("event: ");
    body.push_str(event);
    body.push('\n');
    body.push_str("data: ");
    body.push_str(&data.to_string());
    body.push_str("\n\n");
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

    #[test]
    fn renders_provider_stream_errors_as_anthropic_sse_errors() {
        let rendered = anthropic_stream_error_sse("provider stream broke");

        assert!(rendered.contains("event: error"));
        assert!(rendered.contains("\"type\":\"error\""));
        assert!(rendered.contains("\"type\":\"api_error\""));
        assert!(rendered.contains("\"message\":\"provider stream broke\""));
    }

    #[test]
    fn streams_openai_text_delta_as_anthropic_sse() {
        let request = json!({ "model": "claude-sonnet-4" });
        let mut state = OpenAiStreamState::default();
        let chunk = json!({
            "id": "chatcmpl_1",
            "model": "qwen-test",
            "choices": [{
                "delta": { "content": "Hello" },
                "finish_reason": null
            }]
        });

        let first = openai_stream_chunk_to_anthropic(&mut state, &chunk, &request, &credential());
        let done = finish_anthropic_stream(&mut state);
        let combined = format!("{}{}", first, done);

        assert!(combined.contains("event: message_start"));
        assert!(combined.contains("\"model\":\"claude-sonnet-4\""));
        assert!(combined.contains("\"type\":\"text_delta\""));
        assert!(combined.contains("\"text\":\"Hello\""));
        assert!(combined.contains("\"stop_reason\":\"end_turn\""));
        assert!(finish_anthropic_stream(&mut state).is_empty());
    }

    #[test]
    fn streams_reasoning_content_as_thinking_delta() {
        let request = json!({ "model": "claude-sonnet-4" });
        let mut state = OpenAiStreamState::default();
        let chunk = json!({
            "id": "chatcmpl_1",
            "choices": [{
                "delta": { "reasoning_content": "I should inspect files." },
                "finish_reason": null
            }]
        });

        let rendered =
            openai_stream_chunk_to_anthropic(&mut state, &chunk, &request, &credential());

        assert!(rendered.contains("\"type\":\"thinking\""));
        assert!(rendered.contains("\"type\":\"thinking_delta\""));
        assert!(rendered.contains("\"thinking\":\"I should inspect files.\""));
        let done = finish_anthropic_stream(&mut state);
        assert!(done.contains("\"type\":\"signature_delta\""));
    }

    #[test]
    fn buffers_and_repairs_streamed_tool_arguments() {
        let request = json!({ "model": "claude-sonnet-4" });
        let mut state = OpenAiStreamState::default();
        let first_chunk = json!({
            "id": "chatcmpl_1",
            "choices": [{
                "delta": {
                    "tool_calls": [{
                        "index": 0,
                        "id": "call_1",
                        "type": "function",
                        "function": {
                            "name": "Read",
                            "arguments": "{\"file_path\":"
                        }
                    }]
                },
                "finish_reason": null
            }]
        });
        let second_chunk = json!({
            "id": "chatcmpl_1",
            "choices": [{
                "delta": {
                    "tool_calls": [{
                        "index": 0,
                        "function": { "arguments": "\"main.tex\"" }
                    }]
                },
                "finish_reason": "tool_calls"
            }]
        });

        let first =
            openai_stream_chunk_to_anthropic(&mut state, &first_chunk, &request, &credential());
        let second =
            openai_stream_chunk_to_anthropic(&mut state, &second_chunk, &request, &credential());
        let done = finish_anthropic_stream(&mut state);
        let combined = format!("{}{}{}", first, second, done);

        assert!(!first.contains("\"type\":\"tool_use\""));
        assert!(!second.contains("\"type\":\"tool_use\""));
        assert!(combined.contains("\"type\":\"tool_use\""));
        assert!(combined.contains("\"id\":\"call_1\""));
        assert!(combined.contains("\"name\":\"Read\""));
        assert!(combined.contains("\"type\":\"input_json_delta\""));
        assert!(combined.contains("{\\\"file_path\\\":\\\"main.tex\\\"}"));
        assert!(combined.contains("\"stop_reason\":\"tool_use\""));
    }

    #[test]
    fn normalizes_numeric_streamed_tool_call_ids() {
        let request = json!({ "model": "claude-sonnet-4" });
        let mut state = OpenAiStreamState::default();
        let chunk = json!({
            "id": "chatcmpl_1",
            "choices": [{
                "delta": {
                    "tool_calls": [{
                        "index": 0,
                        "id": "123",
                        "type": "function",
                        "function": {
                            "name": "Read",
                            "arguments": "{\"file_path\":\"main.tex\"}"
                        }
                    }]
                },
                "finish_reason": "tool_calls"
            }]
        });

        openai_stream_chunk_to_anthropic(&mut state, &chunk, &request, &credential());
        let done = finish_anthropic_stream(&mut state);

        assert!(done.contains("\"id\":\"call_"));
        assert!(!done.contains("\"id\":\"123\""));
    }

    #[test]
    fn streams_exit_tool_as_final_text() {
        let request = json!({ "model": "claude-sonnet-4" });
        let mut state = OpenAiStreamState::default();
        let chunk = json!({
            "id": "chatcmpl_1",
            "choices": [{
                "delta": {
                    "tool_calls": [{
                        "index": 0,
                        "id": "call_exit",
                        "type": "function",
                        "function": {
                            "name": "ExitTool",
                            "arguments": "{\"response\":\"all done\"}"
                        }
                    }]
                },
                "finish_reason": "tool_calls"
            }]
        });

        openai_stream_chunk_to_anthropic(&mut state, &chunk, &request, &credential());
        let done = finish_anthropic_stream(&mut state);

        assert!(done.contains("\"type\":\"text_delta\""));
        assert!(done.contains("\"text\":\"all done\""));
        assert!(done.contains("\"stop_reason\":\"end_turn\""));
        assert!(!done.contains("\"type\":\"tool_use\""));
    }
}
