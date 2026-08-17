from typing import Any

from app.clients.github_rest import GitHubAPIError, _GitHubApiClient

_GRAPHQL_PATH = "/graphql"


class GitHubGraphQLClient(_GitHubApiClient):
    """Query GitHub GraphQL (e.g. Projects v2, milestones) with the app token."""

    async def run(self, query: str, variables: dict[str, Any] | None = None) -> dict:
        payload: dict[str, Any] = {"query": query}
        if variables:
            payload["variables"] = variables
        result = await self.request("POST", _GRAPHQL_PATH, json=payload)
        if not isinstance(result, dict):
            raise GitHubAPIError("GraphQL returned a non-object response")
        if result.get("errors"):
            raise GitHubAPIError(f"GraphQL errors: {result['errors']}")
        return result.get("data", {})
