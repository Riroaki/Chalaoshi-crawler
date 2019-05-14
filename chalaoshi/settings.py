# -*- coding: utf-8 -*-

BOT_NAME = 'chalaoshi'

SPIDER_MODULES = ['chalaoshi.spiders']
NEWSPIDER_MODULE = 'chalaoshi.spiders'

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests performed by Scrapy (default: 16)
CONCURRENT_REQUESTS = 32

# Disable cookies (enabled by default)
COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
# TELNETCONSOLE_ENABLED = False

# Override the default request headers:
DEFAULT_REQUEST_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en',
    'Referer': 'https://chalaoshi.cn/',
}

USER_AGENT = 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X)\
 AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1'

# Configure item pipelines
# See https://doc.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
    'chalaoshi.pipelines.ChalaoshiPipeline': 300,
}

# Folder name of download path
DOWNLOAD_FOLDER = 'data'

# Logs
LOG_LEVEL = 'WARNING'

# File recording what has been saved
SAVE_FILE = 'saved_records'

# Teacher index
MAX_INDEX = 5215

# Wait some time
# DOWNLOAD_DELAY = 1.0

# Allowed status code
# HTTPERROR_ALLOWED_CODES = [404, 500]
