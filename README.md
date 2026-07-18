# SRM Core

Core platform repository for SRM services and shared modules.

## Goals
- Keep core platform logic in one maintainable monorepo.
- Enable fast local development and safe CI/CD.
- Support AI-assisted development workflows (Cursor + GitHub Copilot) with clear guardrails.

## Repository Structure

```text
srm-core/
├─ apps/
│  ├─ api/                  # Backend API service
│  ├─ web/                  # Frontend app (admin/user portal)
│  └─ worker/               # Background jobs / queues / schedulers
├─ packages/
│  ├─ config/               # Shared lint/tsconfig/build presets
│  ├─ types/                # Shared TypeScript/domain types
│  └─ utils/                # Shared utilities
├─ docs/
│  ├─ architecture/         # System diagrams and architecture docs
│  ├─ api/                  # API specs and endpoint docs
│  ├─ decisions/            # ADRs (Architecture Decision Records)
│  └─ runbooks/             # Operational guides
├─ infra/
│  ├─ docker/               # Dockerfiles / compose snippets
│  ├─ terraform/            # IaC (or pulumi)
│  └─ github/               # CI/CD helper scripts/templates
├─ scripts/                 # Dev and CI helper scripts
├─ tests/
│  ├─ e2e/
│  ├─ integration/
│  └─ performance/
└─ .github/
   ├─ workflows/
   ├─ ISSUE_TEMPLATE/
   └─ pull_request_template.md
```

## AI-Assisted Delivery Workflow

This repository uses a structured AI workflow:

1. **Spec (Gemini)**  
   Use: `scripts/ai/gemini-spec-prompt.md`

2. **Build (Cursor)**  
   Use: `scripts/ai/cursor-implementation-prompt.md`

3. **Verify (GitHub Copilot)**  
   Use: `scripts/ai/copilot-verify-prompt.md`

4. **Merge (Human Gate)**  
   CI green, acceptance criteria met, reviewer approved, docs updated when needed.

### Required References
- Orchestration playbook: `docs/automation/ai-orchestration.md`
- Task lifecycle runbook: `docs/automation/ai-task-lifecycle.md`
- PR disclosure snippet: `docs/automation/pr-ai-disclosure-snippet.md`
- AI task issue template: `.github/ISSUE_TEMPLATE/ai-task.yml`
