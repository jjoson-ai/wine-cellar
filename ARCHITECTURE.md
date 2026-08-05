# Wine Cellar — architecture

A private mini-site for one person's wine collection. Its single job: answer
*"what should I open tonight?"* at a glance, and give something worth saying when the
bottle is poured.

Live page (**primary bookmark**, public): <https://jjoson-ai.github.io/wine-cellar/>
Mirror (claude.ai, private to owner): <https://claude.ai/code/artifact/0f3ff4ad-fc0b-4240-b8eb-df329ed66f28>

The repo is public (<https://github.com/jjoson-ai/wine-cellar>) and GitHub Pages serves
`docs/` from `main` — so `git push` *is* the deploy. The claude.ai artifact had
device-cache staleness issues as a bookmark; GitHub Pages replaced it as primary on
2026-08-06.

## Shape

No framework, no build tooling, no dependencies. Three source files produce one
self-contained page.

```
wines.json  ──┐              docs/index.html      (GitHub Pages — the deploy artifact)
photos/*.jpg ─┼─→ build.py ─→ dist/index.html     (standalone document, open locally)
template.html ┘              dist/artifact.html   (body only; the Artifact tool supplies
                                                   doctype/head/body)
```

`build.py` is stdlib-only Python. It validates ids, base64-embeds each photo as a data
URI, and substitutes three placeholders in `template.html`:
`/*__WINES__*/`, `/*__PHOTOS__*/`, `/*__BUILT__*/`.

Everything is inlined because the published page runs under a strict CSP that blocks
every external request — no CDNs, no font URLs, no remote images. Typography therefore
uses a system-font stack (Didot / Iowan Old Style / SF Mono) rather than a webfont.

`dist/` is committed. The site should survive without anyone having to rebuild it.

## The organizing idea

Every bottle's drinking window is drawn on **one shared year scale**, with a single
"today" line running down the page through all of them. Urgency is therefore visible
as geometry, not just as a label: you can see which windows are about to close relative
to each other. The scale is derived from the collection each load, so it stretches as
bottles are added.

Bottles fall into three racks, computed client-side from the current date:

- **Drink now** — past peak, or window closes within a year. Past-window bottles sort
  first and get their own rust-coloured flag.
- **Drinking well** — inside the window, no hurry.
- **Hold** — window has not opened.

Because this is computed in the browser rather than baked, the page re-sorts itself over
time with no rebuild. See `INTAKE.md` for the full baked-vs-live split.

Consumed bottles leave the racks entirely and collapse into History.

## Data model

`wines.json` is the single source of truth. One entry per wine:

```jsonc
{
  "id": "tempier-bandol-rouge-2012",   // slug: producer-cuvee-vintage
  "producer": "Domaine Tempier",
  "name": "Bandol Rouge",
  "vintage": 2012,                      // null for NV
  "type": "red",                        // red|white|rose|sparkling|dessert|fortified|orange
  "region": "Bandol, Provence, France",
  "varietals": ["Mourvèdre", "Grenache"],
  "abv": 14.0,
  "quantity": 1,
  "status": "cellar",                   // cellar|consumed
  "consumed_date": null,
  "photo": "photos/tempier-bandol-rouge-2012.jpg",   // null → typed bottle glyph
  "window": {
    "start": 2016, "end": 2027,         // inclusive years
    "peak_start": 2019, "peak_end": 2024,
    "confidence": "medium",             // low|medium|high|owner
    "note": "why this window"
  },
  "rating": { "score": 93, "basis": "estimated — …", "personal": null },
  "notes": "tasting notes",
  "pairing_classic": "…",
  "pairing_offbeat": "…",
  "anecdotes": [{ "kicker": "The producer", "text": "…" }],
  "added": "2026-08-05",
  "sample": true                        // seed rows; deleted at first real intake
}
```

Missing fields degrade rather than break: no photo draws a bottle glyph tinted by wine
type, no anecdotes hides Table talk, no window puts the bottle in Drinking well.

## Honesty

Windows, ratings, pairings and anecdotes are model-generated estimates and are labelled
as such in the UI and the footer. An owner-supplied score lands in `rating.personal` and
the page shows it instead, relabelled as theirs. Nothing invented is presented as fact.

## Intake

The owner posts photos in Claude Code; Claude reads the label and does everything else.
The full procedure — including the requirement to run intake on **Fable 5 / Max** — is
in `INTAKE.md`.
