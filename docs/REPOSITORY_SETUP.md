# Repository Setup

The repository is configured through files wherever GitHub supports it:

- CI: `.github/workflows/ci.yml`
- Release build: `.github/workflows/release.yml`
- Dependency updates: `.github/dependabot.yml`
- Issue templates: `.github/ISSUE_TEMPLATE/`
- Pull request template: `.github/pull_request_template.md`
- Optional GitHub Settings app config: `.github/repository.yml`

Suggested GitHub repository settings are already written in `.github/repository.yml`:

- Description: `Windows cockpit readiness guardian for simracing rigs.`
- Topics: `simracing`, `cockpit`, `windows`, `usb`, `directinput`, `serial`,
  `simhub`, `pyside6`
- Default branch: `main`
- Wiki disabled.
- Issues enabled.
- Downloads enabled.
- Delete branch on merge enabled.

The `.github/repository.yml` file is applied automatically only if the GitHub
Settings app is installed for the repository. Without that app, the file still
documents the intended settings and keeps the project decisions versioned.
