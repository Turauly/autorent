# Branching Strategy

We use a simple Git workflow:

- `main` is always stable and deployable.
- Feature work goes to `feature/<short-name>` branches.
- Bugfixes go to `fix/<short-name>` branches.

Rules:
- Create a pull request into `main`.
- Use small, focused PRs.
- Squash merge is preferred for clean history.
