import os
import sys
import json
import argparse

import logging
import redis
import psycopg2
from nytScraper.etl_utils import NYTScraper, generate_dates, queue_jobs, execute_insertions_nyt, get_places
from nytScraper.etl_utils import insert_results_to_database

LOGGER = logging.getLogger('execute_nyt_scraper')


def execute(api_keys, market_id, feed_id, pg_config, redis_config, begin_date=None, end_date=None):

    LOGGER.info("Starting NYT scraping cycle.")

    if begin_date is None or end_date is None:
        end_date, begin_date = generate_dates()

    pg_conn = psycopg2.connect(**pg_config)

    redis_conn = redis.Redis(**redis_config)

    place_list = get_places(pg_conn, market_id)
    scraper = NYTScraper(api_keys, conn=redis_conn)

    queue_jobs(redis_conn, place_list, begin_date=begin_date, end_date=end_date)
    results = scraper.execute_api_search()
    insert_results_to_database(pg_conn, results, feed_id)

    pg_conn.close()

# sys.path.append(os.path.dirname(os.path.realpath('__file__')))
# print(os.path.join(os.path.dirname(os.path.realpath('__file__')), 'nytScraper'))
# from database_utils import connect_to_database, execute_query
#
# if __name__ == '__main__': from etl_utils import nytScraper, execute_insertions_nyt, generate_dates, execute_api_search
# else: from .etl_utils import nytScraper, execute_insertions_nyt, generate_dates, execute_api_search

# parser = argparse.ArgumentParser()
#
# arg_names = ['--password', '--user', '--host', '--dbname', '--url']
# help_messages = ['Password for postgres database.', 'user.', 'Host for database', 'Name of database.', 'URL string to database. If specified all other options ignored.']
#
# for arg, help in zip(arg_names, help_messages):
#     parser.add_argument(arg, help = help)
#
# parser.add_argument('--port', type = int, default = 5432)
#
# def execute(**kwargs):
#
#     if 'url' in kwargs:
#         conn = connect_to_database(url = kwargs['url'])
#     else:
#         conn = connect_to_database(dbname = kwargs['dbname'], password = kwargs['password'], host = kwargs['host'], user = kwargs['user'])
#
#     # define session constants, must be set as environment variables
#     API_KEYS = os.environ['API_KEYS'].split(',')
#     MARKET_ID = int(os.environ['NYT_MARKET_ID'])
#     FEED_ID = int(os.environ['NYT_FEED_ID'])
#     RERUN_PATH = os.environ['NYT_RERUN_PATH']
#
#     TODAY, YESTERDAY = generate_dates()
#
#     apiScraper = nytScraper(API_KEYS)
#
#     # execute any reruns from last session
#     with open(RERUN_PATH, 'r') as f:
#         to_rerun = json.load(f)
#
#     results, reruns = list(), list()
#     if len(to_rerun) > 0:
#
#         for data in to_rerun:
#
#             today = data['date']['today']
#             yesterday = data['date']['yesterday']
#
#             old_results, old_reruns = execute_api_search(scraper = apiScraper, place_list = data['place_list'], market_id = MARKET_ID, today = today, yesterday = yesterday)
#             results.extend(old_results)
#             reruns.extend(old_reruns)
#
#
#     q = "SELECT place_name, place_id FROM places WHERE market_id = %s"
#     place_list = execute_query(conn, q, data = (MARKET_ID, ), return_values = True)
#
#     new_results, new_reruns = execute_api_search(scraper = apiScraper, place_list = place_list, market_id = MARKET_ID, today = TODAY, yesterday = YESTERDAY)
#
#     results.extend(new_results)
#
#     try:
#         reruns.append(new_reruns)
#         reruns = [r for r in reruns if r != None]   # bugfix for returned None
#     except TypeError:
#         pass
#
#     # serialize reruns
#     with open(RERUN_PATH, 'w') as f:
#         json.dump(reruns, f)
#
#     for r_list in results:
#         for r in r_list['query_results']:
#             execute_insertions_nyt(conn, r, FEED_ID, r_list['place_id'])
#
#     conn.close()
#
#
# if __name__ == '__main__':
#
#     args = parser.parse_args()
#
#     if args.url:
#         execute(url = parser.url)
#     else:
#         missing_value_message = "Must specify database {} as environment variable {} or as argument."
#
#         if args.password: password = args.password
#         elif 'DB_PASSWORD' in os.environ: password = os.environ['DB_PASSWORD']
#         else: raise ValueError(missing_value_message.format('password', 'DB_PASSWORD'))
#
#         if args.user: user = args.user
#         elif 'DB_user' in os.environ: user = os.environ['DB_user']
#         else: raise ValueError(missing_value_message.format('user', 'DB_user'))
#
#         if args.host: host = args.host
#         elif 'DB_HOST' in os.environ: host = os.environ['DB_HOST']
#         else: raise ValueError(missing_value_message.format('host','DB_HOST'))
#
#         if args.dbname: dbname = args.dbname
#         elif 'DB_NAME' in os.environ: dbname = os.environ['DB_NAME']
#         else: raise ValueError(missing_value_message.format('dbname', 'DB_HOST'))
#
#         execute(dbname = dbname, password = password, host = host, user = user, port = args.port)
