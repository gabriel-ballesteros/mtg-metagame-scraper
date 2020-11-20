import logging

logger = logging.getLogger('nodes.data_storage')


def update(client, params):
    logger.info('STARTING DATA POPULATION TO DB AT ' + params.database + ' DATABASE')
    pass


def done(client, params):
    pass
