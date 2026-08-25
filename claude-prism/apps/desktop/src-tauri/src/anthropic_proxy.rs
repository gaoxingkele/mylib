mod messages;
mod providers;
mod stream;
mod tools;
mod transformers;

use self::messages::{anthropic_to_openai_request, openai_to_anthropic_message};
use self::providers::apply_provider_request_transforms;
use self::stream::{sse_response, stream_openai_sse_to_anthropic};
use self::transformers::ProxyTransformerChain;
use serde_json::{json, Value};
use std::net::SocketAddr;
use std::sync::Arc;
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio::net::{TcpListener, TcpStream};

#[derive(Clone, Debug)]
pub(crate) struct OpenAiProxyCredential {
    pub(crate) api_key: String,
    pub(crate) base_url: String,
    pub(crate) model: String,
    pub(crate) transformers: Vec<String>,
    pub(crate) model_transformers: Vec<String>,
}

pub(crate) async fn start_openai_anthropic_proxy(
    credential: OpenAiProxyCredential,
) -> Result<String, String> {
    let listener = TcpListener::bind(("127.0.0.1", 0))
        .await
        .map_err(|err| format!("Failed to start local provider proxy: {}", err))?;
    let addr = listener
        .local_addr()
        .map_err(|err| format!("Failed to read local provider proxy address: {}", err))?;
    let credential = Arc::new(credential);

    tokio::spawn(async move {
        loop {
            let Ok((stream, _)) = listener.accept().await else {
                break;
            };
            let credential = Arc::clone(&credential);
            tokio::spawn(async move {
                if let Err(err) = handle_connection(stream, credential).await {
                    eprintln!("[anthropic-proxy] request failed: {}", err);
                }
            });
        }
    });

    Ok(format!("http://{}", addr))
}

async fn handle_connection(
    mut stream: TcpStream,
    credential: Arc<OpenAiProxyCredential>,
) -> Result<(), String> {
    let request = read_http_request(&mut stream).await?;
    let path = request_path_without_query(&request.path);
    if request.method == "POST" && is_messages_path(path) {
        match handle_messages_to_stream(&request, &credential, &mut stream).await {
            Ok(()) => {
                let _ = stream.shutdown().await;
                return Ok(());
            }
            Err(err) => {
                let response = json_response(
                    502,
                    &json!({
                        "type": "error",
                        "error": {
                            "type": "api_error",
                            "message": err,
                        },
                    }),
                );
                stream
                    .write_all(response.as_bytes())
                    .await
                    .map_err(|err| format!("Failed to write proxy error response: {}", err))?;
                let _ = stream.shutdown().await;
                return Ok(());
            }
        }
    }

    let response = route_request(&request).await;
    stream
        .write_all(response.as_bytes())
        .await
        .map_err(|err| format!("Failed to write proxy response: {}", err))?;
    let _ = stream.shutdown().await;
    Ok(())
}

struct HttpRequest {
    method: String,
    path: String,
    body: Vec<u8>,
}

async fn read_http_request(stream: &mut TcpStream) -> Result<HttpRequest, String> {
    let mut buffer = Vec::new();
    let mut temp = [0_u8; 8192];
    let header_end = loop {
        let n = stream
            .read(&mut temp)
            .await
            .map_err(|err| format!("Failed to read proxy request: {}", err))?;
        if n == 0 {
            return Err("Connection closed before HTTP headers were received".to_string());
        }
        buffer.extend_from_slice(&temp[..n]);
        if let Some(index) = find_header_end(&buffer) {
            break index;
        }
        if buffer.len() > 1024 * 1024 {
            return Err("Proxy request headers are too large".to_string());
        }
    };

    let header_text = String::from_utf8_lossy(&buffer[..header_end]);
    let mut lines = header_text.lines();
    let request_line = lines
        .next()
        .ok_or_else(|| "Proxy request is missing request line".to_string())?;
    let mut request_parts = request_line.split_whitespace();
    let method = request_parts
        .next()
        .ok_or_else(|| "Proxy request is missing method".to_string())?
        .to_string();
    let path = request_parts
        .next()
        .ok_or_else(|| "Proxy request is missing path".to_string())?
        .to_string();

    let content_length = lines
        .filter_map(|line| line.split_once(':'))
        .find(|(key, _)| key.eq_ignore_ascii_case("content-length"))
        .and_then(|(_, value)| value.trim().parse::<usize>().ok())
        .unwrap_or(0);

    let body_start = header_end + 4;
    let mut body = buffer.get(body_start..).unwrap_or_default().to_vec();
    while body.len() < content_length {
        let n = stream
            .read(&mut temp)
            .await
            .map_err(|err| format!("Failed to read proxy request body: {}", err))?;
        if n == 0 {
            break;
        }
        body.extend_from_slice(&temp[..n]);
    }
    body.truncate(content_length);

    Ok(HttpRequest { method, path, body })
}

fn find_header_end(buffer: &[u8]) -> Option<usize> {
    buffer.windows(4).position(|window| window == b"\r\n\r\n")
}

async fn route_request(request: &HttpRequest) -> String {
    let path = request_path_without_query(&request.path);

    if request.method == "GET" && path == "/" {
        return json_response(
            200,
            &json!({ "ok": true, "service": "claude-prism-anthropic-proxy" }),
        );
    }

    if request.method == "POST" && is_count_tokens_path(path) {
        return handle_count_tokens(request);
    }

    json_response(
        400,
        &json!({
            "type": "error",
            "error": {
                "type": "invalid_request_error",
                "message": format!("Unsupported Anthropic proxy endpoint: {} {}", request.method, request.path),
            },
        }),
    )
}

fn request_path_without_query(path: &str) -> &str {
    path.split_once('?').map(|(path, _)| path).unwrap_or(path)
}

fn is_count_tokens_path(path: &str) -> bool {
    path.ends_with("/count_tokens")
}

fn is_messages_path(path: &str) -> bool {
    path.ends_with("/messages")
}

fn handle_count_tokens(request: &HttpRequest) -> String {
    let body = serde_json::from_slice::<Value>(&request.body).unwrap_or(Value::Null);
    let approx_chars = body.to_string().chars().count();
    json_response(
        200,
        &json!({
            "input_tokens": (approx_chars / 4).max(1),
        }),
    )
}

async fn handle_messages_to_stream(
    request: &HttpRequest,
    credential: &OpenAiProxyCredential,
    stream: &mut TcpStream,
) -> Result<(), String> {
    let anthropic_request: Value = serde_json::from_slice(&request.body)
        .map_err(|err| format!("Claude Code sent invalid Anthropic JSON: {}", err))?;
    let wants_stream = anthropic_request
        .get("stream")
        .and_then(|value| value.as_bool())
        .unwrap_or(false);
    let transformers = ProxyTransformerChain::for_credential(credential, wants_stream);
    let mut openai_request =
        anthropic_to_openai_request(&anthropic_request, credential, &transformers)?;
    openai_request["stream"] = Value::Bool(wants_stream);
    apply_provider_request_transforms(
        &mut openai_request,
        &anthropic_request,
        credential,
        wants_stream,
        &transformers,
    );
    if request_contains_openai_image_parts(&openai_request)
        && provider_rejects_openai_image_parts(credential)
    {
        return Err(format!(
            "{} does not accept OpenAI-style image_url message parts. Switch to Claude Code or a vision-capable OpenAI-compatible endpoint for image questions.",
            credential.model
        ));
    }

    let client = reqwest::Client::builder()
        .timeout(std::time::Duration::from_secs(300))
        .build()
        .map_err(|err| format!("Failed to create provider client: {}", err))?;
    let request = client
        .post(openai_chat_completions_url(&credential.base_url))
        .header("Content-Type", "application/json")
        .body(openai_request.to_string());
    let response = with_optional_bearer_auth(request, &credential.api_key)
        .send()
        .await
        .map_err(|err| format!("Provider request failed: {}", err))?;

    let status = response.status();
    if !status.is_success() {
        let response_text = response
            .text()
            .await
            .map_err(|err| format!("Failed to read provider error response: {}", err))?;
        return Err(format!(
            "Provider returned HTTP {}: {}",
            status,
            compact_error_text(&response_text)
        ));
    }

    if wants_stream {
        let content_type = response
            .headers()
            .get(reqwest::header::CONTENT_TYPE)
            .and_then(|value| value.to_str().ok())
            .unwrap_or_default()
            .to_ascii_lowercase();
        if content_type.contains("stream") {
            stream_openai_sse_to_anthropic(stream, response, &anthropic_request, credential).await
        } else {
            let response_text = response
                .text()
                .await
                .map_err(|err| format!("Failed to read provider response: {}", err))?;
            let openai_response: Value = serde_json::from_str(&response_text)
                .map_err(|err| format!("Provider returned invalid JSON: {}", err))?;
            let anthropic_response =
                openai_to_anthropic_message(&anthropic_request, &openai_response, credential)?;
            stream
                .write_all(sse_response(&anthropic_response).as_bytes())
                .await
                .map_err(|err| format!("Failed to write proxy SSE response: {}", err))
        }
    } else {
        let response_text = response
            .text()
            .await
            .map_err(|err| format!("Failed to read provider response: {}", err))?;
        let openai_response: Value = serde_json::from_str(&response_text)
            .map_err(|err| format!("Provider returned invalid JSON: {}", err))?;
        let anthropic_response =
            openai_to_anthropic_message(&anthropic_request, &openai_response, credential)?;
        stream
            .write_all(json_response(200, &anthropic_response).as_bytes())
            .await
            .map_err(|err| format!("Failed to write proxy JSON response: {}", err))
    }
}

fn openai_chat_completions_url(base_url: &str) -> String {
    let clean = base_url.trim_end_matches('/');
    if clean.ends_with("/chat/completions") {
        clean.to_string()
    } else if openai_compatible_base_url_has_chat_root(clean) {
        format!("{}/chat/completions", clean)
    } else {
        format!("{}/v1/chat/completions", clean)
    }
}

fn with_optional_bearer_auth(
    request: reqwest::RequestBuilder,
    api_key: &str,
) -> reqwest::RequestBuilder {
    if api_key.trim().is_empty() {
        request
    } else {
        request.bearer_auth(api_key)
    }
}

fn request_contains_openai_image_parts(value: &Value) -> bool {
    match value {
        Value::Array(values) => values.iter().any(request_contains_openai_image_parts),
        Value::Object(object) => {
            object.get("type").and_then(Value::as_str) == Some("image_url")
                || object.values().any(request_contains_openai_image_parts)
        }
        _ => false,
    }
}

fn provider_rejects_openai_image_parts(credential: &OpenAiProxyCredential) -> bool {
    let base_url = credential.base_url.to_ascii_lowercase();
    base_url == "https://api.deepseek.com" || base_url.starts_with("https://api.deepseek.com/")
}

fn openai_compatible_base_url_has_chat_root(base_url: &str) -> bool {
    let lower = base_url.to_ascii_lowercase();
    if lower == "https://api.deepseek.com" {
        return true;
    }

    let path = lower
        .split_once("://")
        .and_then(|(_, rest)| rest.split_once('/').map(|(_, path)| path))
        .unwrap_or("")
        .trim_matches('/');
    if path.is_empty() {
        return false;
    }

    let segments = path.split('/').collect::<Vec<_>>();
    let last = segments.last().copied().unwrap_or_default();
    matches!(last, "v1" | "v2" | "v3" | "v4" | "beta")
        || path.ends_with("/openai")
        || path.ends_with("compatible-mode/v1")
}

fn json_response(status: u16, value: &Value) -> String {
    http_response(
        status,
        "application/json; charset=utf-8",
        &value.to_string(),
    )
}

fn http_response(status: u16, content_type: &str, body: &str) -> String {
    let reason = match status {
        200 => "OK",
        400 => "Bad Request",
        404 => "Not Found",
        502 => "Bad Gateway",
        _ => "Internal Server Error",
    };
    format!(
        "HTTP/1.1 {} {}\r\nContent-Type: {}\r\nContent-Length: {}\r\nConnection: close\r\n\r\n{}",
        status,
        reason,
        content_type,
        body.as_bytes().len(),
        body
    )
}

fn compact_error_text(text: &str) -> String {
    let compact = text.split_whitespace().collect::<Vec<_>>().join(" ");
    if compact.chars().count() <= 1000 {
        compact
    } else {
        format!("{}...", compact.chars().take(1000).collect::<String>())
    }
}

#[allow(dead_code)]
fn _assert_local_addr(_: SocketAddr) {}

#[cfg(test)]
mod tests {
    use super::transformers::ProxyTransformerChain;
    use super::*;

    #[test]
    fn recognizes_anthropic_messages_paths_with_query_strings() {
        let path = request_path_without_query("/v1/messages?beta=tools");
        assert_eq!(path, "/v1/messages");
        assert!(is_messages_path(path));
        assert!(is_count_tokens_path("/v1/messages/count_tokens"));
    }

    #[test]
    fn detects_openai_image_parts_for_provider_guard() {
        assert!(request_contains_openai_image_parts(&json!({
            "messages": [{
                "role": "user",
                "content": [
                    { "type": "text", "text": "what is this?" },
                    { "type": "image_url", "image_url": { "url": "data:image/png;base64,abc" } }
                ]
            }]
        })));
        assert!(!request_contains_openai_image_parts(&json!({
            "messages": [{ "role": "user", "content": "text only" }]
        })));
    }

    #[test]
    fn converts_tool_use_and_tool_result_messages() {
        let credential = OpenAiProxyCredential {
            api_key: "sk-test".to_string(),
            base_url: "https://api.example.com/v1".to_string(),
            model: "qwen-test".to_string(),
            transformers: Vec::new(),
            model_transformers: Vec::new(),
        };
        let request = json!({
            "system": "system prompt",
            "messages": [
                {
                    "role": "assistant",
                    "content": [{
                        "type": "tool_use",
                        "id": "toolu_1",
                        "name": "Read",
                        "input": { "file_path": "main.tex" }
                    }]
                },
                {
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": "toolu_1",
                        "content": "file text"
                    }]
                }
            ],
            "tools": [{
                "name": "Read",
                "description": "Read a file",
                "input_schema": { "type": "object" }
            }]
        });

        let converted = anthropic_to_openai_request(
            &request,
            &credential,
            &ProxyTransformerChain::from_names(&[]),
        )
        .unwrap();
        assert_eq!(converted["model"], "qwen-test");
        assert_eq!(converted["messages"][0]["role"], "system");
        assert_eq!(
            converted["messages"][1]["tool_calls"][0]["function"]["name"],
            "Read"
        );
        assert_eq!(converted["messages"][2]["role"], "tool");
        assert_eq!(converted["tools"][0]["function"]["name"], "Read");
    }

    #[test]
    fn keeps_tool_results_immediately_after_tool_calls() {
        let credential = OpenAiProxyCredential {
            api_key: "sk-test".to_string(),
            base_url: "https://api.example.com/v1".to_string(),
            model: "qwen-test".to_string(),
            transformers: Vec::new(),
            model_transformers: Vec::new(),
        };
        let request = json!({
            "messages": [
                {
                    "role": "assistant",
                    "content": [{
                        "type": "tool_use",
                        "id": "toolu_1",
                        "name": "Read",
                        "input": { "file_path": "main.tex" }
                    }]
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Now explain it."
                        },
                        {
                            "type": "tool_result",
                            "tool_use_id": "toolu_1",
                            "content": "file text"
                        }
                    ]
                }
            ]
        });

        let converted = anthropic_to_openai_request(
            &request,
            &credential,
            &ProxyTransformerChain::from_names(&[]),
        )
        .unwrap();
        assert_eq!(converted["messages"][0]["role"], "assistant");
        assert_eq!(converted["messages"][1]["role"], "tool");
        assert_eq!(converted["messages"][1]["tool_call_id"], "toolu_1");
        assert_eq!(converted["messages"][2]["role"], "user");
        assert_eq!(converted["messages"][2]["content"], "Now explain it.");
    }

    #[test]
    fn synthesizes_missing_tool_results_before_user_messages() {
        let credential = OpenAiProxyCredential {
            api_key: "sk-test".to_string(),
            base_url: "https://api.example.com/v1".to_string(),
            model: "qwen-test".to_string(),
            transformers: Vec::new(),
            model_transformers: Vec::new(),
        };
        let request = json!({
            "messages": [
                {
                    "role": "assistant",
                    "content": [{
                        "type": "tool_use",
                        "id": "toolu_missing",
                        "name": "Read",
                        "input": { "file_path": "main.tex" }
                    }]
                },
                {
                    "role": "user",
                    "content": "continue"
                }
            ]
        });

        let converted = anthropic_to_openai_request(
            &request,
            &credential,
            &ProxyTransformerChain::from_names(&[]),
        )
        .unwrap();
        assert_eq!(converted["messages"][0]["role"], "assistant");
        assert_eq!(converted["messages"][1]["role"], "tool");
        assert_eq!(converted["messages"][1]["tool_call_id"], "toolu_missing");
        assert_eq!(converted["messages"][2]["role"], "user");
        assert_eq!(converted["messages"][2]["content"], "continue");
    }

    #[test]
    fn converts_openai_tool_call_to_anthropic_message() {
        let credential = OpenAiProxyCredential {
            api_key: "sk-test".to_string(),
            base_url: "https://api.example.com/v1".to_string(),
            model: "deepseek-test".to_string(),
            transformers: Vec::new(),
            model_transformers: Vec::new(),
        };
        let request = json!({ "model": "claude-sonnet-4" });
        let response = json!({
            "id": "chatcmpl_1",
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": null,
                    "tool_calls": [{
                        "id": "call_1",
                        "type": "function",
                        "function": {
                            "name": "Grep",
                            "arguments": "{\"pattern\":\"FastVID\"}"
                        }
                    }]
                },
                "finish_reason": "tool_calls"
            }],
            "usage": { "prompt_tokens": 10, "completion_tokens": 3 }
        });

        let converted = openai_to_anthropic_message(&request, &response, &credential).unwrap();
        assert_eq!(converted["stop_reason"], "tool_use");
        assert_eq!(converted["content"][0]["type"], "tool_use");
        assert_eq!(converted["content"][0]["input"]["pattern"], "FastVID");
    }
}
