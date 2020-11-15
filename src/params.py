# from dotenv import load_dotenv, find_dotenv
import os
from selenium.webdriver.chrome.options import Options


class Params:
    """
    Parameters class.

    This file centralizes anything that can be
    parametrized in the code.

    If you want to use a parameter later in the code, you
    should instantiate params as:
    `params = Params()`,
    send the object `params` within functions and, inside the
    function, call the parameter as an attribute of the `params` object.

    For instance, if you have a parameter called `url` created here, you'd
    call it in a function called `func` as:

    ```
    def func(params):
            ...

            url = params.url

        ...
    ```
    """

    # pre-requeqs

    # magically load environment variables from any .env files
    # load_dotenv(os.path.abspath('../.env'))

    # parameters
    sites_to_scrape = ['https://magic.gg/decklists', 'https://mtgmelee.com/Decklists/Standard']
    mtgmelee_orgs = ['star city games', 'channelfireball']

    chrome_options = Options()
    chrome_options.headless = True
    chrome_path = '/Users/elros/chromedriver'

    raw_data = os.path.abspath('../data/raw/')
    external_data = os.path.abspath('../data/external/')
    processed_data = os.path.abspath('../data/processed/')
    intermediate_data = os.path.abspath('../data/intermediate/')

    log_name = os.path.abspath('../log/dump.log')

    # if this is set to True, then all the nodes will be automatically
    # considered not up-to-date and will be rerun.
    force_execution = True

    # Database connection params
    user = 'postgres'  # find_dotenv('DB_USERNAME')
    password = 'admin'  # find_dotenv('DB_PASSWORD')
    host = 'localhost'
    database = "decks"
