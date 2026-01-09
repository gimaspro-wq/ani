# Parser / Ingestion / ETL Audit

## 1) Directory map (parser/)
path/  
- responsibility  
- depends_on  
- depended_by  
- problems  

parser/  
- Python service entrypoint, env, packaging, docs, Docker image  
- depends_on: parser/parser package  
- depended_by: deployment (Dockerfile), developers  
- problems: none (docs align with code)  

parser/parser/  
- application/orchestration code for parser runtime  
- depends_on: httpx, tenacity, pydantic-settings, asyncio  
- depended_by: CLI, Docker CMD  
- problems: state last_page stored but never used to resume; single RateLimiter shared across services couples limits; no typed DTOs  

parser/parser/clients/  
- HTTP client base + Kodik, Shikimori, Backend adapters (extract/load)  
- depends_on: parser.config, parser.utils.RateLimiter, httpx, tenacity  
- depended_by: orchestrator  
- problems: backend responses assumed shape, minimal validation; retries only at HTTP layer (not semantic); no per-service rate limits  

parser/parser/utils/  
- shared helpers (IDs, backoff, rate limiter)  
- depends_on: asyncio, random, time  
- depended_by: orchestrator, clients, tests  
- problems: backoff jitter only, no cap on attempts beyond tenacity settings in clients  

parser/parser/tests/  
- unit tests for IDs, rate limiting, backoff, schema mapping  
- depends_on: pytest, respx  
- depended_by: CI/dev  
- problems: no coverage for orchestrator/state, no integration with backend contract  

## 2) File-by-file analysis
File: parser/README.md  
Role: User/developer guide for parser service  
Stage: docs  
Reads: n/a  
Writes: n/a  
Called from: n/a  
Calls: n/a  
Problems: Claims idempotency and state resume but last_page not consumed in code  
Refactor potential: Align docs after state resume fix  

File: parser/pyproject.toml  
Role: pytest config  
Stage: tooling  
Reads/Writes: n/a  
Called from: pytest  
Calls: n/a  
Problems: none  
Refactor potential: set asyncio_default_fixture_loop_scope to avoid warning  

File: parser/requirements*.txt  
Role: dependency pins  
Stage: infra  
Reads/Writes: n/a  
Problems: none noted  
Refactor potential: add typing/formatting tools if needed  

File: parser/.env.example  
Role: sample config  
Stage: orchestration setup  
Reads/Writes: n/a  
Problems: none  
Refactor potential: add per-service rate limits/state version key  

File: parser/Dockerfile  
Role: container build (runs `python -m parser.cli run --mode full`)  
Stage: orchestration/runtime  
Reads: requirements, parser package  
Writes: image, /state dir  
Called from: docker runtime  
Calls: parser.cli main  
Problems: no healthcheck; state persisted only if volume mapped  
Refactor potential: add entrypoint flag for mode/limits  

File: parser/parser/__init__.py  
Role: package init/version  
Stage: orchestration  
Reads/Writes: n/a  
Problems: none  
Refactor potential: expose version const to CLI output  

File: parser/parser/config.py  
Role: env settings (Pydantic)  
Stage: orchestration/config  
Reads: .env envvars  
Writes: settings instance  
Called from: clients, orchestrator, CLI  
Calls: BaseSettings loader  
Problems: defaults use test tokens; no validation of URL/token presence for production; STATE_PATH not normalized  
Refactor potential: add validators, per-client rate config, source version  

File: parser/parser/state.py  
Role: persist incremental state (last_run, last_page, processed_anime)  
Stage: orchestration/state  
Reads: JSON file at STATE_PATH  
Writes: JSON file at STATE_PATH  
Called from: ParserOrchestrator  
Calls: json, datetime  
Problems: last_page saved but never consumed in orchestrator; no state version/checkpoints; errors swallowed (returns default state)  
Refactor potential: add resume-from-page, checkpoint per anime/episode, atomic writes (tmp file + replace)  

File: parser/parser/utils/__init__.py  
Role: helpers (ID generation, backoff, rate limiter)  
Stage: utils  
Reads/Writes: time for rate limiter state  
Called from: orchestrator, clients, tests  
Calls: asyncio.sleep, random  
Problems: RateLimiter shared instance across services forces combined RPS; no burst tokens; backoff jitter lacks floor to avoid zero delays  
Refactor potential: per-service limiters, min jitter floor, token-bucket with capacity  

File: parser/parser/clients/__init__.py (HTTPClient)  
Role: base HTTP client with retries/backoff/rate-limit  
Stage: extract/load transport  
Reads: settings for timeouts/backoff  
Writes: outbound HTTP  
Called from: KodikClient, ShikimoriClient, BackendClient  
Calls: httpx.AsyncClient, tenacity.retry  
Problems: `_should_retry` retries 5xx/429/timeouts only; does not cap total elapsed; no structured errors; rate limiter shared externally; closes only manually  
Refactor potential: add circuit breaker, per-request timeout override, semantic retry for 409/412 if backend idempotency needed  

File: parser/parser/clients/kodik.py  
Role: Kodik extract + episode transform helper  
Stage: Extract + partial Transform (parse_episodes)  
Reads: Kodik API responses  
Writes: structured episode dicts  
Called from: orchestrator  
Calls: HTTPClient.get  
Problems: no caching; parse_episodes assumes seasons dict; no dedup for translations; no rate-limit per Kodik; no tracing of lost fields (quality, voice)  
Refactor potential: keep raw payload for analytics; add translation priority rules; normalize episodes to schema class  

File: parser/parser/clients/shikimori.py  
Role: Shikimori metadata extract + transform  
Stage: Extract + Transform  
Reads: Shikimori API responses  
Writes: dict matching backend anime schema  
Called from: orchestrator  
Calls: HTTPClient.get  
Problems: no language preference config; description not sanitized; ignores scores/episodes/ongoing dates that could fuel watch-history/recs  
Refactor potential: add optional fields (episodes_aired, next_episode_at), handle null statuses, add maturity flag  

File: parser/parser/clients/backend.py  
Role: Load into backend internal API  
Stage: Load  
Reads: import payloads  
Writes: backend HTTP POSTs  
Called from: orchestrator  
Calls: HTTPClient.post  
Problems: assumes backend returns JSON with success; errors swallowed returning False; no idempotent upsert keys passed beyond source_name/ids; no batching control  
Refactor potential: map backend errors, add checksum/version, expose dry-run mode  

File: parser/parser/orchestrator.py  
Role: end-to-end orchestration (extract-transform-load)  
Stage: orchestration  
Reads: Kodik catalog, Shikimori anime, state file  
Writes: backend imports, state file  
Called from: CLI main  
Calls: KodikClient, ShikimoriClient, BackendClient, StateManager, utils  
Problems: last_page not used to resume; state not flushed on per-anime completion (only per-page); failures per anime decrement progress but still mark page; video import errors counted but no retry; episodes skipped if no Kodik data (no partial import of metadata only); no dedup for translations; concurrency semaphore covers entire workflow per anime (good) but shared rate limit couples services; no per-source priority/rules  
Refactor potential: resume from state, per-step retries, separate extract/transform/load layers, record per-anime checkpoints, emit metrics hooks  

File: parser/parser/cli.py  
Role: CLI entrypoint  
Stage: orchestration interface  
Reads: argv, env settings  
Writes: stdout/stderr  
Called from: python -m parser.cli / Docker CMD  
Calls: ParserOrchestrator.run/process_anime  
Problems: lacks `--resume` using state.last_page; no health/diagnostics command; debug flag only adjusts root level; exits 0 even if run had failures (since orchestrator returns none)  
Refactor potential: return exit code based on total_failed, add dry-run  

File: parser/parser/tests/*  
Role: unit tests for utils/clients mapping  
Stage: validation  
Reads: sample fixtures  
Writes: n/a  
Called from: pytest  
Calls: code under test  
Problems: no orchestration/state/backfill coverage; no contract tests with backend schemas; no regression for last_page behavior  
Refactor potential: add tests for resume, per-service rate limit, backend error propagation  

## 3) Reconstructed pipeline (actual code)
Source (Kodik `/list`, `/search`) → HTTPClient (parser/clients/__init__.py HTTPClient._request) → Parsing (parser/clients/kodik.py list_anime, get_anime_episodes, parse_episodes) → Processing/Normalization (parser/clients/shikimori.py parse_anime_data; parser/utils ID helpers) → Backend API (parser/clients/backend.py import_anime/import_episodes/import_video) → State (parser/state.py save_state)  

Data shapes:  
- Kodik list_anime input: query params; output: JSON with `results`, `total` (dict).  
- parse_episodes input: list of Kodik result dicts; output: list of dicts {number:int, title:Optional[str], translations:[{translation_id, translation_title, link}]}. Loss: qualities, voice types, season id, episode timestamps dropped.  
- Shikimori get_anime input: path param id; output: JSON anime; parse_anime_data outputs backend payload fields {source_id, title, alternative_titles?, description?, year?, status?, poster?, genres?}. Loss: episodes_aired, duration, rating, scores, next_episode_at.  
- Backend import_anime/episodes/video payloads follow parser/README schemas.  
- State: JSON {last_run, last_page, processed_anime{source_id:{title, episodes_count, timestamp}}}. last_page not consumed; processed_anime prevents duplicate process_anime in same run and future runs.  

## 4) ETL feature checklist (by code)
- EXTRACT layer: Yes (KodikClient.list_anime/get_anime_episodes, ShikimoriClient.get_anime)  
- TRANSFORM layer: Partial (ShikimoriClient.parse_anime_data, KodikClient.parse_episodes, utils ID generation); no centralized schema classes  
- LOAD layer: Yes (BackendClient import_* methods)  
- Idempotency: Partial. process_anime checks StateManager.is_anime_processed; episode/video imports rely on backend idempotency; state written per page only.  
- State/checkpoints: Yes but minimal; last_page unused; no per-step checkpoints.  
- Retry: Yes at HTTP layer via tenacity in HTTPClient._request.  
- Backoff: Yes exponential with jitter via tenacity wait_exponential + retries.  
- Rate-limit: Yes via RateLimiter but single shared limiter for all services.  
- Versioning: No data versioning or schema version keys.  
- Conflict resolution: No explicit handling; relies on backend behavior.  
- Priority sources: Single source; no multi-source priority logic.  

## 5) Recommended parser restructuring (backward compatible)
Current structure: combined orchestration with embedded transforms in clients; shared rate limiter; state not fully leveraged.  
Target structure (backward compatible payloads):  
- parser/parser/extract/ (kodik.py, shikimori.py with pure extract returning raw typed models)  
- parser/parser/transform/ (normalize_shikimori.py, normalize_kodik.py producing backend DTOs + keeping raw metadata)  
- parser/parser/load/ (backend_client.py with explicit upsert + dry-run)  
- parser/parser/state/ (checkpoint manager with per-page/per-anime markers, atomic writes)  
- parser/parser/orchestrator.py (thin coordinator reading checkpoints, composing extract→transform→load pipelines, metrics hooks)  
- Rate limiting per service (two RateLimiter instances) and optional global limiter  
Migration path:  
1. Introduce typed DTOs and transform module wrapping existing parse_anime_data/parse_episodes without changing outputs.  
2. Add resume-from-state support in orchestrator using last_page before altering flows.  
3. Split shared RateLimiter into per-client instances; keep defaults equal to current RATE_LIMIT_RPS to remain compatible.  
4. Gradually move parsing helpers from clients to transform module; keep backward-compatible shim functions in clients.  
5. Add optional `--resume` and `--dry-run` flags to CLI; default behavior unchanged.  

## 6) Ongoings / episodes as first-class data
- Episode lifecycle currently limited to availability=True and translation links; no handling of next_episode_at, release dates, translation status.  
- Recommend capturing from Kodik: translation.id/title, link, season/episode air info (if available). From Shikimori: episodes, episodes_aired, next_episode_at, status.  
- Persist in state/checkpoints to allow refresh of ongoings; retry missing episodes without reimporting anime when metadata unchanged.  

## 7) Platform readiness (watch-history, recs, personalization, analytics)
- Current payloads sufficient for IDs/titles but missing signals: duration, episode air dates, genres confidence, ratings.  
- Add optional fields to backend payloads (if backend accepts): episode availability windows, translation/source priority, content rating.  
- Keep backward compatibility by gating new fields behind presence checks and keeping schemas unchanged when absent.  

## 8) Copilot-friendly atomic tasks
Task: Enable resume-from-state for pages  
Context: last_page stored but unused in orchestrator.run  
Files to change: parser/parser/orchestrator.py, parser/parser/state.py tests  
Backward compatibility: defaults to start at page 1 when state missing  
Expected result: run resumes from last_page+1 when state exists and --resume flag set (or default)  
Validation: pytest covering resume logic + manual run with mock state  

Task: Per-service rate limiting  
Context: single RateLimiter couples Kodik/Shikimori/Backend throughput  
Files to change: parser/parser/orchestrator.py, parser/parser/clients/*.py, config.py  
Backward compatibility: default limits same as current RATE_LIMIT_RPS  
Expected result: distinct limiters allow tuning per API without affecting others  
Validation: unit test for limiter usage; smoke test hitting mocked endpoints  

Task: Transform module + typed DTOs  
Context: transforms live inside clients; harder to reuse/extend  
Files to change: parser/parser/transform/*.py (new), clients/kodik.py, clients/shikimori.py, orchestrator.py  
Backward compatibility: DTOs serialize to same dict schema  
Expected result: clearer Extract vs Transform boundary; reusable normalization  
Validation: extend existing schema mapping tests against DTOs  

Task: Partial failures + retries for video import  
Context: video import errors counted but not retried  
Files to change: parser/parser/orchestrator.py, clients/backend.py  
Backward compatibility: same payloads; adds retry/backoff per video  
Expected result: transient video import errors retried; failures reported per episode  
Validation: unit test using respx to simulate failures  

Task: State versioning & atomic write  
Context: state JSON overwrite without version/checkpoint  
Files to change: parser/parser/state.py, orchestrator.py  
Backward compatibility: version defaults to 1 when absent  
Expected result: safer writes (temp + replace), version field present  
Validation: unit test for save/load with version and crash recovery  

Task: CLI exit codes & diagnostics  
Context: CLI exits 0 even if page failures  
Files to change: parser/parser/cli.py, orchestrator.py  
Backward compatibility: success path unchanged; failures now return non-zero  
Expected result: non-zero exit on any failed anime; `diagnose` command prints config/state summary  
Validation: CLI unit test with mock orchestrator results  

## 9) Final report
1. Current level: Parser is an ingestion service with extract/transform/load pieces but lacks full ETL robustness (resume, versioning, conflict resolution). Idempotency partial via processed_anime state; per-page resume missing.  
2. ETL status: Extract and Load implemented; Transform partial; idempotent/load versioning missing → not full ETL.  
3. Critical improvements: resume from state; per-service rate limits; typed transforms; video import retries; state durability/versioning; exit-code correctness.  
4. Scalable without changes: ID generation, basic backoff/retry, concurrency semaphore, backend contract adherence.  
5. Growth risks: losing last_page progress on interruptions; coupled rate limiter causing upstream throttle; silent backend errors; dropped metadata limiting ongoings/recommendations; no conflict/version control for updates.  
