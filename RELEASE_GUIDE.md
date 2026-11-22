# FocusBoard Release Management & Versioning Guide

## 1. Versioning Standard
FocusBoard adheres to **Semantic Versioning (SemVer 2.0.0)**:
`MAJOR.MINOR.PATCH`

- **MAJOR**: Incompatible API changes, breaking database migrations, or major architectural shifts.
- **MINOR**: Backward-compatible new features (e.g. adding new integrations, enterprise RBAC capabilities, or AI planner improvements).
- **PATCH**: Backward-compatible bug fixes, security patches, or performance optimizations.

---

## 2. Release Lifecycle

```
[Feature Branch] ──► [Pull Request] ──► [CI Quality Gates] ──► [Merge to master]
                                                                      │
[GitHub Release] ◄── [Tagged v*.*.*] ◄── [Staging Verification] ◄────┘
```

### Step 1: Pre-Release Validation
Before cutting a release, verify locally:
```powershell
npm test
npm run build
$env:PYTHONPATH="backend"; .\backend\venv\Scripts\pytest backend\tests -v
```

### Step 2: Create a Release Tag
```bash
git checkout master
git pull origin master
git tag -a v1.0.0 -m "Release v1.0.0: Enterprise Task Management Platform"
git push origin v1.0.0
```

### Step 3: Automated Release Pipeline
Pushing a `v*.*.*` tag automatically activates `.github/workflows/release.yml`, which:
1. Compiles production assets in a clean container.
2. Packages `dist/` into `focusboard-frontend-v1.0.0.tar.gz`.
3. Creates a tagged GitHub Release with automated release notes and downloadable assets.

---

## 3. Rollback Strategy
If an issue is detected post-deployment:
1. **Frontend Rollback**: Instant rollback to previous static bundle via hosting provider (e.g. Vercel instant deployment rollback or Nginx container tag swap).
2. **Backend Rollback**: Re-deploy previous Docker image tag (e.g., `focusboard-backend:v0.9.9`).
3. **Database Considerations**: Avoid destructive downgrades in production. Always favor forward-fix migrations to preserve user data integrity.
