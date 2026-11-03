# Session handoff

This note gives the next contributor enough context to continue the project from a fresh clone. The authoritative requirements are in [`../AGENT_BRIEF.md`](../AGENT_BRIEF.md); read it in full, especially section **1 bis**, which takes priority in case of conflict.

## Start here

1. Check out and update `develop`; at the time this note was written, the latest README update is commit `0c71a9b`.
2. Read `AGENT_BRIEF.md`, [`PROGRESS.md`](PROGRESS.md), [`DATA_SOURCES.md`](DATA_SOURCES.md), and [`METHODS.md`](METHODS.md).
3. Check `data/catalog.yaml` and the actual processed files before claiming any variable is available. The catalogue and progress log have had periods of asynchronous updates and can disagree; verify the live API and on-disk outputs before changing public availability claims.
4. Run the API and web app using the instructions in the root [`README.md`](../README.md).

Do not copy credentials from chat or ask the previous contributor for secrets already present in local credential stores. Never commit Earthdata credentials, `.env`, raw downloads, or generated data that the repository excludes.

## Project context

Earth Trends Detective is a bilingual Vue/TypeScript and FastAPI application for selecting NASA Earth science variables, analyzing a chosen region and time period, viewing trend maps and time series, comparing regions, and explaining statistical results. The current map uses NASA GIBS Blue Marble as geographic context and science-derived slope/significance overlays. It has user controls for overlay visibility and slope opacity.

The main analysis includes seasonal adjustment, linear slope and 95% confidence interval, a t-test, Sen slope, Mann–Kendall, and autocorrelation/FDR methods where the relevant outputs are available. It describes statistical change; it does not establish causation.

The README and repository are on `develop`. The worktree was clean when this handoff was prepared. Recent commits include the map layer controls and `0c71a9b` (professional README and repository architecture). Historical milestone branches are present remotely. Do not assume every milestone is accepted: consult the unchecked acceptance items and outstanding access requirements in `docs/PROGRESS.md`.

## Work requested for a separate feature branch: AI and hydrology / CUAHSI

The project owner specifically wants the next contributor to investigate and implement these as **separate-branch work**, not silently fold them into the current `develop` baseline. Start a feature branch from the latest `develop` (for example `feature/ai-cuahsi-investigation`) and open a reviewable pull request when ready. Follow the milestone ordering and acceptance rules in `AGENT_BRIEF.md`; advanced work must not displace incomplete core requirements or deployment work.

### AI-assisted discovery

- First propose a small, useful AI feature that helps users discover variables or regions, or understand the analysis workflow. The official challenge presents AI as optional.
- Keep suggestions grounded in the live, verified product catalogue and actual analysis-ready data. Do not invent datasets, trends, references, explanations of causes, or results.
- Clearly distinguish a data-backed result from a suggestion. Any scientific context from papers or news must have verified citations; do not imply the model discovered causation.
- Prefer a deterministic, testable design and document model/service requirements, privacy implications, failure behavior, and cost before adding an external inference dependency.
- If there is no reliable, affordable implementation using available resources, document the research and leave the feature explicitly unimplemented rather than adding a mock AI response.

### Hydrology and CUAHSI

- Research what CUAHSI currently provides that is relevant to hydrological time-series discovery, access, and plotting. Verify official documentation and service/API availability before choosing an integration.
- Determine whether the CUAHSI resource can complement the current NASA dataset pipeline or provide a real hydrological variable/region workflow. Do not describe CUAHSI as a NASA data source, and do not add fabricated or synthetic observations to the production catalogue.
- If integrating it, document provenance, licensing/terms, units, temporal resolution, spatial coverage, missing-data handling, and how regional trend statistics remain comparable and scientifically appropriate.
- Build a small end-to-end vertical slice with real accessible data, tests, source attribution, and explicit unavailable/error states. Keep it isolated on the feature branch until reviewed.

## Immediate engineering priorities

1. Reconcile `docs/PROGRESS.md`, the live `/api/catalog` and `/api/variables` responses, `data/catalog.yaml`, and generated outputs so that product readiness is stated consistently.
2. Complete the outstanding M6 guided-flow/demo and browser/mobile acceptance checks recorded in the progress log.
3. M8 deployment is still dependent on actual server access, SSH user/key, public DNS, and open ports 80/443; do not claim a public deployment until the HTTPS walkthrough succeeds.
4. Keep tests and source documentation current. Use small commits and update `docs/PROGRESS.md` as work proceeds.

## Local start commands

From the repository root, run the API in one terminal:

```sh
make dev
```

In a second terminal:

```sh
cd web
npm ci       # first run only
npm run dev
```

Open the Vite URL, normally `http://localhost:5173`. The API and interactive docs are at `http://localhost:8000` and `http://localhost:8000/docs`.
