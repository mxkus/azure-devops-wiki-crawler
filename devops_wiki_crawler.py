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
        """Get all wikis for the project

        Returns:
            list[dict[str, str]]: List of wikis
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url=f"https://dev.azure.com/{self.organization}/{self.project}/_apis/wiki/wikis?api-version=6.0",
                headers=self.headers,
            ) as r:
                return (await r.json())["value"]

    async def get_all_pages_for_wiki(self, wiki_identifier: str) -> list[str]:
        """Get all pages for a wiki

        Args:
            wiki_identifier (str): The identifier of the wiki

        Returns:
            list[str]: List of paths for the pages in the wiki
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url=f"https://dev.azure.com/{self.organization}/{self.project}/_apis/wiki/wikis/{wiki_identifier}/pages?api-version=7.1-preview.1&recursionLevel=Full",
                headers=self.headers,
            ) as r:
                json_response = await r.json()

        def get_page_paths_from_tree(page: dict, paths: list[str]) -> list[str]:
            """Helper function to parse the page tree and get all the paths

            Args:
                page (dict): root page
                paths (list[str]): list of current paths

            Returns:
                list[str]: list of paths
            """
            paths.append(page["path"])
            for sub_page in page.get("subPages", []):
                get_page_paths_from_tree(sub_page, paths)
            return paths

        return get_page_paths_from_tree(json_response, [])

    async def _get_path_content(self, path: str, wiki_identifier: str, session: aiohttp.ClientSession) -> dict[str, str]:
        """Get the content of a page

        Args:
            path (str): The path of the page
            wiki_identifier (str): The identifier of the wiki
            session (aiohttp.ClientSession): The aiohttp session

        Returns:
            dict[str, str]: The markdown content of the page with the path as the key
        """
        base_url = f"https://dev.azure.com/{self.organization}/{self.project}/_apis/wiki/wikis/{wiki_identifier}/pages?path={{pagePath}}&api-version=7.1-preview.1&includeContent=true"
        url = base_url.format(pagePath=path)
        async with session.get(url, headers=self.headers) as resp:
            return {path: (await resp.json()).get("content", "")}

    async def get_all_page_contents_for_wiki(self, wiki_identifier: str, paths: list[str]) -> list[dict[str, str]]:
        """Get the content of all pages in a wiki

        Args:
            wiki_identifier (str): The identifier of the wiki
            paths (list[str]): List of paths for the pages in the wiki

        Returns:
            list[dict[str, str]]: List of dictionaries with the content of the pages
        """
        tasks = []
        async with aiohttp.ClientSession() as session:
            for path in paths:
                tasks.append(asyncio.ensure_future(self._get_path_content(path, wiki_identifier, session)))
            return await asyncio.gather(*tasks)

    async def load_all_wikis_to_file(self, output_path: Path = Path.cwd() / "wikis") -> None:
        """Load all wikis to a one file per wiki

        Args:
            output_path (Path, optional): The path for saving the pages. Defaults to $CWD/"wikis".
        """
        for wiki in await self.get_all_wikis():
            wiki_identifier = wiki["name"]
            paths = await self.get_all_pages_for_wiki(wiki_identifier)

            contents = await self.get_all_page_contents_for_wiki(wiki_identifier, paths)
            output_path.mkdir(exist_ok=True)
            with open(output_path / (wiki_identifier + ".json"), "w") as f:
                json.dump(contents, f)
