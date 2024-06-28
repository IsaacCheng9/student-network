# Contributing to Student Network

## Reporting Issues

We use
[GitHub Projects as a Kanban board](https://github.com/IsaacCheng9/student-network/projects/1)
and integrate the GitHub Issues feature to track the progress of tasks and
related pull requests - remember to link the issue to the Kanban board.

Include the following information when reporting an issue (where possible):

- Breakdown of the problem
- Expected changes
- Reproducible steps (if reporting a bug)

The `high priority` label should be sparingly to avoid diluting its
significance - overuse of this defeats the purpose of the label.

## Project Structure

This project uses _Flask Blueprints_ to organise the application (more info
[here](https://exploreflask.com/en/latest/blueprints.html)).

We use a _functional structure_, where pieces of the application are organised
by what they do (further explanation using Facebook as an example
[here](https://exploreflask.com/en/latest/blueprints.html#which-one-is-best)).
Each Python file in the [/views/](src/student_network/views) directory represents a
blueprint, which is registered in the main application in
[app.py](src/student_network/app.py).

## Pull Requests

Include the following information when submitting a pull request:

- Overview of the changes
  - Where needed, add explanations about what the changes will effect and why
    they were made.
- Related issues
  - Using the `This fixes {link to issue}` syntax will automatically close the
    issue once merged.

## Unit Tests

Unit tests should be created and maintained as changes are made to the core
functionality to improve maintainability.

We use the _Pytest_ framework for this, which has been integrated into GitHub
Actions for automated unit testing (see below).

## GitHub Actions

After pushing to the repository, the workflow in GitHub Actions consists of:

- Running Python code formatting with _Black_
  - This ensures good readability and a consistent style across the codebase to
    reduce diffs for code reviews.
- Running all unit tests for Python with _Pytest_
  - This helps prevent runtime errors in production.
  - Test should be created and kept updated to facilitate this.
