# How to contribute?

Thank you for considering contributing to Artisan. It’s people like you that make Artisan such a valuable tool.

Our vision is to offer a roast logging and evaluation software accessible to every roast master. For this, Artisan needs to run on all major platforms and connecting to all hardware and roasting machines in use. Its UI needs to be comprehensive, available in many languages and designed such that it can be adjusted to many use cases by non-programmers. To be a sustainable, the project needs a lively community of users and companies which support it.

We are looking for contributions of [ideas](https://github.com/artisan-roaster-scope/artisan/issues), [translations](https://github.com/artisan-roaster-scope/artisan/issues), [bug reports](https://github.com/artisan-roaster-scope/artisan/issues), [dicussions](https://github.com/artisan-roaster-scope/artisan/discussions), [documentation](https://artisan-scope.org/docs/quick-start-guide/), [code](https://github.com/artisan-roaster-scope/artisan) and [money](https://artisan-scope.org/donate/).

First read our [Code of Conduct](CODE_OF_CONDUCT.md) to keep our community approachable and respectable.

In this guide you will get an overview of the contribution workflow from opening an issue, creating a PR, reviewing, and merging the PR.

## Did you find a bug or got an idea?

### Create a new issue

If you spot a problem or you have a feature request, search if an issue already exists. If a related issue doesn't exist, you can open a new issue using the issue form under [`Issues`](https://github.com/artisan-roaster-scope/artisan/issues).

### Solve an issue

Scan through our existing issues to find one that interests you. You can narrow down the search using labels as filters. As a general rule, we don’t assign issues to anyone. If you find an issue to work on, you are welcome to open a PR with a fix.

- Fork the repository so that you can make your changes without affecting the original project until you're ready to merge them.
- Create a working branch and start with your changes!


## Pull Request (PR)

When you're finished with the changes, create a [pull request](https://github.com/artisan-roaster-scope/artisan/pulls), also known as a PR incl. a description that allows reviewers understand your changes as well as the purpose of your pull request. Don't forget to link PR to issue if you are solving one.

Enable the checkbox to allow maintainer edits so the branch can be updated for a merge. Once you submit your PR, an Artisan team member will review your proposal. We may ask questions or request additional information.

We may ask for changes to be made before a PR can be merged, either using suggested changes or pull request comments. You can apply suggested changes directly through the UI. You can make any other changes in your fork, then commit them to your branch.

As you update your PR and apply changes, mark each conversation as resolved.
If you run into any merge issues, checkout this git tutorial to help you resolve merge conflicts and other issues.


## Coding conventions

We are using the code analyzer [ruff](https://github.com/astral-sh/ruff) and [pylint](https://github.com/pylint-dev/pylint) and the type checkers [mypy](https://github.com/python/mypy) and [pyright](https://github.com/microsoft/pyright) to verify code quality as configured in [`src/pyproject.toml`](https://github.com/artisan-roaster-scope/artisan/blob/master/src/pyproject.toml).
