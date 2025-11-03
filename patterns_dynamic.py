"""
patterns_dynamic.py
-------------------
Dynamic agentic pattern engine for classifying repositories.

This module:
  ✅ Loads learned agentic keywords from your analysis outputs
  ✅ Dynamically builds regex patterns for each framework
  ✅ Detects agentic signals, integrations, tools, and SDK frameworks
  ✅ Returns structured classification and confidence scores
"""

import json
import os
import re
from collections import defaultdict, Counter


# ======================================================
# CONFIGURATION
# ======================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Paths to the mined data JSONs
SEMANTIC_KEYWORDS_PATH = os.path.join(BASE_DIR, "agentic_semantic_keywords.json")
FRAMEWORK_KEYWORDS_PATH = os.path.join(BASE_DIR, "framework_semantic_keywords.json")

# Fallback in case files aren’t found
DEFAULT_AGENTIC_KEYWORDS = [
    "agent", "planner", "executor", "memory", "workflow",
    "tool", "reasoning", "context", "environment", "coordinator"
]

DEFAULT_FRAMEWORKS = {
    "LangChain": ["llm", "chain", "prompt", "memory", "tool", "workflow"],
    "AutoGen": ["assistant", "groupchat", "planner", "userproxy"],
    "CrewAI": ["crew", "role", "task", "planner", "executor"],
    "SmolAgents": ["codeagent", "multistep", "toolcalling", "reason"],
    "Semantic_Kernel": ["planner", "skill", "function", "semanticfunction"],
}


# ======================================================
# HELPER FUNCTIONS
# ======================================================

def load_json_safe(path, fallback=None):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return fallback or {}


def build_pattern_from_keywords(keywords):
    if not keywords:
        return None
    escaped = [re.escape(k) for k in keywords if k]
    return re.compile(r"\b(" + "|".join(escaped) + r")\b", re.IGNORECASE)


def compute_confidence(matches, total_keywords):
    if not total_keywords:
        return 0.0
    return round(min(1.0, len(matches) / total_keywords), 3)


# ======================================================
# LOAD DATASETS
# ======================================================

AGENTIC_KEYWORDS = load_json_safe(SEMANTIC_KEYWORDS_PATH, DEFAULT_AGENTIC_KEYWORDS)
FRAMEWORK_KEYWORDS = load_json_safe(FRAMEWORK_KEYWORDS_PATH, DEFAULT_FRAMEWORKS)


# ======================================================
# CORE DETECTION PATTERNS
# ======================================================

CATEGORY_PATTERNS = {
    "integration_points": re.compile(
        r"\b(openai|vertexai|huggingface|anthropic|cohere|azure|slack|jira|notion|airtable|zapier)\b",
        re.IGNORECASE,
    ),
    "sdk_refs": re.compile(
        r"\b(langchain|autogen|smolagents|crewai|semantic[_-]?kernel|llamaindex|haystack|uagents)\b",
        re.IGNORECASE,
    ),
    "config_metadata": re.compile(
        r"(model|api[_-]?key|endpoint|tool|env|config|yaml|json)", re.IGNORECASE,
    ),
    "languages": re.compile(r"\.(py|ts|js|java|cs|go|rs)\b", re.IGNORECASE),
}


# ======================================================
# MAIN DETECTION LOGIC
# ======================================================

def detect_agentic_features(text):
    """
    Given repo text (code, readme, configs, etc.), detect agentic signals and classify frameworks.
    Returns a structured dict:
      {
        "is_agentic": True,
        "confidence": 0.87,
        "frameworks": ["LangChain", "SmolAgents"],
        "tools": ["openai", "slack"],
        "sdks": ["langchain"],
        "languages": ["py"],
        "keywords_matched": {...}
      }
    """

    results = defaultdict(list)
    framework_scores = {}
    text_lower = text.lower()

    # --- Agentic core keywords ---
    if isinstance(AGENTIC_KEYWORDS, dict):
        all_keywords = list(AGENTIC_KEYWORDS.keys())
    else:
        all_keywords = AGENTIC_KEYWORDS

    core_pattern = build_pattern_from_keywords(all_keywords)
    if core_pattern:
        results["agentic_keywords"] = core_pattern.findall(text_lower)

    # --- Framework-specific detection ---
    for fw, keywords in FRAMEWORK_KEYWORDS.items():
        pattern = build_pattern_from_keywords(keywords)
        matches = pattern.findall(text_lower) if pattern else []
        if matches:
            framework_scores[fw] = compute_confidence(matches, len(keywords))
            results[fw] = matches

    # --- Generic category patterns ---
    for cat, pattern in CATEGORY_PATTERNS.items():
        matches = pattern.findall(text_lower)
        if matches:
            results[cat] = matches

    # --- Classification summary ---
    frameworks = [fw for fw, score in framework_scores.items() if score > 0.2]
    is_agentic = bool(frameworks or results["agentic_keywords"])
    confidence = max(framework_scores.values(), default=0.0)
    tools = list(set(results.get("integration_points", [])))
    sdks = list(set(results.get("sdk_refs", [])))
    languages = list(set(results.get("languages", [])))

    return {
        "is_agentic": is_agentic,
        "confidence": confidence,
        "frameworks": frameworks,
        "tools": tools,
        "sdks": sdks,
        "languages": languages,
        "keywords_matched": results,
    }


# ======================================================
# COMMAND-LINE TESTING
# ======================================================

if __name__ == "__main__":
    sample_text = """
    from langchain.agents import AgentExecutor
    import openai
    # This agent uses a reasoning planner and memory module.
    """

    result = detect_agentic_features(sample_text)
    print(json.dumps(result, indent=2))

# ======================================================
# REGEX EXPORT UTILITIES
# ======================================================

def export_dynamic_regexes(output_path="agentic_regex_patterns.json"):
    """
    Build reusable regex patterns for external systems, based on learned data.
    Saves a JSON file mapping categories to regex strings.
    """
    regex_map = {}

    # Core agentic detection
    agentic_keywords = (
        list(AGENTIC_KEYWORDS.keys()) if isinstance(AGENTIC_KEYWORDS, dict) else AGENTIC_KEYWORDS
    )
    regex_map["core_agentic"] = r"\b(" + "|".join(map(re.escape, agentic_keywords)) + r")\b"

    # Framework patterns
    for fw, keywords in FRAMEWORK_KEYWORDS.items():
        regex_map[f"framework_{fw.lower()}"] = r"\b(" + "|".join(map(re.escape, keywords)) + r")\b"

    # Integration & metadata
    regex_map["integration_points"] = CATEGORY_PATTERNS["integration_points"].pattern
    regex_map["sdk_refs"] = CATEGORY_PATTERNS["sdk_refs"].pattern
    regex_map["config_metadata"] = CATEGORY_PATTERNS["config_metadata"].pattern
    regex_map["languages"] = CATEGORY_PATTERNS["languages"].pattern

    # Save to file
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(regex_map, f, indent=2)

    print(f"✅ Exported regex patterns to {output_path}")
    return regex_map


if __name__ == "__main__":
    # Quick demo: generate regexes
    regexes = export_dynamic_regexes()
    print(json.dumps(regexes, indent=2))

