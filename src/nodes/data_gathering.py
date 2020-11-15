import logging
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import re
from datetime import datetime
import time

logger = logging.getLogger('nodes.data_gathering')


def get_tournaments_url(url, driver):
    tournaments_list = []
    site = re.match('http[s]?:\/\/(\w+)\.\w+', url).group(1)
    driver.get(url)
    logger.info('Started scraping tournaments at ' + url)
    time.sleep(3)
    if site == 'magic':
        search_box = WebDriverWait(driver, timeout=20, poll_frequency=1).until(EC.presence_of_element_located((By.XPATH, '/html/body/div/div/div/div[1]/div/div/div[1]/div/div[2]/form/div/input')))
        search_box.send_keys('Standard')
        search_box.send_keys(Keys.ENTER)
        time.sleep(2)
        tournaments = WebDriverWait(driver, timeout=20, poll_frequency=1).until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'css-ajYO7')))
        for tournament in tournaments:
            tournaments_list.append(tournament.get_attribute("href"))
    elif site == 'mtgmelee':
        time.sleep(3)
        tournaments = WebDriverWait(driver, timeout=20, poll_frequency=1).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'tr[role="row"]')))
        tournaments = tournaments[1:]
        for tournament in tournaments:
            # if tournament.find_elements_by_tag_name('a')[1].text.lower() in params.mtgmelee_orgs:
            if tournament.find_elements_by_tag_name('td')[3].text.lower() == 'ended' and int(tournament.find_elements_by_tag_name('td')[6].text) >= 64:
                tournaments_list.append(tournament.find_element_by_css_selector('a[data-type="tournament"]').get_attribute("href"))
    else:
        logger.error(site + ' site currently not handled (tournaments)')

    logger.info('Extracted ' + str(len(tournaments_list)) + ' tournaments urls from ' + site)
    return tournaments_list


def get_decklists(url, driver):
    decks_list = []
    site = re.match('http[s]?:\/\/(\w+)\.\w+', url).group(1)
    driver.get(url=url)
    logger.info('Started scraping decklists from tournament ' + url)
    time.sleep(3)
    if site == 'magic':
        decks = WebDriverWait(driver, timeout=20, poll_frequency=1).until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'css-163ya')))
        [decks_list.append(deck.text) for deck in decks]
        logger.info('Added ' + len(decks) + ' decklists from ' + url)
    elif site == 'mtgmelee':
        time.sleep(2)
        decks_urls = WebDriverWait(driver, timeout=20, poll_frequency=1).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'a[data-type="decklist"]')))
        for index, deck_url in enumerate(decks_urls, 1):
            aux_url = deck_url.get_attribute('href')
            main_window = driver.current_window_handle
            driver.execute_script('window.open();')
            driver.switch_to_window(driver.window_handles[1])
            driver.get(aux_url)
            time.sleep(2)
            decks_list.append(driver.find_element_by_xpath('/html/body/div[1]/div[4]/div[1]/div[1]/div[2]/div[1]').text)
            logger.info('Added decklist ' + str(index) + '/' + str(len(decks_urls)) + ' from ' + aux_url)
            driver.close()
            driver.switch_to_window(main_window)
    else:
        logger.error(site + ' site currently not handled (decklists)')
    logger.info('Extracted ' + str(len(decks_list)) + ' decklists from ' + url)
    return site, decks_list


def update(client, params):
    driver = webdriver.Chrome(params.chrome_path, options=params.chrome_options)
    driver.implicitly_wait(10)
    for site in params.sites_to_scrape:
        for t_index, tournament_url in enumerate(get_tournaments_url(site, driver), 1):
            site, decklists = get_decklists(tournament_url, driver)
            for d_index, deck in enumerate(decklists, 1):
                f = open('../data/raw/' + datetime.now().strftime("%Y-%m-%d") + '_' + site + '_' + str(t_index) + '-' + str(d_index) + ".txt", "w")
                f.write(deck)
                f.close()
    driver.quit()
    pass


def done(client, params):
    pass
