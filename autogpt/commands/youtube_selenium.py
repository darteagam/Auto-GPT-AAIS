"""YouTube search module."""
from __future__ import annotations

# import logging
import time
from pathlib import Path
from sys import platform

# from bs4 import BeautifulSoup
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

# import autogpt.processing.text as summary
from autogpt.commands.command import command
from autogpt.config.nconfig import Config
# from autogpt.processing.html import extract_hyperlinks, format_hyperlinks
from autogpt.url_utils.validators import validate_url

FILE_DIR = Path(__file__).parent.parent
CFG = Config()


@command(
    "youtube_search",
    "YouTube Search",
    '"search_description": "<description_of_YouTube_search>"',
)
def youtube_search(search_description: str) -> list[str]:
    """Browse YouTube and return a list with two links:
        - link of the first video result (according to a set of filters)
        - link of search result

    Args:
        search_description (str): The description of the YouTube search given by the user

    Returns:
        list[str]: The list with the link of the first video result and the link of search result
    """
    search_params = extract_youtube_search_params(search_description)
    
    # options_available = {
    #         "chrome": ChromeOptions,
    #         "safari": SafariOptions,
    #         "firefox": FirefoxOptions,
    # }

    # options = options_available[CFG.selenium_web_browser]()
    # options.add_argument(
    #     "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.5615.49 Safari/537.36"
    # )

    # if CFG.selenium_web_browser == "firefox":
    #     if CFG.selenium_headless:
    #         options.headless = True
    #         options.add_argument("--disable-gpu")
    #     driver = webdriver.Firefox(
    #         executable_path=GeckoDriverManager().install(), options=options
    #     )
    # elif CFG.selenium_web_browser == "safari":
    #     # Requires a bit more setup on the users end
    #     # See https://developer.apple.com/documentation/webkit/testing_with_webdriver_in_safari
    #     driver = webdriver.Safari(options=options)
    # else:
    #     if platform == "linux" or platform == "linux2":
    #         options.add_argument("--disable-dev-shm-usage")
    #         options.add_argument("--remote-debugging-port=9222")

    #     options.add_argument("--no-sandbox")
    #     if CFG.selenium_headless:
    #         # options.add_argument("--headless=new")
    #         options.add_argument("--disable-gpu")

    #     chromium_driver_path = Path("/usr/bin/chromedriver")

    #     driver = webdriver.Chrome(
    #         executable_path=chromium_driver_path
    #         if chromium_driver_path.exists()
    #         else ChromeDriverManager().install(),
    #         options=options,
    #     )
    # driver.get('https://www.youtube.com/')
    
    # WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '/html/body/ytd-app/div[1]/div/ytd-masthead/div[4]/div[2]/ytd-searchbox/form/div[1]/div[1]/input')))
    # searchbox = driver.find_element(By.XPATH, '/html/body/ytd-app/div[1]/div/ytd-masthead/div[4]/div[2]/ytd-searchbox/form/div[1]/div[1]/input')
    # searchbox.send_keys(search_params['topic'])
    # searchButton = driver.find_element(By.XPATH, '/html/body/ytd-app/div[1]/div/ytd-masthead/div[4]/div[2]/ytd-searchbox/button')
    # searchButton.click()

    # WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '/html/body/ytd-app/div[1]/ytd-page-manager/ytd-search/div[1]/ytd-two-column-search-results-renderer/div/ytd-section-list-renderer/div[1]/div[2]/ytd-search-sub-menu-renderer/div/div/ytd-toggle-button-renderer/yt-button-shape/button')))
    # # filterButton = driver.find_element(By.CSS_SELECTOR, "ytd-toggle-button-renderer.ytd-search-sub-menu-renderer")
    # filterButton = driver.find_element(By.XPATH, '/html/body/ytd-app/div[1]/ytd-page-manager/ytd-search/div[1]/ytd-two-column-search-results-renderer/div/ytd-section-list-renderer/div[1]/div[2]/ytd-search-sub-menu-renderer/div/div/ytd-toggle-button-renderer/yt-button-shape/button')
    # filterButton.click()
    # f11 = driver.find_element(By.XPATH, '/html/body/ytd-app/div[1]/ytd-page-manager/ytd-search/div[1]/ytd-two-column-search-results-renderer/div/ytd-section-list-renderer/div[1]/div[2]/ytd-search-sub-menu-renderer/div/iron-collapse/div/ytd-search-filter-group-renderer[1]/ytd-search-filter-renderer[2]/a/div/yt-formatted-string')
    # # f11 = driver.find_element(By.CSS_SELECTOR, "ytd-search-filter-group-renderer.style-scope:nth-child(1) > ytd-search-filter-renderer:nth-child(2) > a:nth-child(1)")
    # f11.click()

    # WebDriverWait(driver, 10).until(EC.visibility_of_all_elements_located)
    # # WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.ID, 'thumbnail')))
    # url = driver.current_url
    # print(url)
    # video = driver.find_element(By.XPATH, '/html/body/ytd-app/div[1]/ytd-page-manager/ytd-search/div[1]/ytd-two-column-search-results-renderer/div/ytd-section-list-renderer/div[2]/ytd-item-section-renderer/div[3]/ytd-video-renderer[1]/div[1]/div/div[1]/div/h3/a')
    # print(video.get_attribute('href'))
    # # videos = driver.find_elements(By.ID, 'thumbnail')
    # # for video in videos:
    # #     print(video.get_attribute('href'))
    # # for video in videos:
    # #     # link = video.find_element(By.XPATH, '/html/body/ytd-app/div[1]/ytd-page-manager/ytd-search/div[1]/ytd-two-column-search-results-renderer/div/ytd-section-list-renderer/div[2]/ytd-item-section-renderer/div[3]/ytd-video-renderer[1]/div[1]/div/div[1]/div/h3/a')
    # #     #                                     '/html/body/ytd-app/div[1]/ytd-page-manager/ytd-search/div[1]/ytd-two-column-search-results-renderer/div/ytd-section-list-renderer/div[2]/ytd-item-section-renderer/div[3]/ytd-video-renderer[2]/div[1]/div/div[1]/div/h3/a'
    # #     #                                     '/html/body/ytd-app/div[1]/ytd-page-manager/ytd-search/div[1]/ytd-two-column-search-results-renderer/div/ytd-section-list-renderer/div[2]/ytd-item-section-renderer/div[3]/ytd-video-renderer[1]/div[1]/div/div[1]/div/h3/a'
    # #                                         # '//*[@id="video-title"]'
    # #     link = video.find_element(By.XPATH, './/a[@id="video-title"]')
    # #     print(link.get_attribute('href'))
    # print('done!')

    try:
        urls = get_youtube_video_with_selenium(search_params)
    except WebDriverException as e:
        # These errors are often quite long and include lots of context.
        # Just grab the first line.
        msg = e.msg.split("\n")[0]
        return f"Error: {msg}", None
    print(urls)
    return urls


def extract_youtube_search_params(search_description: str) -> dict[str, str]:
    """Extract parameters for a YouTube search

    Args:
        search_description (str): The description of the YouTube search given by the user

    Returns:
        dict[str, str]: The search parameters in dictionary format (param_name: param_value)
    """
    num_retries = 10
    warned_user = False
    # print('Creating completion model')
    response = None
    for attempt in range(num_retries):
        backoff = 2 ** (attempt + 2)
        try:
            response = openai.Completion.create(
                model="text-davinci-003",
                prompt='Extract the topic of the search, the publishing date and duration of the video, '
                       'as well as the result sorting criteria from this text. Show the information as a'
                       ' Python dictionary with the keys "topic", "date", "duration" and "criterion". For'
                       ' missing values use "None":\n\n' + search_description + '\n\n{"topic":}:',
                temperature=CFG.temperature,
                max_tokens=100,
            )
            # print('Response: ', response)
            # print('prompt_tokens: ', response.usage.prompt_tokens)
            # print('completion_tokens: ', response.usage.completion_tokens)
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
    search_params = eval(resp)
    
    return search_params


def get_youtube_video_with_selenium(search_params: dict[str, str]) -> list[str]:
    """Get YouTube video link using selenium

    Args:
        search_params (dict[str, str]): The search parameters in dictionary format (param_name: param_value)

    Returns:
        list[str]: The list with the link of the first video result and the link of search result
    """
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
    
    # Browse to YouTube website
    driver.get('https://www.youtube.com/')
    
    # Enter search topic and click on the search button
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '/html/body/ytd-app/div[1]/div/ytd-masthead/div[4]/div[2]/ytd-searchbox/form/div[1]/div[1]/input')))
    searchbox = driver.find_element(By.XPATH, '/html/body/ytd-app/div[1]/div/ytd-masthead/div[4]/div[2]/ytd-searchbox/form/div[1]/div[1]/input')
    searchbox.send_keys(search_params['topic'])
    searchButton = driver.find_element(By.XPATH, '/html/body/ytd-app/div[1]/div/ytd-masthead/div[4]/div[2]/ytd-searchbox/button')
    searchButton.click()

    # Click on filter button
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '/html/body/ytd-app/div[1]/ytd-page-manager/ytd-search/div[1]/ytd-two-column-search-results-renderer/div/ytd-section-list-renderer/div[1]/div[2]/ytd-search-sub-menu-renderer/div/div/ytd-toggle-button-renderer/yt-button-shape/button')))
    filterButton = driver.find_element(By.XPATH, '/html/body/ytd-app/div[1]/ytd-page-manager/ytd-search/div[1]/ytd-two-column-search-results-renderer/div/ytd-section-list-renderer/div[1]/div[2]/ytd-search-sub-menu-renderer/div/div/ytd-toggle-button-renderer/yt-button-shape/button')
    filterButton.click()

    # Select the filters
    apply_youtube_filters(search_params, driver)
    
    # Get the URL of the search result
    search_result_url = driver.current_url

    # Get the URL of the first video result
    video = driver.find_element(By.XPATH, '/html/body/ytd-app/div[1]/ytd-page-manager/ytd-search/div[1]/ytd-two-column-search-results-renderer/div/ytd-section-list-renderer/div[2]/ytd-item-section-renderer/div[3]/ytd-video-renderer[1]/div[1]/div/div[1]/div/h3/a')
    video_url = video.get_attribute('href')

    # Close the webdriver
    close_browser(driver)

    return [search_result_url, video_url]


def apply_youtube_filters(search_params: dict[str, str], driver: WebDriver) -> None:
    """Apply filters to YouTube search using selenium

    Args:
        search_params (dict[str, str]): The search parameters in dictionary format (param_name: param_value)
        driver (WebDriver): The webdriver to use to scrape the links
    """
    # Select the upload date filter
    if 'date' in search_params.keys():
        if search_params['date'] == 'last hour':
            f = driver.find_element(By.XPATH, '/html/body/ytd-app/div[1]/ytd-page-manager/ytd-search/div[1]/ytd-two-column-search-results-renderer/div/ytd-section-list-renderer/div[1]/div[2]/ytd-search-sub-menu-renderer/div/iron-collapse/div/ytd-search-filter-group-renderer[1]/ytd-search-filter-renderer[1]/a/div/yt-formatted-string')
            f.click()
        elif search_params['date'] == 'today':
            f = driver.find_element(By.XPATH, '/html/body/ytd-app/div[1]/ytd-page-manager/ytd-search/div[1]/ytd-two-column-search-results-renderer/div/ytd-section-list-renderer/div[1]/div[2]/ytd-search-sub-menu-renderer/div/iron-collapse/div/ytd-search-filter-group-renderer[1]/ytd-search-filter-renderer[2]/a/div/yt-formatted-string')
            f.click()
        elif search_params['date'] == 'this week':
            f = driver.find_element(By.XPATH, '/html/body/ytd-app/div[1]/ytd-page-manager/ytd-search/div[1]/ytd-two-column-search-results-renderer/div/ytd-section-list-renderer/div[1]/div[2]/ytd-search-sub-menu-renderer/div/iron-collapse/div/ytd-search-filter-group-renderer[1]/ytd-search-filter-renderer[3]/a/div/yt-formatted-string')
            f.click()
        elif search_params['date'] == 'this month':
            f = driver.find_element(By.XPATH, '/html/body/ytd-app/div[1]/ytd-page-manager/ytd-search/div[1]/ytd-two-column-search-results-renderer/div/ytd-section-list-renderer/div[1]/div[2]/ytd-search-sub-menu-renderer/div/iron-collapse/div/ytd-search-filter-group-renderer[1]/ytd-search-filter-renderer[4]/a/div/yt-formatted-string')
            f.click()
        elif search_params['date'] == 'this year':
            f = driver.find_element(By.XPATH, '/html/body/ytd-app/div[1]/ytd-page-manager/ytd-search/div[1]/ytd-two-column-search-results-renderer/div/ytd-section-list-renderer/div[1]/div[2]/ytd-search-sub-menu-renderer/div/iron-collapse/div/ytd-search-filter-group-renderer[1]/ytd-search-filter-renderer[5]/a/div/yt-formatted-string')
            f.click()

    # Select the duration filter
    if 'duration' in search_params.keys():
        if search_params['duration'] == 'less than 4 minutes':
            f = driver.find_element(By.XPATH, '/html/body/ytd-app/div[1]/ytd-page-manager/ytd-search/div[1]/ytd-two-column-search-results-renderer/div/ytd-section-list-renderer/div[1]/div[2]/ytd-search-sub-menu-renderer/div/iron-collapse/div/ytd-search-filter-group-renderer[3]/ytd-search-filter-renderer[1]/a/div/yt-formatted-string')
            f.click()
        elif search_params['duration'] == 'from 4 to 20 minutes':
            f = driver.find_element(By.XPATH, '/html/body/ytd-app/div[1]/ytd-page-manager/ytd-search/div[1]/ytd-two-column-search-results-renderer/div/ytd-section-list-renderer/div[1]/div[2]/ytd-search-sub-menu-renderer/div/iron-collapse/div/ytd-search-filter-group-renderer[3]/ytd-search-filter-renderer[2]/a/div/yt-formatted-string')
            f.click()
        elif search_params['duration'] == 'more than 20 minutes':
            f = driver.find_element(By.XPATH, '/html/body/ytd-app/div[1]/ytd-page-manager/ytd-search/div[1]/ytd-two-column-search-results-renderer/div/ytd-section-list-renderer/div[1]/div[2]/ytd-search-sub-menu-renderer/div/iron-collapse/div/ytd-search-filter-group-renderer[3]/ytd-search-filter-renderer[3]/a/div/yt-formatted-string')
            f.click()
    
    # Select the sort criterion (sorted by) filter
    if 'criterion' in search_params.keys():
        if search_params['criterion'] == 'relevance':
            f = driver.find_element(By.XPATH, '/html/body/ytd-app/div[1]/ytd-page-manager/ytd-search/div[1]/ytd-two-column-search-results-renderer/div/ytd-section-list-renderer/div[1]/div[2]/ytd-search-sub-menu-renderer/div/iron-collapse/div/ytd-search-filter-group-renderer[5]/ytd-search-filter-renderer[1]/a/div/yt-formatted-string')
            f.click()
        elif search_params['criterion'] == 'upload date':
            f = driver.find_element(By.XPATH, '/html/body/ytd-app/div[1]/ytd-page-manager/ytd-search/div[1]/ytd-two-column-search-results-renderer/div/ytd-section-list-renderer/div[1]/div[2]/ytd-search-sub-menu-renderer/div/iron-collapse/div/ytd-search-filter-group-renderer[5]/ytd-search-filter-renderer[2]/a/div/yt-formatted-string')
            f.click()
        elif search_params['criterion'] == 'views':
            f = driver.find_element(By.XPATH, '/html/body/ytd-app/div[1]/ytd-page-manager/ytd-search/div[1]/ytd-two-column-search-results-renderer/div/ytd-section-list-renderer/div[1]/div[2]/ytd-search-sub-menu-renderer/div/iron-collapse/div/ytd-search-filter-group-renderer[5]/ytd-search-filter-renderer[3]/a/div/yt-formatted-string')
            f.click()
        elif search_params['criterion'] == 'rating':
            f = driver.find_element(By.XPATH, '/html/body/ytd-app/div[1]/ytd-page-manager/ytd-search/div[1]/ytd-two-column-search-results-renderer/div/ytd-section-list-renderer/div[1]/div[2]/ytd-search-sub-menu-renderer/div/iron-collapse/div/ytd-search-filter-group-renderer[5]/ytd-search-filter-renderer[4]/a/div/yt-formatted-string')
            f.click()

    # Wait until filters have been applied
    WebDriverWait(driver, 10).until(EC.visibility_of_all_elements_located)


def close_browser(driver: WebDriver) -> None:
    """Close the browser

    Args:
        driver (WebDriver): The webdriver to close

    Returns:
        None
    """
    driver.quit()


if __name__ == "__main__":
    r = youtube_search('Play the first dota 2 video of less than 4 minutes length sorted by views')