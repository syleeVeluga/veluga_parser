---
name: orchestrate
description: Orchestrate the full 3-Agent harness workflow end-to-end
disable-model-invocation: true
argument-hint: "<feature requirements>"
---

# Orchestrator

You are the **orchestrator** of the 3-Agent harness.
Your role is to coordinate the entire workflow and invoke each agent in sequence.

## Requirements
$ARGUMENTS

## Workflow Execution

### Phase 1: Initialization
```bash
mkdir -p .harness/sprints
```
Create the `.harness/` directory if it doesn't exist.

### Phase 2: Planning
Run the `/plan` command to generate the spec document.
Show the generated `.harness/spec.md` to the user and request approval.

**Do NOT proceed to the next phase without user approval.**

### Phase 3: Sprint Iteration
For each Sprint:

1. **Contract negotiation**: Write a Sprint contract agreed upon by Generator and Evaluator
2. **Implementation**: Run `/build sprint-N`
3. **Evaluation**: Run `/evaluate sprint-N`
4. **Result check**:
   - PASS → Move to next Sprint
   - FAIL → Incorporate feedback and re-run `/build sprint-N` (max 3 attempts)

### Phase 4: Final Report
After all Sprints are complete, produce a final summary:
- List of implemented features
- Overall test results
- Estimated total time/cost
- Known limitations

## Context Reset Triggers
Consider a context reset when:
- The conversation has become very long
- The agent appears to be forgetting earlier instructions
- The agent is rushing to finish tasks prematurely ("context anxiety" symptoms)

On reset:
1. Serialize current state to `.harness/` files
2. Start new session reading from `.harness/` files

## Emergency Stop
After 3 consecutive FAILs:
- Save current progress
- Write a problem analysis summary
- Request manual intervention from the user
