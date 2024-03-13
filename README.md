# azure-devops-wiki
An asynchronous azure devops wiki crawler.

## Prerequisites
* Python 3.x

* Install aiohttp as http client:
`pip install aiohttp`

or

`poetry install`

* An azure devops PAT: https://learn.microsoft.com/en-us/azure/devops/organizations/accounts/use-personal-access-tokens-to-authenticate?view=azure-devops&tabs=Windows

## Examples

Here are a few examples to help you get started with the Azure DevOps Wiki Crawler:

### Example 1: Crawling a Wiki

To crawl all possible wikis, you can use the following code snippet:

```python
from devops_wiki_crawler import DevOpsWikiCrawler
import os


pat = os.environ["AZURE_DEVOPS_PAT"]  # your azure devops pat token
organization = os.environ["ORGANIZATION"]
project = os.environ["PROJECT"]
crawler = DevOpsWikiCrawler(pat, organization, project)
asyncio.run(crawler.load_all_wikis_to_file())
```
