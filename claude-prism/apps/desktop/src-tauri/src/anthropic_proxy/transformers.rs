use super::OpenAiProxyCredential;

const CLEANCACHE: &str = "cleancache";
const DEEPSEEK: &str = "deepseek";
const ENHANCETOOL: &str = "enhancetool";
const STREAMOPTIONS: &str = "streamoptions";
const TOOLUSE: &str = "tooluse";

#[derive(Clone, Debug, Default, PartialEq, Eq)]
pub(super) struct ProxyTransformerChain {
    names: Vec<String>,
}

impl ProxyTransformerChain {
    pub(super) fn for_credential(credential: &OpenAiProxyCredential, wants_stream: bool) -> Self {
        let mut chain = Self::default();
        chain.push(CLEANCACHE);
        if wants_stream {
            chain.push(STREAMOPTIONS);
        }
        if is_deepseek_credential(credential) {
            chain.push(DEEPSEEK);
        }

        // ClaudePrism already buffers and repairs tool-call arguments before
        // returning them to Claude Code. Naming it here keeps the behavior
        // traceable to Claude Code Router's enhancetool transformer.
        chain.push(ENHANCETOOL);
        for name in &credential.transformers {
            chain.push(name);
        }
        for name in &credential.model_transformers {
            chain.push(name);
        }
        for name in configured_transformer_names() {
            chain.push(&name);
        }
        chain
    }

    pub(super) fn has(&self, name: &str) -> bool {
        self.names
            .iter()
            .any(|candidate| candidate.eq_ignore_ascii_case(name))
    }

    pub(super) fn has_tooluse(&self) -> bool {
        self.has(TOOLUSE)
    }

    pub(super) fn has_cleancache(&self) -> bool {
        self.has(CLEANCACHE)
    }

    pub(super) fn has_deepseek(&self) -> bool {
        self.has(DEEPSEEK)
    }

    pub(super) fn has_streamoptions(&self) -> bool {
        self.has(STREAMOPTIONS)
    }

    #[cfg(test)]
    pub(super) fn from_names(names: &[&str]) -> Self {
        let mut chain = Self::default();
        for name in names {
            chain.push(name);
        }
        chain
    }

    fn push(&mut self, name: &str) {
        let name = name.trim();
        if name.is_empty() || self.has(name) {
            return;
        }
        self.names.push(name.to_ascii_lowercase());
    }
}

fn configured_transformer_names() -> Vec<String> {
    std::env::var("CLAUDE_PRISM_PROXY_TRANSFORMERS")
        .ok()
        .into_iter()
        .flat_map(|value| {
            value
                .split(',')
                .map(str::trim)
                .filter(|name| !name.is_empty())
                .map(str::to_string)
                .collect::<Vec<_>>()
        })
        .collect()
}

fn is_deepseek_credential(credential: &OpenAiProxyCredential) -> bool {
    let base_url = credential.base_url.to_ascii_lowercase();
    let model = credential.model.to_ascii_lowercase();
    base_url.contains("deepseek") || model.contains("deepseek")
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
    fn includes_ccr_style_defaults_for_common_provider_adapters() {
        let chain = ProxyTransformerChain::for_credential(
            &credential("https://api.deepseek.com", "deepseek-chat"),
            true,
        );

        assert!(chain.has_cleancache());
        assert!(chain.has_streamoptions());
        assert!(chain.has_deepseek());
        assert!(chain.has(ENHANCETOOL));
    }

    #[test]
    fn does_not_enable_tooluse_unless_configured() {
        let chain = ProxyTransformerChain::for_credential(
            &credential("https://api.example.com/v1", "qwen"),
            false,
        );

        assert!(!chain.has_tooluse());
    }

    #[test]
    fn accepts_explicit_model_transformers() {
        let mut credential = credential("https://api.example.com/v1", "qwen");
        credential.model_transformers = vec!["tooluse".to_string()];

        let chain = ProxyTransformerChain::for_credential(&credential, false);

        assert!(chain.has_tooluse());
    }
}
