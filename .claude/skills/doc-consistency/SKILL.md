---
name: doc-consistency
description: Scan the five TOGAF design documents for cross-document consistency — orphaned IDs, broken references, terminology drift.
allowed-tools: Read, Glob, Grep
---

# Doc Consistency

Scan the five design documents in `docs/markdown/` for cross-document consistency issues.

## Documents

1. `conceptual-design.md` — Requirements, constraints, traceability matrix
2. `logical-design.md` — Design decisions with rationale
3. `physical-design.md` — IP addressing, specs, technology selections
4. `deliver.md` — Deployment procedures, verification steps
5. `operate.md` — SOPs, lifecycle management, health checks

## Checks

### 1. Requirements Traceability

- Read the Requirements Traceability Matrix in `conceptual-design.md` Section 12
- For each requirement ID (R-xxx, C-xxx): verify it is referenced in at least one design decision in `logical-design.md`
- For each design decision ID (XXX-NN) in `logical-design.md`: verify the referenced requirement exists in `conceptual-design.md`
- Flag orphaned requirement IDs (defined but never referenced) and orphaned decision IDs (referenced but never defined)

### 2. Decision ID Completeness

- Every design decision table in `logical-design.md` must have all five columns: Req., Decision ID, Design Decision, Design Justification, Risk / Mitigation
- Flag any table with missing columns or empty cells in the Justification or Risk columns

### 3. Cross-Document References

- Find all markdown links between the five documents (e.g., `[text](logical-design.md#section)`)
- Verify each link target exists — check that the referenced file and section heading are real
- Flag broken links

### 4. Terminology Consistency

Check these terms are used consistently across all five documents:

- Product names: "VCF Installer" not "Cloud Builder", "VCF Operations" not "VCF Ops", "VCF Automation" not "VCF Auto", "VMware Kubernetes Runtime (VKr)" not "VMware Kubernetes releases"
- Acronyms: expanded on first use per document, then short form thereafter
- Qualified names on first use: "vSphere Supervisor" not bare "Supervisor", "NSX Tier-0 Gateway" not bare "Tier-0" (first use only)

### 5. Implementation Coverage

- For each design decision in `logical-design.md`, check if `deliver.md` contains a corresponding implementation or deployment step
- Flag decisions with no implementation reference

## Report Format

```
## Doc Consistency Report

### Traceability
- [x] All requirement IDs referenced in design decisions
- [ ] **R-007** defined in conceptual-design.md but not referenced in any design decision

### Decision Completeness
- [x] All decision tables have complete columns

### Cross-References
- [ ] Broken link in deliver.md: `[Logical Design](logical-design.md#network-design)` — section heading is actually `## Network Design Decisions`

### Terminology
- [ ] physical-design.md line 142: "Cloud Builder" should be "VCF Installer"
- [ ] operate.md: "Supervisor" used without "vSphere" qualification on first use (line 38)

### Implementation Coverage
- [ ] **NET-06** has no corresponding deployment step in deliver.md

**Summary:** 4 issues found across 3 documents.
```
