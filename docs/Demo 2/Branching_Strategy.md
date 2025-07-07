# SAMFMS Git Flow Branching Strategy
**Version:** 2.1  
**Effective:** March 2025  
**Owner:** DevOps Team @ Tyto Insights

## 1. Overview
```mermaid
graph TD
    A[main] -->|Release| B[develop]
    B -->|Feature| C[feature/sblock-*]
    B -->|Release| D[release/v*]
    A -->|Hotfix| E[hotfix/*]
    D --> A
    E --> A
    E --> B
    
2. Branch Specifications
2.1 Protected Branches
Branch	Environment	Retention	Required Checks
main	Production	Forever	- 2 Approvals
- SAST Scan
- E2E Tests
develop	Staging	30 days	- 1 Approval
- Unit Tests
2.2 Branch Naming Conventions
Type	Pattern	Examples
Feature	feature/[sblock]-[jira]	feature/gps-fms451
Release	release/v[major].[minor]	release/v1.4
Hotfix	hotfix/[system]-[jira]	hotfix/auth-fms789
3. Core Workflows
3.1 New Feature Development
bash
# Create from develop
git checkout -b feature/gps-fms451 develop

# Commit changes
git commit -m "feat(gps): #FMS-451 Add speed limit alerts"

# Push and create MR
git push -u origin feature/gps-fms451
3.2 Release Process
bash
# Create release branch
git checkout -b release/v1.4 develop

# Final verification
./run_integration_tests.sh

# Merge to main
git checkout main
git merge --no-ff release/v1.4
git tag -a v1.4.0 -m "Production Release"
4. Quality Controls
4.1 Automated Checks
Stage	Tools	Threshold
Pre-commit	ESLint, Black	0 Warnings
PR Gate	SonarQube	A Rating
Deployment	OWASP ZAP	0 Critical
4.2 Manual Checks
Architecture Review

UX Approval

Legal Compliance (GDPR)

5. SBlock Version Matrix
Module	Version	Owner
MCORE	2.2.0	Platform Team
GPS Tracking	1.1.3	Telemetry Team
Driver Analytics	0.5.0	AI Team
6. CI/CD Pipeline
Diagram
Code








7. Compliance Requirements
Security:

All merges to main require:

SBOM Generation

Secret Scanning

Legal:

Data residency validation

Right-to-be-forgotten workflow

8. Emergency Procedures
Severity 1 Incident:

Create hotfix branch

bash
git checkout -b hotfix/auth-fms789 main
Bypass reviews with:

git
git commit -m "[EMERGENCY] fix(auth): #FMS-789 Patch zero-day"
Post-mortem within 24 hours

Approvals

Role	Name	Signature	Date
CTO	Mark Botros	[Digital]	2025-03-20
Security Lead	Adir Miller	[Digital]	2025-03-20

### Key Features:
1. **Mermaid.js Diagrams** for visual workflows
2. **Ready-to-Use** Git commands
3. **Compliance-Focused** checks
4. **Modular Versioning** table
5. **Emergency Protocols** with CLI examples

