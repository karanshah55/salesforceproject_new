# Test Plan: Online Banking Portal, User Login

| Item | Value |
|---|---|
| Document | Test Plan, Online Banking Portal, User Login feature |
| Version | 0.1 (Draft for management review) |
| Prepared by | Test Management |
| Date | 2026-11-24 |
| Status | Draft. Pending answers to the open questions below |
| Detailed test cases | Produced separately by the `test-cases` agent (see Section 24) |

---

## Requirement Register (IDs used throughout this plan)

| ID | Type | Requirement |
|---|---|---|
| FR-01 | Functional | Registered users can log in using username and password |
| FR-02 | Functional | Username must be a valid email address |
| FR-03 | Functional | Password must contain at least 8 characters, at least 1 uppercase letter and at least 1 number |
| FR-04 | Functional | After successful login the user is redirected to the Dashboard and the last login timestamp is updated |
| FR-05 | Functional | After 5 consecutive failed login attempts the account is locked for 15 minutes |
| FR-06 | Functional | A "Forgot Password" link is available on the login page |
| FR-07 | Functional | The user session expires after 15 minutes of inactivity |
| FR-08 | Functional / Security | Error messages do not reveal whether the username or the password was incorrect |
| NFR-01 | Performance | Login response time is less than 3 seconds |
| NFR-02 | Scalability | The system supports 5,000 concurrent users |
| NFR-03 | Compatibility | The login page works on Chrome, Firefox, Edge and Safari |

---

## Assumptions Made and Open Questions for the Business

The requirement did not state team size, dates, environments or technology stack. The following working assumptions were made so the plan and estimate can be produced. Each one must be confirmed or corrected; the effort estimate (Section 23) changes if they change.

### Working assumptions

| # | Assumption |
|---|---|
| A-01 | The Online Banking Portal is a web application with a browser UI and a backend REST/JSON authentication API (for example `POST /auth/login`, `POST /auth/logout`, session/token refresh) |
| A-02 | Test team: 1 Test Lead, 2 Functional QA, 1 Automation Engineer, plus a Performance Engineer (50%) and a Security Tester (50%). See Section 22 |
| A-03 | Test window of about 5 calendar weeks (2 test cycles plus a regression/sign-off cycle), starting when entry criteria (Section 18) are met |
| A-04 | Three environments are available: QA (functional), Staging/Pre-Prod (production-like, used for performance and security) and Production (out of scope for testing apart from smoke checks after deployment) |
| A-05 | "Password rules" (FR-03) are enforced at password creation/reset time; on the login screen the system authenticates against the stored credential and does not reveal rule details on failure (consistent with FR-08) |
| A-06 | "Consecutive failed attempts" (FR-05) are counted per account (not per IP or device), and a successful login resets the counter |
| A-07 | The 15 minute lock (FR-05) unlocks automatically; no admin action is required |
| A-08 | "Inactivity" (FR-07) means no user-initiated request to the server; background polling does not extend the session |
| A-09 | NFR-01 "less than 3 seconds" is measured server-side plus network at the 95th percentile, under the NFR-02 load, from the click on Login to Dashboard rendered |
| A-10 | NFR-02 "5,000 concurrent users" means 5,000 concurrently authenticated, active sessions, with a login arrival rate still to be confirmed (see Q-06) |
| A-11 | NFR-03 covers the current and previous major desktop versions of each browser; mobile browsers are out of scope unless confirmed |
| A-12 | The existing Playwright + pytest Page Object Model framework in this repository is reused as the automation approach (Section 9) |
| A-13 | Synthetic test data only. No production customer data is used in any non-production environment |
| A-14 | Multi-factor authentication (MFA/OTP) is not part of this release |

### Open questions for the business

| # | Question | Affects |
|---|---|---|
| Q-01 | What are the target dates (code freeze, test start, go-live) and the size/availability of the test team? | Sections 22, 23 |
| Q-02 | Which environments exist, who owns them, and is Staging sized like Production for performance testing? | NFR-01, NFR-02, Section 16 |
| Q-03 | What is the tech stack (front-end framework, auth service, identity provider, database, session store, CDN/WAF)? | Sections 11, 12, 13 |
| Q-04 | Is MFA/OTP or device binding required for login? Regulators often expect strong customer authentication for banking | Scope, FR-01 |
| Q-05 | Does the lockout counter apply per account, per IP or both? Does a successful login reset it? Is the user notified (email/SMS) of a lock? Can support unlock early? | FR-05 |
| Q-06 | For NFR-02, what is the peak login rate (logins per second), and the expected ramp profile (for example a salary-day peak)? | NFR-01, NFR-02 |
| Q-07 | Is NFR-01 measured at average, p90 or p95, and under what load? | NFR-01 |
| Q-08 | Which browser versions and OS combinations (Safari on macOS only, or also iPadOS/iOS)? Is mobile web in scope? | NFR-03 |
| Q-09 | Is the session timeout warning shown before expiry (for example at 13 minutes), and can the user extend the session? Is there also an absolute session limit? | FR-07 |
| Q-10 | Where is "last login timestamp" displayed (Dashboard, profile), in which time zone, and is it the current or the previous login? | FR-04 |
| Q-11 | Is the Forgot Password flow itself (email delivery, reset token, new password) in scope for this release, or only the presence of the link? | FR-06 |
| Q-12 | What is the exact wording of the generic login error message, and is it localised? | FR-08 |
| Q-13 | Are usernames case-insensitive (`User@Bank.com` vs `user@bank.com`)? Is whitespace trimmed? | FR-01, FR-02 |
| Q-14 | What are the compliance obligations (PCI DSS, local banking regulator, GDPR, accessibility WCAG 2.1 AA)? | Sections 13, 25 |
| Q-15 | Does a lock also apply to accounts that do not exist (to avoid user enumeration via lock behaviour)? | FR-05, FR-08 |

---

## 1. Project Overview

The Online Banking Portal is a customer-facing web application. This release delivers the **User Login** feature: authentication of registered customers with an email username and password, redirection to the Dashboard, account lockout after repeated failures, a Forgot Password entry point, inactivity session expiry and non-revealing error messages. The feature is the security gateway to every other banking function, so defects here have direct financial, regulatory and reputational impact.

This plan defines how the feature will be verified against FR-01 to FR-08 and NFR-01 to NFR-03, the risks involved, the measurable criteria for starting and finishing testing, and the evidence needed for a go/no-go decision.

## 2. Scope

Testing covers the login journey end to end: the login page UI, client-side and server-side validation, the authentication API, the session lifecycle, the account lockout mechanism, the persistence of the last login timestamp, the presence and navigation of the Forgot Password link, response time and concurrency under load, cross-browser compatibility and login-specific security controls.

Coverage of each requirement by test type:

| Req ID | Functional (UI) | API | Integration | Security | Performance | Cross-browser | Automation (regression) |
|---|---|---|---|---|---|---|---|
| FR-01 | Yes | Yes | Yes (auth service, DB) | Yes | Yes | Yes | Yes |
| FR-02 | Yes | Yes | - | Yes (injection in field) | - | Yes | Yes |
| FR-03 | Yes | Yes | Yes (password store) | Yes | - | Yes | Yes |
| FR-04 | Yes | Yes | Yes (DB timestamp) | - | Yes (redirect time) | Yes | Yes |
| FR-05 | Yes | Yes | Yes (lock store, clock) | Yes (brute force) | Yes (lock under load) | Sample | Yes (API level) |
| FR-06 | Yes | - | Yes (reset service link) | Yes (enumeration) | - | Yes | Yes |
| FR-07 | Yes | Yes | Yes (session store) | Yes (session fixation, reuse) | - | Yes | Yes (API, shortened timeout where configurable) |
| FR-08 | Yes | Yes | - | Yes (enumeration, timing) | - | Sample | Yes |
| NFR-01 | Sample | Yes | - | - | Yes | Sample | Monitoring checks |
| NFR-02 | - | Yes | Yes | - | Yes | - | - |
| NFR-03 | Yes | - | - | - | - | Yes | Yes (browser matrix) |

## 3. Objectives

1. Verify that every requirement FR-01 to FR-08 behaves as specified, with 100% requirement traceability to executed test cases.
2. Confirm that login is not vulnerable to user enumeration, brute force, session hijacking or injection (FR-05, FR-07, FR-08), with 0 open Critical/High security findings at release.
3. Demonstrate that login p95 response time is under 3 seconds (NFR-01) while sustaining 5,000 concurrent users (NFR-02) with an error rate of 1% or less.
4. Demonstrate consistent behaviour on Chrome, Firefox, Edge and Safari (NFR-03).
5. Deliver an automated UI and API regression suite for login that can run on every build.
6. Provide management with objective, metric-based evidence for the release decision (Section 25).

## 4. In Scope Features

| # | Feature | Req IDs |
|---|---|---|
| 1 | Login with valid registered credentials | FR-01 |
| 2 | Username email format validation (client and server side) | FR-02 |
| 3 | Password rule validation and handling of non-compliant passwords | FR-03 |
| 4 | Redirection to Dashboard and update of last login timestamp | FR-04 |
| 5 | Lockout after 5 consecutive failures, automatic unlock after 15 minutes, counter reset | FR-05 |
| 6 | Forgot Password link presence, visibility, accessibility and navigation target | FR-06 |
| 7 | Session expiry after 15 minutes of inactivity, redirect to login, protected pages blocked after expiry | FR-07 |
| 8 | Generic, non-revealing error messages (UI text, API response body, status code, timing) | FR-08 |
| 9 | Login response time and concurrency | NFR-01, NFR-02 |
| 10 | Browser compatibility on Chrome, Firefox, Edge, Safari | NFR-03 |
| 11 | Logout as part of the session lifecycle (needed to verify FR-07 and FR-04) | FR-04, FR-07 |
| 12 | Basic accessibility of the login form (labels, keyboard navigation, focus, screen reader error announcement) | FR-01, FR-06, FR-08 |

## 5. Out of Scope Features

| # | Item | Reason |
|---|---|---|
| 1 | Full Forgot Password / reset flow beyond the link (email, token, new password) | Only link availability is required by FR-06. To be brought into scope if Q-11 says so |
| 2 | User registration / onboarding | Separate feature; registered test users will be provisioned |
| 3 | MFA / OTP | Not in the requirement (A-14, Q-04) |
| 4 | Dashboard functionality beyond successful landing | Separate feature |
| 5 | Native mobile apps and mobile browsers | Not in NFR-03 (A-11, Q-08) |
| 6 | Production load testing | Performed in Staging only |
| 7 | Full penetration test of the whole portal | Login-specific security testing only; a full pen test is a separate engagement |
| 8 | AI/ML components | None in this feature (Section 15) |

## 6. Assumptions

All assumptions A-01 to A-14 listed before Section 1 apply. In addition:

- A-15: Requirements FR-01 to FR-08 and NFR-01 to NFR-03 are baselined and changes go through change control.
- A-16: The development team delivers unit tests and a build that passes a smoke test before each test cycle.
- A-17: Timeouts (lockout 15 minutes, session 15 minutes) can be shortened by configuration in the QA environment to allow efficient automated testing, with a final verification at the real 15 minute values.
- A-18: Server and application logs, plus database read access, are available to QA to verify FR-04 timestamps and FR-05 counters.
- A-19: Defects are tracked in a single tool (for example Jira) agreed with the development team.

## 7. Risks

| Risk ID | Risk | Likelihood (H/M/L) | Impact (H/M/L) | Mitigation | Owner |
|---|---|---|---|---|---|
| R-01 | User enumeration through differing error text, HTTP status, response time or lock behaviour (FR-08, FR-05, FR-06) | M | H | Compare UI text, API body, status code and response time for "unknown user" vs "wrong password" vs "locked"; timing analysis over 100+ samples; include Forgot Password response in checks | Security Tester |
| R-02 | Lockout logic defects: counter not reset on success, race conditions allowing more than 5 attempts under parallel requests, lock not lifted after 15 minutes (FR-05) | H | H | Boundary tests (4, 5, 6 attempts), parallel request tests via API, clock/config controlled tests, verification at real 15 minute value | Functional QA / Automation |
| R-03 | Lockout used as denial of service: attacker locks out real customers (FR-05) | M | H | Raise with business (Q-05, Q-15); test IP/rate limiting if implemented; record residual risk for sign-off | Test Lead / Product Owner |
| R-04 | Session not invalidated server-side after 15 minutes (only client-side timer), or token reusable after logout/expiry (FR-07) | M | H | API tests replaying old session token after expiry and logout; multi-tab tests; check cookie flags | Security Tester |
| R-05 | Performance environment not production-like, making NFR-01/NFR-02 results unreliable | H | H | Confirm Staging sizing early (Q-02); document scaling factor; run a baseline then a full load; agree acceptance with architecture | Performance Engineer / Environment Owner |
| R-06 | Ambiguous NFR definitions (percentile, load profile, concurrency meaning) lead to disputed results (NFR-01, NFR-02) | H | M | Get answers to Q-06/Q-07 signed off before performance scripting starts; record agreed SLA in this plan | Test Lead |
| R-07 | Safari testing needs macOS hardware or cloud grid that may not be available (NFR-03) | M | M | Use Playwright WebKit for daily runs plus real Safari via a cloud device grid or a Mac for final certification | Automation Engineer |
| R-08 | 15 minute timers make manual and automated tests slow and flaky (FR-05, FR-07) | H | M | Configurable timeouts in QA (A-17); API-level tests; schedule real-time verification once per cycle | Automation Engineer |
| R-09 | Last login timestamp wrong due to time zone or recorded before authentication completes (FR-04) | M | M | DB verification against server UTC; display check across time zones; verify failed logins do not update it | Functional QA |
| R-10 | Password rules enforced differently in UI and API (FR-03, FR-02) | M | H | Test every rule at UI and directly at API to confirm server-side enforcement | Functional QA |
| R-11 | Test data contamination: shared accounts locked by parallel test runs (FR-05) | H | M | Dedicated account pools per test type; data reset scripts; unique accounts for lockout tests | Automation Engineer |
| R-12 | Late delivery of a stable build compresses the test window | M | H | Entry criteria gate (Section 18); risk-based prioritisation of P1 cases; contingency in estimate | Test Lead / Dev Lead |
| R-13 | Unstated regulatory requirements (MFA, audit logging) discovered late (Q-04, Q-14) | M | H | Raise Q-04/Q-14 at plan review; Compliance sign-off on scope | Product Owner / Compliance |
| R-14 | Credentials or tokens leaked in logs, URLs or browser storage | L | H | Log and network inspection; check no password in query string, local storage or logs | Security Tester |

## 8. Dependencies

| # | Dependency | Needed for | Owner |
|---|---|---|---|
| D-01 | Stable build deployed to QA with release notes | All testing | Dev Lead / DevOps |
| D-02 | Production-like Staging environment, load generators and monitoring (APM, DB, server metrics) | NFR-01, NFR-02 | DevOps / Environment Owner |
| D-03 | Authentication API specification (OpenAPI/Swagger) and error code catalogue | API tests, FR-08 | Dev Lead |
| D-04 | Provisioned test accounts (active, locked, near-lock, expired password etc.) and ability to reset them | All FRs | DBA / Dev |
| D-05 | Configurable lockout and session timeout values in QA | FR-05, FR-07 | Dev Lead |
| D-06 | Browser grid access, including real Safari (cloud grid or macOS) | NFR-03 | DevOps / Automation |
| D-07 | Forgot Password target page/service available (at least a stub) | FR-06 | Dev Lead |
| D-08 | Security tooling licences (for example OWASP ZAP / Burp Suite) and approval to scan Staging | Section 13 | Security team |
| D-09 | Business answers to Q-01 to Q-15 | Scope, estimate, NFR acceptance | Product Owner |

## 9. Test Approach

A risk-based approach is used: FR-05, FR-07, FR-08 and NFR-01/NFR-02 carry the highest business and security risk and receive the deepest coverage and earliest testing.

**Test levels**

| Level | Owner | Focus |
|---|---|---|
| Unit | Development | Email validation, password rules, counter and timer logic |
| API / Service | QA | Authentication endpoint contract, lockout, session, error responses (FR-01 to FR-05, FR-07, FR-08) |
| System (UI) | QA | End-to-end login journey on all browsers (FR-01 to FR-08, NFR-03) |
| Integration | QA | Auth service with user DB, session store, lock store, Dashboard, Forgot Password service |
| Non-functional | Performance / Security | NFR-01, NFR-02, security controls |
| UAT | Business | Business acceptance of the journey and messages |

**Test cycles**

1. Cycle 1: smoke, API and functional P1/P2, early security scan, performance baseline.
2. Cycle 2: full functional, cross-browser matrix, full load and soak tests, security testing, defect retests.
3. Regression and sign-off: automated regression, real-time 15 minute verifications (FR-05, FR-07), final metrics.

**Techniques**: equivalence partitioning and boundary value analysis (FR-02, FR-03, FR-05: 4/5/6 attempts, 7/8 password characters; FR-07: 14:59 vs 15:01 minutes), state transition testing for account and session states (active, failed-n, locked, unlocked; active, idle, expired), decision tables for error messages (FR-08), negative and exploratory testing.

**Automation approach (reusing this repository's framework)**

The existing Playwright + pytest Page Object Model framework in this repository is the reusable pattern for the Online Banking Portal login suite:

- UI: Playwright page objects per area (for example `pages/login/` with `login_page.py`), selectors kept in YAML (`login_selectors.yaml`) and test data in JSON (`login_values.json`), shared components in `pages/common/`.
- API: REST clients under `api/` built on a base client (`api/base_api.py` pattern) with endpoints in YAML and payloads in JSON, used for FR-01 to FR-05, FR-07, FR-08 checks and for fast test data setup (for example locking an account through the API before a UI test).
- Orchestration: `tests/conftest.py` run order and prerequisites (login first, logout last), and `make test <modules>` in the `Makefile` to run selected modules in CI.
- Evidence: HTML run reports in `reports/` and failure screenshots in `screenshots/`, attached to the test summary report and defects.
- Cross-browser: the same suite parameterised for Chromium, Firefox, WebKit and branded channels (Chrome, Edge), plus real Safari via grid for NFR-03.
- Performance testing uses a dedicated load tool (for example k6, JMeter or Locust) rather than Playwright.

Target: 80% or more of P1/P2 functional cases automated at UI or API level by the regression cycle.

## 10. Functional Testing Strategy

| Req ID | What will be tested | Key conditions |
|---|---|---|
| FR-01 | Valid login; invalid username; invalid password; both invalid; blank fields; unregistered user; deactivated user; case sensitivity of username (Q-13); leading/trailing spaces; Enter key vs button; double submit | Positive and negative, UI and API |
| FR-02 | Valid email formats (subdomains, plus addressing, long local part) and invalid formats (missing @, missing domain, spaces, double dots, Unicode, over-length input); client and server validation messages | Equivalence classes and boundaries |
| FR-03 | Password of 7 vs 8 characters; no uppercase; no digit; only digits; special characters; very long passwords; whitespace; paste behaviour; masking and show/hide toggle | Boundary values; server-side enforcement (R-10) |
| FR-04 | Redirect lands on Dashboard URL; back button after login; deep link redirect after login (if supported); last login timestamp updated in DB only on success; displayed value and time zone (Q-10); failed attempts do not change it | DB verification |
| FR-05 | 4 failures then success (counter reset); 5 failures lock; 6th attempt with correct password still rejected while locked; unlock after 15 minutes; lock message is generic (FR-08); failures spread across sessions/browsers still count; parallel attempts | State transition, real-time and shortened timer runs |
| FR-06 | Link visible without scrolling, enabled, keyboard reachable, correct target, opens in expected tab, available in locked state and after errors | UI on all browsers |
| FR-07 | Idle 14:59 keeps session; idle 15:00+ expires; activity resets timer; expired session redirects to login on next action; protected URLs and API calls rejected after expiry; multi-tab behaviour; warning dialog if specified (Q-09) | Shortened and real-time timers |
| FR-08 | Same message, status code and response shape for unknown user, wrong password, and wrong case; no hints in tooltips, field highlighting or page title | Decision table, comparison with FR-05 lock message |
| NFR-03 | Full P1 suite on Chrome, Firefox, Edge, Safari (layout, validation, focus, autofill, password managers) | Browser matrix in Section 16 |

Accessibility checks on the login form (labels, focus order, error announcement, contrast) are run alongside functional testing.

## 11. API Testing Strategy

Assumes a REST/JSON authentication API (A-01, Q-03).

| Area | Tests | Req IDs |
|---|---|---|
| Contract | Request/response schema against OpenAPI spec; required fields; content types; HTTP methods allowed (POST only) | FR-01 |
| Validation | Invalid email, password rule violations, missing/null/oversized fields, wrong data types, extra fields, injection payloads | FR-02, FR-03 |
| Authentication | Valid login returns session/token with correct expiry; token works on protected endpoints; invalid credentials return a generic 401 | FR-01, FR-08 |
| Last login | Last login value returned or persisted (verified through profile API or DB) on success only | FR-04 |
| Lockout | Sequential and parallel failed requests; lock state returned generically; unlock after timeout; counter reset after success | FR-05 |
| Session | Token rejected after 15 minutes idle; activity extends; token rejected after logout; refresh token behaviour | FR-07 |
| Error uniformity | Identical status, body and headers for all credential failure types; response time variance within agreed tolerance | FR-08 |
| Response time | Single-user API latency baseline per build | NFR-01 |

API tests are implemented as Playwright `APIRequestContext` clients following the `api/` pattern in this repository and run in CI on every build.

## 12. Integration Testing Strategy

| Integration point | Verification | Req IDs |
|---|---|---|
| Login UI to Authentication API | Correct payloads, error propagation, no credentials in URL | FR-01, FR-08 |
| Authentication service to user store/DB | Credential check, last login write, transactional behaviour on failure | FR-01, FR-04 |
| Authentication service to lock/counter store | Counter increments, resets, persists across nodes (load-balanced instances) | FR-05 |
| Session store / gateway | Idle timeout enforced server side across all nodes; logout invalidates everywhere | FR-07 |
| Login to Dashboard | Redirect and session hand-off; Dashboard shows last login | FR-04 |
| Login page to Forgot Password service | Link target reachable and passes no sensitive data | FR-06 |
| Audit logging / SIEM (if applicable) | Successful, failed and locked events logged without passwords | FR-05, FR-08 |
| Notification service (if applicable, Q-05) | Lock notification sent | FR-05 |

## 13. Security Testing Strategy

Aligned with the OWASP ASVS (authentication and session management chapters) and OWASP Top 10.

| Area | Tests | Req IDs |
|---|---|---|
| User enumeration | Error text, status, headers, timing comparison; Forgot Password and lock responses for existing vs non-existing users | FR-08, FR-05, FR-06 |
| Brute force and credential stuffing | Lockout effectiveness, parallel request race, distributed attempts, rate limiting/CAPTCHA if present | FR-05 |
| Account lockout DoS | Ability to lock arbitrary accounts; residual risk documented | FR-05 |
| Session management | Session ID regenerated after login (fixation), cookie flags (Secure, HttpOnly, SameSite), server-side expiry, reuse after logout/expiry, concurrent sessions policy | FR-07 |
| Transport | HTTPS only, HSTS, TLS 1.2+ configuration, no mixed content | FR-01 |
| Input handling | SQL/NoSQL/LDAP injection, XSS in username field and error rendering, header injection | FR-02, FR-03 |
| Credential handling | No password in logs, URL, browser storage or autocomplete where prohibited; password hashed at rest (dev evidence) | FR-01, FR-03 |
| Clickjacking and headers | X-Frame-Options/CSP, security headers on login page | FR-01 |
| Automated scanning | DAST scan (for example OWASP ZAP) on Staging login flow each cycle | All |

Severity follows CVSS. Release requires 0 open Critical/High security findings (Section 19).

## 14. Performance Testing Strategy

| Test type | Profile | Pass criteria | Req IDs |
|---|---|---|---|
| Baseline | 1 to 50 users, steady | p95 login under 1.5 s (reference) | NFR-01 |
| Load | Ramp to 5,000 concurrent users over 15 min, hold 60 min, login rate per Q-06 | p95 login under 3 s, p99 under 5 s, error rate 1% or less, CPU under 75%, no memory growth | NFR-01, NFR-02 |
| Stress | Ramp beyond 5,000 (to about 7,500) until breaking point | Graceful degradation, no data corruption, recovery within 5 min | NFR-02 |
| Spike | 0 to 5,000 logins in 2 minutes (for example morning or salary-day peak) | p95 under 3 s after 2 min stabilisation; no lock-store errors | NFR-01, NFR-02 |
| Soak | 3,000 to 5,000 users for 4 hours | No degradation over 10% in p95; no leaks; sessions expire as per FR-07 | NFR-02, FR-07 |
| Lockout under load | Mix including 5% failed logins | Lock counts accurate under concurrency | FR-05 |

- Measurement: response time from submit to Dashboard response at the server and load generator, plus browser-side timing samples with Playwright for end-user render time.
- Tools: k6/JMeter/Locust (to be confirmed, Q-03), APM and infrastructure monitoring.
- Environment: Staging sized like Production (R-05). If smaller, results are extrapolated with an agreed scaling factor and flagged as a residual risk.

## 15. AI/ML Validation Strategy (if applicable)

Not applicable: the User Login feature contains no AI/ML components. If risk-based authentication or fraud scoring is added later, this section will be revisited.

## 16. Test Environment Requirements

| Environment | Purpose | Requirements |
|---|---|---|
| QA | Functional, API, integration, automation | Latest build, configurable lockout/session timeouts, DB read access, logs, test account reset scripts, Forgot Password stub or service |
| Staging / Pre-Prod | Performance, security, final regression, UAT | Production-like sizing and topology (load balancer, multiple app nodes, shared session/lock store), real 15 minute timeouts, APM, security scan approval |
| Production | Post-deployment smoke only | Dedicated smoke test account, read-only checks |
| CI | Automated regression | Pipeline runner with Python, Playwright browsers, `make test` targets, report and screenshot artefact publishing |

**Browser matrix (NFR-03)**, versions to be confirmed (Q-08):

| Browser | Versions | OS | Execution |
|---|---|---|---|
| Google Chrome | Latest, Latest-1 | Windows 11, macOS | Automated (Playwright channel `chrome`) |
| Mozilla Firefox | Latest, Latest-1 | Windows 11, macOS | Automated (Playwright Firefox) |
| Microsoft Edge | Latest, Latest-1 | Windows 11 | Automated (Playwright channel `msedge`) |
| Apple Safari | Latest, Latest-1 | macOS | Playwright WebKit daily; real Safari via cloud grid/Mac for certification |

Tooling: Playwright + pytest (UI/API), load tool (Section 14), OWASP ZAP/Burp (Section 13), defect tracker, test management tool, screen reader/axe for accessibility.

## 17. Test Data Requirements

| Data set | Purpose | Req IDs |
|---|---|---|
| Active registered users (pool of at least 20 for functional, separate pool per automation worker) | Successful login | FR-01, FR-04 |
| Users with known last login timestamp | Timestamp update checks | FR-04 |
| Lockout pool (dedicated, resettable accounts) | Lock and unlock tests, avoid contamination (R-11) | FR-05 |
| Pre-locked and near-lock (4 failures) accounts | State transition tests | FR-05 |
| Deactivated / suspended users | Negative tests | FR-01, FR-08 |
| Non-existent but valid-format emails | Enumeration tests | FR-08 |
| Valid and invalid email format list | Validation | FR-02 |
| Passwords at each rule boundary | Validation | FR-03 |
| Security payload lists (injection, XSS) | Security | FR-02, FR-03 |
| 5,000+ unique performance users with known credentials | Load tests | NFR-01, NFR-02 |

Rules: synthetic data only (A-13); data stored in JSON files next to page objects and API clients, following the repository pattern; credentials for test accounts kept in a secrets store or CI variables, not in source control; reset scripts run before each cycle.

## 18. Entry Criteria

Testing (each cycle) starts only when all of the following are met:

| # | Criterion | Measure |
|---|---|---|
| EN-01 | Requirements FR-01 to FR-08 and NFR-01 to NFR-03 baselined and signed off | Sign-off recorded; Q-01 to Q-15 answered or accepted as risks |
| EN-02 | Test plan approved | Approval by Test Lead, Product Owner, Dev Lead |
| EN-03 | Test cases designed and reviewed | 100% of requirements traced to at least one test case; 100% of P1 cases peer reviewed |
| EN-04 | Build deployed to QA with release notes | Build ID recorded; unit test pass rate 100% for login modules; code coverage at least 80% for auth module |
| EN-05 | Smoke test passed | 100% of smoke cases pass (valid login, invalid login, Dashboard redirect, Forgot Password link visible) |
| EN-06 | Environment and data ready | QA environment availability at least 95% in the previous 2 days; 100% of test data sets in Section 17 provisioned |
| EN-07 | No blocking defects | 0 open Blocker defects on the login flow |
| EN-08 (performance) | Staging ready for load | Staging topology confirmed; monitoring in place; functional P1 pass rate at least 95% in Staging |
| EN-09 (security) | Approval to scan | Written approval for DAST on Staging |

## 19. Exit Criteria

Testing is complete when all of the following are met:

| # | Criterion | Measure |
|---|---|---|
| EX-01 | Execution coverage | 100% of P1 and P2 test cases executed; at least 95% of P3 executed |
| EX-02 | Pass rate | At least 98% pass rate for P1; at least 95% overall |
| EX-03 | Requirement coverage | 100% of FR-01 to FR-08 and NFR-01 to NFR-03 have at least one executed and passed test |
| EX-04 | Defects | 0 open Critical/High defects; Medium defects 5 or fewer, each with an agreed workaround and fix date; all Low defects triaged |
| EX-05 | Security | 0 open Critical/High security findings; FR-08 enumeration tests 100% passed |
| EX-06 | Performance | NFR-01: p95 login under 3 s at 5,000 concurrent users; NFR-02: 5,000 concurrent users held 60 min with error rate 1% or less; soak shows under 10% p95 degradation |
| EX-07 | Compatibility | 100% of P1 cases passed on Chrome, Firefox, Edge and Safari (NFR-03) |
| EX-08 | Timers verified at real values | FR-05 (15 min unlock) and FR-07 (15 min idle expiry) passed at least once at real timeout values in Staging |
| EX-09 | Regression | Automated regression suite pass rate 100% (or failures analysed and accepted) on the release candidate build |
| EX-10 | Reporting | Test Summary Report published and signed off; UAT sign-off obtained |

## 20. Defect Management Process

**Lifecycle**: New, Triaged, Assigned, In Progress, Fixed, Ready for Retest, Retest Passed / Reopened, Closed (or Deferred / Rejected with justification).

**Severity and response targets**

| Severity | Definition (login context) | Example | Fix target |
|---|---|---|---|
| Critical | Security breach or login unavailable for all users | Login with wrong password succeeds; lockout bypass; session never expires | 24 hours |
| High | Major requirement fails, no workaround | Account not unlocked after 15 minutes; error reveals which field is wrong; p95 over 3 s | 2 working days |
| Medium | Requirement partially fails, workaround exists | Timestamp shown in wrong time zone; layout broken on one browser | 5 working days |
| Low | Cosmetic | Typo, alignment | Next release or backlog |

- Priority (P1 to P4) is set at daily triage by the Test Lead, Dev Lead and Product Owner.
- Each defect records: requirement ID (FR/NFR), build, environment, browser, steps, expected vs actual, and evidence (HTML report from `reports/`, screenshot from `screenshots/`, logs, HAR file).
- Security defects are restricted-visibility tickets.
- Every fix is retested and the related automated regression set re-run.

## 21. Reporting Metrics

| Metric | Target / use | Frequency |
|---|---|---|
| Test execution progress (planned vs executed vs passed, by FR/NFR) | Track to plan | Daily |
| Pass rate by priority | Exit criteria EX-02 | Daily |
| Requirement coverage (FR-01 to NFR-03) | 100% | Weekly |
| Defects by severity, status, age and requirement | 0 open Critical/High at exit | Daily |
| Defect density (defects per requirement) | Highlight risky areas | Weekly |
| Defect reopen rate | 10% or less | Weekly |
| Automation coverage and pass rate | At least 80% of P1/P2 automated | Per build |
| Browser matrix status (NFR-03) | 100% P1 pass per browser | Per cycle |
| Performance results (p50/p95/p99, throughput, error rate, resource use) | NFR-01, NFR-02 | Per performance run |
| Security findings by CVSS severity | 0 Critical/High at exit | Per cycle |

Outputs: daily status email, weekly dashboard for management, and the final Test Summary Report. Automated runs publish the HTML report (`reports/latest.html`) and screenshots as CI artefacts.

## 22. Resource Plan

Based on assumption A-02 (to be confirmed, Q-01):

| Role | Count / allocation | Responsibilities |
|---|---|---|
| Test Lead / Test Manager | 1 (100%) | Planning, risk management, triage, reporting, sign-off |
| Functional QA Engineer | 2 (100%) | Test design, manual functional, integration and cross-browser execution, UAT support |
| Automation Engineer | 1 (100%) | Extend Playwright/pytest POM framework for UI and API, CI integration, test data scripts |
| Performance Engineer | 1 (50%) | Load model, scripts, execution, analysis (NFR-01, NFR-02) |
| Security Tester | 1 (50%) | Security testing and DAST (Section 13) |
| Business users (UAT) | 2 (part-time, 3 days) | UAT and message wording acceptance |
| Support roles | Dev Lead, DevOps, DBA (on call) | Builds, environments, data, defect fixes |

Training needs: banking security standards briefing for QA; framework walkthrough of the existing Playwright POM repository for any new automation staff.

## 23. Effort Estimation

| # | Activity | Person-days | Main roles |
|---|---|---|---|
| 1 | Test planning, requirement analysis, open question resolution | 4 | Test Lead |
| 2 | Test design: scenarios, test cases, traceability (via `test-cases`), review | 8 | Functional QA, Test Lead |
| 3 | Environment and test data setup (account pools, reset scripts, browser grid) | 4 | Automation, DevOps support |
| 4 | Functional and integration execution, 2 cycles (FR-01 to FR-08) | 12 | Functional QA |
| 5 | Cross-browser execution (NFR-03) | 4 | Functional QA |
| 6 | API testing (design and execution) | 4 | Automation / Functional QA |
| 7 | Automation: UI page objects, API clients, CI integration | 14 | Automation Engineer |
| 8 | Security testing (FR-05, FR-07, FR-08 focus, DAST) | 6 | Security Tester |
| 9 | Performance testing: load model, scripts, baseline, load, stress, spike, soak, analysis (NFR-01, NFR-02) | 9 | Performance Engineer |
| 10 | Regression (automated runs plus manual P1 re-run, real-time timer checks) | 6 | Automation, Functional QA |
| 11 | Defect triage, retesting | 5 | All QA |
| 12 | UAT support | 2 | Functional QA |
| 13 | Reporting, metrics, Test Summary Report, sign-off | 3 | Test Lead |
| | **Subtotal** | **81** | |
| | Contingency (15%) for risks R-05, R-08, R-12 and open questions | 12 | |
| | **Total** | **93 person-days** | |

**Duration**: about 5 calendar weeks (25 working days) with the team in Section 22 (about 5 FTE of QA effort), structured as week 1 planning/design/setup, weeks 2 to 3 cycle 1 and automation build, week 4 cycle 2 plus performance and security, week 5 regression, UAT and sign-off.

**Assumptions behind the numbers**

- Team and allocation as in A-02; 1 person-day = 8 productive hours.
- About 120 to 150 test cases in total (approximately 10 to 20 per requirement), of which about 80% of P1/P2 are automated.
- The existing Playwright/pytest POM framework is reused, so no framework build from scratch (reduces automation effort by an estimated 30 to 40%).
- Configurable timeouts in QA (A-17); without them, add about 5 person-days for real-time waits.
- Staging is production-like and available for performance by week 4; otherwise add about 3 to 5 person-days and calendar delay.
- Forgot Password flow beyond the link is out of scope; if added (Q-11), add about 6 to 8 person-days.
- MFA is out of scope; if added (Q-04), add about 10 to 12 person-days.
- At most 2 build drops per cycle and defect fix turnaround as in Section 20.

## 24. Test Deliverables

| Deliverable | Timing |
|---|---|
| Test Plan (this document) | Before testing |
| Requirement Traceability Matrix (FR-01 to NFR-03 to test cases) | End of design |
| Detailed test scenarios and test cases. **Produce these with the `test-cases` agent**, using the requirement IDs in this plan | End of design |
| Test data sets and reset scripts (JSON data, account pools) | Before cycle 1 |
| Automated UI and API test suite (page objects, YAML selectors, JSON data, API clients, Makefile targets) | Incrementally, complete by regression |
| Performance test scripts, load model and performance test report | End of cycle 2 |
| Security test report (findings with CVSS scores) | End of cycle 2 |
| Daily status reports and weekly dashboard | During testing |
| Automated run reports (HTML in `reports/`) and screenshots (`screenshots/`) | Every run |
| Defect reports | Ongoing |
| Test Summary Report with release recommendation | End of testing |

## 25. Release Recommendation Criteria

| Recommendation | Conditions |
|---|---|
| **GO** | All exit criteria EX-01 to EX-10 met; 0 open Critical/High functional or security defects; NFR-01 and NFR-02 targets met in a production-like environment; NFR-03 P1 pass on all four browsers; UAT signed off |
| **GO with conditions** | All Critical/High closed; up to 5 Medium defects open with approved workarounds and fix dates; NFR-01 met at p95 but minor deviations (for example p99) documented and accepted by architecture and Product Owner; residual risks (for example R-03 lockout DoS) formally accepted by the business |
| **NO-GO** | Any open Critical/High defect, especially any failure of FR-05 (lockout), FR-07 (session expiry) or FR-08 (non-revealing errors); NFR-01 p95 at or above 3 s or NFR-02 not sustained; any browser in NFR-03 failing P1 cases; P1 pass rate under 98% |

The Test Lead issues the recommendation in the Test Summary Report. The final go/no-go decision is made by the Product Owner, Engineering Lead, Security/Compliance and Operations at the release readiness meeting.

---

*For detailed test cases with requirement traceability, use the `test-cases` agent with the requirement register above.*
