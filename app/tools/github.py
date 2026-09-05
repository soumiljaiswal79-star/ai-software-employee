from __future__ import annotations

import os
import re
from typing import Any

from github import Github
from github.GithubException import GithubException


def _error(message: str) -> dict[str, Any]:
    return {
        "error": message,
    }


def _get_client() -> Github | None:
    token = os.getenv("GITHUB_TOKEN")

    if not token:
        return None

    return Github(token)


def _valid_branch_name(branch: str) -> bool:
    """Allow safe GitHub branch names."""
    return bool(
        branch
        and len(branch) <= 200
        and re.fullmatch(r"[A-Za-z0-9._/-]+", branch)
        and not branch.startswith("/")
        and not branch.endswith("/")
        and ".." not in branch
    )


def github_auth_status() -> dict[str, Any]:
    """Verify that the GitHub token works without exposing the token."""
    github = _get_client()

    if github is None:
        return _error("GITHUB_TOKEN is not configured.")

    try:
        user = github.get_user()

        return {
            "authenticated": True,
            "username": user.login,
        }

    except GithubException:
        return _error("GitHub authentication failed.")


def github_get_repository(
    owner: str,
    repository: str,
) -> dict[str, Any]:
    """Check access to a GitHub repository."""
    if not owner or not repository:
        return _error("Repository owner and name are required.")

    github = _get_client()

    if github is None:
        return _error("GITHUB_TOKEN is not configured.")

    try:
        repo = github.get_repo(f"{owner}/{repository}")

        return {
            "accessible": True,
            "owner": repo.owner.login,
            "repository": repo.name,
            "default_branch": repo.default_branch,
            "private": repo.private,
            "url": repo.html_url,
        }

    except GithubException:
        return _error("Unable to access the GitHub repository.")


def github_get_branch(
    owner: str,
    repository: str,
    branch: str,
) -> dict[str, Any]:
    """Get information about a GitHub branch."""
    if not owner or not repository or not branch:
        return _error("Owner, repository, and branch are required.")

    github = _get_client()

    if github is None:
        return _error("GITHUB_TOKEN is not configured.")

    try:
        repo = github.get_repo(f"{owner}/{repository}")
        git_branch = repo.get_branch(branch)

        return {
            "exists": True,
            "branch": git_branch.name,
            "sha": git_branch.commit.sha,
        }

    except GithubException as error:
        if getattr(error, "status", None) == 404:
            return {
                "exists": False,
                "branch": branch,
            }

        return _error("Unable to access the GitHub branch.")


def github_create_branch(
    owner: str,
    repository: str,
    branch: str,
    from_branch: str = "main",
) -> dict[str, Any]:
    """Create a GitHub branch from an existing branch."""
    if not owner or not repository:
        return _error("Repository owner and name are required.")

    if not _valid_branch_name(branch):
        return _error("Invalid branch name.")

    if not _valid_branch_name(from_branch):
        return _error("Invalid source branch name.")

    if branch == from_branch:
        return _error("New branch must be different from source branch.")

    github = _get_client()

    if github is None:
        return _error("GITHUB_TOKEN is not configured.")

    try:
        repo = github.get_repo(f"{owner}/{repository}")

        source = repo.get_branch(from_branch)

        try:
            repo.get_branch(branch)

            return _error(f"Branch '{branch}' already exists.")

        except GithubException as error:
            if getattr(error, "status", None) != 404:
                return _error("Unable to check whether the branch exists.")

        repo.create_git_ref(
            ref=f"refs/heads/{branch}",
            sha=source.commit.sha,
        )

        return {
            "created": True,
            "branch": branch,
            "from_branch": from_branch,
            "sha": source.commit.sha,
            "url": f"{repo.html_url}/tree/{branch}",
        }

    except GithubException:
        return _error("Unable to create GitHub branch.")