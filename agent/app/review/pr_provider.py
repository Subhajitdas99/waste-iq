"""Pull request providers — GitHub (read-only) and built-in fixture.

The review agent only ever READS pull request data (metadata + diff). It
never posts comments, never merges, never writes. The provider returns
structured PullRequestData; files carry hunks parsed from the patch plus
full head content fetched read-only from the files API.
"""

from __future__ import annotations

import base64
import logging
import time
from typing import Any, Protocol

import httpx

from app.core.config import settings
from app.review.diff import parse_patch
from app.review.fixtures import demo_patch, demo_pull_request
from app.review.review_models import (
    ChangedFile,
    PullRequestData,
    ReviewError,
    ReviewUnavailable,
)

logger = logging.getLogger(__name__)

_RETRY_STATUSES = {429, 500, 502, 503, 504}
_MAX_RETRIES = 3
_DIFF_ACCEPT = "application/vnd.github.v3.diff"


class PullRequestProvider(Protocol):
    def get_pull_request(self, repo_full_name: str, number: int) -> PullRequestData: ...
    def get_patch(self, repo_full_name: str, number: int) -> str: ...
    def find_pull_request_for_head(
        self, repo_full_name: str, head_branch: str
    ) -> PullRequestData | None: ...


class GitHubPullRequestProvider:
    """Read-only GitHub provider using a PAT or installation token."""

    def __init__(
        self,
        token: str,
        base_url: str | None = None,
        timeout: float = 15.0,
        max_files: int | None = None,
    ) -> None:
        self._token = token
        self._base_url = (base_url or settings.agent_github_api_base_url).rstrip("/")
        self._timeout = timeout
        self._max_files = max_files or settings.agent_review_max_files

    def get_pull_request(self, repo_full_name: str, number: int) -> PullRequestData:
        diff = self.get_patch(repo_full_name, number)
        metadata = self._get_json(f"/repos/{repo_full_name}/pulls/{number}")
        files = self._fetch_files(repo_full_name, number, metadata.get("head", {}).get("sha"))
        if not files:
            files = parse_patch(diff)
        return PullRequestData(
            number=number,
            repo_full_name=repo_full_name,
            title=metadata.get("title") or "",
            branch=metadata.get("head", {}).get("ref"),
            base_branch=metadata.get("base", {}).get("ref"),
            commit_sha=metadata.get("head", {}).get("sha"),
            author=metadata.get("user", {}).get("login"),
            state=metadata.get("state"),
            diff=diff,
            files=files,
            raw=metadata,
        )

    def get_patch(self, repo_full_name: str, number: int) -> str:
        try:
            response = self._request(
                "GET", f"/repos/{repo_full_name}/pulls/{number}", headers={"Accept": _DIFF_ACCEPT}
            )
        except ReviewUnavailable:
            raise
        except ReviewError as exc:
            raise ReviewUnavailable(str(exc)) from exc
        return response.text

    def find_pull_request_for_head(
        self, repo_full_name: str, head_branch: str
    ) -> PullRequestData | None:
        response = self._get_json(
            f"/repos/{repo_full_name}/pulls", params={"state": "open", "per_page": 100}
        )
        for pull in response:
            if pull.get("head", {}).get("ref") == head_branch:
                return self.get_pull_request(repo_full_name, int(pull["number"]))
        return None

    # ------------------------------------------------------------------
    def _fetch_files(
        self, repo_full_name: str, number: int, head_sha: str | None
    ) -> list[ChangedFile]:
        response = self._get_json(
            f"/repos/{repo_full_name}/pulls/{number}/files", params={"per_page": 100}
        )
        files: list[ChangedFile] = []
        for entry in response[: self._max_files]:
            status = entry.get("status", "modified")
            changed = ChangedFile(path=entry.get("filename", ""), status=status)
            patch = entry.get("patch")
            if patch:
                parsed = parse_patch(f"diff --git a/{changed.path} b/{changed.path}\n" + patch)
                if parsed:
                    changed.hunks = parsed[0].hunks
            if status in ("added", "modified") and head_sha:
                changed.content = self._fetch_content(repo_full_name, changed.path, head_sha)
            files.append(changed)
        return files

    def _fetch_content(self, repo_full_name: str, path: str, head_sha: str) -> str | None:
        try:
            payload = self._get_json(
                f"/repos/{repo_full_name}/contents/{path}", params={"ref": head_sha}
            )
        except (ReviewUnavailable, ReviewError):
            logger.warning("content fetch failed path=%s", path, exc_info=True)
            return None
        if isinstance(payload, dict) and payload.get("encoding") == "base64":
            try:
                return base64.b64decode(payload["content"]).decode("utf-8")
            except (ValueError, UnicodeDecodeError):
                return None
        return None

    def _get_json(self, path: str, params: dict | None = None) -> Any:
        try:
            response = self._request("GET", path, params=params)
        except ReviewUnavailable:
            raise
        except ReviewError as exc:
            raise ReviewUnavailable(str(exc)) from exc
        return response.json()

    def _request(
        self, method: str, path: str, params: dict | None = None, headers: dict | None = None
    ) -> httpx.Response:
        url = f"{self._base_url}{path}"
        request_headers = {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            **(headers or {}),
        }
        last_error: Exception | None = None
        with httpx.Client(timeout=self._timeout) as client:
            for attempt in range(_MAX_RETRIES):
                try:
                    response = client.request(method, url, params=params, headers=request_headers)
                except httpx.HTTPError as exc:
                    last_error = exc
                    if attempt < _MAX_RETRIES - 1:
                        time.sleep(0.5 * (attempt + 1))
                        continue
                    break
                if response.status_code in _RETRY_STATUSES and attempt < _MAX_RETRIES - 1:
                    time.sleep(0.5 * (attempt + 1))
                    continue
                if response.status_code == 404:
                    raise ReviewUnavailable(f"pull request not found: {path}")
                if response.status_code >= 400:
                    raise ReviewError(f"github api error status={response.status_code} path={path}")
                return response
        raise ReviewError(f"github api unreachable: {last_error}")


class FixturePullRequestProvider:
    """Serves the built-in demo PR — used in tests and local smoke runs."""

    def get_pull_request(self, repo_full_name: str, number: int) -> PullRequestData:
        if number != 1:
            raise ReviewUnavailable(f"fixture pull request not found: {repo_full_name}#{number}")
        return demo_pull_request(repo_full_name)

    def get_patch(self, repo_full_name: str, number: int) -> str:
        return demo_patch()

    def find_pull_request_for_head(
        self, repo_full_name: str, head_branch: str
    ) -> PullRequestData | None:
        from app.review.fixtures import DEMO_BRANCH

        if head_branch == DEMO_BRANCH:
            return demo_pull_request(repo_full_name)
        return None
