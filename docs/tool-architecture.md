# Tool architecture

Anders should avoid becoming one giant CLI with fifty pages of docs.

## Principle

Use **small, task-specific CLIs/tools** with clear names, narrow scopes, and short help output.

The agent should be able to inspect the repo and quickly choose the right tool for a job, whether the task is email, calendar, LinkedIn, housing data, finances, projects, or some future arbitrary source.

## Shape

Prefer a toolbox layout:

```txt
tools/
  anders-day/          # daily folder/bootstrap utilities
  anders-google/       # Google auth/email/calendar orchestration
  anders-linkedin/     # LinkedIn notification/export handling
  anders-housing/      # future housing data tools
  anders-brief/        # summarize/render morning briefs
  anders-sources/      # source registry/discovery
```

Each tool should have:

- a short README
- a focused CLI entrypoint
- examples that fit on one screen
- explicit input/output files
- no hidden writes outside the configured data repo

## Public vs private split

- `anders` owns reusable tools, schemas, docs, and anonymized examples.
- `anders-life` owns Doug-specific data, goals, source outputs, and briefings.

Tools should accept the private data repo path explicitly or via:

```bash
ANDERS_DATA_REPO=/Users/douglasschonholtz/repos/anders-life
```

## Discovery

Maintain a lightweight tool index so agents do not need to read every README:

```txt
tools/index.md
```

Each entry should include:

- tool name
- purpose
- when to use
- examples
- privacy/safety notes

## Guidance for future tools

When adding a new source or domain:

1. Create or update the smallest relevant tool.
2. Document the tool in `tools/index.md`.
3. Keep full provider/API notes in the tool folder, not top-level docs.
4. Do not add everything to a single global CLI unless it is only a thin dispatcher.

A thin dispatcher is okay, but the source-specific tools should remain independently understandable and runnable.
