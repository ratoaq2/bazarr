# coding=utf-8
import os
import platform
import re
import subprocess
import tarfile
import logging
import requests

import bazarr
import sqlite3
import json
import requests

from get_args import args
from config import settings

class FakeLock(object):
    """
    If no locking or request throttling is needed, use this
    """
    
    def __enter__(self):
        """
        Do nothing on enter
        """
        pass
    
    def __exit__(self, type, value, traceback):
        """
        Do nothing on exit
        """
        pass


if not args.no_update:
    import git
fake_lock = FakeLock()


def runGit(args):
    git_locations = ['git']
    
    if platform.system().lower() == 'darwin':
        git_locations.append('/usr/local/git/bin/git')
    
    output = err = None
    
    for cur_git in git_locations:
        cmd = cur_git + ' ' + args
        
        try:
            logging.debug('Trying to execute: "' + cmd + '"')
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
            output, err = p.communicate()
            output = output.strip()
            
            logging.debug('Git output: ' + output)
        except OSError:
            logging.debug('Command failed: %s', cmd)
            continue
        
        if 'not found' in output or "not recognized as an internal or external command" in output:
            logging.debug('Unable to find git with command ' + cmd)
            output = None
        elif 'fatal:' in output or err:
            logging.error('Git returned bad info. Are you sure this is a git installation?')
            output = None
        elif output:
            break
    
    return (output, err)


def getVersion():
    if os.path.isdir(os.path.join(os.path.dirname(__file__), '..', '.git')):
        
        bazarr.INSTALL_TYPE = 'git'
        output, err = runGit('rev-parse HEAD')
        
        if not output:
            logging.error('Could not find latest installed version.')
            cur_commit_hash = None
        
        cur_commit_hash = str(output)
        
        if not re.match('^[a-z0-9]+$', cur_commit_hash):
            logging.error('Output does not look like a hash, not using it.')
            cur_commit_hash = None
        
        if get_general_settings()[5]:
            branch_name = get_general_settings()[5]
        
        else:
            remote_branch, err = runGit('rev-parse --abbrev-ref --symbolic-full-name @{u}')
            remote_branch = remote_branch.rsplit('/', 1) if remote_branch else []
            if len(remote_branch) == 2:
                remote_name, branch_name = remote_branch
            else:
                remote_name = branch_name = None
            
            if not remote_name and get_general_settings()[5]:
                logging.error('Could not retrieve remote name from git. Defaulting to origin.')
                branch_name = get_general_settings()[5]
            
            if not branch_name:
                logging.error('Could not retrieve branch name from git. Defaulting to master.')
                branch_name = 'master'
        
        return cur_commit_hash, 'origin', branch_name
    
    else:
        bazarr.INSTALL_TYPE = 'source'
        
        if bazarr.CURRENT_VERSION:
            return bazarr.CURRENT_VERSION, 'origin', get_general_settings()[5]
        else:
            return None, 'origin', get_general_settings()[5]


def check_updates():
    check_github()
    if not bazarr.CURRENT_VERSION:
        bazarr.UPDATE_AVAILABLE = None
    elif bazarr.COMMITS_BEHIND > 0 and get_general_settings()[5] in ('master') and \
            ('V' + bazarr.VERSION) != bazarr.LATEST_RELEASE:
        bazarr.UPDATE_AVAILABLE = 'release'
    elif bazarr.COMMITS_BEHIND > 0 and bazarr.CURRENT_VERSION != bazarr.LATEST_VERSION:
        bazarr.UPDATE_AVAILABLE = 'commit'
    else:
        bazarr.UPDATE_AVAILABLE = False


def check_github():
    bazarr.COMMITS_BEHIND = 0
    
    # Get the latest version available from github
    logging.info('Retrieving latest version information from GitHub')
    url = 'https://api.github.com/repos/morpheus65535/bazarr/commits/%s' % get_general_settings()[5]
    version = request_json(url, timeout=20, validator=lambda x: type(x) == dict)
    
    if version is None:
        logging.warn('Could not get the latest version from GitHub. Are you running a local development version?')
        return bazarr.CURRENT_VERSION
    
    bazarr.LATEST_VERSION = version['sha']
    logging.debug("Latest version is %s", bazarr.LATEST_VERSION)
    
    # See how many commits behind we are
    if not bazarr.CURRENT_VERSION:
        logging.info('You are running an unknown version of Bazarr. Run the updater to identify your version')
        return bazarr.LATEST_VERSION
    
    if bazarr.LATEST_VERSION == bazarr.CURRENT_VERSION:
        logging.info('Bazarr is up to date')
        return bazarr.LATEST_VERSION
    
    logging.info('Comparing currently installed version with latest GitHub version')
    url = 'https://api.github.com/repos/morpheus65535/bazarr/compare/%s...%s' % (bazarr.LATEST_VERSION,
                                                                                 bazarr.CURRENT_VERSION)
    commits = request_json(url, timeout=20, whitelist_status_code=404, validator=lambda x: type(x) == dict)
    
    if commits is None:
        logging.warn('Could not get commits behind from GitHub.')
        return bazarr.LATEST_VERSION
    
    try:
        bazarr.COMMITS_BEHIND = int(commits['behind_by'])
        logging.debug("In total, %d commits behind", bazarr.COMMITS_BEHIND)
    except KeyError:
        logging.info('Cannot compare versions. Are you running a local development version?')
        bazarr.COMMITS_BEHIND = 0
    
    if bazarr.COMMITS_BEHIND > 0:
        logging.info('New version is available. You are %s commits behind' % bazarr.COMMITS_BEHIND)
        
        url = 'https://api.github.com/repos/morpheus65535/bazarr/releases'
        releases = request_json(url, timeout=20, whitelist_status_code=404, validator=lambda x: type(x) == list)
        
        if releases is None:
            logging.warn('Could not get releases from GitHub.')
            return bazarr.LATEST_VERSION
        
        if get_general_settings()[5] == 'master':
            release = next((r for r in releases if not r['prerelease']), releases[0])
        else:
            release = releases[0]
        bazarr.LATEST_RELEASE = release['tag_name']
    
    elif bazarr.COMMITS_BEHIND == 0:
        logging.info('Bazarr is up to date')
    
    return bazarr.LATEST_VERSION


def update():
    if bazarr.INSTALL_TYPE == 'git':
        output, err = runGit('pull ' + 'origin' + ' ' + get_general_settings()[5])
        
        if not output:
            logging.error('Unable to download latest version')
            return
        
        for line in output.split('\n'):
            
            if 'Already up-to-date.' in line:
                logging.info('No update available, not updating')
                logging.info('Output: ' + str(output))
            elif line.endswith(('Aborting', 'Aborting.')):
                logging.error('Unable to update from git: ' + line)
                logging.info('Output: ' + str(output))
    
    else:
        tar_download_url = 'https://github.com/morpheus65535/bazarr/tarball/{}'.format(get_general_settings()[5])
        update_dir = os.path.join(os.path.dirname(__file__), '..', 'update')
        
        logging.info('Downloading update from: ' + tar_download_url)
        data = request_content(tar_download_url)
        
        if not data:
            logging.error("Unable to retrieve new version from '%s', can't update", tar_download_url)
            return
        
        download_name = get_general_settings()[5] + '-github'
        tar_download_path = os.path.join(os.path.dirname(__file__), '..', download_name)
        
        # Save tar to disk
        with open(tar_download_path, 'wb') as f:
            f.write(data)
        
        # Extract the tar to update folder
        logging.info('Extracting file: ' + tar_download_path)
        tar = tarfile.open(tar_download_path)
        tar.extractall(update_dir)
        tar.close()
        
        # Delete the tar.gz
        logging.info('Deleting file: ' + tar_download_path)
        os.remove(tar_download_path)
        
        # Find update dir name
        update_dir_contents = [x for x in os.listdir(update_dir) if os.path.isdir(os.path.join(update_dir, x))]
        if len(update_dir_contents) != 1:
            logging.error("Invalid update data, update failed: " + str(update_dir_contents))
            return
        content_dir = os.path.join(update_dir, update_dir_contents[0])
        
        # walk temp folder and move files to main folder
        for dirname, dirnames, filenames in os.walk(content_dir):
            dirname = dirname[len(content_dir) + 1:]
            for curfile in filenames:
                old_path = os.path.join(content_dir, dirname, curfile)
                new_path = os.path.join(os.path.dirname(__file__), '..', dirname, curfile)
                
                if os.path.isfile(new_path):
                    os.remove(new_path)
                os.renames(old_path, new_path)


def checkout_git_branch():
    if bazarr.INSTALL_TYPE == 'git':
        output, err = runGit('fetch origin')
        output, err = runGit('checkout %s' % get_general_settings()[5])
        
        if not output:
            logging.error('Unable to change git branch.')
            return
        
        for line in output.split('\n'):
            if line.endswith(('Aborting', 'Aborting.')):
                logging.error('Unable to checkout from git: ' + line)
                logging.info('Output: ' + str(output))
        
        output, err = runGit('pull origin %s' % get_general_settings()[5])


def request_content(url, **kwargs):
    """
    Wrapper for `request_response', which will return the raw content.
    """
    
    response = request_response(url, **kwargs)
    
    if response is not None:
        return response.content


def request_response(url, method="get", auto_raise=True,
                     whitelist_status_code=None, lock=fake_lock, **kwargs):
    """
    Convenient wrapper for `requests.get', which will capture the exceptions
    and log them. On success, the Response object is returned. In case of a
    exception, None is returned.

    Additionally, there is support for rate limiting. To use this feature,
    supply a tuple of (lock, request_limit). The lock is used to make sure no
    other request with the same lock is executed. The request limit is the
    minimal time between two requests (and so 1/request_limit is the number of
    requests per seconds).
    """
    
    # Convert whitelist_status_code to a list if needed
    if whitelist_status_code and type(whitelist_status_code) != list:
        whitelist_status_code = [whitelist_status_code]
    
    # Disable verification of SSL certificates if requested. Note: this could
    # pose a security issue!
    kwargs["verify"] = True
    
    # Map method to the request.XXX method. This is a simple hack, but it
    # allows requests to apply more magic per method. See lib/requests/api.py.
    request_method = getattr(requests, method.lower())
    
    try:
        # Request URL and wait for response
        with lock:
            logging.debug(
                "Requesting URL via %s method: %s", method.upper(), url)
            response = request_method(url, **kwargs)
        
        # If status code != OK, then raise exception, except if the status code
        # is white listed.
        if whitelist_status_code and auto_raise:
            if response.status_code not in whitelist_status_code:
                try:
                    response.raise_for_status()
                except:
                    logging.debug(
                        "Response status code %d is not white "
                        "listed, raised exception", response.status_code)
                    raise
        elif auto_raise:
            response.raise_for_status()
        
        return response
    except requests.exceptions.SSLError as e:
        if kwargs["verify"]:
            logging.error(
                "Unable to connect to remote host because of a SSL error. "
                "It is likely that your system cannot verify the validity"
                "of the certificate. The remote certificate is either "
                "self-signed, or the remote server uses SNI. See the wiki for "
                "more information on this topic.")
        else:
            logging.error(
                "SSL error raised during connection, with certificate "
                "verification turned off: %s", e)
    except requests.ConnectionError:
        logging.error(
            "Unable to connect to remote host. Check if the remote "
            "host is up and running.")
    except requests.Timeout:
        logging.error(
            "Request timed out. The remote host did not respond timely.")
    except requests.HTTPError as e:
        if e.response is not None:
            if e.response.status_code >= 500:
                cause = "remote server error"
            elif e.response.status_code >= 400:
                cause = "local client error"
            else:
                # I don't think we will end up here, but for completeness
                cause = "unknown"
            
            logging.error(
                "Request raise HTTP error with status code %d (%s).",
                e.response.status_code, cause)
            
            # Debug response
            # if bazarr.DEBUG:
            #     server_message(e.response)
        else:
            logging.error("Request raised HTTP error.")
    except requests.RequestException as e:
        logging.error("Request raised exception: %s", e)


def request_json(url, **kwargs):
    """
    Wrapper for `request_response', which will decode the response as JSON
    object and return the result, if no exceptions are raised.

    As an option, a validator callback can be given, which should return True
    if the result is valid.
    """
    
    validator = kwargs.pop("validator", None)
    response = request_response(url, **kwargs)
    
    if response is not None:
        try:
            result = response.json()
            
            if validator and not validator(result):
                logging.error("JSON validation result failed")
            else:
                return result
        except ValueError:
            logging.error("Response returned invalid JSON data")
            
            # Debug response
            # if bazarr.DEBUG:
            #     server_message(response)
