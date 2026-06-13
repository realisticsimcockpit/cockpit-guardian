## Summary

- Describe the change and why it is needed.

## Verification

- [ ] `python -m compileall -q src tests`
- [ ] `python -m pytest -q`
- [ ] UI smoke test when the change affects PySide6 screens
- [ ] Windows hardware validation when the change affects COM, USB, joystick order, or restore behavior

## Risk

- Note any device, Windows, SimHub, Arduino, or ESP behavior that needs real hardware validation.
