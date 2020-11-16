import logging
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import re
import time
from slugify import slugify

logger = logging.getLogger('nodes.data_gathering')


def get_tournaments_url(url, driver, params):
    tournaments_list = []
    site = re.match('http[s]?:\/\/(\w+)\.\w+', url).group(1)
    driver.get(url)
    logger.info('Started scraping tournaments at ' + url)
    time.sleep(5)
    if site == 'magic':
        search_box = WebDriverWait(driver, timeout=20, poll_frequency=1).until(EC.presence_of_element_located((By.XPATH, '/html/body/div/div/div/div[1]/div/div/div[1]/div/div[2]/form/div/input')))
        search_box.send_keys('Standard')
        search_box.send_keys(Keys.ENTER)
        time.sleep(5)
        tournaments = WebDriverWait(driver, timeout=20, poll_frequency=1).until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'css-ajYO7')))
        for tournament in tournaments:
            tournaments_list.append(tournament.get_attribute("href"))
    elif site == 'mtgmelee':
        time.sleep(2)
        tournaments = WebDriverWait(driver, timeout=20, poll_frequency=1).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'tr[role="row"]')))
        tournaments = tournaments[1:]
        for tournament in tournaments:
            # if tournament.find_elements_by_tag_name('a')[1].text.lower() in params.mtgmelee_orgs:
            if tournament.find_elements_by_tag_name('td')[3].text.lower() == 'ended' and int(tournament.find_elements_by_tag_name('td')[6].text) >= params.min_t_players:
                tournaments_list.append(tournament.find_element_by_css_selector('a[data-type="tournament"]').get_attribute("href"))
    else:
        logger.error(site + ' site currently not handled (tournaments)')

    logger.info('Extracted ' + str(len(tournaments_list)) + ' tournaments urls from ' + site)
    return tournaments_list


def get_decklists(url, driver, params):
    decks_list = []
    site = re.match('http[s]?:\/\/(\w+)\.\w+', url).group(1)
    driver.get(url=url)
    logger.info('Started scraping decklists from tournament ' + url)
    time.sleep(5)
    if site == 'magic':
        decks = WebDriverWait(driver, timeout=20, poll_frequency=1).until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'css-163ya')))
        for index, deck in enumerate(decks, 1):
            decks_list.append(deck.text)
            # logger.info('Added decklist ' + str(index) + '/' + str(len(decks)) + ' from ' + url)
    elif site == 'mtgmelee':
        decks_urls = WebDriverWait(driver, timeout=20, poll_frequency=1).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'a[data-type="decklist"]')))
        for index, deck_url in enumerate(decks_urls[:params.top_d_cut], 1):
            aux_url = deck_url.get_attribute('href')
            main_window = driver.current_window_handle
            driver.execute_script('window.open();')
            driver.switch_to_window(driver.window_handles[1])
            driver.get(aux_url)
            time.sleep(2)
            decks_list.append(driver.find_element_by_xpath('/html/body/div[1]/div[4]/div[1]/div[1]/div[2]/div[1]').text)
            # logger.info('Added decklist ' + str(index) + '/' + str(min(len(decks_urls), params.top_d_cut)) + ' from ' + aux_url)
            driver.close()
            driver.switch_to_window(main_window)
    else:
        logger.error(site + ' site currently not handled (decklists)')
    logger.info('Extracted ' + str(len(decks_list)) + ' decklists from ' + url)
    return site, decks_list


def update(client, params):
    logger.info('STARTING DATA EXCTRACTION FROM: ' + str(params.sites_to_scrape))
    driver = webdriver.Chrome(params.chrome_path, options=params.chrome_options)
    driver.implicitly_wait(10)
    for site in params.sites_to_scrape:
        for tournament_url in get_tournaments_url(site, driver, params):
            site, decklists = get_decklists(tournament_url, driver, params)
            for d_index, deck in enumerate(decklists, 1):
                f = open(params.raw_data + site + '_' + slugify(re.search('\.\w+/(.*)', tournament_url).group(1)) + '_' + str(d_index) + ".txt", "w")
                f.write(deck)
                f.close()
    driver.quit()
    pass


def done(client, params):
    pass
