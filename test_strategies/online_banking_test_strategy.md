# Test Strategy: Online Banking Portal

| Item | Value |
|---|---|
| Document | Test Strategy, Online Banking Portal (product level) |
| Version | 0.1 (Draft for management review) |
| Prepared by | Test Management |
| Date | 2026-11-24 |
| Status | Draft. Pending answers to the open questions below |
| Applies to | All releases and features of the Online Banking Portal. User Login is the first specified feature and is used as the worked example |
| Standards | ISTQB Foundation/Advanced Test Management, ISO/IEC/IEEE 29119-2/-3, OWASP ASVS 4.x and Top 10, WCAG 2.1 AA |
| Related documents | Test Plan: `test_plans/online_banking_login_test_plan.md` (applies this strategy to User Login). Detailed test cases: produced by the `test-cases` agent |

---

## Requirement Register

The requirement IDs below are the same as in the User Login Test Plan and are used throughout this strategy. Future features will extend the register with new IDs (for example FR-09 onwards, NFR-04 onwards) under the same scheme.

| ID | Type | Requirement | Strategy risk class |
|---|---|---|---|
| FR-01 | Functional | Registered users can log in using username and password | Critical (security gateway) |
| FR-02 | Functional | Username must be a valid email address | Medium |
| FR-03 | Functional | Password must contain at least 8 characters, at least 1 uppercase letter and at least 1 number | High |
| FR-04 | Functional | After successful login the user is redirected to the Dashboard and the last login timestamp is updated | Medium |
| FR-05 | Functional | After 5 consecutive failed login attempts the account is locked for 15 minutes | Critical |
| FR-06 | Functional | A "Forgot Password" link is available on the login page | Medium |
| FR-07 | Functional | The user session expires after 15 minutes of inactivity | Critical |
| FR-08 | Functional / Security | Error messages do not reveal whether the username or the password was incorrect | Critical |
| NFR-01 | Performance | Login response time is less than 3 seconds | High |
| NFR-02 | Scalability | The system supports 5,000 concurrent users | High |
| NFR-03 | Compatibility | The login page works on Chrome, Firefox, Edge and Safari | High |

Risk class drives test depth and priority (see Section 10): Critical = P1 tests at every applicable level plus security testing; High = P1/P2 tests at UI and API level; Medium = P2/P3 tests.

## Assumptions and Open Questions

### Assumptions

These are working assumptions made at strategy level. Each must be confirmed or corrected; they are consistent with assumptions A-01 to A-19 in the User Login Test Plan.

| # | Assumption |
|---|---|
| SA-01 | The portal is a customer-facing web application with a browser UI and a REST/JSON backend (authentication, accounts, payments and other services added over time) |
| SA-02 | Delivery is iterative (Agile/Scrum or similar) with a CI/CD pipeline; each feature release gets its own Test Plan that applies this strategy |
| SA-03 | Four environment tiers exist or will exist: CI/ephemeral, QA, Staging/Pre-Prod (production-like) and Production |
| SA-04 | The existing Playwright + pytest Page Object Model framework in this repository is the standard UI and API automation framework for the portal |
| SA-05 | Only synthetic or irreversibly masked data is used outside Production; no real customer data in non-production environments |
| SA-06 | The product-wide performance standard is p95 under 3 seconds for interactive user transactions at the agreed peak load (NFR-01 is the first instance), error rate 1% or less |
| SA-07 | The product-wide compatibility standard is the latest and latest-1 desktop versions of Chrome, Firefox, Edge and Safari (NFR-03); mobile web is out of scope until confirmed |
| SA-08 | Severity is assigned by business/security impact; security findings use CVSS v3.1/v4 scores mapped to the same severity scale |
| SA-09 | The product has no AI/ML or LLM features today |
| SA-10 | A defect tracker (for example Jira) and a test management tool (for example Xray, Zephyr or TestRail) are used for all releases |

### Open questions for the business

| # | Question | Affects |
|---|---|---|
| SQ-01 | Which regulations apply (PCI DSS, local banking regulator, PSD2/strong customer authentication, GDPR, accessibility law)? Is MFA/OTP mandatory for login? | Scope, Security Testing, Exit Criteria |
| SQ-02 | What is the release cadence (for example two-weekly minor, quarterly major) and the change-freeze policy? | Release Strategy |
| SQ-03 | Which environments exist today, who owns them, and is Staging sized like Production? | Environment Strategy, Performance Testing |
| SQ-04 | What is the tech stack (front end, identity provider, session store, database, CDN/WAF, cloud)? | Test Levels, Tools |
| SQ-05 | What is the agreed peak load model (logins per second, salary-day peaks) behind NFR-02, and is NFR-01 measured at p95? | Performance Testing, KPIs |
| SQ-06 | Is mobile web or a native app planned? Which Safari platforms (macOS only, or also iOS/iPadOS)? | Compatibility, Environment Strategy |
| SQ-07 | Is test execution in-house only, or will a partner/vendor provide testing (for example independent penetration testing)? | Resource Strategy |
| SQ-08 | Are any AI features planned (chatbot, fraud detection, risk-based authentication, recommendations)? | Section 5 AI test types; Section 16 |
| SQ-09 | Is there a canary/feature flag capability for production releases, and what are the rollback time objectives? | Release Strategy |
| SQ-10 | Can lockout and session timeouts (FR-05, FR-07) be shortened by configuration in non-production environments? | Automation, Environment Strategy |

---

## 1. Test Strategy Overview

The Online Banking Portal is the customer-facing channel for digital banking. Because it handles authentication, money and personal data, quality failures translate directly into financial loss, regulatory breach and loss of customer trust. This strategy sets the long-term, release-independent testing standards for the portal: the test levels and types, the automation approach and quality gates, environment and data rules, defect and risk management, measurable entry/exit criteria, release rules, metrics and the organisation of testing.

Principles:

1. **Risk-based testing (ISO/IEC/IEEE 29119-2, ISTQB):** test depth follows the risk class of each requirement. Security and money-movement functions get the deepest coverage.
2. **Shift left:** requirements reviewed for testability, unit and API tests written with the code, and security and performance checks run in CI rather than only at the end.
3. **Automation first for regression:** every repeatable P1/P2 check is automated at the lowest practical level (unit, then API, then UI).
4. **Security by default:** every feature is tested against OWASP ASVS controls relevant to it; FR-05, FR-07 and FR-08 are the first examples.
5. **Evidence-based release decisions:** go/no-go is made on the measurable criteria in Sections 11 to 13, not on opinion.
6. **One standard, many plans:** each release Test Plan (the User Login plan being the first) applies these standards and adds dates, effort and feature detail.

## 2. Testing Objectives

| # | Objective | Measure | Example (Login) |
|---|---|---|---|
| OBJ-01 | Verify every requirement is met | 100% of requirements traced to executed, passed tests at release | FR-01 to FR-08, NFR-01 to NFR-03 |
| OBJ-02 | Protect customers and the bank from security failures | 0 open Critical/High security findings at release | Enumeration (FR-08), brute force (FR-05), session expiry (FR-07) |
| OBJ-03 | Meet performance and scalability targets | p95 under 3 s at agreed peak load, error rate 1% or less | NFR-01, NFR-02 |
| OBJ-04 | Ensure consistent behaviour on supported browsers | 100% of P1 tests pass on every supported browser | NFR-03 |
| OBJ-05 | Provide a fast, reliable automated regression safety net | At least 80% of P1/P2 cases automated; merge gate under 15 minutes; flaky rate under 2% | Login UI and API suite |
| OBJ-06 | Detect defects early | At least 85% of defects found before System Test exit (Defect Detection Percentage at least 95% before Production) | Unit and API tests on validation rules (FR-02, FR-03) |
| OBJ-07 | Meet accessibility obligations | 0 open WCAG 2.1 AA Critical/Serious violations on released pages | Login form labels, focus, error announcement |
| OBJ-08 | Give management transparent quality information | KPIs in Section 14 reported at the stated frequency | Release dashboard |

## 3. Scope

### In scope (product level)

- All customer-facing web functions of the Online Banking Portal, starting with User Login (FR-01 to FR-08) and extending to future features (for example account overview, transfers, payments, statements, profile management).
- Backend APIs and integrations behind those functions (identity, session, core banking, notification, audit/SIEM).
- Non-functional quality: security, performance and scalability, compatibility (NFR-03 browser set), accessibility, usability of error messages, resilience and recoverability, logging and audit.
- Test automation framework, CI/CD quality gates, test environments and test data management.
- Production validation (smoke tests, synthetic monitoring) after each deployment.

### Out of scope (today)

| Item | Reason / trigger to bring into scope |
|---|---|
| Native mobile apps and mobile browsers | Not in NFR-03; in scope when SQ-06 confirms |
| AI/ML components | None today (SA-09); in scope when any AI feature is added (Section 5 AI Validation, Prompt and Hallucination Testing, 16) |
| Core banking system internals | Owned by the core platform team; the portal tests the integration contract only |
| Full independent penetration test | Commissioned separately per major release; this strategy defines the in-sprint security testing |
| Production load testing | Performance testing runs in Staging; Production gets synthetic monitoring only |

## 4. Test Levels

Summary:

| Level | Objective | Owner | Primary tools | Entry rule | Exit rule |
|---|---|---|---|---|---|
| Unit | Verify components and business rules in isolation | Development | Language unit framework (for example JUnit/pytest/Jest), coverage tool, SAST | Code compiles; acceptance criteria known | 100% unit tests pass; at least 80% line coverage on changed security-critical modules (for example auth) |
| API | Verify service contracts, rules and security at the API layer | QA (Automation) | Playwright `APIRequestContext` via `api/` clients, pytest, OpenAPI validation | API spec available; build deployed to CI/QA; unit gate passed | 100% P1 API tests pass; 0 open Critical/High API defects |
| System | Verify end-to-end journeys, integration and non-functional requirements in a production-like stack | QA, Performance, Security | Playwright + pytest POM, k6/JMeter/Locust, OWASP ZAP/Burp, axe | Smoke passed; API P1 pass rate at least 95%; environment and data ready | Exit criteria in Section 12 (System) met |
| UAT | Confirm business fitness and acceptance | Product Owner and business users | Test management tool, Staging | System Test exit met or deviations accepted; UAT scripts approved | 100% UAT scenarios executed; 0 open Critical/High; written sign-off |
| Production Validation | Confirm the release works in Production and stays healthy | QA with Operations/SRE | Playwright smoke subset, synthetic monitoring, APM | Deployment completed; go decision recorded | 100% smoke pass within 30 minutes of deploy; no SLO breach in the first 24 hours |

### Unit Testing

- **Objective:** catch logic defects at the cheapest point, especially rule-heavy and security-critical code.
- **Owner:** Development (QA reviews coverage of risk areas).
- **Scope:** validation rules (FR-02 email format, FR-03 password rules), lockout counter and timer logic (FR-05), session timeout calculation (FR-07), timestamp handling (FR-04), error-message mapping (FR-08). Future features: calculations, limits, formatting of amounts and dates.
- **Tools:** the stack's unit framework, mocking library, coverage tool, static analysis (SAST) and dependency scanning in the pipeline.
- **Entry/exit rule:** entry when a story has acceptance criteria; exit when all unit tests pass and coverage on changed code is at least 80% (at least 80% for the auth module, as in the Login Test Plan EN-04).

### API Testing

- **Objective:** verify each service contract, business rule and security control independently of the UI, and provide fast regression.
- **Owner:** QA Automation Engineer, with developers contributing contract tests.
- **Scope:** request/response schemas, validation, status codes, authentication and authorisation, error uniformity (FR-08), lockout (FR-05), session validity (FR-07), idempotency and concurrency for future money-movement APIs.
- **Tools:** Playwright `APIRequestContext` clients following the `api/base_api.py` pattern (endpoints in YAML, payloads in JSON), pytest, OpenAPI schema validation; Pact or similar for consumer-driven contracts where several teams share a service.
- **Entry/exit rule:** entry when the OpenAPI spec is baselined and the build is deployed; exit when 100% of P1 API tests pass and there are 0 open Critical/High API defects.

### System Testing

- **Objective:** verify complete user journeys and non-functional requirements on an integrated, production-like system.
- **Owner:** QA (functional, compatibility, accessibility), Performance Engineer (NFR-01, NFR-02), Security Tester (security controls).
- **Scope:** end-to-end journeys (for example login to Dashboard, FR-04), cross-browser (NFR-03), integration with identity, session, lock store, notification and audit services, security, performance, accessibility, real-value timer checks (FR-05, FR-07 at 15 minutes).
- **Tools:** Playwright + pytest POM (`pages/<area>/` with YAML selectors and JSON data), browser matrix (Chromium, Firefox, WebKit, `chrome` and `msedge` channels, real Safari via grid), k6/JMeter/Locust, OWASP ZAP/Burp, axe-core.
- **Entry/exit rule:** see Sections 11 and 12.

### UAT

- **Objective:** confirm the feature meets business needs, wording and regulatory expectations.
- **Owner:** Product Owner; executed by business users; QA supports and records evidence.
- **Scope:** business scenarios, customer-facing wording (for example the generic FR-08 error message and lock message), usability of key journeys, operational procedures (for example support handling of a locked account).
- **Tools:** test management tool, Staging environment, screen recordings.
- **Entry/exit rule:** entry when System Test exit criteria are met (or deviations accepted); exit with 100% UAT scenarios executed, 0 open Critical/High defects and written sign-off.

### Production Validation

- **Objective:** confirm each deployment is healthy and detect regressions that only appear in Production.
- **Owner:** QA (smoke suite) with Operations/SRE (monitoring).
- **Scope:** read-only or dedicated-account smoke tests (login with the smoke account, Dashboard reached, Forgot Password link present, logout), synthetic login transaction every 5 minutes, APM and error-rate checks against SLOs, security headers check.
- **Tools:** tagged Playwright smoke subset run from the pipeline, synthetic monitoring tool, APM/log platform.
- **Entry/exit rule:** entry after deployment; exit when 100% of smoke tests pass within 30 minutes and no SLO breach (p95 under 3 s, error rate 1% or less) in the first 24 hours. A smoke failure triggers the rollback decision in Section 13.

## 5. Test Types

### Functional Testing

- **What is tested:** each functional requirement and business rule through the UI, including positive, negative and boundary behaviour.
- **Approach and techniques:** requirement-based and risk-based design; equivalence partitioning and boundary value analysis (FR-02, FR-03 7 vs 8 characters, FR-05 4/5/6 attempts, FR-07 14:59 vs 15:00 idle); state transition testing (account: active, failed-n, locked, unlocked; session: active, idle, expired); decision tables (FR-08 error messages); session-based exploratory testing for each new feature.
- **Tools:** Playwright + pytest POM, test management tool.
- **Requirements covered:** FR-01 to FR-08, NFR-03 (functional on each browser); all future FRs.
- **Automated:** yes for P1/P2 regression (target at least 80%); exploratory and first-time usability checks stay manual.

### API Testing

- **What is tested:** service contracts, validation, authentication/authorisation, error handling, lockout and session behaviour at the API.
- **Approach and techniques:** contract (schema) testing against OpenAPI; negative and boundary payloads; parallel request tests for race conditions (FR-05); token replay after logout and expiry (FR-07); response uniformity comparison (FR-08); API used to set up test state for UI tests.
- **Tools:** Playwright `APIRequestContext`, `api/` client pattern, pytest, schema validator.
- **Requirements covered:** FR-01 to FR-05, FR-07, FR-08, NFR-01 (single-user latency baseline).
- **Automated:** yes, fully automated and run on every merge.

### Integration Testing

- **What is tested:** interaction between the portal and its dependencies: identity provider, user store (FR-04 timestamp), lock/counter store (FR-05), session store and gateway (FR-07), Dashboard (FR-04), Forgot Password service (FR-06), audit/SIEM and notification services; for future features, core banking and payment gateways.
- **Approach and techniques:** interface-by-interface verification, contract tests, service virtualisation/stubs for unavailable dependencies in CI, full integration in Staging; failure injection (dependency down or slow) to verify safe error handling.
- **Tools:** pytest + API clients, WireMock or similar for stubs, DB read access, log inspection.
- **Requirements covered:** FR-01, FR-04, FR-05, FR-06, FR-07, FR-08.
- **Automated:** yes for contract and stubbed tests in CI; Staging end-to-end integration partly automated, partly manual.

### Security Testing

- **What is tested:** authentication, session management, input handling, transport security, credential handling, security headers, and (future) authorisation and transaction integrity.
- **Approach and techniques:** OWASP ASVS Level 2 as the baseline (Level 3 for money movement); threat modelling per feature; SAST and dependency scanning on commit; DAST (OWASP ZAP baseline) on merge to main and full scan nightly; manual testing for enumeration (FR-08 text, status, timing), brute force and lockout DoS (FR-05), session fixation and reuse (FR-07), injection and XSS (FR-02, FR-03); independent penetration test per major release.
- **Tools:** SAST tool, SCA/dependency scanner, OWASP ZAP, Burp Suite, secrets scanner.
- **Requirements covered:** FR-01, FR-02, FR-03, FR-05, FR-06, FR-07, FR-08.
- **Automated:** partly. SAST, SCA, secrets scanning and DAST baseline are automated gates; enumeration, logic abuse and penetration testing are manual.

### Performance Testing

- **What is tested:** response time, throughput, scalability, stability and recovery of user transactions.
- **Approach and techniques:** workload model from production analytics or business forecast (SQ-05); baseline, load, stress, spike, soak and endurance tests; tests run in production-like Staging; Playwright browser timing samples for end-user render time. Product standard: p95 under 3 s for interactive transactions at the agreed peak, p99 under 5 s, error rate 1% or less, CPU under 75% (matching the Login Test Plan Section 14).
- **Tools:** k6, JMeter or Locust (one to be chosen, SQ-04), APM and infrastructure monitoring.
- **Requirements covered:** NFR-01, NFR-02; also FR-05 (lockout accuracy under load) and FR-07 (sessions expire during soak).
- **Automated:** yes. A short performance smoke runs nightly; full load, stress and soak run per release candidate.

### Accessibility Testing

- **What is tested:** conformance to WCAG 2.1 AA: labels, keyboard navigation, focus order, contrast, screen reader announcement of errors (FR-08 message, FR-05 lock message), time limits (FR-07 should allow warning/extension under WCAG 2.2.1, see Login Test Plan Q-09).
- **Approach and techniques:** automated rule checks on every page in the UI suite, manual keyboard and screen reader checks (NVDA, VoiceOver) per new or changed page, accessibility acceptance criteria in each story.
- **Tools:** axe-core integrated into Playwright tests, Lighthouse, NVDA/JAWS, VoiceOver.
- **Requirements covered:** FR-01, FR-06, FR-07, FR-08 (UI elements); all future UI features.
- **Automated:** partly. Automated rule checks run on merge; manual assistive-technology testing per release.

### AI Validation Testing

Not applicable today: the Online Banking Portal has no AI/ML features. Comes into scope when any AI or ML capability is introduced, for example an AI chatbot or virtual assistant, a fraud-detection or risk-based authentication model on login, or AI-driven product recommendations (SQ-08).

### Prompt Testing

Not applicable today: there are no LLM prompts in the product. Comes into scope when any LLM-based chat, search, summarisation or assistant feature is added (SQ-08).

### Hallucination Testing

Not applicable today: no generative AI produces content for customers. Comes into scope when any generative AI feature answers customer questions or produces text (for example a support chatbot explaining fees or account activity) (SQ-08).

## 6. Test Automation Strategy

### Test pyramid and target proportions

| Layer | Target share of automated tests | Examples |
|---|---|---|
| Unit | About 60% | FR-02 email validator, FR-03 password rules, FR-05 counter logic, FR-07 timeout calculation |
| API / service / contract | About 30% | Login endpoint contract, lockout via parallel requests, token rejection after expiry, error uniformity |
| UI end-to-end | About 10% | Login to Dashboard journey, Forgot Password link, session expiry redirect, browser matrix |

Manual testing sits beside the pyramid for exploratory, usability, accessibility with assistive technology and penetration testing.

### What to automate

- All P1/P2 regression cases that are stable and repeatable (FR-01 to FR-08).
- Smoke suite for every deployment, including Production.
- API contract, validation, lockout and session tests.
- Cross-browser execution of the P1 UI set (NFR-03).
- Automated accessibility rule checks and security scans (SAST, SCA, DAST baseline).
- Test data setup and reset (for example locking an account via API before a UI test).

### What not to automate

- One-off or rapidly changing UI during early design.
- Exploratory testing, usability judgement and message-wording acceptance (UAT).
- Penetration testing and complex abuse scenarios.
- Full real-time 15 minute waits in every run: they run once per release candidate in Staging; regular runs use shortened, configurable timeouts (SQ-10).
- Visual checks that need human judgement, unless a stable visual baseline tool is adopted.

### Framework and design patterns

The framework in this repository is the standard:

- **Page Object Model:** one page object per area under `pages/<area>/` (for example `pages/login/`), selectors in YAML, test data in JSON, shared behaviour in `pages/base_page.py` and `pages/common/`.
- **API clients:** under `api/`, built on `api/base_api.py` with configuration in `api/api_config.yaml`, one sub-package per service.
- **Orchestration:** pytest fixtures and the journey order in `tests/conftest.py` (login first, logout last); `make test <modules>` in the `Makefile` to run selected modules; tags/markers for smoke, regression, browser and priority.
- **Evidence:** HTML reports in `reports/` and screenshots in `screenshots/`, published as CI artefacts and attached to defects.
- **Patterns:** data-driven tests, fixture-based setup/teardown, API-based state setup, stable test IDs (`data-testid`) agreed with developers, no hard-coded waits (Playwright auto-wait), secrets from CI variables or a vault, parallel execution with isolated account pools.
- **Performance and security** use dedicated tools (k6/JMeter/Locust, ZAP), not Playwright.

### CI/CD quality gates

| Gate | Trigger | Checks | Pass condition | Max duration |
|---|---|---|---|---|
| Commit | Every push / pull request update | Build, unit tests, lint, SAST, secrets scan, dependency (SCA) scan | 100% unit tests pass; coverage on changed code at least 80%; 0 new Critical/High SAST or SCA findings; 0 secrets | 10 min |
| Merge | Pull request to main | Commit gate plus API P1 suite, UI smoke on Chromium, contract tests, axe checks on changed pages, ZAP baseline | 100% P1 API and smoke pass; 0 new Critical/Serious accessibility violations; 0 new High DAST alerts | 15 min |
| Nightly | Scheduled on main | Full UI and API regression on Chrome, Firefox, Edge, WebKit; full DAST; performance smoke (for example 100 users, 10 min) | At least 95% overall pass, 100% P1 pass (failures triaged by 10:00 next working day); performance smoke p95 under 3 s; flaky rate under 2% | 2 h |
| Release | Release candidate in Staging | Full regression incl. real Safari, real 15 min timer checks (FR-05, FR-07), full load/stress/soak (NFR-01, NFR-02), security test report, UAT sign-off | Exit criteria in Section 12 met | Per release plan |

### Target automation coverage

| Measure | Target |
|---|---|
| P1/P2 regression cases automated (UI or API) | At least 80% (matches the Login Test Plan target) |
| P1 regression cases automated | At least 90% within two releases of a feature going live |
| API endpoints with automated contract tests | 100% of public endpoints |
| Requirements with at least one automated test | At least 90% of FRs |
| Unit coverage on security-critical modules | At least 80% line coverage, at least 70% branch coverage |

### Maintenance approach

- Selectors kept only in YAML files, so UI changes need a single edit.
- Flaky test policy: a test failing intermittently is quarantined within 1 working day, fixed or removed within 5 working days; flaky rate tracked as a KPI (under 2%).
- Automation code is reviewed like product code (pull requests, lint, shared conventions).
- Test suite reviewed each release: obsolete tests removed, new requirements added, run time kept within gate limits.
- Framework dependencies (Playwright, browsers, pytest) upgraded at least quarterly in a dedicated branch with a full regression run.

## 7. Environment Strategy

| Environment | Purpose | Data | Characteristics | Owner |
|---|---|---|---|---|
| CI / ephemeral | Commit and merge gates | Seeded synthetic data per run | Containerised, stubs for external services, shortened timeouts | DevOps |
| QA | Functional, API, integration, automation, exploratory | Synthetic, resettable account pools | Latest build, configurable lockout/session timeouts (SQ-10), DB read access and logs for QA | DevOps / QA |
| Staging / Pre-Prod | System test of release candidate, performance, security, UAT, real timer checks | Synthetic at production volume (for example 5,000+ performance users) | Production-like topology: load balancer, multiple app nodes, shared session/lock store, CDN/WAF, real 15 minute timeouts, APM | Environment Owner |
| Production | Post-deployment smoke and synthetic monitoring | Dedicated smoke accounts only | Read-only checks; no load or security scanning | Operations / SRE |

**Browser matrix standard (NFR-03):** Chrome, Firefox, Edge and Safari, latest and latest-1 desktop versions, on Windows 11 and macOS (Safari on macOS). Daily runs use Playwright Chromium, Firefox, WebKit and `chrome`/`msedge` channels; release certification includes real Safari via a cloud grid or macOS runner.

**Rules:**

- Environment availability target: at least 95% during test windows for QA and Staging.
- Staging configuration differences from Production are documented; performance results from an undersized Staging are scaled with an agreed factor and recorded as a residual risk.
- Every deployment is traceable (build ID, configuration, feature flags) and recorded in test reports.
- Environment refresh and data reset are scripted and run before each test cycle.

## 8. Test Data Strategy

- **Synthetic first:** all non-production data is synthetic or irreversibly masked; no real customer PII, account numbers or card data (PCI DSS, GDPR).
- **Data catalogue per feature:** each Test Plan lists its data sets (Login example: active users, lockout pool, near-lock accounts, deactivated users, valid-format non-existent emails, password boundary values, injection payloads, 5,000+ performance users).
- **Isolation:** separate account pools per test type and per parallel worker, so lockout tests (FR-05) never lock shared accounts.
- **Storage:** test inputs in JSON files next to page objects and API clients (repository pattern); credentials and tokens in CI secrets or a vault, never in source control.
- **Provisioning and reset:** data created through APIs or seed scripts and reset before each cycle; API-based setup preferred over UI setup.
- **Boundary and negative libraries:** shared, versioned lists of invalid emails, password boundaries and security payloads reused across features.
- **Volume data:** performance data generated to production scale in Staging.
- **Time-dependent data:** clock or configuration control for timers (FR-05, FR-07) in QA; real values in Staging.
- **Retention:** test data and evidence retained per the bank's records policy; Production smoke accounts reviewed quarterly.

## 9. Defect Management Strategy

**Lifecycle:** New, Triaged, Assigned, In Progress, Fixed, Ready for Retest, Retest Passed / Reopened, Closed (or Deferred / Rejected with justification).

**Severity definitions (product standard, used unchanged in all Test Plans):**

| Severity | Definition | Login example | Fix target |
|---|---|---|---|
| Critical | Security breach, data exposure, financial loss, or a core function unavailable for all users | Login with wrong password succeeds; lockout bypass; session never expires | 24 hours |
| High | Major requirement fails with no workaround, or NFR target missed | Account not unlocked after 15 minutes; error reveals which field is wrong; p95 over 3 s | 2 working days |
| Medium | Requirement partially fails, workaround exists | Timestamp in wrong time zone; layout broken on one browser | 5 working days |
| Low | Cosmetic or minor | Typo, alignment | Next release or backlog |

**Rules:**

- Priority (P1 to P4) is set at triage by the Test Lead, Dev Lead and Product Owner; triage is daily during test cycles.
- Every defect records: requirement ID (FR/NFR), build, environment, browser, steps, expected vs actual, evidence (HTML report from `reports/`, screenshot from `screenshots/`, logs, HAR).
- Security defects are restricted-visibility tickets; CVSS score is mapped to severity (9.0+ Critical, 7.0 to 8.9 High, 4.0 to 6.9 Medium, under 4.0 Low).
- Every fix is retested and the related automated regression set re-run; each escaped Critical/High defect gets an automated regression test and a root cause analysis.
- Deferral of a High defect requires Product Owner and Security/Compliance approval and a fix date.

## 10. Risk Management Strategy

### Quality risk register (product level)

| Risk ID | Risk | Likelihood (H/M/L) | Impact (H/M/L) | Mitigation | Owner |
|---|---|---|---|---|---|
| SR-01 | User enumeration through error text, status code, timing or lock behaviour (FR-08, FR-05, FR-06) | M | H | Decision-table tests on UI and API; timing comparison over 100+ samples; FR-08 checks as P1 regression; pen test focus | Security Tester |
| SR-02 | Brute force or credential stuffing bypasses lockout via race conditions or distributed attempts (FR-05) | H | H | Parallel API tests; boundary tests 4/5/6 attempts; rate limiting/WAF tests; lockout under load in performance runs | QA Automation / Security Tester |
| SR-03 | Lockout abused to deny service to real customers (FR-05) | M | H | Raise policy question (Login Test Plan Q-05, Q-15); test IP/rate controls; residual risk accepted formally | Product Owner / Test Lead |
| SR-04 | Session not invalidated server side, or token reusable after logout/expiry (FR-07) | M | H | API token replay tests after expiry and logout; cookie flag checks; real 15 min check per release | Security Tester |
| SR-05 | Performance targets missed at peak, or results unreliable because Staging is not production-like (NFR-01, NFR-02) | H | H | Confirm Staging sizing (SQ-03); nightly performance smoke; full load per release candidate; APM in Production | Performance Engineer / Environment Owner |
| SR-06 | Ambiguous NFRs (percentile, load profile) lead to disputed results | H | M | Product standard: p95 at agreed peak (SA-06); load model signed off before scripting (SQ-05) | Test Lead |
| SR-07 | Browser-specific defects, especially Safari, missed because only engines are emulated (NFR-03) | M | M | WebKit nightly plus real Safari certification per release; browser KPI | QA Automation |
| SR-08 | Unstated regulatory requirements (MFA/SCA, audit logging, accessibility) discovered late | M | H | SQ-01 answered at strategy review; compliance checklist per feature; Compliance in RACI | Product Owner / Compliance |
| SR-09 | Customer data leaked into logs, URLs, browser storage or non-production environments | L | H | Log and network inspection tests; synthetic data only (SA-05); secrets scanning gate | Security Tester / DevOps |
| SR-10 | Flaky or slow automation erodes trust in quality gates | M | M | Flaky quarantine policy; gate time limits; isolated data pools; stable test IDs | QA Automation |
| SR-11 | Test data contamination (shared accounts locked or changed by parallel runs) | H | M | Per-worker account pools; reset scripts before each cycle | QA Automation |
| SR-12 | Time-based behaviour (15 min lock and idle timeout) slows testing and hides defects (FR-05, FR-07) | H | M | Configurable timeouts in QA (SQ-10); real-value checks once per release candidate in Staging | Dev Lead / QA Automation |
| SR-13 | Integration failures with identity, session or core banking services under failure conditions | M | H | Contract tests; stubs in CI; failure-injection tests in Staging | QA / Dev Lead |
| SR-14 | Late or unstable builds compress test windows | M | H | Entry criteria gate; risk-based prioritisation of P1 cases; shift-left unit and API tests | Test Lead / Dev Lead |
| SR-15 | Future AI features (chatbot, fraud model) introduced without AI-specific testing | L | H | Trigger in Section 5 AI Validation, Prompt and Hallucination Testing and 16; strategy update required before any AI feature enters development | Test Manager |

### Risk review

- Risks are identified at strategy creation, at each Test Plan (feature risks, for example R-01 to R-14 in the Login Test Plan) and at sprint refinement.
- The register is reviewed every sprint by the Test Lead and at each release readiness meeting by the Product Owner, Dev Lead and Security; closed, new and changed risks are reported in the weekly dashboard.
- Risk score = Likelihood x Impact (H=3, M=2, L=1). Score 6 to 9 needs a named mitigation and owner before testing starts; residual risks with score 6 or more at release need written business acceptance.

### How risk drives test priority

| Risk score | Test priority | Coverage expected |
|---|---|---|
| 9 (H/H) | P1 | All applicable levels (unit, API, UI), security and/or performance testing, automated regression, tested first in each cycle |
| 6 (H/M or M/H) | P1/P2 | API and UI, automated regression, negative and boundary cases |
| 3 to 4 | P2/P3 | Main positive and negative paths, automated where stable |
| 1 to 2 | P3/P4 | Sampled or exploratory |

For Login this places FR-05, FR-07, FR-08, NFR-01 and NFR-02 at the top of the order, which is the order used in the Login Test Plan.

## 11. Entry Criteria

### General (every test cycle)

| # | Criterion | Measure |
|---|---|---|
| EN-S01 | Requirements baselined | 100% of in-scope requirements have IDs and acceptance criteria; open questions answered or logged as risks |
| EN-S02 | Test Plan approved | Signed by Test Lead, Product Owner and Dev Lead |
| EN-S03 | Test design ready | 100% of requirements traced to at least one test case; 100% of P1 cases peer reviewed |
| EN-S04 | Environment and data ready | Environment availability at least 95% in the previous 2 working days; 100% of planned data sets provisioned |
| EN-S05 | No blockers | 0 open Blocker defects on the feature under test |

### Per test level

| Level | Entry criteria |
|---|---|
| Unit | Story has acceptance criteria; code builds |
| API | OpenAPI spec baselined; build deployed to CI/QA; commit gate passed (100% unit pass, coverage at least 80% on changed security-critical code) |
| System | Build deployed with release notes; smoke 100% pass; API P1 pass rate at least 95%; for performance: Staging topology confirmed and monitoring in place, functional P1 pass at least 95% in Staging; for security: written approval to scan |
| UAT | System Test exit criteria met (or deviations accepted by Product Owner); UAT scenarios approved; UAT users trained and available |
| Production Validation | Go decision recorded; deployment completed; smoke accounts valid |

These match entry criteria EN-01 to EN-09 in the Login Test Plan.

## 12. Exit Criteria

### General (release candidate)

| # | Criterion | Measure |
|---|---|---|
| EX-S01 | Execution coverage | 100% of P1 and P2 cases executed; at least 95% of P3 executed |
| EX-S02 | Pass rate | At least 98% pass for P1; at least 95% overall |
| EX-S03 | Requirement coverage | 100% of in-scope requirements have at least one executed and passed test |
| EX-S04 | Defects | 0 open Critical/High; 5 or fewer open Medium, each with workaround and fix date; all Low triaged |
| EX-S05 | Security | 0 open Critical/High security findings; 100% of enumeration and session tests passed for authentication features |
| EX-S06 | Performance | p95 under 3 s at agreed peak load; target concurrency (5,000 for login, NFR-02) held 60 minutes with error rate 1% or less; soak p95 degradation under 10% |
| EX-S07 | Compatibility | 100% of P1 cases pass on Chrome, Firefox, Edge and Safari (NFR-03) |
| EX-S08 | Accessibility | 0 open WCAG 2.1 AA Critical/Serious violations on changed pages |
| EX-S09 | Regression | Automated regression 100% pass (or failures analysed and accepted) on the release candidate build |
| EX-S10 | Sign-off | Test Summary Report published; UAT sign-off obtained |

### Per test level

| Level | Exit criteria |
|---|---|
| Unit | 100% unit tests pass; at least 80% line coverage on changed code and security-critical modules; 0 new Critical/High SAST findings |
| API | 100% P1 API tests pass; at least 95% overall; 100% public endpoints contract-tested; 0 open Critical/High API defects |
| System | EX-S01 to EX-S09; real-value timer checks passed at least once (FR-05 15 min unlock, FR-07 15 min idle expiry) |
| UAT | 100% UAT scenarios executed; 0 open Critical/High; written business sign-off |
| Production Validation | 100% smoke pass within 30 minutes of deployment; synthetic login p95 under 3 s and error rate 1% or less for 24 hours |

These match exit criteria EX-01 to EX-10 in the Login Test Plan.

## 13. Release Strategy

### Release types and regression scope

| Release type | Description | Regression scope | Non-functional testing | Approval |
|---|---|---|---|---|
| Major | New features, architecture or platform change (for example a new auth provider or MFA) | Full automated regression on all browsers; full manual P1 set; real-value timer checks; exploratory testing of changed areas | Full load, stress, spike and soak; full DAST and independent penetration test; full accessibility audit | Release readiness board (Product Owner, Engineering Lead, Security/Compliance, Operations) |
| Minor | Enhancements and fixes within existing features | Full automated regression; manual P1 tests for changed features and impacted areas (impact analysis via traceability) | Load test at target peak for changed transactions; DAST; accessibility checks on changed pages | Product Owner, Test Lead, Engineering Lead |
| Hotfix | Urgent fix for Production Critical/High defect | Fix verification; automated smoke plus P1 regression of the affected feature (for login: FR-01, FR-05, FR-07, FR-08); full automated regression within 2 working days after release | Performance smoke if the fix touches a performance-sensitive path; security review of the fix | Emergency change approval (Engineering Lead, Product Owner, Operations) |

### Go/no-go rules

| Decision | Conditions |
|---|---|
| GO | All exit criteria in Section 12 met; 0 open Critical/High functional or security defects; NFR targets met in production-like environment; UAT signed off |
| GO with conditions | All Critical/High closed; up to 5 Medium open with approved workarounds and fix dates; minor NFR deviations (for example p99) accepted in writing by architecture and Product Owner; residual risks formally accepted |
| NO-GO | Any open Critical/High defect; any failure of an authentication security control (for login: FR-05, FR-07, FR-08); p95 at or above 3 s at agreed load or target concurrency not sustained; any supported browser failing P1 cases; P1 pass rate under 98% |

These rules are applied unchanged in each Test Plan (see Login Test Plan Section 25).

### Rollback

- Every release has a tested rollback plan (previous build and database migration reversal or backward-compatible migrations); rollback is rehearsed in Staging for major releases.
- Feature flags or canary deployment are used where available (SQ-09) so a faulty feature can be switched off without redeploying.
- Rollback triggers: any Production smoke failure on a P1 journey, error rate over 1% or p95 at or above 3 s for 15 minutes, or any confirmed security control failure.

### Post-release validation

- Automated Production smoke immediately after deployment (target: complete within 30 minutes).
- Synthetic login transaction every 5 minutes; APM alerts on p95 and error rate.
- 24-hour hypercare: QA and Operations review error logs, lock and session metrics, and customer support tickets.
- Production incidents found within 30 days are counted as escaped defects (KPI) and fed into regression.

## 14. Metrics & Reporting

### KPIs

| KPI | Definition | Formula | Target |
|---|---|---|---|
| Requirement coverage | Share of in-scope requirements with executed, passed tests | Requirements with passed tests / in-scope requirements x 100 | 100% at release |
| Test execution rate | Planned tests executed | Executed / planned x 100 | 100% P1/P2; at least 95% P3 |
| P1 pass rate | P1 tests passing | Passed P1 / executed P1 x 100 | At least 98% |
| Overall pass rate | All tests passing | Passed / executed x 100 | At least 95% |
| Open Critical/High defects | Unresolved severe defects at release | Count | 0 |
| Defect Detection Percentage (DDP) | Defects found before Production | Pre-production defects / (pre-production + Production defects in 30 days) x 100 | At least 95% |
| Defect reopen rate | Fixes that fail retest | Reopened / fixed x 100 | 10% or less |
| Mean time to fix (Critical/High) | Average time from triage to verified fix | Sum of fix times / number of defects | Within severity fix targets (24 h / 2 working days) |
| Automation coverage | P1/P2 regression automated | Automated P1/P2 cases / total P1/P2 cases x 100 | At least 80% |
| Flaky test rate | Tests with inconsistent results on unchanged code | Flaky tests / automated tests x 100 | Under 2% |
| Merge gate duration | Time for merge gate pipeline | Median pipeline time | 15 minutes or less |
| Performance (p95) | 95th percentile response time at agreed load | From load tool / APM | Under 3 s (NFR-01) |
| Load error rate | Failed requests under peak load | Failed / total requests x 100 | 1% or less |
| Browser P1 pass | P1 pass rate per supported browser | Passed P1 / executed P1 per browser x 100 | 100% (NFR-03) |
| Security findings | Open findings by CVSS severity | Count | 0 Critical/High |
| Accessibility violations | WCAG 2.1 AA Critical/Serious violations | Count from axe and manual audit | 0 |
| Escaped defects | Production defects within 30 days of release | Count by severity | 0 Critical; High 1 or fewer per release |

### Reports by audience and frequency

| Report | Audience | Frequency | Content |
|---|---|---|---|
| CI run report | Developers, QA | Every pipeline run | HTML report (`reports/`), screenshots (`screenshots/`), failed tests, gate result |
| Daily status | Delivery team, Test Lead | Daily during test cycles | Execution progress, pass rate, new and open defects, blockers |
| Quality dashboard | Product Owner, Engineering Lead, management | Weekly | KPIs above, risk register changes, trend charts |
| Performance and security reports | Architecture, Security, Compliance | Per release candidate | NFR results, findings by CVSS, residual risks |
| Test Summary Report | Release readiness board | Per release | Exit criteria status, release recommendation (GO / GO with conditions / NO-GO) |
| Quality review | Senior management | Quarterly | DDP, escaped defects, automation trend, process improvements |

## 15. Resource Strategy

### Roles and responsibilities (RACI)

R = Responsible, A = Accountable, C = Consulted, I = Informed.

| Activity | Test Manager | Test Lead | Functional QA | QA Automation Engineer | Performance Engineer | Security Tester | Developers | Product Owner | DevOps / Environment Owner | Compliance / Security Officer |
|---|---|---|---|---|---|---|---|---|---|---|
| Test Strategy | A/R | C | I | C | C | C | I | C | I | C |
| Test Plan per release | A | R | C | C | C | C | C | C | C | I |
| Test case design | I | A | R | C | C | C | C | C | I | I |
| Unit testing | I | I | I | C | I | I | A/R | I | I | I |
| API and UI automation | I | A | C | R | I | I | C | I | C | I |
| Functional and integration execution | I | A | R | R | I | I | C | I | C | I |
| Performance testing | I | A | I | C | R | I | C | I | C | I |
| Security testing | I | A | I | C | I | R | C | I | C | C |
| Accessibility testing | I | A | R | R | I | I | C | I | I | C |
| Environments and CI pipeline | I | C | I | C | C | I | C | I | A/R | I |
| Test data management | I | A | R | R | C | I | C | I | C | C |
| Defect triage | I | R | C | C | C | C | R | A | I | I |
| UAT | I | C | C | I | I | I | I | A/R | I | I |
| Go/no-go recommendation | A | R | C | C | C | C | C | C | C | C |
| Release decision | C | C | I | I | I | I | C | A | C | C |

### Skills needed

- Banking domain knowledge (authentication, payments, regulatory expectations).
- Test design techniques (ISTQB): boundary values, state transitions, decision tables, risk-based testing.
- Automation: Python, pytest, Playwright (UI and `APIRequestContext`), Page Object Model, YAML/JSON data design, Git and CI pipelines.
- API testing: REST, OpenAPI, authentication tokens, contract testing.
- Performance engineering: workload modelling, k6/JMeter/Locust, APM analysis.
- Security testing: OWASP ASVS/Top 10, ZAP/Burp, session and authentication attacks.
- Accessibility: WCAG 2.1 AA, screen readers, axe.
- Future: AI/ML testing skills (model evaluation, prompt testing) when the AI trigger in SQ-08 is met.

### Sourcing approach

| Area | Approach |
|---|---|
| Test management, functional testing, automation framework | In-house (retain domain and framework knowledge) |
| Performance testing | In-house engineer, with tool vendor support as needed |
| Security testing | In-house in-sprint testing plus an independent, accredited external penetration test per major release (regulatory independence) |
| Real-browser and Safari coverage | Cloud device/browser grid service |
| Peak capacity (for example large regression or UAT support) | Outsourced or contract testers working to this strategy and the repository framework (SQ-07) |
| Tools | Open source where mature (Playwright, pytest, k6, ZAP, axe); commercial for test management, defect tracking, APM and grid |

## 16. AI Quality Metrics

Not applicable today: the Online Banking Portal has no AI/ML or LLM features, so no AI quality metrics are tracked. This section comes into scope when any AI capability is added, for example an AI chatbot or virtual assistant, a fraud-detection or risk-based login model, or AI-driven product recommendations (SQ-08). At that point this strategy will be updated before development starts, and this section will define, as a minimum: accuracy/F1 against a labelled baseline, false positive and false negative rates (critical for fraud detection), hallucination rate, groundedness, answer relevance, toxicity and safety violation rate, bias and fairness metrics, prompt-injection resistance, latency, cost per request and drift, each with a measurement method and target.

---

*This strategy is applied per release by the `test-plan` agent (first application: `test_plans/online_banking_login_test_plan.md`). Detailed test cases with traceability to the requirement IDs above are produced by the `test-cases` agent.*
