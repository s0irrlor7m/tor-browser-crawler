#!/bin/bash

# configures and runs a crawl (inside a docker container)

# globals
PYTHON_VERSION='python2.7'
PYTHON_PATH=`which $PYTHON_VERSION`
TOR_VERSION='9.0a7'
BASE='/home/docker/tbcrawl'

# set offloads
ifconfig eth0 mtu 1500
ethtool -K eth0 tx off rx off tso off gso off gro off lro off

# install python requirements
pushd ${BASE}
pip install -U -r requirements.txt

# added by Daniel: customized tbcrawler

if [ -d "tor-browser-selenium" ]; then
	rm -rf tor-browser-selenium
fi
	
git clone https://github.com/s0irrlor7m/tor-browser-selenium.git
#git clone https://github.com/webfp/tor-browser-selenium.git
cd tor-browser-selenium
python setup.py install
cd ..


# copy tor browser bundle
#rm -rf tor-browser_en-US
#cp -r /home/docker/tbb_setup/tor-browser_en-US .


# TODO: do other stuff here if you need to

# copy add-on to TBB
cp /home/docker/tbcrawl/extensions/harexporttrigger@getfirebug.com.xpi /home/docker/tbcrawl/tor-browser_en-US/Browser/TorBrowser/Data/Browser/profile.default/extensions/


# throttle Tor connection
git clone https://github.com/magnific0/wondershaper.git
# cd wondershaper
# ./wondershaper -a eth0 -u 10
# cd ..

# Run command with params
python bin/tbcrawler.py $1
