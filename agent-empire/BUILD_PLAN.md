# Agent Empire — v0.1 Build Plan

## 1. Product decision

Build a single-player, browser-based management strategy game. The player is the CEO of an AI-operated startup. A run lasts roughly 12–20 minutes and consists of organisation design followed by a compressed execution simulation.

This is deliberately a game first. It must feel strategic, readable, and replayable before it tries to become a real agent-orchestration product. The later Atlas export is represented by a structured end-of-run blueprint, not by real agent execution.

### v0.1 success criteria

- A player can start a run, receive a distinct business scenario, build an org chart, run the simulation, make decisions, and see a scored outcome.
- At least three viable organisation styles can win different scenarios: lean and fast, balanced, and specialist-heavy.
- No role, manager, or team shape is universally optimal.
- Every decision has a clear trade-off shown before confirmation.
- The app works entirely in-browser with no account, backend, API key, or network dependency.
- A completed run can be exported as a human-readable organisation blueprint in Markdown and a machine-readable JSON object.

### Explicit non-goals for v0.1

- No live LLM calls, real sub-agents, multiplayer, login, payments, external data, or backend.
- No generated artwork requirement. Use a polished dark UI, icons, initials, and simple CSS/HTML shapes.
- No fully free-form org editor. Use a constrained manager → agent reporting model so rules stay explainable.
- No endless tycoon mode. A run ends after the Growth phase.

## 2. Technical decisions

Use React + TypeScript + Vite. Use CSS modules or a single global CSS file with CSS variables. Do not add a state-management framework; React `useReducer` plus selectors is sufficient. Do not use a component library.

Use the browser `localStorage` for settings, the active run snapshot, run history, and the most recently generated blueprint. A random seed stored at run creation must make each run reproducible while developing and debugging.

Suggested structure:

```text
src/
  app/
    App.tsx
    routes.ts
  data/
    roles.ts
    managers.ts
    agents.ts
    scenarios.ts
    events.ts
    tools.ts
  engine/
    rng.ts
    initialiseRun.ts
    validation.ts
    scoring.ts
    simulation.ts
    events.ts
    blueprint.ts
  components/
    Layout.tsx
    StatChip.tsx
    ResourceBar.tsx
    AgentCard.tsx
    ManagerCard.tsx
    OrgChart.tsx
    EventModal.tsx
    PhaseTimeline.tsx
    DecisionPreview.tsx
  screens/
    HomeScreen.tsx
    BriefingScreen.tsx
    OrgBuilderScreen.tsx
    SimulationScreen.tsx
    ResultsScreen.tsx
    ArchiveScreen.tsx
  styles/
    tokens.css
    app.css
  types.ts
```

## 3. Game loop

1. **Home**: start a new company or view saved run history.
2. **Company briefing**: receive one random scenario, starting cash, deadline, success criteria, and risks. The player may reroll once per run.
3. **Organisation builder**: hire managers, assign agents, choose tools, and submit the org when validation passes.
4. **Simulation**: advance phase-by-phase. Each phase calculates performance, then may surface one decision event.
5. **Intervention**: the player accepts an event choice, restructures the company, or continues without intervention.
6. **Results**: reveal metrics, outcome tier, financial result, event log, final org chart, and exportable blueprint.

All runs always visit Research → Planning → Build → Launch → Growth. A critical failure does not stop the game early; it becomes a weak final outcome with an explanation. This makes every run useful for learning and export.

## 4. Core data model

Implement these as TypeScript interfaces. Persist the complete `RunState` after every player action.

```ts
type Department =
  | 'product' | 'research' | 'development' | 'design' | 'marketing'
  | 'sales' | 'finance' | 'legal' | 'security' | 'qa' | 'support';

type Phase = 'research' | 'planning' | 'build' | 'launch' | 'growth';
type Difficulty = 'easy' | 'standard' | 'hard';
type EventSeverity = 'opportunity' | 'warning' | 'crisis';

interface Stats {
  skill: number;          // 1–10
  speed: number;          // 1–10
  reliability: number;    // 1–10
  creativity: number;     // 1–10
  autonomy: number;       // 1–10
  contextCapacity: number;// 1–10
  collaboration: number;  // 1–10
}

interface Manager extends Stats {
  id: string;
  name: string;
  title: string;
  department: Department;
  weeklyCost: number;
  managementCapacity: number; // 2–5 direct reports
  speciality: string;
  trait: string;
}

interface Agent extends Stats {
  id: string;
  name: string;
  role: Department;
  weeklyCost: number;
  speciality: string;
  trait: string;
  preferredManagerDepartment?: Department;
  conflictsWithTrait?: string;
}

interface Scenario {
  id: string;
  name: string;
  pitch: string;
  targetCustomer: string;
  productType: 'saas' | 'consumer-app' | 'service' | 'marketplace' | 'content-product';
  budget: number;
  deadlineWeeks: number;
  successTargets: Partial<RunMetrics>;
  criticalDepartments: Department[];
  optionalDepartments: Department[];
  risks: string[];
  difficulty: Difficulty;
}

interface RunMetrics {
  productQuality: number;     // 0–100
  schedule: number;           // 0–100, 100 is fully on time
  budgetHealth: number;       // 0–100, 100 is under budget
  revenue: number;            // currency value
  customerSatisfaction: number;// 0–100
  reputation: number;         // 0–100
  stability: number;          // 0–100
}

interface CompanyState {
  cashRemaining: number;
  currentWeek: number;
  managers: Record<string, Manager>;
  agents: Record<string, Agent>;
  reportsTo: Record<string, string>; // agent id -> manager id
  selectedTools: string[];
}

interface RunState {
  id: string;
  seed: string;
  scenario: Scenario;
  company: CompanyState;
  metrics: RunMetrics;
  phase: Phase;
  resolvedEvents: ResolvedEvent[];
  log: LogEntry[];
  status: 'briefing' | 'building-org' | 'simulating' | 'complete';
}
```

## 5. Content required for the first playable version

### Scenarios

Ship five fixed scenario templates. Randomise their title, target customer, budget variation (±10%), deadline variation (±1 week), and one secondary risk using the seed.

| ID | Scenario | Budget | Deadline | Critical departments | Main tension |
| --- | --- | ---: | ---: | --- | --- |
| `compliance-copilot` | AI compliance evidence assistant for mid-sized fintechs | 95,000 | 12 weeks | product, development, legal, security, qa, sales | quality and trust vs speed |
| `creator-clips` | AI short-form clip tool for independent creators | 70,000 | 8 weeks | product, development, design, marketing, support | fast launch vs retention |
| `hotel-concierge` | multilingual AI concierge for boutique hotels | 85,000 | 10 weeks | research, development, design, sales, support | customer fit vs enterprise delivery |
| `tender-radar` | AI tender discovery and bid-prep service | 80,000 | 11 weeks | research, product, development, legal, sales | research breadth vs sales focus |
| `ops-brief` | AI daily operations brief for multi-site restaurants | 65,000 | 9 weeks | product, development, design, qa, marketing | simplicity vs operational reliability |

### Manager roster

Create 12 managers: one primary manager for each department plus a second option for Product. Their stats must be deliberately asymmetric. Example: a very creative Product lead has lower reliability; a cautious Security lead slows delivery but protects reputation. Every manager has a capacity between 2 and 5.

### Agent roster

Create 30 agents: 2–4 per department. Each agent needs a distinct specialism and one trait. Reuse no more than three traits: `bold`, `methodical`, `pragmatic`, `visionary`, `careful`, `fast`, `empathetic`, `independent`.

Use clear names that read like roster characters, for example: Mira (UX systems), Rook (secure infrastructure), Elias (B2B discovery), Nova (concept design), and Sable (adversarial QA). Do not imply they are real people.

### Tools

Use six optional tools, each costing a one-off amount and adding a narrow modifier:

| Tool | Cost | Effect |
| --- | ---: | --- |
| Research Workspace | 4,000 | +8 research effectiveness |
| Design System | 5,000 | +8 design quality and +4 speed in Build |
| CI Test Grid | 6,000 | +10 QA effectiveness and +6 stability |
| Security Scanner | 5,000 | +10 security effectiveness and +8 reputation protection |
| Sales CRM | 4,000 | +8 sales effectiveness and +10% Launch revenue |
| Support Desk | 3,000 | +8 support effectiveness and +6 customer satisfaction |

Tools must be visible in the builder and included in the final blueprint.

## 6. Organisation rules

### Hiring and reporting

- The CEO is implicit and costs nothing.
- An agent cannot be hired unless at least one manager is hired.
- Every agent must report to exactly one manager.
- A manager may supervise agents from any department, but a department match gives a `+10` functional-fit bonus.
- A manager over capacity is allowed but creates `-8 stability` and `-5 reliability` per excess direct report during every remaining phase.
- A manager with no reports is allowed but gives no direct production value; only hire one when it is part of an intentional restructure.
- The initial company must include at least one manager and at least three agents; maximum 5 managers and 12 agents.
- Total expected payroll across the scenario deadline plus selected tool costs cannot exceed the starting budget at submission. Show this calculation continuously.

### Team chemistry

Evaluate chemistry once at submission and again after every restructure. For each manager-agent edge:

- `+4` if the agent’s preferred manager department matches.
- `+3` when manager collaboration and agent collaboration are both at least 7.
- `+2` when manager autonomy is within 2 points of agent autonomy.
- `-4` when the agent’s `conflictsWithTrait` matches the manager trait.
- `-3` when autonomy differs by 5 or more.

The company chemistry score is the average edge score, clamped to 0–100 after converting `(average + 4) / 13 * 100`. It contributes to stability and schedule, not directly to revenue.

### Functional coverage

For each critical department, calculate its assigned work score from the best relevant manager and all relevant agents. Missing a critical department does not block launch, but applies an obvious scenario-specific penalty, for example missing Security on `compliance-copilot` reduces reputation by 18 and stability by 12.

## 7. Simulation engine

The engine must be deterministic for a stored seed. All random rolls use one seeded RNG utility. Never use `Math.random()` outside the seed initialisation function.

### Phase weighting

Each phase checks particular departments more heavily:

| Phase | Primary departments | Secondary departments | Weeks consumed |
| --- | --- | --- | ---: |
| Research | research, product | sales, legal | 2 |
| Planning | product, design | development, security | 2 |
| Build | development, design, qa | product, security | 3 |
| Launch | marketing, sales, support | qa, legal | 2 |
| Growth | support, sales, product | development, finance | 2 |

For each department in a phase, calculate:

```text
functionalScore =
  managerContribution + agentContribution + toolModifier + fitModifier

managerContribution = manager.skill * 0.45 + manager.reliability * 0.20
                    + manager.speed * 0.15 + manager.collaboration * 0.20

agentContribution = average(relevantAgent.skill * 0.40
                  + relevantAgent.speed * 0.25
                  + relevantAgent.reliability * 0.20
                  + relevantAgent.contextCapacity * 0.15)

fitModifier = average(teamChemistryEdgeBonuses) / 2
```

If no manager or agent is relevant, set that department score to `0`. Convert the weighted departmental result to a 0–100 phase effectiveness score by multiplying by 10 then clamping.

### Metric updates

At the end of every phase, apply these calculations. All values are clamped to 0–100 unless stated otherwise.

```text
qualityDelta = (build + planning + qa) / 18 - 8
scheduleDelta = (phaseSpeed + chemistry / 10) - 10 - overloadPenalty
stabilityDelta = (reliabilityAverage * 1.2 + chemistry / 10 + security / 20) - 12
reputationDelta = (quality + security + legal + support) / 32 - 8
customerSatisfactionDelta = (quality + design + support) / 30 - 8
```

For Research and Planning, quality deltas are applied at half strength. For Launch and Growth, quality is stable and customer satisfaction/reputation take full strength.

Payroll cost for a phase equals the sum of weekly costs of all hired people × weeks consumed. Deduct it at phase start. Budget health is:

```text
budgetHealth = clamp((cashRemaining / startingBudget) * 100, 0, 100)
```

Revenue begins at Launch:

```text
launchRevenue = baseMarketValue * (sales + marketing + productQuality) / 300
growthRevenue = launchRevenue * (1 + customerSatisfaction / 200 + reputation / 250)
```

Set `baseMarketValue` to 50,000 for the five v0.1 scenarios. Revenue can exceed the starting budget.

### Failure thresholds

- Cash below zero: the company continues but `schedule -15`, `stability -15`, and no further tools/hiring allowed.
- Stability below 25: trigger a mandatory crisis event in the next phase.
- Reputation below 30 after Launch: reduce next revenue by 35%.
- Product quality below 35 at Launch: reduce customer satisfaction by 20.
- Any critical department completely missing: apply that scenario's declared missing-function penalty once at the related phase.

## 8. Events and decisions

After each phase, trigger exactly one event. Pick from that phase’s event pool using the seed and current weakest metric. Events are not purely random: a weak metric must make the related problem more likely.

Create 15 events, three per phase. Each event has an option A, B, and C. Every option must disclose its immediate monetary cost and its likely trade-off in plain language, but keep the exact modifier hidden.

Example Build event:

```ts
{
  id: 'integration-slip',
  phase: 'build',
  severity: 'warning',
  title: 'Integration slip',
  body: 'The development team reports that a core integration will miss the planned handoff.',
  choices: [
    { id: 'scope', label: 'Cut the non-essential workflow', hint: 'Protects the date, may weaken product quality.', effects: { schedule: +12, productQuality: -7 } },
    { id: 'hire', label: 'Bring in a contract specialist', hint: 'Costs cash, protects both quality and timing.', cost: 8000, effects: { schedule: +8, productQuality: +4, stability: -2 } },
    { id: 'autonomy', label: 'Let the team solve it independently', hint: 'No cost. Outcome depends on autonomy and reliability.', conditional: 'developmentAutonomyRoll' }
  ]
}
```

The autonomy option succeeds when the relevant department’s average autonomy + reliability is at least a seeded threshold between 10 and 17. On success: `schedule +8`, `stability +3`. On failure: `schedule -10`, `stability -7`.

Use three intervention types only during v0.1:

- **Replace:** fire one person and hire one unassigned roster candidate. Charge one week of their new cost as a transition penalty. Their former manager may become under/over capacity.
- **Reassign:** move an existing agent to another manager. Costs no money but reduces stability by 2 in the current phase.
- **Add tool:** buy one unselected tool if cash allows. Its modifier starts in the next phase.

Do not permit deleting managers or firing people except in a Replace action for v0.1. This keeps edge cases controlled.

## 9. UI specification

### Visual language

Use the dark Atlas-adjacent aesthetic without copying the HQ idea literally: charcoal background, slightly lighter panels, warm off-white text, muted gold for positive values, controlled coral/red for danger, and a cool blue for interactive selections. Avoid gradients that obscure data. The whole game should feel like a strategic operations dashboard, not a generic SaaS admin panel.

### Persistent HUD

Display on every in-run screen:

- Scenario name and phase
- Cash remaining
- Week / deadline
- Product quality
- Reputation
- Stability

Colour thresholds: green 70+, amber 40–69, red below 40. Always pair colour with text or an icon so state is not colour-only.

### Home screen

- Title: `Agent Empire`
- One-sentence premise
- `Start New Company` primary button
- `Run Archive` secondary button
- Small note: “Experimental prototype. Teams are simulated, not live agents.”

### Briefing screen

- Scenario title, pitch, customer, budget, deadline, critical departments, risks, and success targets.
- `Reroll brief` once, visibly disabled after use.
- `Build organisation` enters builder.

### Organisation builder

Use three columns on desktop and one stacked column on mobile:

1. **Available roster**: filters for Managers / Agents and department. Cards show cost, role, stat shorthand, trait, and hire button.
2. **Company structure**: CEO root, manager slots beneath, agent chips beneath each manager. Support drag-and-drop only if it is effortless; otherwise use an explicit `Assign to…` menu. Correctness matters more than drag-and-drop.
3. **Company health**: payroll projection, cash reserve, staffing coverage, capacity warnings, chemistry score, selected tools, and submission checklist.

The `Approve organisation` button must be disabled until all validation conditions pass. On hover/tap, show exactly what remains invalid.

### Simulation screen

- A five-step phase timeline across the top.
- Left: final/current org chart, compact and non-editable unless an intervention is open.
- Centre: current phase card with a `Run phase` button. On click, animate metric changes and append a short plain-English report.
- Right: metric bars, cash, team chemistry, and activity log.
- After phase calculation, show an event modal before the next phase can begin.
- Add an `Intervene` button after each event choice, opening Replace / Reassign / Add Tool. The user may intervene once per phase.

### Results screen

Show, in this order:

1. Outcome tier and one-sentence headline
2. Final metric scorecard
3. Revenue, spend, and cash remaining
4. What worked / what limited the company, generated from the lowest and highest metric drivers
5. Final org chart
6. Timeline of choices and results
7. `Download Blueprint (.md)`, `Download Blueprint (.json)`, `Save to Archive`, and `Start Another Run`

## 10. Outcome tiers

Calculate a 0–100 final score:

```text
finalScore =
  productQuality * 0.22 +
  schedule * 0.14 +
  budgetHealth * 0.12 +
  min(revenue / 1000, 100) * 0.16 +
  customerSatisfaction * 0.14 +
  reputation * 0.12 +
  stability * 0.10
```

| Score | Tier | Player-facing summary |
| ---: | --- | --- |
| 85–100 | Category leader | The company launched a credible product and built momentum. |
| 70–84 | Strong launch | The company met most goals with manageable weaknesses. |
| 50–69 | Survived | The product exists, but execution trade-offs constrained it. |
| 30–49 | Stalled | The company reached market with material organisational problems. |
| 0–29 | Collapse | The company burned trust, time, or cash before it could establish itself. |

## 11. Blueprint export contract

Generate both a Markdown document and a JSON object from the exact final `RunState`.

Markdown headings, in this exact order:

```text
# Agent Empire Blueprint: [Company / Scenario]
## Run summary
## Business mandate
## Final organisation
## Responsibilities and reporting lines
## Tools and operating setup
## Approval gates
## Phase performance
## Key decisions and incidents
## Final results
## Recommended improvements
## Atlas export notes
```

`Approval gates` must include CEO approval for: organisation approval, tool spend above 5,000, replacing a manager, launch readiness, and budget increases. In v0.1 these gates are descriptive, since the player is the CEO.

`Recommended improvements` must be generated by deterministic rules:

- lowest department coverage → recommend relevant agent/manager capability
- chemistry below 50 → recommend reporting or trait changes
- stability below 50 → recommend reducing manager overload / increasing reliability
- budget health below 35 → recommend a leaner team or lower-cost tool set
- quality below 55 → recommend QA, product, or design coverage based on the weakest phase score

`Atlas export notes` must say that the blueprint is a simulation output and requires human review before becoming a real operating design.

## 12. Build order and acceptance checks

Build in the exact sequence below. Do not start visual polish until the milestone’s acceptance checks pass.

### Milestone 1 — App shell and seed

- Create Vite React TypeScript app.
- Add routes/screens with local screen state.
- Add seeded RNG and a `New Run` factory.
- Add five scenario templates and render the briefing.

Acceptance: refreshing the page preserves the same active run; starting with the same seed yields the same scenario variation.

### Milestone 2 — Roster and organisation builder

- Add all manager, agent, and tool data.
- Implement hire, assign, reassign, remove-before-approval, tool selection, and validation.
- Implement projected payroll, capacity, coverage, and chemistry calculation.

Acceptance: approval is impossible with missing reporting lines, too few agents, broken budget, or unassigned hires. Warnings accurately update after every action.

### Milestone 3 — Simulation engine

- Implement phase scores, payroll deduction, metric deltas, critical-function penalties, seeded event selection, and conditional autonomy choices.
- Add phase log entries explaining the most important score drivers.

Acceptance: identical saved run states always produce identical phase results; a team with better relevant coverage scores better than an irrelevant team; an overloaded manager visibly harms the simulation.

### Milestone 4 — Events and interventions

- Implement 15 events and choice application.
- Implement one intervention per phase: replace, reassign, add tool.
- Persist all choices in the event log.

Acceptance: each phase produces exactly one event, cash never becomes inconsistent, intervention limits are enforced, and the final log reconstructs every key decision.

### Milestone 5 — Results, exports, archive

- Implement final score, tier, explanation rules, Markdown/JSON downloads, and local archive.
- Add a run archive list showing scenario, tier, score, date, and `View blueprint`.

Acceptance: downloaded Markdown matches displayed final data; JSON contains the complete final state; reloading then opening an archived run preserves its result.

### Milestone 6 — Visual refinement and QA

- Apply final visual system, responsive layouts, keyboard support, and reduced-motion-safe animations.
- Test at 375px mobile width and 1440px desktop width.
- Add empty, disabled, warning, and error states.

Acceptance: no screen traps a player, no primary action is below the fold on common mobile sizes, and every metric change has a textual explanation.

## 13. Test matrix

Write unit tests for seeded RNG, payroll, chemistry, validation, overload penalty, phase scoring, event choice effects, final score, and blueprint generation. Add a lightweight end-to-end test for: new run → builder → approve → five phases → results → export.

Manually verify these representative configurations:

| Case | Expected result |
| --- | --- |
| Lean creator team | Can launch fast but risks low reliability/support in Growth. |
| Compliance specialist team | Scores strong reputation/stability but may strain deadline/budget. |
| Overloaded star manager | Gives warning and causes repeat stability/reliability penalties. |
| Missing critical Security | Allows game to proceed but visibly damages compliance scenario outcome. |
| High-autonomy team | Conditional “let them solve it” decisions have a higher success rate. |
| Low cash after Build | Locks further discretionary hiring/tools and applies stated penalties. |
| Same seed twice | Produces the same scenario variants, events, and phase outcomes. |

## 14. Decisions reserved for v0.2

Only consider these after v0.1 is playable and balanced:

- More scenarios, managers, agent classes, tools, and event chains.
- Animated org chart, drag-and-drop, richer visuals, and sound.
- Meta-progression, unlocks, difficulty selection, and leaderboards.
- User-authored business briefs.
- Real workflow templates / Atlas blueprint import and export.
- Optional live-model narration, strictly behind a user-controlled feature flag.

## 15. Definition of done

Agent Empire v0.1 is done when a new player can complete two clearly different runs, understand why they received different outcomes, export an organisation blueprint, and immediately want to try a different team strategy. If a mechanic does not create a visible organisation trade-off or improve that loop, leave it for a later version.
