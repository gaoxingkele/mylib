use serde_json::{json, Value};

pub(super) fn repaired_tool_arguments_value(arguments: &str) -> Value {
    serde_json::from_str::<Value>(&repair_tool_arguments(arguments)).unwrap_or_else(|_| json!({}))
}

pub(super) fn normalized_tool_call_id(id: Option<&str>) -> String {
    let id = id.unwrap_or_default().trim();
    if id.is_empty() || id.chars().all(|ch| ch.is_ascii_digit()) {
        format!("call_{}", uuid::Uuid::new_v4().simple())
    } else {
        id.to_string()
    }
}

pub(super) fn repair_tool_arguments(arguments: &str) -> String {
    let trimmed = trim_code_fence(arguments.trim());
    if trimmed.is_empty() || trimmed == "{}" {
        return "{}".to_string();
    }

    let mut candidates = Vec::new();
    push_candidate(&mut candidates, trimmed.to_string());
    if let Some(extracted) = extract_json_like(trimmed) {
        push_candidate(&mut candidates, extracted);
    }

    let seeds = candidates.clone();
    for candidate in seeds {
        let without_comments = strip_json_comments(&candidate);
        push_candidate(&mut candidates, without_comments.clone());

        let without_trailing_commas = remove_trailing_commas(&without_comments);
        push_candidate(&mut candidates, without_trailing_commas.clone());

        let json5_like =
            normalize_single_quoted_strings(&quote_unquoted_object_keys(&without_trailing_commas));
        push_candidate(&mut candidates, json5_like.clone());

        if let Some(with_commas) = insert_missing_commas_between_fields(&json5_like) {
            push_candidate(&mut candidates, with_commas.clone());
            if let Some(balanced) = repair_balanced_json(with_commas) {
                push_candidate(&mut candidates, balanced);
            }
        }
        if let Some(balanced) = repair_balanced_json(json5_like) {
            push_candidate(&mut candidates, balanced);
        }
        if let Some(balanced) = repair_balanced_json(without_trailing_commas) {
            push_candidate(&mut candidates, balanced);
        }
    }

    for candidate in candidates {
        if let Some(repaired) = parse_tool_arguments_candidate(&candidate) {
            return repaired;
        }
    }

    "{}".to_string()
}

fn push_candidate(candidates: &mut Vec<String>, value: String) {
    let value = value.trim().to_string();
    if value.is_empty() || candidates.iter().any(|candidate| candidate == &value) {
        return;
    }
    candidates.push(value);
}

fn parse_tool_arguments_candidate(value: &str) -> Option<String> {
    serde_json::from_str::<Value>(value)
        .ok()
        .or_else(|| serde_yaml::from_str::<Value>(value).ok())
        .and_then(canonical_tool_arguments)
}

fn canonical_tool_arguments(value: Value) -> Option<String> {
    match value {
        Value::Object(map) => {
            if map.keys().any(|key| key.contains(':')) {
                return None;
            }
            Some(Value::Object(map).to_string())
        }
        Value::Array(_) => Some(value.to_string()),
        _ => None,
    }
}

fn trim_code_fence(value: &str) -> &str {
    let value = value.trim();
    if !value.starts_with("```") {
        return value;
    }
    let Some(first_newline) = value.find('\n') else {
        return value;
    };
    let value = &value[first_newline + 1..];
    value
        .strip_suffix("```")
        .map(str::trim)
        .unwrap_or(value.trim())
}

fn extract_json_like(value: &str) -> Option<String> {
    let object_start = value.find('{');
    let array_start = value.find('[');
    let start = match (object_start, array_start) {
        (Some(object), Some(array)) => object.min(array),
        (Some(object), None) => object,
        (None, Some(array)) => array,
        (None, None) => return None,
    };
    let end = value.rfind('}').or_else(|| value.rfind(']'))?;
    if end <= start {
        return None;
    }
    Some(value[start..=end].to_string())
}

fn repair_balanced_json(value: String) -> Option<String> {
    let mut output = String::with_capacity(value.len() + 8);
    let mut stack = Vec::new();
    let mut in_string = false;
    let mut escaped = false;

    for ch in value.chars() {
        output.push(ch);
        if in_string {
            if escaped {
                escaped = false;
            } else if ch == '\\' {
                escaped = true;
            } else if ch == '"' {
                in_string = false;
            }
            continue;
        }

        match ch {
            '"' => in_string = true,
            '{' => stack.push('}'),
            '[' => stack.push(']'),
            '}' | ']' => {
                if stack.last().copied() == Some(ch) {
                    stack.pop();
                }
            }
            _ => {}
        }
    }

    if in_string {
        output.push('"');
    }
    while let Some(ch) = stack.pop() {
        output.push(ch);
    }
    Some(output)
}

fn remove_trailing_commas(value: &str) -> String {
    let mut output = String::with_capacity(value.len());
    let mut chars = value.chars().peekable();
    let mut in_string = false;
    let mut escaped = false;

    while let Some(ch) = chars.next() {
        if in_string {
            output.push(ch);
            if escaped {
                escaped = false;
            } else if ch == '\\' {
                escaped = true;
            } else if ch == '"' {
                in_string = false;
            }
            continue;
        }

        if ch == '"' {
            in_string = true;
            output.push(ch);
            continue;
        }

        if ch == ',' {
            let mut lookahead = chars.clone();
            while matches!(lookahead.peek(), Some(next) if next.is_whitespace()) {
                lookahead.next();
            }
            if matches!(lookahead.peek(), Some('}' | ']')) {
                continue;
            }
        }
        output.push(ch);
    }

    output
}

fn strip_json_comments(value: &str) -> String {
    let mut output = String::with_capacity(value.len());
    let mut chars = value.chars().peekable();
    let mut in_double_string = false;
    let mut in_single_string = false;
    let mut escaped = false;

    while let Some(ch) = chars.next() {
        if in_double_string || in_single_string {
            output.push(ch);
            if escaped {
                escaped = false;
            } else if ch == '\\' {
                escaped = true;
            } else if in_double_string && ch == '"' {
                in_double_string = false;
            } else if in_single_string && ch == '\'' {
                in_single_string = false;
            }
            continue;
        }

        match ch {
            '"' => {
                in_double_string = true;
                output.push(ch);
            }
            '\'' => {
                in_single_string = true;
                output.push(ch);
            }
            '/' if chars.peek() == Some(&'/') => {
                chars.next();
                for next in chars.by_ref() {
                    if next == '\n' {
                        output.push('\n');
                        break;
                    }
                }
            }
            '/' if chars.peek() == Some(&'*') => {
                chars.next();
                let mut previous = '\0';
                for next in chars.by_ref() {
                    if previous == '*' && next == '/' {
                        break;
                    }
                    previous = next;
                }
            }
            _ => output.push(ch),
        }
    }

    output
}

fn quote_unquoted_object_keys(value: &str) -> String {
    let mut output = String::with_capacity(value.len() + 16);
    let chars = value.chars().collect::<Vec<_>>();
    let mut index = 0;
    let mut in_double_string = false;
    let mut in_single_string = false;
    let mut escaped = false;
    let mut expects_key = false;

    while index < chars.len() {
        let ch = chars[index];
        if in_double_string || in_single_string {
            output.push(ch);
            if escaped {
                escaped = false;
            } else if ch == '\\' {
                escaped = true;
            } else if in_double_string && ch == '"' {
                in_double_string = false;
            } else if in_single_string && ch == '\'' {
                in_single_string = false;
            }
            index += 1;
            continue;
        }

        match ch {
            '"' => {
                in_double_string = true;
                output.push(ch);
                expects_key = false;
                index += 1;
            }
            '\'' => {
                in_single_string = true;
                output.push(ch);
                expects_key = false;
                index += 1;
            }
            '{' | ',' => {
                expects_key = true;
                output.push(ch);
                index += 1;
            }
            '}' | ']' => {
                expects_key = false;
                output.push(ch);
                index += 1;
            }
            ch if expects_key && ch.is_whitespace() => {
                output.push(ch);
                index += 1;
            }
            ch if expects_key && is_identifier_start(ch) => {
                let start = index;
                index += 1;
                while index < chars.len() && is_identifier_continue(chars[index]) {
                    index += 1;
                }
                let mut lookahead = index;
                while lookahead < chars.len() && chars[lookahead].is_whitespace() {
                    lookahead += 1;
                }
                if lookahead < chars.len() && chars[lookahead] == ':' {
                    output.push('"');
                    for key_ch in &chars[start..index] {
                        output.push(*key_ch);
                    }
                    output.push('"');
                    expects_key = false;
                } else {
                    for key_ch in &chars[start..index] {
                        output.push(*key_ch);
                    }
                    expects_key = false;
                }
            }
            _ => {
                output.push(ch);
                index += 1;
            }
        }
    }

    output
}

fn normalize_single_quoted_strings(value: &str) -> String {
    let mut output = String::with_capacity(value.len());
    let mut chars = value.chars().peekable();
    let mut in_double_string = false;
    let mut in_single_string = false;
    let mut escaped = false;

    while let Some(ch) = chars.next() {
        if in_double_string {
            output.push(ch);
            if escaped {
                escaped = false;
            } else if ch == '\\' {
                escaped = true;
            } else if ch == '"' {
                in_double_string = false;
            }
            continue;
        }

        if in_single_string {
            if escaped {
                match ch {
                    '\'' => output.push('\''),
                    '"' => {
                        output.push('\\');
                        output.push('"');
                    }
                    '\\' => output.push('\\'),
                    _ => {
                        output.push('\\');
                        output.push(ch);
                    }
                }
                escaped = false;
            } else if ch == '\\' {
                escaped = true;
            } else if ch == '\'' {
                output.push('"');
                in_single_string = false;
            } else if ch == '"' {
                output.push('\\');
                output.push('"');
            } else {
                output.push(ch);
            }
            continue;
        }

        if ch == '"' {
            in_double_string = true;
            output.push(ch);
        } else if ch == '\'' {
            in_single_string = true;
            output.push('"');
        } else {
            output.push(ch);
        }
    }

    if in_single_string {
        output.push('"');
    }
    output
}

fn insert_missing_commas_between_fields(value: &str) -> Option<String> {
    let mut output = String::with_capacity(value.len() + 8);
    let chars = value.chars().collect::<Vec<_>>();
    let mut index = 0;
    let mut changed = false;
    let mut in_string = false;
    let mut escaped = false;

    while index < chars.len() {
        let ch = chars[index];
        output.push(ch);
        if in_string {
            if escaped {
                escaped = false;
            } else if ch == '\\' {
                escaped = true;
            } else if ch == '"' {
                in_string = false;
            }
            index += 1;
            continue;
        }

        if ch == '"' {
            in_string = true;
            index += 1;
            continue;
        }

        if matches!(ch, '"' | '}' | ']' | '0'..='9' | 'e' | 'E' | 'l') {
            let mut lookahead = index + 1;
            while lookahead < chars.len() && chars[lookahead].is_whitespace() {
                lookahead += 1;
            }
            if lookahead < chars.len()
                && chars[lookahead] == '"'
                && previous_non_whitespace(&chars, index) != Some(':')
            {
                output.push(',');
                changed = true;
            }
        }
        index += 1;
    }

    changed.then_some(output)
}

fn previous_non_whitespace(chars: &[char], index: usize) -> Option<char> {
    if index == 0 {
        return None;
    }
    let mut cursor = index - 1;
    loop {
        if !chars[cursor].is_whitespace() {
            return Some(chars[cursor]);
        }
        if cursor == 0 {
            return None;
        }
        cursor -= 1;
    }
}

fn is_identifier_start(ch: char) -> bool {
    ch == '_' || ch == '$' || ch.is_ascii_alphabetic()
}

fn is_identifier_continue(ch: char) -> bool {
    is_identifier_start(ch) || ch.is_ascii_digit() || ch == '-' || ch == '.'
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn repairs_partial_tool_arguments() {
        assert_eq!(
            repair_tool_arguments("{\"file_path\":\"main.tex\""),
            "{\"file_path\":\"main.tex\"}"
        );
    }

    #[test]
    fn repairs_fenced_tool_arguments() {
        assert_eq!(
            repair_tool_arguments("```json\n{\"pattern\":\"FastVID\",}\n```"),
            "{\"pattern\":\"FastVID\"}"
        );
    }

    #[test]
    fn repairs_json5_style_tool_arguments_like_ccr_enhancetool() {
        let repaired: Value = serde_json::from_str(&repair_tool_arguments(
            "{file_path:'main.tex', replace_all:false,}",
        ))
        .unwrap();

        assert_eq!(
            repaired,
            json!({ "file_path": "main.tex", "replace_all": false })
        );
    }

    #[test]
    fn repairs_commented_tool_arguments() {
        let repaired: Value = serde_json::from_str(&repair_tool_arguments(
            "{\n  // target file\n  file_path: 'main.tex',\n  old_string: 'A',\n  new_string: 'B',\n}",
        ))
        .unwrap();

        assert_eq!(
            repaired,
            json!({ "file_path": "main.tex", "old_string": "A", "new_string": "B" })
        );
    }

    #[test]
    fn repairs_mixed_quote_tool_arguments() {
        let repaired: Value = serde_json::from_str(&repair_tool_arguments(
            "{\"file_path\": 'main.tex', \"pattern\": 'FastVID'}",
        ))
        .unwrap();

        assert_eq!(
            repaired,
            json!({ "file_path": "main.tex", "pattern": "FastVID" })
        );
    }

    #[test]
    fn falls_back_to_empty_object_for_unrepairable_arguments() {
        assert_eq!(repair_tool_arguments("not json at all"), "{}");
    }

    #[test]
    fn normalizes_numeric_tool_call_ids() {
        let id = normalized_tool_call_id(Some("123"));

        assert!(id.starts_with("call_"));
        assert_ne!(id, "123");
    }

    #[test]
    fn preserves_provider_tool_call_ids() {
        assert_eq!(normalized_tool_call_id(Some("call_abc")), "call_abc");
    }
}
