# Intake — how new bottles get onto the site

This is the operating manual for whoever (Claude, usually) processes a photo drop.
The owner's job is only to post photos in Claude Code and say what happened.

## Model

**Use Fable 5 at Max effort for every intake.** The enrichment — tasting notes,
drinking window, rating, both pairings, and the table-talk anecdotes — is written once
and then frozen into `wines.json`, so it is worth spending real reasoning on. A weak
pass here is not corrected by anything downstream; it just sits on the page.

## What is baked vs. what is live

Knowing the split matters, because it decides when a rebuild is needed.

| Baked at intake (frozen into `wines.json`) | Computed live in the browser, every page load |
| --- | --- |
| Producer, cuvée, vintage, region, grapes, ABV | Which urgency group a bottle falls in |
| Tasting notes | The shared year scale and its ticks |
| Drinking window start / end / peak | Position of the "today" line |
| Rating and its basis | Sort order within each group |
| Classic and offbeat pairings | The masthead sentence and counts |
| Table-talk anecdotes | |

So the page keeps re-sorting itself as time passes with no rebuild — a bottle slides
from Hold into Drinking well into Drink now on its own. A rebuild is only needed when
the *facts* change: a new bottle, a corrected window, a bottle opened.

## Steps

1. **Read the label.** Extract producer, cuvée, vintage, region, grapes, ABV. Ask only
   if the label is genuinely illegible or ambiguous — do not invent a vintage. If a
   detail cannot be read and cannot be inferred, leave the field `null` rather than
   guessing.

2. **Save the photo.** Resize first, or the built page bloats:

   ```bash
   sips -Z 600 ~/Downloads/<photo>.jpg --out ~/Projects/wine-cellar/photos/<id>.jpg
   ```

   `<id>` is the wine's slug: `producer-cuvee-vintage`, lowercase, hyphenated,
   e.g. `tempier-bandol-rouge-2012`.

3. **Write the entry** in `wines.json` (see the schema in `ARCHITECTURE.md`). All of it:
   notes, window, rating, both pairings, anecdotes.

   - **Drinking window** — reason from producer, appellation, vintage quality and
     structure. Put the reasoning in `window.note`; it shows on the detail page.
   - **Offbeat pairing** — genuinely non-traditional, and explain *why* it works
     (acid, fat, char, sweetness). Filipino and Southeast Asian dishes land well here
     and the owner likes them; do not force it on every bottle.
   - **Anecdotes** — 2–4 items, each `{kicker, text}`. The kicker names what the story
     is *about* (`The producer`, `The grape`, `The vintage`, `The place`, `The name`).
     These get said out loud at a table, so: specific, checkable, and short. No
     "wine has been made here for centuries" filler. If there is no real story for a
     supermarket bottle, write fewer — or none.
   - Mark everything you inferred as estimated in `rating.basis`. If the owner gives
     their own score, put it in `rating.personal`; the page prefers it and relabels.

4. **Remove the seed samples.** On the first real intake, delete every entry with
   `"sample": true`.

5. **Build and publish:**

   ```bash
   cd ~/Projects/wine-cellar && python3 build.py
   ```

   The build writes three copies: `docs/index.html` (GitHub Pages — **the owner's
   bookmark**), `dist/index.html` (local preview), `dist/artifact.html` (claude.ai
   mirror).

   Publishing is the **git push** (step 6) — GitHub Pages redeploys
   `https://jjoson-ai.github.io/wine-cellar/` automatically within a minute.
   After pushing, also republish `dist/artifact.html` to the same claude.ai artifact
   URL (pass it as `url` to the Artifact tool) so the mirror stays in sync. Both URLs
   are recorded in `ARCHITECTURE.md`. Never mint a new URL of either kind — bookmarks
   break.

6. **Commit and push.** `git add -A && git commit && git push`. The repo is **public**
   (github.com/jjoson-ai/wine-cellar): keep personal details out of commit messages and
   entries, and author commits as `jjoson-ai <jjoson-ai@users.noreply.github.com>`
   (already the repo-local git config — do not override it with `-c user.email=...`).
   The local-only branch `pre-github-history` holds the pre-publication history and
   must never be pushed.

## Other things the owner says

- **"We drank the X"** → set `status: "consumed"`, `consumed_date: "YYYY-MM-DD"`. It
  moves to History and drops out of the urgency groups. Ask for their own score if they
  have one; that becomes `rating.personal`.
- **"That window is wrong"** → update it and set `window.confidence` to `"owner"`.
  Their call always beats the estimate.
- **A photo of several bottles** → one entry per bottle; crop is unnecessary, the same
  photo can be referenced by each, but a per-bottle shot looks better on the page.
