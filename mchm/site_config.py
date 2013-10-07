#################################
#  TURN THIS OFF IN PRODUCTION  #
#################################
APP_DEBUG_MODE = False
#################################

#APP CONFIG
APP_NAME = 'mchm'
ZEROCONF_IP = '169.254.169.254'

# change to 'https' if you are using SSL on upstream server
URL_SCHEME = 'http'
if APP_DEBUG_MODE:
    HOSTNAME = 'localhost'
    PORT = 5000
else:
    HOSTNAME = 'mchm.ho.kanetix.com'
    PORT = 5000

# Config data lifetime.
# If you change this you will have to recreate the index with
# the build_index script.
DOC_LIFETIME = 3600

#DB CONFIG
MONGO_DB_NAME = 'mchm'
MONGO_URI = "mongodb://localhost"

#File Logging
LOG_PATH = 'mchm/logs/{!s}.log'.format(APP_NAME)
LOG_SIZE = 524288  # size of each log file in bytes
LOG_ARCHIVES = 10  # how many log archives to keep
LOG_FORMAT = ('\n[%(asctime)s %(levelname)s]: '
              '%(message)s <in %(pathname)s:%(lineno)d>')