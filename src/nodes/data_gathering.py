import logging
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import re
import time
from slugify import slugify
import datetime

logger = logging.getLogger('nodes.data_gathering')


def normalize_date(site, s):
    if site == 'magic':
        s_date = datetime.datetime.strptime(s, '%B %d, %Y')
    elif site == 'mtgmelee':
        d = re.search('(.+) at .+', s).group(1)
        today = datetime.date.today()
        if (d == 'Today'):
            s_date = today
        elif (d == 'Yesterday'):
            s_date = today - datetime.timedelta(1)
        elif (d == 'Last Monday'):
            s_date = today + datetime.timedelta(days=today.weekday())
        elif (d == 'Last Tuesday'):
            s_date = today + datetime.timedelta(days=today.weekday() + 1)
        elif (d == 'Last Wednesday'):
            s_date = today + datetime.timedelta(days=today.weekday() + 2)
        elif (d == 'Last Thursday'):
            s_date = today + datetime.timedelta(days=today.weekday() + 3)
        elif (d == 'Last Friday'):
            s_date = today + datetime.timedelta(days=today.weekday() + 4)
        elif (d == 'Last Saturday'):
            s_date = today + datetime.timedelta(days=today.weekday() + 5)
        elif (d == 'Last Sunday'):
            s_date = today + datetime.timedelta(days=today.weekday() + 6)
        else:
            s_date = datetime.datetime.strptime(d, '%m/%d/%y')
    return s_date.strftime('%Y-%m-%d')


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
            date = normalize_date(site, tournament.find_element_by_class_name('css-3xJlN').text)
            tournaments_list.append([date, tournament.get_attribute("href")])
    elif site == 'mtgmelee':
        time.sleep(8)
        # size_selector = WebDriverWait(driver, timeout=20, poll_frequency=1).until(EC.presence_of_element_located((By.CLASS_NAME, 'select2-selection')))
        # size_selector.click()
        # time.sleep(1)
        # per_page_500 = WebDriverWait(driver, timeout=20, poll_frequency=1).until(EC.presence_of_element_located((By.XPATH, '/html/body/span[2]/span/span[2]/ul/li[5]')))
        # per_page_500.click()
        # time.sleep(10)
        tournaments = WebDriverWait(driver, timeout=20, poll_frequency=1).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'tr[role="row"]')))
        tournaments = tournaments[1:]
        for tournament in tournaments:
            if tournament.find_elements_by_tag_name('td')[3].text.lower() == 'ended' and int(tournament.find_elements_by_tag_name('td')[6].text) >= params.min_t_players:
                date = normalize_date(site, tournament.find_element_by_class_name('StartDate-column').text)
                tournaments_list.append([date, tournament.find_element_by_css_selector('a[data-type="tournament"]').get_attribute("href")])
    else:
        logger.warning(site + ' site currently not handled (tournaments)')

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
            driver.close()
            driver.switch_to_window(main_window)
    else:
        logger.warning(site + ' site currently not handled (decklists)')
    logger.info('Extracted ' + str(len(decks_list)) + ' decklists from ' + url)
    return site, decks_list


def update(client, params):
    logger.info('STARTING DATA EXCTRACTION FROM: ' + str(params.sites_to_scrape))
    driver = webdriver.Chrome(params.chrome_path, options=params.chrome_options)
    driver.implicitly_wait(10)
    for site in params.sites_to_scrape:
        for tournament_url in get_tournaments_url(site, driver, params):
            tournament_date = tournament_url[0]
            tournament_link = tournament_url[1]
            site, decklists = get_decklists(tournament_link, driver, params)
            for d_index, deck in enumerate(decklists, 1):
                f = open(params.raw_data + site + '_' + tournament_date + '_' + slugify(re.search('\.\w+/(.*)', tournament_link).group(1)) + '_' + str(d_index) + ".txt", "w")
                f.write(deck)
                f.close()
    driver.quit()
    pass


def done(client, params):
    pass
