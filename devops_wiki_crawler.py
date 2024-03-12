import base64
import json
from pathlib import Path

import aiohttp
import asyncio


class DevOpsWikiCrawler:
    def __init__(self, pat: str, organization: str, project: str):
        self.pat = pat
        self.organization = organization
        self.project = project

        authorization = str(base64.b64encode(bytes(":" + pat, "ascii")), "ascii")
        self.headers = {"Accept": "application/json", "Authorization": f"Basic {authorization}"}

    async def get_all_wikis(self) -> list[dict[str, str]]:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url=f"https://dev.azure.com/{self.organization}/{self.project}/_apis/wiki/wikis?api-version=6.0",
                headers=self.headers,
            ) as r:
                return (await r.json())["value"]

    async def get_all_pages_for_wiki(self, wiki_identifier: str) -> list[str]:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url=f"https://dev.azure.com/{self.organization}/{self.project}/_apis/wiki/wikis/{wiki_identifier}/pages?api-version=7.1-preview.1&recursionLevel=Full",
                headers=self.headers,
            ) as r:
                json_response = await r.json()

        def get_page_paths_from_tree(page: dict, paths: list[str]) -> list[str]:
            paths.append(page["path"])
            for sub_page in page.get("subPages", []):
                get_page_paths_from_tree(sub_page, paths)
            return paths

        return get_page_paths_from_tree(json_response, [])

    async def _get_path_content(self, path: str, wiki_identifier: str, session: aiohttp.ClientSession) -> dict[str, str]:
        base_url = f"https://dev.azure.com/{self.organization}/{self.project}/_apis/wiki/wikis/{wiki_identifier}/pages?path={{pagePath}}&api-version=7.1-preview.1&includeContent=true"
        url = base_url.format(pagePath=path)
        async with session.get(url, headers=self.headers) as resp:
            return {path: (await resp.json()).get("content", "")}

    async def get_all_page_contents_for_wiki(self, wiki_identifier: str, paths: list[str]) -> list[dict[str, str]]:
        tasks = []
        async with aiohttp.ClientSession() as session:
            for path in paths:
                tasks.append(asyncio.ensure_future(self._get_path_content(path, wiki_identifier, session)))
            return await asyncio.gather(*tasks)

    async def load_all_wikis_to_file(self, output_path: Path = Path.cwd() / "wikis"):
        for wiki in await self.get_all_wikis():
            wiki_identifier = wiki["name"]
            paths = await crawler.get_all_pages_for_wiki(wiki_identifier)

            contents = await crawler.get_all_page_contents_for_wiki(wiki_identifier, paths)
            output_path.mkdir(exist_ok=True)
            with open(output_path / (wiki_identifier + ".json"), "w") as f:
                json.dump(contents, f)
