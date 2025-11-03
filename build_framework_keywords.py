import json
import re
from collections import defaultdict, Counter

INPUT_JSON = "agentic_semantic_features.json"
GLOBAL_KEYWORDS = "agentic_semantic_keywords.json"
OUTPUT_JSON = "framework_semantic_keywords.json"

# Framework name normalizations
FRAMEWORK_ALIASES = {
    "langchain": "LangChain",
    "autogen": "AutoGen",
    "smolagents": "SmolAgents",
    "crewai": "CrewAI",
    "superagi": "SuperAGI",
    "metagpt": "MetaGPT",
    "agno": "Agno",
    "haystack": "Haystack",
    "llamaindex": "LlamaIndex",
    "openai": "OpenAI",
    "vertexai": "VertexAI",
    "semantic_kernel": "SemanticKernel",
    "agentverse": "AgentVerse",
    "uagents": "uAgents",
    "anyagent": "AnyAgent",
    "letta": "Letta",
    "agentscope": "AgentScope",
    "lagent": "Lagent",
}

def normalize_token(t):
    t = re.sub(r"[^a-zA-Z0-9_]", "", t)
    return t.lower()

def build_framework_keywords():
    with open(INPUT_JSON, encoding="utf-8") as f:
        data = json.load(f)

    # Try to load global keywords for weighting
    global_tokens = set()
    try:
        with open(GLOBAL_KEYWORDS, encoding="utf-8") as g:
            kw_data = json.load(g)
            global_tokens = {k for k, _ in kw_data.get("semantic_keywords", [])}
    except Exception:
        pass

    framework_keywords = defaultdict(Counter)

    for provider, repo in data.items():
        signals = repo.get("framework_signals", {})
        frameworks = signals.get("frameworks", [])
        if not frameworks:
            continue

        # Derive normalized framework name(s)
        frameworks_norm = set()
        for fw in frameworks:
            fw_norm = normalize_token(fw)
            if fw_norm in FRAMEWORK_ALIASES:
                frameworks_norm.add(FRAMEWORK_ALIASES[fw_norm])
            else:
                frameworks_norm.add(fw.title())

        # Gather all tokens from semantic fields
        all_tokens = []
        for cat, values in signals.items():
            if isinstance(values, list):
                all_tokens.extend(values)
        all_tokens = [normalize_token(v) for v in all_tokens if v]

        # Update counters
        for fw in frameworks_norm:
            framework_keywords[fw].update(all_tokens)

    # Build output
    framework_patterns = {}
    for fw, counter in framework_keywords.items():
        common = [tok for tok, _ in counter.most_common(50)]
        # Filter out overly generic terms
        filtered = [
            t for t in common
            if len(t) > 2 and t not in {"tool", "step", "task", "context", "schema"}
        ]
        framework_patterns[fw] = filtered

    with open(OUTPUT_JSON, "w", encoding="utf-8") as out:
        json.dump(framework_patterns, out, indent=2)

    print(f"✅ Framework keyword sets written to {OUTPUT_JSON}")

if __name__ == "__main__":
    build_framework_keywords()
