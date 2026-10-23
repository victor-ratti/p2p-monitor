# Prompts

One file per version of the judge's system prompt: `judge_v1.md`, `judge_v2.md`, ... Never edit a version in place:
copy it, change ONE thing, and replay the evals (`python evals/run.py --prompt v2`). A prompt is a specification;
the eval results in `evals/results/` are its proof.
