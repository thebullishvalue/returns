# Changelog

All notable changes to the Returns Portfolio Tracker will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [v1.3.0] — 2026-04-05

### Added
- External `style.css` design system file (Hemrek Capital dark theme with gold accent)
- `.gitignore` file for Python, IDE, and OS artifacts
- Comprehensive `README.md` with installation, usage, architecture, and design documentation
- `CHANGELOG.md` for release history tracking
- UI primitive helper functions: `_section_header()`, `_section_divider()`, `_metric_card()`
- 4-column top metrics layout (Original Investment, Valuation, P/L, Positions)
- CSV download button with formatted portfolio export
- IST timezone display in footer (UTC+5:30)

### Changed
- **Complete UI/UX overhaul** to match Pragyam 7.0.5 design system
- Sidebar branding with centered gold header and section titles with emoji icons
- Collapsed sidebar by default (was expanded) for cleaner initial view
- Premium header with radial gradient glow effect
- Enhanced tab styling with active state indicators
- Improved section dividers with gradient fade effect
- Consolidated all datetime imports into single top-level import
- Moved `plotly.express` import from deferred inline import to top level
- Updated footer to use consistent Hemrek Capital format with IST timestamp

### Fixed
- Fragmented datetime imports (consolidated `timezone` into main import block)
- Unconventional deferred `plotly.express` import pattern

### Removed
- Dead Python imports: `numpy` and `time` (zero references in codebase)
- Dead dependency: `matplotlib` from `requirements.txt` (plotly handles all visualization)
- Dead CSS classes (~290 lines, ~41% of style.css): regime badges, signal pills, feature cards, topline strips, implication cards (unused in Returns tracker)
- Inline CSS block from `returns.py` (moved to external `style.css`)
- `.qwen/settings.json.orig` backup artifact

### Security
- External CSS loaded with explicit UTF-8 encoding and graceful fallback on missing file

---

## [v1.2.1] — Previous Release

Initial release of the Portfolio Returns Tracker with basic valuation engine.
