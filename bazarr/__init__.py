# coding=utf-8

import threading

from check_update import getVersion

VERSION = '0.6.8'
INSTALL_TYPE = None
CURRENT_VERSION = None
LATEST_VERSION = None
COMMITS_BEHIND = None
PREV_RELEASE = None
LATEST_RELEASE = None
UPDATE_AVAILABLE = False
INIT_LOCK = threading.Lock()
_INITIALIZED = False

def initialize():
    with INIT_LOCK:

        global _INITIALIZED
        global CURRENT_VERSION
        # global LATEST_VERSION
        global PREV_RELEASE

        if _INITIALIZED:
            return False

        # Get the currently installed version. Returns None or the git
        # hash.
        CURRENT_VERSION, GIT_REMOTE, GIT_BRANCH = getVersion()

        # # Check for new versions
        # try:
        #     LATEST_VERSION = check_update.check_updates()
        #     print LATEST_VERSION
        # except:
        #     logging.exception(u"Unhandled exception")
        #     LATEST_VERSION = CURRENT_VERSION

        PREV_RELEASE = VERSION

        _INITIALIZED = True
        return True
