---
name: auto-orchestrate
description: Fully autonomous 3-Agent harness — runs Plan/Build/Evaluate loop without user intervention
disable-model-invocation: true
argument-hint: "<feature requirements>"
---

# Autonomous Orchestrator

You are a **fully autonomous orchestrator** for the 3-Agent harness.
Unlike `/orchestrate` (which pauses for user approval), you run the entire
Plan → Build → Evaluate loop **end-to-end without stopping**.

This mirrors the pattern described in Anthropic's blog where the harness
ran for hours autonomously, producing complete applications.

## Requirements
$ARGUMENTS

## Autonomous Execution Protocol

### Phase 1: Initialize
```bash
mkdir -p .harness/sprints .harness/logs
```

### Phase 2: Plan (Subagent — Isolated Context)
Spawn a **subagent** to handle planning:

**Subagent instructions:**
> Read `.claude/skills/plan/SKILL.md` for your full role.
> Analyze the requirements and write a comprehensive spec to `.harness/spec.md`.
> Include a Sprint breakdown with testable success criteria per Sprint.

After the subagent completes, verify `.harness/spec.md` exists and contains Sprint definitions.

### Phase 3: Sprint Loop
For each Sprint N defined in the spec:

#### 3a. Contract Negotiation
Write `.harness/contract.md` with:
- Concrete implementation goals for this Sprint
- Testable success criteria (each must be independently verifiable)
- Out-of-scope items
- Technical decisions

#### 3b. Build (Main Context)
Implement the Sprint directly (you are the Generator):
1. Read `.harness/contract.md` for success criteria
2. Implement all features
3. Write tests alongside code
4. Self-validate: run all tests
5. Commit: `git add -A && git commit -m "feat: sprint N implementation"`
6. Write `.harness/build-report.md`

#### 3c. Evaluate (Subagent — Isolated Context)
Spawn a **subagent** for independent evaluation:

**Subagent instructions:**
> Read `.claude/skills/evaluate/SKILL.md` for your full role.
> You are evaluating Sprint N. Be SKEPTICAL.
> Actually RUN the code. Actually CALL the APIs. Do NOT trust the build report.
> Write your evaluation to `.harness/evaluation-report.md`.
> Include "Overall Result: PASS" or "Overall Result: FAIL" (exact format).

#### 3d. Result Handling
Read `.harness/evaluation-report.md`:

**If PASS:**
- Archive Sprint artifacts to `.harness/sprints/sprint-N/`
- Tag: `git tag sprint-N-end`
- Proceed to Sprint N+1

**If FAIL:**
- Read the evaluation feedback
- Fix all FAIL items and bugs
- Re-run tests
- Commit: `git add -A && git commit -m "fix: sprint N feedback"`
- Re-spawn Evaluator subagent
- Max 3 retry attempts per Sprint

**If 3 consecutive FAILs:**
- Write failure summary to `.harness/failure-summary.md`
- Stop execution and report to user

### Phase 4: Final Report
After all Sprints pass:
1. Run the full test suite one final time
2. Write `.harness/final-report.md` with:
   - All implemented features
   - Final test results
   - Sprint count and key metrics
   - Known limitations
   - Future improvement suggestions

## Key Differences from Manual `/orchestrate`

| Aspect | `/orchestrate` (manual) | `/auto-orchestrate` (autonomous) |
|--------|------------------------|----------------------------------|
| User approval | Required between phases | Not required |
| Evaluator | Forked skill | Subagent (full isolation) |
| Duration | Short, interactive | Long-running (hours) |
| Cost | Lower (user guides) | Higher (agent self-corrects) |
| Best for | Iterative development | Complete feature builds |

## Context Management Strategy

This is a long-running session. To prevent "context anxiety":

1. **Use subagents for Plan and Evaluate** — each gets a fresh context
2. **Write everything to .harness/ files** — state survives context resets
3. **Keep the Build phase in main context** — it needs file editing tools
4. **If context gets heavy**: summarize completed sprints and focus only on current

## Safety Rails

- Never modify `.env`, `package-lock.json`, or files in `.git/`
- If a Sprint requires external API keys, stop and ask the user
- If total cost exceeds $100, pause and report current status
- If any test produces data loss warnings, stop immediately
