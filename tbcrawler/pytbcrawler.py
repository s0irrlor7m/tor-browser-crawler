import argparse
import ConfigParser
import sys
import traceback
from contextlib import contextmanager
from logging import INFO, DEBUG
from os import stat, chdir
import os   # to modify environment variables, -SDL
from os.path import isfile, join, basename
from shutil import copyfile
from sys import maxsize, argv
from urlparse import urlparse

from tbselenium.tbdriver import TorBrowserDriver
from tbselenium.common import USE_RUNNING_TOR

import common as cm
import utils as ut
import crawler as crawler_mod
from log import add_log_file_handler
from log import wl_log, add_symlink
from torcontroller import TorController


def run():
    # build dirs
    build_crawl_dirs()
    
    # setup environment variables for exporting keys
    os.environ['TOR_CIRCUIT_KEY_EXPORT'] = cm.CRAWL_DIR + "/circuit-key.txt"
    os.environ['TOR_SSL_KEY_EXPORT'] = cm.CRAWL_DIR + "/ssl-key.txt"


    # Parse arguments
    args, config = parse_arguments()

    # Read URLs
    url_list = parse_url_list(args.url_file, args.start, args.stop)
    host_list = [urlparse(url).hostname for url in url_list]

    # Configure logger
    add_log_file_handler(wl_log, cm.DEFAULT_CRAWL_LOG)

    # Configure controller
    torrc_config = ut.get_dict_subconfig(config, args.config, "torrc")
    controller = TorController(cm.TBB_DIR,
                               torrc_dict=torrc_config,
                               pollute=False)

    # Configure browser
    ffprefs = ut.get_dict_subconfig(config, args.config, "ffpref")
    driver = TorBrowserWrapper(cm.TBB_DIR,
                               tbb_logfile_path=cm.DEFAULT_FF_LOG,
                               tor_cfg=USE_RUNNING_TOR,
                               pref_dict=ffprefs,
                               socks_port=int(torrc_config['socksport']))

    # Instantiate crawler
    crawl_type = getattr(crawler_mod, "Crawler" + args.type)
    crawler = crawl_type(driver, controller, args.screenshots, args.export_har)

    # Configure crawl
    job_config = ut.get_dict_subconfig(config, args.config, "job")
    job = crawler_mod.CrawlJob(job_config, url_list)

    # Run display
    xvfb_display = setup_virtual_display(args.virtual_display)

    # Run the crawl
    chdir(cm.CRAWL_DIR)
    try:
        crawler.crawl(job)
    except KeyboardInterrupt:
        wl_log.warning("Keyboard interrupt! Quitting...")
        sys.exit(-1)
    finally:
        # Post crawl
        post_crawl()

        # Close display
        ut.stop_xvfb(xvfb_display)

    # die
    sys.exit(0)

def setup_virtual_display(virt_display):
    """Start a virtual display with the given dimensions (if requested)."""
    if virt_display:
        w, h = (int(dim) for dim in virt_display.lower().split("x"))
        return ut.start_xvfb(w, h)

def post_crawl():
    """Operations after the crawl."""
    # TODO: pack crawl
    # TODO: sanity checks
    pass


def build_crawl_dirs():
    # build crawl directory
    ut.create_dir(cm.RESULTS_DIR)
    ut.create_dir(cm.CRAWL_DIR)
    ut.create_dir(cm.LOGS_DIR)
    copyfile(cm.CONFIG_FILE, join(cm.LOGS_DIR, 'config.ini'))
    add_symlink(join(cm.RESULTS_DIR, 'latest_crawl'), basename(cm.CRAWL_DIR))


def parse_url_list(file_path, start, stop):
    """Return list of urls from a file."""
    url_list = []
    try:
        with open(file_path) as f:
            file_contents = f.read()
            url_list = file_contents.splitlines()
            url_list = url_list[start - 1:stop]
    except Exception as e:
        ut.die("ERROR: while parsing URL list: {} \n{}".format(e, traceback.format_exc()))
    return url_list


def parse_arguments():
    # Read configuration file
    config = ConfigParser.RawConfigParser()
    config.read(cm.CONFIG_FILE)

    # Parse arguments
    parser = argparse.ArgumentParser(description='Crawl a list of URLs in multiple batches.')

    # List of urls to be crawled
    parser.add_argument('-u', '--url-file', required=True,
                        help='Path to the file that contains the list of URLs to crawl.',
                        default=cm.LOCALIZED_DATASET)
    parser.add_argument('-t', '--type',
                        choices=cm.CRAWLER_TYPES,
                        help="Crawler type to use for this crawl.",
                        default='Base')
    parser.add_argument('-o', '--output',
                        help='Directory to dump the results (default=./results).',
                        default=cm.CRAWL_DIR)
    parser.add_argument('-c', '--config',
                        help="Crawler tor driver and controller configurations.",
                        choices=config.sections(),
                        default="default")
    parser.add_argument('-b', '--tbb-path',
                        help="Path to the Tor Browser Bundle directory.",
                        default=cm.TBB_DIR)
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='increase output verbosity',
                        default=False)

    # Crawler features
    parser.add_argument('-x', '--virtual-display',
                        help='Dimensions of the virtual display, eg 1200x800',
                        default='')
    parser.add_argument('-s', '--screenshots', action='store_true',
                        help='Capture page screenshots',
                        default=False)
    # export HAR
    parser.add_argument('-e', '--export-har', action='store_true',
                        help='Export HAR',
                        default=False)
    # Limit crawl
    parser.add_argument('--start', type=int,
                        help='Select URLs from this line number: (default: 1).',
                        default=1)
    parser.add_argument('--stop', type=int,
                        help='Select URLs after this line number: (default: EOF).',
                        default=maxsize)

    # Parse arguments
    args = parser.parse_args()

    # Set verbose level
    wl_log.setLevel(DEBUG if args.verbose else INFO)
    del args.verbose

    # Change results dir if output
    cm.CRAWL_DIR = args.output
    del args.output

    wl_log.debug("Command line parameters: %s" % argv)
    return args, config


class TorBrowserWrapper(object):
    """Wraps the TorBrowserDriver to configure it at the constructor
    and run it with the `launch` method.

    We might consider to change the TorBrowserDriver itself to follow
    torcontroller and stem behaviour: init configures and a method is
    used to launch driver/controller, and this method is the one used
    to implement the contextmanager.
    """
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.driver = None

    def __getattr__(self, item):
        if self.driver is None:
            return
        if item == "launch":
            return getattr(self, item)
        return getattr(self.driver, item)

    @contextmanager
    def launch(self):
        self.driver = TorBrowserDriver(*self.args, **self.kwargs)
        yield self.driver
        self.driver.quit()


if __name__ == '__main__':
    run()
