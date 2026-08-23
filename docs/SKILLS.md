# Skills

This workflow is driven by an AI assistant with a set of skills installed. A
skill is a folder of instructions the assistant loads when a task matches it.

Two sources: a bundled custom skill for the search workflow, and an open-source
pack for the document work.

---

## The custom skill: `job-hunt`

Included in this repo at [`skills/job-hunt/`](../skills/job-hunt/). It encodes
the workflow in [WORKFLOW.md](WORKFLOW.md) so the assistant applies the
eligibility gate before it gets enthusiastic about a role, rather than after.

Use it when searching for roles, checking whether a posting is worth applying
to, or working through the to-prepare pile.

Its `references/sources.md` is where you record **what has actually worked**,
ranked by outcome rather than by traffic. That file is the memory of the search
and it is the most valuable thing in the repo after a few weeks. Keep notes on
sources that wasted your time, not only ones that paid off.

---

## The document pack: ResumeSkills

Install from [github.com/Paramchoudhary/ResumeSkills](https://github.com/Paramchoudhary/ResumeSkills)
into `.claude/skills/`. Twenty-three skills; these are the ones that carry the
weight in this workflow.

### Used on nearly every application

| Skill | What it does |
|---|---|
| `job-description-analyzer` | Parses a posting, scores the match, names the gaps, produces a keyword set. Run it first; its output drives the tailoring |
| `resume-tailor` | Rewrites the CV for one posting while staying truthful |
| `resume-bullet-writer` | Turns weak bullets into achievement statements with real impact |
| `resume-ats-optimizer` | Checks ATS parseability and keyword coverage |
| `cover-letter-generator` | Drafts the letter from CV plus posting |
| `application-form-filler` | Answers screening questions in the candidate's voice |

### Used at specific moments

| Skill | When |
|---|---|
| `tech-resume-optimizer` | Engineering and PM roles specifically |
| `resume-section-builder` | Building a section from scratch |
| `resume-formatter` | ATS-safe layout |
| `resume-quantifier` | Finding metrics you already have. **See the warning below** |
| `resume-version-manager` | Tracking a master CV against tailored versions |
| `interview-prep-generator` | STAR stories and practice questions from the CV |
| `cold-email-writer` | Direct outreach to a hiring manager |
| `linkedin-profile-optimizer` | Profile and headline |
| `portfolio-case-study-writer` | Turning a bullet into a case study. Excellent for private work you cannot link |
| `salary-negotiation-prep` | Market rates and counter-offer scripts |
| `offer-comparison-analyzer` | Comparing offers on total compensation |
| `reference-list-builder` | Formatting references |
| `career-changer-translator` | Translating skills across industries |
| `academic-cv-builder` | Academic CVs with publications and grants |
| `executive-resume-writer` | C-suite and VP |
| `creative-portfolio-resume` | Design roles, balancing visuals against ATS |

### One warning, and it is the important one

**Never let a skill invent a number.** `resume-quantifier` will offer to
estimate metrics you do not have, and an estimated figure on a CV is a claim you
cannot defend in an interview.

Keep a single source of truth for every factual claim: one file holding your
real numbers, with a verification step that fails the render if a number in the
CV does not trace back to it. Skills propose; the source file decides.

---

## Installing

```bash
mkdir -p .claude/skills
git clone https://github.com/Paramchoudhary/ResumeSkills .claude/skills/resume-skills
cp -r skills/job-hunt .claude/skills/
```

Then restart your assistant so it picks them up.

## Rendering documents

This repo does not ship a CV renderer, because the layout is personal and any
templating approach works. Two notes from experience:

**If you use a downloaded .docx template, check its hyperlink targets.**
Templating libraries replace visible text but do not touch the relationship
targets in `word/_rels/document.xml.rels`. A template can display your URL and
link to the template author's. This is invisible in the document and survives
every render.

```bash
unzip -p CV.docx word/_rels/document.xml.rels | grep -o 'Target="http[^"]*"'
```

**Never trust a verification line whose source you have not read.** A check that
confirms "2 hyperlinks intact" may be asserting the presence of exactly the
wrong links.
