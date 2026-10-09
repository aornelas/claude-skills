# How the Claude Code team uses Claude Code — Concept Notes

**Source:** https://youtu.be/S-sYlFiGFv8 · Claude (YouTube channel) · informal roundtable with several members of the Claude Code team (about 3,500 words of transcript)

## Concept Summary

Three ideas run through the conversation, all about where to put effort when the model underneath changes every couple of months.

**1. Fan out, verify adversarially, then filter.** Code review is where the team first used a large fan-out: Claude searches for every possible bug in parallel, then each candidate bug gets an adversarial review from several different perspectives to check whether it is real, and only the survivors reach a human. They call this spending test-time compute to build confidence, and describe it as a MapReduce problem: once you fan out you have too much output to read, so you must filter back down for human consumption. The same shape works for performance issues and general research (their example is planning a trip, with many searches, then agents that rank results, then agents that verify them). Notably, Claude writes the orchestration itself as code, so a plain `for` loop guarantees every item gets the same treatment, which is why one speaker says it raises his trust. It mixes deterministic code with agentic behavior.

**2. Harness features are scaffolding for current model weaknesses, so expect them to expire.** The to-do list feature arrived when a model would be given five things and quietly give up after three. A year later it was barely needed. Another speaker spent a long time designing the ask-user-question tool, and now mostly gets questions through an HTML artifact with diagrams and mockups instead. The lesson they state: stay unattached to what you build, because it covers for failure modes the next model may not have, and then check what the bigger tasks now require.

**3. Move up one level of abstraction.** The progression described is local sessions, then hosted containers, then cloud routines (for example, a daily job that buckets incoming feedback and fixes the ones it is confident about), then a Slack-native agent where the human sees only the messages the agent chooses to send, with transcripts one link away. Human code review shifts from nitpicks that signal "I read this" to the bigger picture the model may lack, such as why a service boundary sits where it does. Verification, code review, and feedback are named as the three primitives that make this work.

**What's actually new:** the patterns (map-reduce, adversarial verification, routines) are familiar. The distinctive claim is operational: assume your own scaffolding has a short shelf life and design for removing it.

**Preconditions:** a verification step Claude can run itself (tests, screenshots, recordings), and an environment where Claude can build and test the project end to end without you.

## Application Options

### New skill: fan-out, adversarial verify, coalesce
A reusable procedure for any "find everything that might be wrong or relevant" task: split into N parallel candidate-finders, run each candidate past several differently-framed skeptic passes, and return only what survives with the evidence. The transcript's examples are code review and trip research, so the skill's trigger could be review, audit, or research requests. Whether the first use is a code review or something else in your work depends on what you review most.

### Implementation plan: audit existing skills for expired scaffolding
For each skill you maintain, list the steps that exist to compensate for a model weakness (forced checklists, repeated reminders, step-by-step hand-holding), then run the skill with and without them on a recent model and keep only the steps that still change the result. This is the to-do-list lesson applied to your own setup. It needs a few representative test inputs per skill, and I don't know which of your skills are old enough to carry this.

## Ready-to-Use Prompt

> You are helping me prune and strengthen my Claude skills. Background: a team that builds Claude Code observed that much of what they build into a harness (checklists, special tools, hand-holding steps) exists to cover a specific weakness of the current model, and that these features often become unnecessary within about a year as models improve. They also found that for "find everything that might be wrong" tasks, the reliable pattern is to fan out many parallel searches, run each candidate through adversarial review from several perspectives, and return only the ones that survive.
>
> Do this with me:
> 1. List the skills in my skills folder with a one-line purpose each, and ask me to pick one or two I use most.
> 2. For each chosen skill, read its instructions and mark every step or rule that looks like compensation for a model weakness (for example, steps that force the model to keep going, restate its plan, or double-check basic work). Show me the list and ask which ones I want to test.
> 3. Propose 3 realistic test inputs per skill, run the skill as written and again with the marked steps removed, and compare the outputs side by side. Tell me which steps changed the result and which didn't, and recommend what to cut. Don't edit anything until I approve.
> 4. Separately, ask whether any of my skills does a "find all the issues" job (review, audit, research). If so, propose a fan-out version: parallel finders, then 2-3 skeptic passes per candidate with different framings, then a short ranked list with evidence.
>
> Keep every change small and reversible, and use version control so I can undo it.
