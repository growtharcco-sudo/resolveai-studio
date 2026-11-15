# ResolveAI studio

This repo makes and posts one Reel a day (and one Instagram carousel on Saturdays) for ResolveAI (Instagram @resolveai.software, YouTube @resolveaisoftware).
For every run, follow `ROUTINE.md` step by step. Never post directly: queue it, and GitHub Actions posts at `post_at`.
Hard rules:
- Write a brief and build the spec with `pipeline/kit.py`. Never hand-write scene coordinates or edit specs by hand.
- Check a Reel with `make_reel.py --sheet` and read only that one sheet.png, not single stills.
- Every fact from a reputable source fetched the same day; every number in `math`, checked in Python.
- Examples are labelled as typical examples. Never invent clients, results, reviews, prices or team size.
- No em dashes or en dashes. Never "small team". No personal or founder names; the company speaks as ResolveAI.
- Instagram caption ends with a real question, then exactly 5 hashtags including #resolveai.
  YouTube description has a Sources list and 3 hashtags: #Shorts, #ResolveAI and one topic tag.
- Voice is Kokoro am_liam at 1.15. Instagram AI label and YouTube synthetic-content disclosure stay on.
- Full quality: 1080x1920, 30 fps, CRF 16. Never lower quality to save time or file size.
- Do not change the look (fx.py, engine.py drawing) unless the owner asks.
- If the owner replies "skip", create `queue/<id>/SKIP`, commit and push.
- Never put tokens or passwords in files or chat: they live only in GitHub Secrets.
