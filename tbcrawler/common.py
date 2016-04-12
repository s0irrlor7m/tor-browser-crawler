import os
from os.path import join, dirname, abspath, pardir
from time import strftime


def parse_config(fname):
    config_dict = {}
    with open(fname) as f:
        for line in f:
            if line.startswith('#') or line.startswith('\n'):
                continue
            option, args = line.rstrip().split(" ", 1)
            args = args.split("#", 1)[0]
            config_dict.update({option: args})
    return config_dict


env_vars = os.environ
# whether we're running on Travis CI or not
running_in_CI = "CONTINUOUS_INTEGRATION" in env_vars and "TRAVIS" in env_vars

# defaults for batch and instance numbers
NUM_BATCHES = 10
NUM_INSTANCES = 4
MAX_SITES_PER_TOR_PROCESS = 100  # reset tor process after crawling 100 sites

# max dumpcap size in KB
MAX_DUMP_SIZE = 40000
# max filename length
MAX_FNAME_LENGTH = 200
STREAM_CLOSE_TIMEOUT = 20  # wait 20 seconds before raising an alarm signal
# otherwise we had many cases where get_streams hanged

# timeouts
SOFT_VISIT_TIMEOUT = 120     # timeout used by selenium and dumpcap
# signal based hard timeout in case soft timeout fails
HARD_VISIT_TIMEOUT = SOFT_VISIT_TIMEOUT + 10

DEFAULT_SOCKS_PORT = 9051

CRAWLER_TYPES = ['Base', 'WebFP', 'Multitab']

# virtual display dimensions
XVFB_W = 1280
XVFB_H = 720

# Default paths
BASE_DIR = abspath(join(dirname(__file__), pardir))
RESULTS_DIR = join(BASE_DIR, 'results')
ETC_DIR = join(BASE_DIR, 'etc')
CONFIG_DIR = join(BASE_DIR, 'config')
DEFAULT_CONFIG_DIR = join(CONFIG_DIR, "default")
TORRC_FILE = join(DEFAULT_CONFIG_DIR, 'torrc')
FFPREF_FILE = join(DEFAULT_CONFIG_DIR, 'ffprefs')
SRC_DIR = join(BASE_DIR, 'tbcrawler')
CRAWL_DIR = join(RESULTS_DIR, strftime('%y%m%d_%H%M%S'))
LOGS_DIR = join(CRAWL_DIR, 'logs')
DEFAULT_CRAWL_LOG = join(LOGS_DIR, 'crawl.log')
DEFAULT_TOR_LOG = join(LOGS_DIR, 'tor.log')
DEFAULT_FF_LOG = join(LOGS_DIR, 'ff.log')
TEST_DIR = join(SRC_DIR, 'test')
TBB_DIR = join(BASE_DIR, 'tor-browser_en-US')
# Top URLs localized (DE) to prevent the effect of localization
LOCALIZED_DATASET = join(ETC_DIR, "localized-urls-100-top.csv")

VBOX_GATEWAY_IP = "10.0.2.2"  # default gateway IP of VirtualBox
LXC_GATEWAY_IP = "10.0.3.1"  # default gateway IP of LXC
LOCALHOST_IP = "127.0.0.1"  # default localhost IP
DEFAULT_FILTER = 'tcp and not host %s and not tcp port 22 and not tcp port 20' % LOCALHOST_IP

TORRC = parse_config(TORRC_FILE)
FFPREFS = parse_config(FFPREF_FILE)