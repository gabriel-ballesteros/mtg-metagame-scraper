import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import re

logger = logging.getLogger('nodes.data_gathering')

def get_tournaments(url,driver):
    tournaments_list = []
    driver.get(url)
    site = re.match(r'\w+\.\w+\.+',url).group(1)
    if site == 'mtgmelee':
        #mtgmelee_orgs = ['Star City Games','Channelfireball']
        tournaments = WebDriverWait(driver, timeout=60, poll_frequency=2).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'tr[role="row"]')))
        tournaments = tournaments[1:]
        print(len(tournaments))
        for tournament in tournaments:
            #if tournament.find_elements_by_tag_name('a')[1].text in mtgmelee_orgs:
            if int(tournament.find_elements_by_tag_name('td')[6].text) > 100:
                tournaments_list.append(tournament.find_element_by_css_selector('a[data-type="tournament"]').get_attribute("href"))
    elif site == 'magic':
        pass
    else:
        logger.error(site + ' site currently not handled (tournaments)')
    driver.quit()
    return(tournaments_list)

def get_decklists(url_list,driver):
    decks_list = []
    for url in url_list:
        site = re.match(r'\w+\.\w+\.+',url).group(1)
        if site == 'magic':
            driver.get(url=url)
            decks = WebDriverWait(driver, 15).until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'css-163ya')))
            driver.quit()
            [decks_list.append(deck) for deck in decks]

        elif site == 'mtgmelee':
            driver.get(url=url)
            decks = 0
        else:
            logger.error(site + ' site currently not handled (decklists)')
        return site, decks_list

def update(client, params):
    options = Options()
    options.headless = True
    chrome_path = '/Users/elros/chromedriver'
    driver = webdriver.Chrome(chrome_path, options=options)
    for url in params.sites_to_scrape:
        get_tournaments(url,driver)
    pass

def done(client, params):
    pass