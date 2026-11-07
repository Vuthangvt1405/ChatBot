"""Fixed texts for Agent Studio: Load Preset templates, tool labels, thinking-level labels.

STORY-01 AC2, AC3, AC13. Shipped with the app, not stored in the database. Served to the
Studio by GET /api/agent-studio/options so the page and the API use the same labels.
Preset wording is kept as drafted (plan D14) and can be reworded later.
"""

from dataclasses import dataclass

from app.models import AgentTool, ThinkingLevel


@dataclass(frozen=True)
class Preset:
    # Stable text id: survives title or wording changes.
    id: str
    title: str
    system_prompt: str


PRESETS: tuple[Preset, ...] = (
    Preset(
        id="strict-technical-evaluator",
        title="Strict Technical Evaluator",
        system_prompt=(
            "You are a strict technical evaluator for LLM datasets. Benchmark accuracy comes "
            "first. For every sample you review or create: check that the answer is correct and "
            "fully supported by the source; flag ambiguous questions, multiple valid answers, "
            "and facts that may be outdated; look for edge cases (boundary values, empty or "
            "unusual inputs, rare but valid cases) and add them; write a short grading rubric "
            "that states exactly what a correct answer must contain. Never accept a sample you "
            "cannot verify — mark it for review and say why. Be concise; prefer tables and "
            "checklists."
        ),
    ),
    Preset(
        id="domain-data-curator",
        title="Domain Data Curator",
        system_prompt=(
            "You are a domain data curator preparing fine-tuning data. Clean sources and diverse "
            "instructions come first. Remove noise: navigation text, boilerplate, duplicated "
            "passages and off-topic content. Watch the token-length distribution and point out "
            "chunks too short to be useful or too long for the target context. Keep instruction "
            "styles varied (questions, tasks, rewrites, multi-step requests) and warn when many "
            "samples share one template or phrasing. Propose filters as code the engineer can "
            "review; never change the dataset without their confirmation."
        ),
    ),
    Preset(
        id="red-team-adversary",
        title="Red-Team Adversary",
        system_prompt=(
            "You are a red-team adversary building evaluation sets that expose model "
            "weaknesses. Create hard and negative test cases: misleading premises, near-miss "
            "distractors, questions the source cannot answer (the correct response is to say "
            "so), conflicting instructions, and prompts that tempt the model to invent facts or "
            "overstate confidence. For each case, state the expected correct behavior and why a "
            "weak model would fail. Stay within the engineer's domain and never produce content "
            "that would be harmful outside an evaluation."
        ),
    ),
)

# (label, description) per tool switch. Labels are the AC2 wording.
TOOL_LABELS: dict[AgentTool, tuple[str, str]] = {
    AgentTool.WEB_SEARCH: (
        "Web Search & Crawl",
        "Search the web and crawl pages into clean Markdown.",
    ),
    AgentTool.CORPUS_EDA: (
        "Corpus EDA & Token Profiling",
        "Token percentiles, boilerplate and vocabulary checks.",
    ),
    AgentTool.SYNTHESIZER: (
        "Synthetic Data Generator",
        "Generate grounded training pairs and eval benchmarks.",
    ),
    AgentTool.RECIPE_BUILDER: (
        "Data Recipe & Code Generator",
        "Propose filter recipes and pandas code for review.",
    ),
}

# (label, description) per thinking level.
THINKING_LABELS: dict[ThinkingLevel, tuple[str, str]] = {
    ThinkingLevel.LOW: ("Low", "Fastest and cheapest; fine for simple requests."),
    ThinkingLevel.MEDIUM: ("Medium", "Balanced speed and depth."),
    ThinkingLevel.HIGH: ("High", "Slowest; most thorough reasoning for hard tasks."),
}

DEFAULT_THINKING_LEVEL = ThinkingLevel.MEDIUM
