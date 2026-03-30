---
name: cdn-purge
description: Purge jsDelivr CDN cache for PocketOP database files after changes
disable-model-invocation: true
---

# CDN Purge — PocketOP Database

After any commit that modifies one or more of the database files (`devices.json`, `lenses.json`, `ptz_cameras.json`), purge the jsDelivr CDN cache so the PocketOP app picks up the new data.

## Steps

1. Determine which database files were changed. Check `git diff HEAD~1 --name-only` or the current working tree for modifications to:
   - `devices.json`
   - `lenses.json`
   - `ptz_cameras.json`

2. For each changed file, send a GET request to the jsDelivr purge endpoint. The purge URL is the CDN URL with `cdn.` replaced by `purge.`:

   ```
   curl -s https://purge.jsdelivr.net/gh/directimages/PocketOP-Database@main/devices.json
   curl -s https://purge.jsdelivr.net/gh/directimages/PocketOP-Database@main/lenses.json
   curl -s https://purge.jsdelivr.net/gh/directimages/PocketOP-Database@main/ptz_cameras.json
   ```

3. Only purge files that actually changed. Report the result of each purge call to the user.

## Important

- The changes must already be pushed to `main` on GitHub before purging, otherwise the CDN will re-cache the old version.
- jsDelivr allows ~3-4 purge calls per URL per hour. Do not retry excessively.
- If the user has not yet pushed, remind them to push first (or offer to push for them) before purging.
