# Fullstack Web App Development Harness

## Project Overview
This project uses a 3-Agent harness pattern to develop fullstack web applications.
Follow the Planner → Generator → Evaluator workflow.

## Tech Stack (defaults — modify per project)
- **Frontend**: React 18 + Vite + TailwindCSS
- **Backend**: FastAPI (Python 3.11+) or Express.js
- **Database**: SQLite (dev) → PostgreSQL (prod)
- **Testing**: pytest + Playwright (E2E)
- **VCS**: Git (meaningful commits per Sprint)

## Core Rules

### Coding Conventions
- Maximum 300 lines per file. Split if exceeded
- One responsibility per function. Consider splitting if over 20 lines
- Error handling required on all API endpoints
- Environment variables via `.env` only — never hardcode secrets
- When using TypeScript, `any` type is forbidden

### Git Conventions
- Commit messages: `type(scope): description` (conventional commits)
- Tag Sprint boundaries: `sprint-N-start`, `sprint-N-end`
- Feature branches: `feat/feature-name`

### Recommended Directory Structure
```
src/
├── frontend/          # React app
│   ├── components/    # UI components
│   ├── pages/         # Page components
│   ├── hooks/         # Custom hooks
│   ├── services/      # API calls
│   └── styles/        # Global styles
├── backend/           # API server
│   ├── routes/        # Route handlers
│   ├── models/        # DB models
│   ├── services/      # Business logic
│   └── middleware/     # Middleware
├── tests/             # Tests
│   ├── unit/
│   ├── integration/
│   └── e2e/
└── .harness/          # Agent communication files
    ├── spec.md
    ├── contract.md
    └── sprints/
```

## Workflow

### For New Feature Development
1. `/plan <requirements>` — Planner generates spec document
2. Review spec, then `/build` — Generator implements in Sprint units
3. After Sprint completion, `/evaluate` — Evaluator independently verifies
4. On FAIL, incorporate feedback and re-run `/build`

### For Quick Fixes
- Direct fixes without the harness are fine
- But always verify tests pass: `npm test` or `pytest`

## Build & Test Commands
```bash
# Frontend
cd src/frontend && npm install && npm run dev    # Dev server
cd src/frontend && npm run build                 # Production build
cd src/frontend && npm test                      # Frontend tests

# Backend
cd src/backend && pip install -r requirements.txt
cd src/backend && uvicorn main:app --reload      # Dev server
cd src/backend && pytest                         # Backend tests

# E2E
npx playwright test                              # E2E tests
```

## Important Notes
- Files in `.harness/` are for inter-agent communication. Do not modify manually
- See `.claude/skills/` for detailed prompts for each agent
- See `.claude/skills/evaluate/SKILL.md` for evaluation criteria
