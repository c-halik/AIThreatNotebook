# Agentic AI Security Primer

A starter reference. Replace or expand this with your own curated material
(OWASP LLM Top 10, MITRE ATLAS, vendor threat reports, etc.).

## Core threat categories for agentic AI systems

1. **Prompt injection** - untrusted content (web pages, documents, tool
   output) contains instructions that hijack the agent's behavior. Direct
   injection comes from the user; indirect injection comes from data the
   agent reads while performing a task.

2. **Excessive agency** - an agent is granted more permissions, tools, or
   autonomy than the task requires, so a successful injection or reasoning
   error has a larger blast radius (e.g. an agent with unscoped file-delete
   or shell access).

3. **Tool/plugin abuse** - attacker-controlled input reaches a tool call
   (code execution, HTTP requests, database queries) with insufficient
   validation, enabling classic vulnerabilities (SSRF, command injection,
   SQL injection) via the LLM as an intermediary.

4. **Insecure output handling** - downstream systems trust LLM output
   without sanitization, letting the model's output become an injection
   vector into other components (e.g. rendering model output as HTML/JS).

5. **Memory/context poisoning** - long-running agents with persistent
   memory or RAG stores can be poisoned by attacker-supplied data that
   later biases the agent's decisions in future sessions.

6. **Multi-agent trust boundary issues** - in systems where multiple agents
   delegate tasks to each other, a compromised or malicious sub-agent can
   propagate bad instructions or data up the chain.

## Relevant frameworks to track

- OWASP Top 10 for LLM Applications
- MITRE ATLAS (Adversarial Threat Landscape for AI Systems)
- NIST AI Risk Management Framework

## Practical mitigations

- Principle of least privilege for tool/agent permissions, scoped per task.
- Treat all retrieved/tool content as untrusted input, never as instructions.
- Human-in-the-loop approval for high-impact actions (payments, deletions,
  privilege changes).
- Log and audit every tool call an agent makes, with the reasoning that led
  to it, for post-incident review.
