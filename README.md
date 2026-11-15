# ResolveAI studio

Reels and Shorts for ResolveAI: ERP software and AI automation for established businesses.

```
briefs/<id>.json  --pipeline/kit.py-->  specs/<id>.json  --pipeline/make_reel.py-->  queue/<id>/video.mp4
```

- `pipeline/kit.py`: brief -> spec from tested scene blocks + layout check (exits 1 on LAYOUT PROBLEMS)
- `pipeline/make_reel.py`: channel rule checks, voice, render. `--sheet` = one check image for the whole Reel
- `pipeline/engine.py`: renders the illustrated look, word-highlight captions, sound and the cover
- `pipeline/fx.py`: the drawing blocks (night places, people, cards, chips, icons, phone and browser frames)
- `pipeline/voice.py`: Kokoro am_liam narration (model downloads once to ~/.cache/kokoro)
- `assets/fonts`: Inter Tight (OFL, Google Fonts). `assets/shots`: real screens of the live demos. `assets/logo.png`

- `poster/`: posting (GitHub Actions): `publish_due.py` posts queued Reels at `post_at` to YouTube and Instagram;
  videos are served from the `media` branch by GitHub Pages
- `tools/`: `check_keys.py`, `deep_check.py` (no public posts), `get_youtube_token.py`, `backfill_thumbnails.py`
- `pages/`: the public site (home, privacy, terms) shown on GitHub Pages

How to make a Reel: `ROUTINE.md`. One-time setup: `SETUP.md`.
- `pipeline/carousel.py`: weekly Instagram carousel (1080x1350 slides) from a brief in `carousels/`
