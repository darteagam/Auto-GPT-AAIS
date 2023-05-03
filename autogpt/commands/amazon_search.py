"""Amazon Products Search command for Autogpt."""
from __future__ import annotations

from selectorlib import Extractor
import requests 
import json 
from time import sleep
from pathlib import Path
from autogpt.config import Config

import openai
from openai.error import APIError, RateLimitError

FILE_DIR = Path(__file__).parent.parent
CFG = Config()
openai.api_key = CFG.openai_api_key

# Create an Extractor by reading from the YAML file
e = Extractor.from_yaml_file('{FILE_DIR}/yml/search_results.yml')


def amazon_search(url: str, question: str) -> str:
    """Return the results of an Amazon products search

    Args:
        url (str): The url of the website to browse
        question (str): The question asked by the user

    Returns:
        str: The results of the Amazon products search.
    """
    data = scrape(url)
    search_params = extract_search_params(question)
    search_results = []
    if not query:
        return json.dumps(search_results)

    results = ddg(query, max_results=num_results)
    if not results:
        return json.dumps(search_results)

    for j in results:
        search_results.append(j)

    return json.dumps(search_results, ensure_ascii=False, indent=4)


def scrape(url: str) -> dict:
    """Scrape the search results from the Amazon website

    Args:
        url (str): The url of the website to scrape

    Returns:
        dict: The scraped search results
    """
    headers = {
        'dnt': '1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-user': '?1',
        'sec-fetch-dest': 'document',
        'referer': 'https://www.amazon.com/',
        'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
    }

    request_cnt = 0
    # Download the page using requests
    print('Downloading %s'%url)

    while True:
        request_cnt += 1
        print('Request #%d'%request_cnt)
        r = requests.get(url, headers=headers)
        # Simple check to check if page was blocked (Usually 503)
        if r.status_code > 500:
            if 'To discuss automated access to Amazon data please contact' in r.text:
                print('Page %s was blocked by Amazon. Please try using better proxies\n'%url)
            else:
                print('Page %s must have been blocked by Amazon as the status code was %d'%(url,r.status_code))
            sleep(2.5)
        else:
            return e.extract(r.text)


def extract_search_params(question: str) -> dict:
    """Extract the search parameters from the question asked by the user

    Args:
        question (str): The question asked by the user

    Returns:
        dict: The search parameters extracted from the question
    """
    response = None
    num_retries = 10
    for attempt in range(num_retries):
        backoff = 2 ** (attempt + 2)
        try:
            if CFG.use_azure:
                response = openai.ChatCompletion.create(
                    deployment_id=CFG.get_azure_deployment_id_for_model(model),
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            else:
                response = openai.ChatCompletion.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            break
        except RateLimitError:
            if CFG.debug_mode:
                print(
                    Fore.RED + "Error: ",
                    f"Reached rate limit, passing..." + Fore.RESET,
                )
        except APIError as e:
            if e.http_status == 502:
                pass
            else:
                raise
            if attempt == num_retries - 1:
                raise
        time.sleep(backoff)
    if response is None:
        raise RuntimeError(f"Failed to get response after {num_retries} retries")

    return response.choices[0].message["content"]