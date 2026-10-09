# Claude Chat vs Cowork vs Code: Which One Should You Use? — Concept Notes

**Source:** https://www.youtube.com/watch?v=PtGQaduZwmA · Futurepedia · short explainer (transcript is about 2,000 words)

> Note: the auto-generated captions mishear product names ("Cogram", "Coda"). These notes use the real names, Cowork and Code. Plan and availability details are the video's claims at recording time and change quickly.

## Concept Summary

The video gives one rule for choosing between Claude's three products: **Chat to think, Cowork to delegate, Code to build.** The useful part is the reasoning behind it. Chat finishes when it has produced an answer, inside a single turn, whether or not the job is done. Cowork works toward a goal: it builds a checklist, works through it (sometimes with sub-agents), and stops only when the goal is met, which might take 2 minutes or 40. The speaker's analogy is a vending machine (Chat) versus a kitchen (Cowork).

Two further differences follow from that. Cowork gets a persistent workspace it keeps building on across the whole job, instead of one-off tool calls. And it can run on a schedule without you, such as a Monday-morning briefing built from last week's email threads and meeting transcripts, with a follow-up email already drafted. The video also claims Cowork and Code are the same agentic architecture underneath: files plus connected apps is Cowork, and adding a code repository makes it Code.

The practical trigger is a smell test: if you are copying Chat's output into a doc or stitching pieces together, that is delegation work you are doing by hand. If your problem is "I wish a tool existed for this," that is a Code job.

The location of the workspace matters. On desktop, Cowork and Code work on local folders. On web and mobile they run in a cloud sandbox, which keeps working with your computer off but cannot see local files. The speaker's workaround is a Google Drive folder as shared "home base," read and written through the Drive connector, so any surface can reach it.

**What's actually new:** nothing technical. It is a decision framework, and the "same architecture, different loaded context" point is the most transferable piece.

**Preconditions:** a paid plan for Cowork and Code, and (per the video) a GitHub repo for cloud Code sessions.

## Application Options

### New skill: a "which surface should this task go to" check
Package the video's three tests (does it finish in one turn, does it need a persistent workspace, should it run unattended) plus the copy-paste-assembly smell test into a skill that reads a task description and recommends Chat, Cowork or Code, with the reason. This is only worth it if you often misroute work, which depends on your habits.

### Implementation plan: make an existing cloud-readable home base and a first scheduled task
The Drive-folder workaround only helps if your working files already live somewhere a connector can reach. Pick one recurring job (the video's example is a weekly briefing), put its inputs in that folder, and set it up as a scheduled Cowork task so it runs without a device online. If your notes or project files already sync to a cloud drive, the first step may be nearly done; check which folder the connector can actually see.

## Ready-to-Use Prompt

> You are helping me decide which Claude product to use for my recurring work, and then set one up. Background: Claude has three modes. Chat is a thinking partner that finishes after one answer. Cowork takes a goal, builds a checklist, works through it with its own workspace (my local folder on desktop, or a cloud sandbox on web and mobile) until the goal is met, and can run on a schedule while I'm away. Code is the same agent with a code repository loaded, used to build apps, scripts and tools. A sign I'm in the wrong mode is when I copy Chat's output into a document or stitch pieces together by hand.
>
> Do this with me step by step:
> 1. Ask me to list 5-10 tasks I did in the last two weeks. For each one, classify it as think (Chat), delegate (Cowork) or build (Code), and tell me which of the three tests it passed: finishes in one turn, needs a persistent workspace, or could run unattended.
> 2. Point out any task where I was doing copy-paste assembly by hand, and say how I would hand it off instead.
> 3. Pick the one recurring task with the most value as a scheduled Cowork job. Ask what inputs it needs and where they live. If they are only on my local machine, suggest moving them to a cloud folder that a connector can read, so the job can run with my computer off.
> 4. Write the exact goal statement I would give Cowork, the schedule, and what the finished deliverable should look like, so I can paste it in.
>
> Don't assume which plan I'm on or which features are available to me; ask me to check in the app.
