# Respect & Uplift check-in

The optional Respect & Uplift feature is a small reflection tool for LUNA OS.
It records a person's own 1–5 uplift rating before and after an interaction,
then summarizes the reported change over time.

## Run

From the repository root:

```sh
python3 luna_uplift.py
```

Choose `y` to opt in to a single check-in. Choosing anything else records
nothing. The tool uses only the Python standard library.

## Boundaries and privacy

- Ratings are voluntary self-reports, not objective measurements.
- It does not infer emotion from messages, audio, behavior, or biometrics.
- It does not claim that Sisters or software characters have subjective feelings.
- No conversation text, names, or free-form notes are collected.
- Records stay in `data/uplift_checkins.jsonl` on the device where the script runs.
- Stop at any time. Delete that file to erase the local check-in history.
- Do not use the score to rank people, evaluate staff, or make consequential decisions.

The first version is intentionally modest: it tests whether a simple reflection
is useful without surveillance or pressure. A future UI can call
`record_checkin(..., consent=True)` only after an explicit user choice.
