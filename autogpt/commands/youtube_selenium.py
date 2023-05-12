"""Selenium web scraping module."""
from __future__ import annotations

import logging
import time
from pathlib import Path
from sys import platform

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.safari.options import Options as SafariOptions
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager

import openai
from openai.error import APIError, RateLimitError, Timeout

import autogpt.processing.text as summary
from autogpt.commands.command import command
from autogpt.config.nconfig import Config
from autogpt.processing.html import extract_hyperlinks, format_hyperlinks
from autogpt.url_utils.validators import validate_url

FILE_DIR = Path(__file__).parent.parent
CFG = Config()


@command(
    "youtube_search",
    "YouTube Search",
    '"search_description": "<description_of_YouTube_search>"',
)
def youtube_search(search_description: str) -> str:#list[str]
    """Browse YouTube and return a list with two links:
        - link of the first video result (according to a set of filters)
        - link of search result

    Args:
        search_description (str): The description of the YouTube search given by the user

    Returns:
        List[str]: The list with the link of the first video result and the link of search result
    """
    num_retries = 10
    warned_user = False
    print('Creating completion model')
    response = None
    for attempt in range(num_retries):
        backoff = 2 ** (attempt + 2)
        try:
            response = openai.Completion.create(
                model="text-davinci-003",
                prompt='Extract the topic of the search, the publishing date and duration of the video, '
                       'as well as the result sorting criteria from this text. Show the information as a'
                       ' Python dictionary with the keys "topic", "date", "duration" and "criteria". For'
                       ' missing values use "None":\n\n' + search_description + '\n\n{"topic":}:',
                temperature=CFG.temperature,
                max_tokens=100,
                # api_key=CFG.openai_api_key,
            )
            print('Response: ', response)
            print('prompt_tokens: ', response.usage.prompt_tokens)
            print('completion_tokens: ', response.usage.completion_tokens)
            break
        except RateLimitError:
            print('Error: Reached rate limit')
            if not warned_user:
                print(
                      'Please double check that you have setup a PAID OpenAI API Account. '
                      'You can read more here: https://docs.agpt.co/setup/#getting-an-api-key'
                     )
                warned_user = True
        except (APIError, Timeout) as e:
            if e.http_status != 502:
                raise
            if attempt == num_retries - 1:
                raise
        print('Error: API Bad gateway. Waiting ' + backoff + ' seconds...')
        time.sleep(backoff)
    if response is None:
        print(
              "FAILED TO GET RESPONSE FROM OPENAI, Auto-GPT has failed to get a response from OpenAI's services. "
              "Try running Auto-GPT again, and if the problem the persists try running it with `--debug`."
             )
        if CFG.debug_mode:
            raise RuntimeError(f"Failed to get response after {num_retries} retries")
        else:
            quit(1)
    resp = '{"topic":' + response.choices[0].text
    print(resp)
    search_params = resp
    try:
        driver, text = scrape_text_with_selenium(url)
    except WebDriverException as e:
        # These errors are often quite long and include lots of context.
        # Just grab the first line.
        msg = e.msg.split("\n")[0]
        return f"Error: {msg}", None

    add_header(driver)
    summary_text = summary.summarize_text(url, text, question, driver)
    links = scrape_links_with_selenium(driver, url)

    # Limit links to 5
    if len(links) > 5:
        links = links[:5]
    close_browser(driver)
    return resp


def scrape_text_with_selenium(url: str) -> tuple[WebDriver, str]:
    """Scrape text from a website using selenium

    Args:
        url (str): The url of the website to scrape

    Returns:
        Tuple[WebDriver, str]: The webdriver and the text scraped from the website
    """
    logging.getLogger("selenium").setLevel(logging.CRITICAL)

    options_available = {
        "chrome": ChromeOptions,
        "safari": SafariOptions,
        "firefox": FirefoxOptions,
    }

    options = options_available[CFG.selenium_web_browser]()
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.5615.49 Safari/537.36"
    )

    if CFG.selenium_web_browser == "firefox":
        if CFG.selenium_headless:
            options.headless = True
            options.add_argument("--disable-gpu")
        driver = webdriver.Firefox(
            executable_path=GeckoDriverManager().install(), options=options
        )
    elif CFG.selenium_web_browser == "safari":
        # Requires a bit more setup on the users end
        # See https://developer.apple.com/documentation/webkit/testing_with_webdriver_in_safari
        driver = webdriver.Safari(options=options)
    else:
        if platform == "linux" or platform == "linux2":
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--remote-debugging-port=9222")

        options.add_argument("--no-sandbox")
        if CFG.selenium_headless:
            options.add_argument("--headless=new")
            options.add_argument("--disable-gpu")

        chromium_driver_path = Path("/usr/bin/chromedriver")

        driver = webdriver.Chrome(
            executable_path=chromium_driver_path
            if chromium_driver_path.exists()
            else ChromeDriverManager().install(),
            options=options,
        )
    driver.get(url)

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    # Get the HTML content directly from the browser's DOM
    page_source = driver.execute_script("return document.body.outerHTML;")
    soup = BeautifulSoup(page_source, "html.parser")

    for script in soup(["script", "style"]):
        script.extract()

    text = soup.get_text()
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = "\n".join(chunk for chunk in chunks if chunk)
    return driver, text


def scrape_links_with_selenium(driver: WebDriver, url: str) -> list[str]:
    """Scrape links from a website using selenium

    Args:
        driver (WebDriver): The webdriver to use to scrape the links

    Returns:
        List[str]: The links scraped from the website
    """
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, "html.parser")

    for script in soup(["script", "style"]):
        script.extract()

    hyperlinks = extract_hyperlinks(soup, url)

    return format_hyperlinks(hyperlinks)


def close_browser(driver: WebDriver) -> None:
    """Close the browser

    Args:
        driver (WebDriver): The webdriver to close

    Returns:
        None
    """
    driver.quit()


def add_header(driver: WebDriver) -> None:
    """Add a header to the website

    Args:
        driver (WebDriver): The webdriver to use to add the header

    Returns:
        None
    """
    try:
        with open(f"{FILE_DIR}/js/overlay.js", "r") as overlay_file:
            overlay_script = overlay_file.read()
        driver.execute_script(overlay_script)
    except Exception as e:
        print(f"Error executing overlay.js: {e}")


if __name__ == "__main__":
    r = youtube_search('Play the first dota 2 video of less than 5 minutes length sorted by views')