use std::collections::HashMap;
use std::sync::Arc;

use tauri::{Emitter, Manager, WebviewWindow};
use tokio::io::{AsyncBufReadExt, AsyncWriteExt, BufReader};
use tokio::process::{Child, Command};
use tokio::sync::Mutex;

#[cfg(windows)]
const CREATE_NO_WINDOW: u32 = 0x08000000;

#[derive(Clone)]
pub struct ClaudeProcessState {
    pub processes: Arc<Mutex<HashMap<String, Child>>>,
}

impl Default for ClaudeProcessState {
    fn default() -> Self {
        Self {
            processes: Arc::new(Mutex::new(HashMap::new())),
        }
    }
}

#[derive(Clone, serde::Serialize)]
struct ClaudeOutputEvent {
    tab_id: String,
    data: String,
}

#[derive(Clone, serde::Serialize)]
struct ClaudeCompleteEvent {
    tab_id: String,
    success: bool,
}

#[derive(Clone, serde::Serialize)]
struct ClaudeErrorEvent {
    tab_id: String,
    data: String,
}

#[derive(Clone)]
pub struct SpawnProviderMetadata {
    pub provider: &'static str,
    pub provider_credential_id: String,
    pub model: String,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum ClaudeStopMode {
    /// User pressed Stop; terminate the run immediately.
    Terminate,
    /// User wants to guide the next turn; prefer a graceful interrupt so
    /// Claude Code can persist session state before the frontend resumes it.
    Interrupt,
}

fn process_key(window_label: &str, tab_id: &str) -> String {
    format!("{}:{}", window_label, tab_id)
}

/// Spawn the Claude CLI process and stream output via Tauri events.
/// Events are emitted only to the originating window, tagged with tab_id.
pub async fn spawn_claude_process(
    window: WebviewWindow,
    mut cmd: Command,
    tab_id: String,
    stdin_payload: Option<String>,
    provider_metadata: Option<SpawnProviderMetadata>,
) -> Result<(), String> {
    let window_label = window.label().to_string();
    let process_key = process_key(&window_label, &tab_id);

    if stdin_payload.is_some() {
        cmd.stdin(std::process::Stdio::piped());
    }

    let mut child = cmd.spawn().map_err(|e| {
        eprintln!(
            "[claude-spawn] Failed to spawn process for tab {}: {}",
            tab_id, e
        );
        format!(
            "Failed to spawn Claude process: {}. Is Claude Code CLI installed?",
            e
        )
    })?;

    if let Some(payload) = stdin_payload {
        let mut stdin = child
            .stdin
            .take()
            .ok_or_else(|| "Failed to acquire stdin for Claude process".to_string())?;
        stdin
            .write_all(payload.as_bytes())
            .await
            .map_err(|e| format!("Failed to write prompt to Claude process stdin: {}", e))?;
        stdin
            .shutdown()
            .await
            .map_err(|e| format!("Failed to close Claude process stdin: {}", e))?;
    }

    let stdout = child.stdout.take().ok_or("Failed to capture stdout")?;
    let stderr = child.stderr.take().ok_or("Failed to capture stderr")?;

    let process_arc = window
        .state::<ClaudeProcessState>()
        .inner()
        .processes
        .clone();

    {
        let mut processes = process_arc.lock().await;
        if let Some(mut existing) = processes.remove(&process_key) {
            let _ = existing.kill().await;
        }
        processes.insert(process_key.clone(), child);
    }

    let stdout_reader = BufReader::new(stdout);
    let stderr_reader = BufReader::new(stderr);
    let result_success_holder: Arc<std::sync::Mutex<Option<bool>>> =
        Arc::new(std::sync::Mutex::new(None));

    let start_time = std::time::Instant::now();

    let win_stdout = window.clone();
    let result_success_stdout = result_success_holder.clone();
    let tab_id_stdout = tab_id.clone();
    let provider_metadata_stdout = provider_metadata.clone();
    let stdout_task = tokio::spawn(async move {
        let mut lines = stdout_reader.lines();
        let mut line_count: u64 = 0;
        while let Ok(Some(mut line)) = lines.next_line().await {
            line_count += 1;
            let elapsed = start_time.elapsed().as_secs_f64();

            if let Ok(mut msg) = serde_json::from_str::<serde_json::Value>(&line) {
                let msg_type = msg.get("type").and_then(|v| v.as_str()).unwrap_or("?");
                let msg_sub = msg.get("subtype").and_then(|v| v.as_str()).unwrap_or("");
                eprintln!(
                    "[claude-stdout] [{}] +{:.1}s #{} type={} sub={} len={}",
                    tab_id_stdout,
                    elapsed,
                    line_count,
                    msg_type,
                    msg_sub,
                    line.len()
                );

                if msg.get("type").and_then(|v| v.as_str()) == Some("system")
                    && msg.get("subtype").and_then(|v| v.as_str()) == Some("init")
                {
                    if let Some(metadata) = provider_metadata_stdout.as_ref() {
                        if let Some(object) = msg.as_object_mut() {
                            object.insert(
                                "provider".to_string(),
                                serde_json::Value::String(metadata.provider.to_string()),
                            );
                            object.insert(
                                "provider_credential_id".to_string(),
                                serde_json::Value::String(metadata.provider_credential_id.clone()),
                            );
                            object.insert(
                                "model".to_string(),
                                serde_json::Value::String(metadata.model.clone()),
                            );
                        }
                        line = msg.to_string();
                    }
                }

                if msg.get("type").and_then(|v| v.as_str()) == Some("result") {
                    let is_success = msg.get("subtype").and_then(|v| v.as_str()) == Some("success");
                    if let Ok(mut guard) = result_success_stdout.lock() {
                        *guard = Some(is_success);
                    }
                }
            }

            let _ = win_stdout.emit(
                "claude-output",
                ClaudeOutputEvent {
                    tab_id: tab_id_stdout.clone(),
                    data: line,
                },
            );
        }
        eprintln!(
            "[claude-stdout] [{}] stream ended after {} lines ({:.1}s)",
            tab_id_stdout,
            line_count,
            start_time.elapsed().as_secs_f64()
        );
    });

    let win_stderr = window.clone();
    let tab_id_stderr = tab_id.clone();
    let stderr_task = tokio::spawn(async move {
        let mut lines = stderr_reader.lines();
        while let Ok(Some(line)) = lines.next_line().await {
            eprintln!(
                "[claude-stderr] [{}] +{:.1}s {}",
                tab_id_stderr,
                start_time.elapsed().as_secs_f64(),
                &line[..line.len().min(200)]
            );
            let _ = win_stderr.emit(
                "claude-error",
                ClaudeErrorEvent {
                    tab_id: tab_id_stderr.clone(),
                    data: line,
                },
            );
        }
    });

    let process_arc_wait = process_arc.clone();
    let win_wait = window;
    let process_key_wait = process_key;
    let tab_id_wait = tab_id;
    let result_success_wait = result_success_holder.clone();
    tokio::spawn(async move {
        let _ = stdout_task.await;
        let _ = stderr_task.await;

        let mut processes = process_arc_wait.lock().await;
        let success = if let Some(mut child) = processes.remove(&process_key_wait) {
            match child.wait().await {
                Ok(status) => {
                    let exit_success = status.success();
                    let result_success = result_success_wait.lock().ok().and_then(|guard| *guard);
                    let success = exit_success || result_success == Some(true);
                    eprintln!(
                        "[claude-process] [{}] exited with status={} result_success={:?} final_success={} ({:.1}s)",
                        tab_id_wait,
                        status,
                        result_success,
                        success,
                        start_time.elapsed().as_secs_f64()
                    );
                    success
                }
                Err(e) => {
                    eprintln!(
                        "[claude-process] [{}] wait error: {} ({:.1}s)",
                        tab_id_wait,
                        e,
                        start_time.elapsed().as_secs_f64()
                    );
                    false
                }
            }
        } else {
            eprintln!(
                "[claude-process] [{}] no child found in map ({:.1}s)",
                tab_id_wait,
                start_time.elapsed().as_secs_f64()
            );
            false
        };
        drop(processes);

        let _ = win_wait.emit(
            "claude-complete",
            ClaudeCompleteEvent {
                tab_id: tab_id_wait,
                success,
            },
        );
    });

    Ok(())
}

pub async fn stop_claude_process(
    window: WebviewWindow,
    tab_id: String,
    mode: ClaudeStopMode,
) -> Result<bool, String> {
    let window_label = window.label().to_string();
    let process_key = process_key(&window_label, &tab_id);
    let claude_state = window.state::<ClaudeProcessState>();
    let mut processes = claude_state.processes.lock().await;
    if let Some(mut child) = processes.remove(&process_key) {
        drop(processes);
        let stopped = match mode {
            ClaudeStopMode::Terminate => {
                terminate_process_tree(&mut child).await;
                true
            }
            ClaudeStopMode::Interrupt => interrupt_or_terminate(&mut child).await,
        };
        return Ok(stopped);
    }
    drop(processes);

    let _ = window.emit(
        "claude-complete",
        ClaudeCompleteEvent {
            tab_id,
            success: false,
        },
    );
    Ok(false)
}

#[cfg(unix)]
async fn interrupt_or_terminate(child: &mut Child) -> bool {
    if let Some(pid) = child.id() {
        let status = tokio::process::Command::new("kill")
            .arg("-INT")
            .arg(pid.to_string())
            .status()
            .await;
        if matches!(status, Ok(status) if status.success()) {
            return true;
        }
    }
    terminate_process_tree(child).await;
    true
}

#[cfg(not(unix))]
async fn interrupt_or_terminate(child: &mut Child) -> bool {
    // Windows GUI processes do not have a reliable console-control path from
    // Tauri without a PTY/ConPTY session. For guided follow-ups, fall back to
    // terminating the current run so the frontend can immediately continue the
    // same tab with the queued guidance.
    terminate_process_tree(child).await;
    true
}

#[cfg(windows)]
async fn terminate_process_tree(child: &mut Child) {
    if let Some(pid) = child.id() {
        let _ = Command::new("taskkill")
            .creation_flags(CREATE_NO_WINDOW)
            .args(["/PID", &pid.to_string(), "/T", "/F"])
            .status()
            .await;
    }
    let _ = child.start_kill();
}

#[cfg(not(windows))]
async fn terminate_process_tree(child: &mut Child) {
    let _ = child.start_kill();
}

/// Kill all Claude processes associated with a specific window label.
/// Called when a window is destroyed.
pub async fn kill_process_for_window(state: &ClaudeProcessState, window_label: &str) {
    let mut processes = state.processes.lock().await;
    let prefix = format!("{}:", window_label);
    let keys_to_remove: Vec<String> = processes
        .keys()
        .filter(|k| k.starts_with(&prefix))
        .cloned()
        .collect();
    for key in keys_to_remove {
        if let Some(mut child) = processes.remove(&key) {
            let _ = child.kill().await;
        }
    }
}
