#!/bin/bash
# ============================================================================
# Fullstack Agent Harness - Autonomous Orchestrator
# ============================================================================
# Runs the full Plan → Build → Evaluate loop autonomously via Claude Code CLI.
# Based on Anthropic's "Harness Design for Long-Running Apps" pattern.
#
# Usage:
#   ./harness.sh "Build a todo app with user auth and real-time sync"
#   ./harness.sh "Add payment processing with Stripe" --max-sprints 3
#   ./harness.sh "Implement dashboard analytics" --skip-plan
#
# Requirements:
#   - Claude Code CLI installed and authenticated
#   - jq installed
#   - Project has .claude/ directory with skills configured
# ============================================================================

set -euo pipefail

# ── Configuration ──────────────────────────────────────────────────────────
MAX_SPRINTS="${MAX_SPRINTS:-5}"
MAX_RETRIES="${MAX_RETRIES:-3}"        # Max FAIL retries per Sprint
MAX_BUDGET="${MAX_BUDGET:-50}"         # Max USD per agent call
MODEL="${MODEL:-opus}"                 # Model to use
HARNESS_DIR=".harness"
LOG_DIR="${HARNESS_DIR}/logs"
SKIP_PLAN=false

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ── Argument Parsing ───────────────────────────────────────────────────────
REQUIREMENTS=""

while [[ $# -gt 0 ]]; do
  case $1 in
    --max-sprints)
      MAX_SPRINTS="$2"
      shift 2
      ;;
    --max-retries)
      MAX_RETRIES="$2"
      shift 2
      ;;
    --max-budget)
      MAX_BUDGET="$2"
      shift 2
      ;;
    --model)
      MODEL="$2"
      shift 2
      ;;
    --skip-plan)
      SKIP_PLAN=true
      shift
      ;;
    --help)
      echo "Usage: ./harness.sh \"<requirements>\" [options]"
      echo ""
      echo "Options:"
      echo "  --max-sprints N    Maximum number of sprints (default: 5)"
      echo "  --max-retries N    Max retries per sprint on FAIL (default: 3)"
      echo "  --max-budget N     Max USD per agent call (default: 50)"
      echo "  --model MODEL      Model to use: opus, sonnet (default: opus)"
      echo "  --skip-plan        Skip planning phase (use existing spec.md)"
      echo "  --help             Show this help message"
      exit 0
      ;;
    *)
      REQUIREMENTS="$1"
      shift
      ;;
  esac
done

if [ -z "$REQUIREMENTS" ] && [ "$SKIP_PLAN" = false ]; then
  echo -e "${RED}Error: Requirements argument is required.${NC}"
  echo "Usage: ./harness.sh \"<requirements>\" [options]"
  exit 1
fi

# ── Helper Functions ───────────────────────────────────────────────────────

log() {
  local level="$1"
  local message="$2"
  local timestamp
  timestamp=$(date '+%Y-%m-%d %H:%M:%S')

  case "$level" in
    INFO)  echo -e "${CYAN}[$timestamp]${NC} ${BLUE}[INFO]${NC}  $message" ;;
    OK)    echo -e "${CYAN}[$timestamp]${NC} ${GREEN}[OK]${NC}    $message" ;;
    WARN)  echo -e "${CYAN}[$timestamp]${NC} ${YELLOW}[WARN]${NC}  $message" ;;
    ERROR) echo -e "${CYAN}[$timestamp]${NC} ${RED}[ERROR]${NC} $message" ;;
    PHASE) echo -e "\n${CYAN}[$timestamp]${NC} ${GREEN}═══════════════════════════════════════${NC}"
           echo -e "${CYAN}[$timestamp]${NC} ${GREEN}  $message${NC}"
           echo -e "${CYAN}[$timestamp]${NC} ${GREEN}═══════════════════════════════════════${NC}\n" ;;
  esac

  # Also write to log file
  echo "[$timestamp] [$level] $message" >> "${LOG_DIR}/harness.log"
}

run_agent() {
  local prompt="$1"
  local label="$2"
  local log_file="${LOG_DIR}/${label}.log"

  log INFO "Running agent: $label"
  log INFO "Budget limit: \$${MAX_BUDGET}"

  local start_time
  start_time=$(date +%s)

  # Run Claude Code in print mode with budget cap
  claude -p "$prompt" \
    --model "$MODEL" \
    --max-budget-usd "$MAX_BUDGET" \
    --output-format text \
    2>&1 | tee "$log_file"

  local exit_code=${PIPESTATUS[0]}
  local end_time
  end_time=$(date +%s)
  local duration=$(( end_time - start_time ))

  log INFO "Agent '$label' completed in ${duration}s (exit: $exit_code)"

  return $exit_code
}

check_evaluation_result() {
  local report="${HARNESS_DIR}/evaluation-report.md"

  if [ ! -f "$report" ]; then
    log WARN "No evaluation report found"
    echo "UNKNOWN"
    return
  fi

  # Extract overall result from the report
  local result
  result=$(grep -i "Overall Result:" "$report" | head -1 || echo "")

  if echo "$result" | grep -qi "PASS"; then
    echo "PASS"
  elif echo "$result" | grep -qi "FAIL"; then
    echo "FAIL"
  else
    echo "UNKNOWN"
  fi
}

extract_sprint_count() {
  local spec="${HARNESS_DIR}/spec.md"

  if [ ! -f "$spec" ]; then
    echo "$MAX_SPRINTS"
    return
  fi

  # Count Sprint headers in spec
  local count
  count=$(grep -c "^### Sprint" "$spec" || echo "0")

  if [ "$count" -gt 0 ] && [ "$count" -le "$MAX_SPRINTS" ]; then
    echo "$count"
  else
    echo "$MAX_SPRINTS"
  fi
}

# ── Initialize ─────────────────────────────────────────────────────────────

mkdir -p "$HARNESS_DIR/sprints" "$LOG_DIR"

log PHASE "HARNESS STARTING"
log INFO "Requirements: $REQUIREMENTS"
log INFO "Config: max_sprints=$MAX_SPRINTS, max_retries=$MAX_RETRIES, model=$MODEL"

TOTAL_START=$(date +%s)

# ── Phase 1: Planning ──────────────────────────────────────────────────────

if [ "$SKIP_PLAN" = false ]; then
  log PHASE "PHASE 1: PLANNING"

  PLAN_PROMPT="You are the Planner agent. Read .claude/skills/plan/SKILL.md for your full instructions.

Your task: $REQUIREMENTS

IMPORTANT:
- Write the complete spec to .harness/spec.md
- Include a Sprint breakdown with clear success criteria per Sprint
- Be concrete and specific — the Generator must be able to implement directly from your spec
- Focus on WHAT to build, not HOW"

  if ! run_agent "$PLAN_PROMPT" "phase1-plan"; then
    log ERROR "Planning phase failed"
    exit 1
  fi

  if [ ! -f "${HARNESS_DIR}/spec.md" ]; then
    log ERROR "Planner did not create spec.md"
    exit 1
  fi

  log OK "Planning complete. Spec written to ${HARNESS_DIR}/spec.md"
else
  log INFO "Skipping planning phase (--skip-plan)"
  if [ ! -f "${HARNESS_DIR}/spec.md" ]; then
    log ERROR "No existing spec.md found. Cannot skip planning."
    exit 1
  fi
fi

# ── Phase 2: Sprint Loop ──────────────────────────────────────────────────

TOTAL_SPRINTS=$(extract_sprint_count)
log INFO "Detected $TOTAL_SPRINTS sprints in spec"

for (( sprint=1; sprint<=TOTAL_SPRINTS; sprint++ )); do
  log PHASE "PHASE 2: SPRINT $sprint / $TOTAL_SPRINTS"

  retry_count=0
  sprint_passed=false

  # ── Sprint Contract ──
  log INFO "Negotiating Sprint $sprint contract..."

  CONTRACT_PROMPT="You are the Generator agent. Read .claude/skills/build/SKILL.md for your full instructions.

TASK: Create the Sprint $sprint contract.

1. Read .harness/spec.md to understand the full spec
2. Write a Sprint contract to .harness/contract.md with:
   - Specific implementation goals for Sprint $sprint
   - Testable success criteria (checkboxes)
   - What is OUT of scope for this Sprint
   - Technical decisions

The contract must contain concrete, testable success criteria that the Evaluator can verify independently."

  run_agent "$CONTRACT_PROMPT" "sprint${sprint}-contract"

  while [ $retry_count -lt $MAX_RETRIES ] && [ "$sprint_passed" = false ]; do
    retry_count=$((retry_count + 1))

    # ── Build ──
    log INFO "Sprint $sprint — Build attempt $retry_count/$MAX_RETRIES"

    if [ $retry_count -eq 1 ]; then
      BUILD_PROMPT="You are the Generator agent. Read .claude/skills/build/SKILL.md for your full instructions.

TASK: Implement Sprint $sprint.

1. Read .harness/spec.md for the full spec
2. Read .harness/contract.md for this Sprint's success criteria
3. Implement all features listed in the contract
4. Write tests alongside your implementation
5. Run all tests and verify they pass
6. Write your build report to .harness/build-report.md
7. Commit your changes with: git add -A && git commit -m 'feat: sprint $sprint implementation'

Follow all conventions in .claude/CLAUDE.md. Do NOT skip any success criteria."
    else
      BUILD_PROMPT="You are the Generator agent. Read .claude/skills/build/SKILL.md for your full instructions.

TASK: Fix Sprint $sprint issues (attempt $retry_count).

1. Read .harness/evaluation-report.md for the Evaluator's feedback
2. Fix ALL items marked as FAIL
3. Fix ALL bugs listed in the report
4. Re-run tests to verify fixes
5. Update .harness/build-report.md
6. Commit fixes with: git add -A && git commit -m 'fix: sprint $sprint evaluation feedback (attempt $retry_count)'

Address every single issue raised by the Evaluator. Do not skip any."
    fi

    if ! run_agent "$BUILD_PROMPT" "sprint${sprint}-build-attempt${retry_count}"; then
      log WARN "Build failed (attempt $retry_count)"
      continue
    fi

    # ── Evaluate ──
    log INFO "Sprint $sprint — Evaluating (attempt $retry_count)"

    EVAL_PROMPT="You are the Evaluator agent. Read .claude/skills/evaluate/SKILL.md for your full instructions.

TASK: Evaluate Sprint $sprint implementation.

CRITICAL RULES:
- Be SKEPTICAL. Do not trust the Generator's self-assessment.
- Actually RUN the tests. Actually START the server. Actually CALL the APIs.
- Every judgment must have EVIDENCE.
- 'It probably works' = FAIL. Only confirmed results = PASS.

Steps:
1. Read .harness/contract.md for success criteria
2. Read .harness/build-report.md for what was implemented
3. Run ALL tests (pytest, npm test, etc.)
4. Verify EACH contract item independently
5. Hunt for bugs with malformed input, edge cases, etc.
6. Write your evaluation report to .harness/evaluation-report.md

The report MUST contain:
- 'Overall Result: PASS' or 'Overall Result: FAIL' (exact format)
- Scores for each category
- Evidence for every PASS/FAIL judgment"

    if ! run_agent "$EVAL_PROMPT" "sprint${sprint}-eval-attempt${retry_count}"; then
      log WARN "Evaluation agent failed"
      continue
    fi

    # ── Check Result ──
    result=$(check_evaluation_result)

    case "$result" in
      PASS)
        log OK "Sprint $sprint PASSED on attempt $retry_count"
        sprint_passed=true

        # Archive Sprint artifacts
        mkdir -p "${HARNESS_DIR}/sprints/sprint-${sprint}"
        cp "${HARNESS_DIR}/contract.md" "${HARNESS_DIR}/sprints/sprint-${sprint}/" 2>/dev/null || true
        cp "${HARNESS_DIR}/build-report.md" "${HARNESS_DIR}/sprints/sprint-${sprint}/" 2>/dev/null || true
        cp "${HARNESS_DIR}/evaluation-report.md" "${HARNESS_DIR}/sprints/sprint-${sprint}/review.md" 2>/dev/null || true

        # Tag in git
        git tag "sprint-${sprint}-end" 2>/dev/null || true
        ;;
      FAIL)
        log WARN "Sprint $sprint FAILED (attempt $retry_count/$MAX_RETRIES)"
        ;;
      *)
        log WARN "Sprint $sprint evaluation result unclear (attempt $retry_count)"
        ;;
    esac
  done

  if [ "$sprint_passed" = false ]; then
    log ERROR "Sprint $sprint failed after $MAX_RETRIES attempts. Stopping."
    log ERROR "Check ${HARNESS_DIR}/evaluation-report.md for details."

    # Write failure summary
    cat > "${HARNESS_DIR}/failure-summary.md" << EOF
# Harness Failure Summary

## Stopped at Sprint $sprint after $MAX_RETRIES failed attempts

## Last Evaluation Report
$(cat "${HARNESS_DIR}/evaluation-report.md" 2>/dev/null || echo "No report available")

## Recommendation
Review the evaluation feedback and either:
1. Fix issues manually, then run: ./harness.sh --skip-plan
2. Adjust the spec and re-run from scratch
EOF

    exit 1
  fi
done

# ── Phase 3: Final Report ─────────────────────────────────────────────────

log PHASE "PHASE 3: FINAL REPORT"

TOTAL_END=$(date +%s)
TOTAL_DURATION=$(( TOTAL_END - TOTAL_START ))
TOTAL_MINUTES=$(( TOTAL_DURATION / 60 ))

FINAL_PROMPT="You are writing the final project report.

1. Read .harness/spec.md for original requirements
2. Read all sprint reviews in .harness/sprints/*/review.md
3. Run the full test suite one final time
4. Write a final report to .harness/final-report.md including:
   - Summary of all implemented features
   - Final test results
   - Total sprints completed: $TOTAL_SPRINTS
   - Total wall time: ${TOTAL_MINUTES} minutes
   - Known limitations
   - Suggestions for future improvements"

run_agent "$FINAL_PROMPT" "final-report"

log PHASE "HARNESS COMPLETE"
log OK "All $TOTAL_SPRINTS sprints completed in ${TOTAL_MINUTES} minutes"
log OK "Final report: ${HARNESS_DIR}/final-report.md"
log OK "Logs: ${LOG_DIR}/"
