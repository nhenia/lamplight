# Happy hour data pipeline

## Authoritative data

- Editable CSV: `shared/src/commonMain/composeResources/files/happy_hours_tinyfish_2026_10_22.csv`
- GitHub raw read URL: `https://raw.githubusercontent.com/nhenia/lamplight/main/shared/src/commonMain/composeResources/files/happy_hours_tinyfish_2026_10_22.csv`
- Research baseline: TinyFish report of 2026-10-22 (not a continuously updated source).

## Runtime

The Android app loads bundled CSV on first install, saves a valid fetched CSV to `SettingsStore`, and attempts a fresh GitHub raw fetch on each ViewModel startup. A failed fetch preserves cached or bundled data. Happy Hour under Discover displays every row, even when its venue is not in the existing 419-place catalog. Times are displayed as source strings, not parsed into 'open now' claims. No backend account or API key is needed.

The web target currently uses bundled/cached data and does not yet perform a live request. Deploy/reinstall a build containing the new code once; later CSV edits become visible on the next Android app launch.

## Scheduled source monitor

`.github/workflows/happy-hours.yml` runs each day at 13:00 UTC (Central time varies seasonally). It calls `scripts/update_happy_hours.py`, fetching currently recorded source URLs and saving source fingerprints and a review report in `data/happy-hours/`. It does not use TinyFish, nor does it update prices or add venues automatically. GitHub Actions can miss or delay scheduled runs, and pages requiring JavaScript/PDF/social login are not supported by the source scanner.

**Important: a source changing is NOT verification that a particular deal changed.** Do not rewrite the canonical CSV based only on webpage fingerprints. The daily scan produces a review queue; an editor must confirm exact new prices/hours from authoritative sources before publishing. To make that step automatic, a separate trustworthy extraction/verification system is required, including a way to discover venues across the metro. No such service or credentials are currently configured.

## Run manually

Open GitHub → Actions → Happy hour source monitor → Run workflow.

## Current data limitations

The initial 54 records contain research and some uncertain/secondary entries. There is no guarantee of metro-wide completeness or daily fresh prices yet. Any source with ambiguous verification remains flagged.
