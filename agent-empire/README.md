# Agent Empire

**Status:** Experimental browser-game prototype  
**Home:** `AI_Playground/agent-empire/`  
**Future path:** If it becomes a serious simulator or an Atlas component, split it into its own repository.

## Build document

The implementation-ready specification lives in [BUILD_PLAN.md](./BUILD_PLAN.md). It fixes the first-version scope, game rules, data contracts, UI, balancing, and build order so an implementation agent can proceed without reopening core design decisions.

## Premise

*Agent Empire* is a browser-based strategy game where the player is CEO of an AI-run company. Each run begins with a randomly generated business idea that could realistically be built and operated by AI agents, plus a starting budget, deadline, and business requirements.

The player builds the organisation that must execute it: selecting managers, assigning specialised agents beneath them, and deciding how work reports and flows through the company.

## Organisation builder

Available roles can include product, research, development, design, marketing, sales, finance, legal, security, QA, and customer support.

Every manager and agent has stats such as:

- Skill
- Speed
- Cost
- Reliability
- Creativity
- Autonomy
- Context capacity
- Collaboration

Managers have limits on how many agents they can supervise effectively. The strongest individual agents do not automatically make the strongest company: team chemistry, reporting structure, mission requirements, and coordination affect the outcome.

## Simulation loop

Once the organisation is approved, the company progresses through simulated phases:

1. Research
2. Planning
3. Building
4. Launch
5. Growth

During execution, the player receives progress reports and must handle disagreements, delays, opportunities, and crises. Possible interventions include replacing agents, changing managers, restructuring departments, adjusting the budget, or letting the organisation resolve the issue independently.

## Performance and replayability

Runs are evaluated across product quality, time, budget, revenue, customer satisfaction, reputation, and organisational stability.

Each business idea should reward different structures and trade-offs. The game should avoid a single universally perfect organisation.

## End-of-run blueprint

At the end of a run, generate an organisational blueprint containing:

- Final org chart
- Responsibilities
- Workflows
- Approval gates
- Tools
- Performance results
- Recommended improvements

## Longer-term direction

The first version is a fun, replayable management game. Its organisation-building system should nevertheless be designed so successful teams can eventually be exported as blueprints for real multi-agent environments such as Atlas.
