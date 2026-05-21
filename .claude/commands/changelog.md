# changelog

Maintain CHANGELOG.md in the project root with date headings and commit-based bullets.

## Steps

1. **Check for CHANGELOG.md** at the project root.

2. **If CHANGELOG.md does not exist:**
   - Run `git log --pretty=format:"%ad %s" --date=short` to get all commits with dates.
   - Group commits by date (YYYY-MM-DD).
   - Write CHANGELOG.md with this structure:
     ```
     # Changelog

     ## YYYY-MM-DD
     - <commit subject>
     - <commit subject>

     ## YYYY-MM-DD
     - <commit subject>
     ```
   - Dates should be in descending order (newest first).
   - Exclude merge commits (`--no-merges`) and the initial scaffold commit if it is clearly just "initial commit" or "Initial commit".

3. **If CHANGELOG.md already exists:**
   - Parse the most recent date heading in the file (format `## YYYY-MM-DD`).
   - Run `git log --pretty=format:"%ad %s" --date=short --no-merges --after="<most recent date>"` to find commits made after that date.
   - If there are new commits:
     - Group them by date.
     - Prepend new date sections at the top of the changelog (after the `# Changelog` title line), newest date first.
   - If there are no new commits, report that the changelog is already up to date.

4. **Formatting rules:**
   - Title: `# Changelog`
   - Date headings: `## YYYY-MM-DD`
   - Bullets: `- ` prefix, sentence-case, no trailing period.
   - One blank line between sections.
   - Do not duplicate entries already present in the file.

5. **After writing or updating the file**, show the user a summary of what was added (e.g., "Added 3 entries under 2026-05-21").
