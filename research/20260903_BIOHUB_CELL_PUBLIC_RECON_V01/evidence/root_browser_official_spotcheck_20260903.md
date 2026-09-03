# Root browser official-page spot check

- tool_surface: `browser:control-in-app-browser`
- browser: Codex in-app browser
- access_window_utc: `2026-09-03T07:55:00Z/2026-09-03T08:05:53Z`
- access_window_asia_singapore: `2026-09-03T15:55:00+08:00/2026-09-03T16:05:53+08:00`
- operation_scope: read-only navigation, DOM body text extraction, page expansion and scrolling
- external_writes: `0`
- downloads: `0`

This file is a secondary spot check. Canonical source-manifest rows use the per-source timestamps and evidence created by the dedicated collection pass.

## Overview

- URL: https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/overview
- title: `Biohub - Cell Tracking During Development | Kaggle`
- rendered body characters: `6667`
- rendered body UTF-8 bytes: `6679`
- rendered body SHA-256: `dc9387841b1ac67b21a65ed907aed35ca059a4483d4a0422fe2a346b3d91c9f1`
- observed sections: Overview, Description, Evaluation, Submission File, Timeline, Prizes, Code Requirements, Citation
- verified short facts: 3D+time cell detection/linking/division/lineage task; combined score; 7.0 µm matching threshold; physical voxel scaling; 2026-06-29 start and 2026-09-29 final deadline; 12-hour CPU/GPU limit; internet disabled.

## Data

- URL: https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/data
- title: `Biohub - Cell Tracking During Development | Kaggle`
- rendered body characters: `5169`
- rendered body UTF-8 bytes: `5188`
- rendered body SHA-256: `1a29939ad5ea949eec78bf21cc468f6d6e2f8dd9e3208be5b205f7fb86af3273`
- observed sections: Dataset Description, Data Format, Ground Truth, Embryo Identity, Files, License
- verified short facts: Zarr v3 image arrays and GEFF Zarr v3 graphs; sparse training annotations; train/test embryo-disjoint; page displayed `24,886 files`, `87.61 GB`, and `CC0: Public Domain`.

## Rules

- URL: https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/rules
- title: `Biohub - Cell Tracking During Development | Kaggle`
- rendered body characters: `37391`
- rendered body UTF-8 bytes: `37513`
- rendered body SHA-256: `6ed1ef6fff39ec11fb29249278feea9d5ea36019056544477372a9e0e36d42f9`
- verified short facts: Sponsor Biohub SF; total prizes USD 60,000; winner license MIT; data access/use CC0; maximum team size 5; maximum 5 submissions/day; up to 2 final submissions; external data must satisfy public/equal-access and reasonableness conditions.
- pre-existing state note: the page displayed that the signed-in account had already accepted the rules. No rule acceptance, entry, or account action occurred during this task.

## Leaderboard

- URL: https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/leaderboard
- title: `Biohub - Cell Tracking During Development | Kaggle`
- initial rendered body characters: `3202`
- initial rendered body UTF-8 bytes: `3231`
- initial rendered body SHA-256: `6e6c403c123d05825d63c87ef4082120004488098e9c5bb179d061dbb87b9cd6`
- expansion method: clicked the visible `See 1751 More` control, then scrolled until rank 100 was rendered.
- page statement: Public leaderboard approximately 29% of test data; final results use the other 71%.
- dynamic observed public scores: rank 1 `0.963`; rank 5 `0.955`; rank 10 `0.949`; rank 25 `0.944`; rank 50 `0.940`; rank 100 `0.937`.
- clustering observation: ranks 64 through 94 shown in the expanded view were mostly `0.938`; ranks 1 and 2 both showed `0.963`.
- state warning: these are time-bound page observations and are not bound here to any submission record. The page also showed a pre-existing account/team row and an in-progress scoring indicator; neither was created by this task.
