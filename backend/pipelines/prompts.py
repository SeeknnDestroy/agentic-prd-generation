"""Prompt templates for the agentic PRD generation pipeline."""

# Aether's Rationale:
# Using a structured, detailed prompt is crucial for guiding the LLM to
# produce high-quality, consistent output. These prompts are designed to
# be clear, specific, and focused on a single task.

OUTLINE_PROMPT = """
You are a world-class product manager. Your task is to create a structured
outline for a Product Requirements Document (PRD) based on a given project idea.

The outline should cover all standard sections of a PRD, including:
1.  Executive Summary
2.  Problem Statement & User Personas
3.  Goals & Success Metrics
4.  Functional Requirements (Features)
5.  Non-Functional Requirements (Performance, Security, etc.)
6.  Out-of-Scope Items
7.  Risks & Mitigations

Please generate a Markdown-formatted outline for the following project idea:

**Project Idea:** "{idea}"

**Instructions:**
- Use Markdown headings (`#`, `##`, `###`) to structure the document.
- For each section, include a brief, one-sentence placeholder description of
  what it will contain.
- Do NOT write the full content of the PRD yet. Just the outline.
"""

DRAFT_PROMPT = """
You are a world-class product manager. Your task is to expand a given PRD
outline into a full first draft.

Use the provided outline and flesh out each section with detailed, clear, and
concise content. Make reasonable assumptions where necessary, but clearly
state them.

**PRD Outline to Draft:**
```markdown
{outline}
```

**Instructions:**
- Write comprehensive content for every section of the outline.
- Use clear and professional language.
- Format the output as a complete Markdown document.
- Ensure the functional requirements are specific and actionable.
- The draft should be complete enough for a stakeholder to understand the
  entire scope of the project.
"""

CRITIQUE_PROMPT = """
You are a meticulous and critical product manager. Your task is to review a
draft of a Product Requirements Document (PRD) and provide constructive
feedback.

Analyze the following PRD draft for clarity, completeness, coherence, and
realism. Identify any ambiguities, contradictions, or missing information.

**PRD Draft to Critique:**
```markdown
{draft}
```

**Instructions:**
- Provide your critique as a list of bullet points.
- For each point, specify the section of the PRD it refers to.
- Focus on actionable feedback that can be used to improve the document.
- Be ruthless but fair. The goal is to make the PRD as strong as possible.
- If you find no issues, simply respond with "No issues found."
"""

REVISE_PROMPT = """
You are a world-class product manager. Your task is to revise a Product
Requirements Document (PRD) draft based on a set of critiques.

Carefully review the original draft and the provided feedback. Update the PRD
to address all the points raised in the critique.

**Original PRD Draft:**
```markdown
{draft}
```

**Critique to Address:**
```
{critique}
```

**Instructions:**
- Produce a new, complete version of the PRD in Markdown format.
- Incorporate all the suggested changes from the critique.
- Ensure the revised document is coherent and consistent.
- Do not include the critique in the final output. Only the revised PRD.
"""
