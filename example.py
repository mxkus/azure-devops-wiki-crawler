import os
from dotenv import load_dotenv
import asyncio

from devops_wiki_crawler import DevOpsWikiCrawler


if __name__ == "__main__":
    load_dotenv()

    pat = os.environ["AZURE_DEVOPS_PAT"]
    organization = os.environ["ORGANIZATION"]
    project = os.environ["PROJECT"]
    crawler = DevOpsWikiCrawler(pat, organization, project)
    asyncio.run(crawler.load_all_wikis_to_file())
