# Building Secure Agents for Knowledge Work — Concept Notes

**Source:** https://youtu.be/z7cNbsr3b5s · Claude (YouTube channel) · conversation with the Every team about the Every Agent, built on Claude Managed Agents

## Concept Summary

Every built a single shared "AI coworker" that lives in Slack. The interesting part isn't the Slack form factor or the infrastructure. It's how they make the agent good at *their* work: they turn accumulated human judgment into skills, then close a feedback loop so the skills keep improving.

The clearest example is "Kate Pass." Every's editor-in-chief has a taste for copy edits that doesn't scale with the company. They took about 30,000 of her historical edits and distilled them into a skill. Anyone can ask for a "Kate pass" on a draft, and the agent leaves suggested changes in the Google Doc as her, which she accepts or rejects. They then track the extra edits she still has to make and fold those back into the skill, so it catches more over time. She also sees a graph of time saved and suggested new rules. The framing: taste is hard to describe in one go, but easy to distill from a thousand examples.

The second idea is personal evals ("bench-pilled"). Whenever someone likes or dislikes a model's output, they capture it, explain why, and the platform turns that into unit-test-like checks (e.g. "is the headline sentence case?"). They can then run many models on the same real scenario and score them against their own taste, instead of trusting generic benchmarks. They compare benchmarks to SAT scores: useful directionally, but once every model scores 1600 you need a reference check and a work trial instead.

Supporting ideas: one shared agent beats one agent per person, because gains compound when many people invest in the same skills. Managed Agents primitives (sandboxes, memory, session control) made it possible to copy production memory into an isolated "staging" agent for experiments. And the agent acts as a separate entity that, for tool calls, acts on behalf of the requesting user.

**What's actually new:** mostly familiar patterns (learn from examples, write evals, close the loop) applied to non-coding knowledge work and packaged well. The sharpest reframing is "hire for a job": treat a model as a new grad on day one and build a system that makes it better on day 10.

**Preconditions:** a large pile of real examples of the judgment you want to capture; a way to see what the human changed after the agent's output; and someone willing to review.

## Application Options

### New skill: distill taste from my own historical corrections
Take any repeatable task where you've already corrected output many times (edits, rewrites, reviews) and package those corrections into a skill that applies the same judgment on request. The Kate Pass skill works because it was built from tens of thousands of real edits rather than a written description of taste. Which task in your own work has the biggest pile of past corrections depends on your setup, which I don't know.

### Implementation plan: a correction-capture loop for an existing skill
For a skill you already use, log what you change in its output each time, and periodically fold those changes back into the skill's rules. This is Every's "track the extra work she added, then compound it back" step, and it can be added to an existing skill without redesigning it. A simple version is a file of dated corrections plus a periodic review that proposes new rules for approval.

### Implementation plan: personal evals from captured likes and dislikes
Keep a running list of outputs you liked or disliked with one line of why, convert recurring reasons into pass/fail checks, and run a skill or model against fixed scenarios to see whether it still passes. This gives you an eval that reflects your taste rather than a public benchmark, and it makes a model or prompt change testable instead of a vibe check.

## Ready-to-Use Prompt

> You are helping me turn my own accumulated judgment into a self-improving skill. Context: a team built an AI coworker where one person's taste (an editor's ~30,000 historical copy edits) was distilled into a skill anyone could invoke. They then tracked every extra edit the editor still made after the agent's pass and folded it back into the skill so it improved over time. They also built personal evals: captured outputs they liked or disliked, wrote down why, and converted the reasons into unit-test-style checks (for example, "is the headline in sentence case?") to compare models on real work.
>
> Do this with me, one step at a time, asking before you assume anything:
> 1. Ask me which task I repeat most where I routinely correct the output, and where my past corrections live (files, docs, git history, chat).
> 2. Read a sample of those corrections and propose a short list of the rules and tastes they imply. Show me concrete before/after examples for each rule, and ask me to confirm, reject or refine them.
> 3. Draft a skill (a SKILL.md with a clear trigger description) that applies the confirmed rules, plus a `corrections.md` log where each run's leftover manual edits get recorded.
> 4. Turn the confirmed rules into 10-20 pass/fail checks and a small set of fixed test scenarios, so I can re-run them whenever I change the skill or the model.
> 5. Propose a lightweight review routine, such as a weekly pass over `corrections.md` that suggests new rules for me to approve, so the skill compounds instead of going stale.
>
> Keep everything in plain files I can version-control. Don't invent rules I haven't confirmed.
