# Security Policy

## Supported Versions

| Version | Supported |
| --- | --- |
| 0.1.x | Yes |

## Reporting a Vulnerability

Report security issues privately through GitHub Security Advisories:

https://github.com/realisticsimcockpit/cockpit-guardian/security/advisories/new

If GitHub Security Advisories are not available, open a GitHub issue with a
minimal description and avoid posting exploit details publicly.

## Security Expectations

- Restore actions must create backups before modifying Windows state.
- Actions requiring administrator rights should explain why elevation is needed.
- Logs should avoid storing secrets, tokens, or credentials.
- Device identifiers may include serial numbers and should be treated as local
  diagnostic data.
