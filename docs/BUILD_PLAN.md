# SRM Core ??? Build Plan

> **Single source of truth** for implementation scope, packet order, and acceptance criteria.
> Implementation agents must follow this document and implement only the active packet.

## 1. Product Overview

**App:** `srm_core` (SRM Intelligence Platform)  
**Publisher:** Chibase Consulting  
**Platform:** Frappe / ERPNext v15  
**Primary workspace:** Stakeholder Relations Hub

SRM Core is a Frappe app that centralises stakeholder relationship management (SRM) for infrastructure and mining projects operating under Social Licence to Build (SL2B) frameworks. It supports geographic stakeholder mapping, engagement logging, issue and commitment tracking, compliance reporting, and political intelligence capture.

### Current repository state (baseline)

| Item | Status |
|------|--------|
| Frappe app scaffold | Done |
| Module `Srm Core` | Done |
| Workspace `Stakeholder Relations Hub` | Done (empty shell) |
| Custom DocTypes | Not started |
| API / server scripts | Not started |
| Reports / dashboards | Not started |

## 2. Architecture Principles

1. **Frappe-native first** ??? DocTypes, permissions, workspaces, reports, and patches; avoid custom frameworks where Frappe provides equivalents.
2. **Packet-driven delivery** ??? One packet = one focused commit on `develop`.
3. **Minimal scope** ??? Implement only what the active packet specifies.
4. **Quality gates** ??? Every packet runs `bench migrate` and `bench --site <SITE> run-tests --app srm_core` before commit.
5. **Documentation** ??? Update `docs/CHANGELOG_INTERNAL.md` per packet; record architectural choices in `docs/DECISIONS.md`.

## 3. Domain Model (planned)

The following entities are planned. DocType names may be refined in later packets; order reflects dependency.

| Phase | Entity | Purpose |
|-------|--------|---------|
| 1 | Geographic Area | Hierarchical geography (country ??? province ??? municipality ??? ward/community) for stakeholder placement |
| 1 | Stakeholder Category | Classification (community, government, NGO, traditional authority, media, etc.) |
| 2 | Stakeholder | Core contact/organisation record with geographic and category links |
| 2 | Stakeholder Group | Named collections of stakeholders for engagement campaigns |
| 3 | Engagement | Logged interactions (meetings, calls, site visits) with participants and outcomes |
| 3 | Issue / Grievance | Tracked concerns raised by stakeholders with status workflow |
| 4 | Commitment | Promises made to stakeholders with due dates and fulfilment tracking |
| 4 | Project Site | Project or operation site linking geographic scope to SRM activity |
| 5 | Intelligence Note | Political / contextual intelligence records with source and confidence |
| 5 | SLP Indicator | Social Labour Plan compliance indicators and progress snapshots |

## 4. Packet Roadmap

| Packet | Name | Scope summary | Status |
|--------|------|---------------|--------|
| 00 | Structure baseline | Docs, `.gitignore`, repo hygiene | **Active** |
| 01 | Geographic Area | DocType, tree view, permissions, workspace link | Planned |
| 02 | Stakeholder foundation | Stakeholder Category + Stakeholder DocTypes | Planned |
| 03 | Engagement logging | Engagement DocType + list/form UX | Planned |
| 04 | Issues & commitments | Issue/Grievance + Commitment DocTypes | Planned |
| 05 | Project Site & workspace | Project Site DocType; populate Stakeholder Relations Hub | Planned |
| 06 | Intelligence & SLP | Intelligence Note + SLP Indicator DocTypes | Planned |
| 07 | Reports & dashboards | Standard reports, number cards, charts | Planned |
| 08 | API & integrations | Whitelisted methods, optional sl2b_app hooks | Planned |

## 5. Active Packet Template

When a packet is activated, the implementation agent receives:

```
Active packet: Packet NN - <Name>

Goals:
- ...

Acceptance criteria:
- ...
```

The agent must not implement scope from other packets unless explicitly directed.

## 6. Quality Gates (every packet)

```bash
cd /home/frappe/frappe-bench
bench --site <SITE_NAME> migrate
bench --site <SITE_NAME> run-tests --app srm_core
```

## 7. Repository Layout

```
srm_core/
????????? docs/
???   ????????? BUILD_PLAN.md          # This file
???   ????????? DECISIONS.md           # Architecture decision log
???   ????????? CHANGELOG_INTERNAL.md  # Per-packet change log
????????? srm_core/
???   ????????? hooks.py
???   ????????? modules.txt
???   ????????? patches.txt
???   ????????? srm_core/
???       ????????? doctype/           # Created per packet
???       ????????? workspace/
???           ????????? stakeholder_relations_hub/
????????? pyproject.toml
```

## 8. Dependencies

| App | Relationship |
|-----|--------------|
| `frappe` | Required platform |
| `erpnext` | Installed on target bench; optional integration points TBD |
| `sl2b_app` | Sister app on bench; cross-app hooks deferred to Packet 08 |

## 9. Out of Scope (unless a future packet says otherwise)

- Custom front-end SPA outside Frappe desk
- Third-party CRM sync
- Mobile-native apps
- AI / sentiment analysis (future phase)

## 10. Revision History

| Date | Change |
|------|--------|
| 2026-07-02 | Initial BUILD_PLAN created (Packet 00) |

