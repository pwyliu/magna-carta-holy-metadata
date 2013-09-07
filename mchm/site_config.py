#################################
#  TURN THIS OFF IN PRODUCTION  #
#################################
APP_DEBUG_MODE = True
#################################

#APP CONFIG
APP_NAME = 'mchm'
PORT = 5000

# Config data lifetime.
# If you change this you have to recreate the index
# in Mongo with the build_index script.
LIFETIME = 3600

#DB CONFIG
MONGO_DB_NAME = 'mchm'
MONGO_URI = "mongodb://localhost"

#File Logging
LOG_PATH = 'mchm/logs/{!s}.log'.format(APP_NAME)
LOG_SIZE = 524288  # size of each log file in bytes
LOG_ARCHIVES = 10  # how many log archives to keep
LOG_FORMAT = ('\n[%(asctime)s %(levelname)s]: '
              '%(message)s <in %(pathname)s:%(lineno)d>')