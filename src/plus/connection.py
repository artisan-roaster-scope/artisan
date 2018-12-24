#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# connection.py
#
# Copyright (c) 2018, Paul Holleis, Marko Luther
# All rights reserved.
# 
# 
# ABOUT
# This module connects to the artisan.plus inventory management service

# LICENSE
# This program or module is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 2 of the License, or
# version 3 of the License, or (at your option) any later versison. It is
# provided for educational purposes and is distributed in the hope that
# it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
# the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import requests
import gzip
import json

#import keyring.backends.file
#import keyring.backends.Gnome
#import keyring.backends.Google
#import keyring.backends.pyfs
#import keyring.backends.kwallet
#import keyring.backends.multi

import platform

if platform.system().startswith("Windows") or platform.system() == 'Darwin':
    import keyring.backends.fail
    import keyring.backends.OS_X
    import keyring.backends.SecretService
    import keyring.backends.Windows
import keyring # @Reimport # imported last to make py2app work


from plus import config
from artisanlib import __version__

from PyQt5.QtCore import QSemaphore

token_semaphore = QSemaphore(1) # protects access to the session token which is manipluated only here


def getToken():
    try:
        token_semaphore.acquire(1)
        return config.token
    except:
        return None
    finally:
        if token_semaphore.available() < 1:
            token_semaphore.release(1)
            
def getNickname():
    try:
        token_semaphore.acquire(1)
        return config.nickname
    except:
        return None
    finally:
        if token_semaphore.available() < 1:
            token_semaphore.release(1)              

def setToken(token,nickname=None):
    try:
        token_semaphore.acquire(1)
        config.token = token
        config.nickname = nickname
        if config.app_window.qmc.operator is None or config.app_window.qmc.operator == "" and nickname is not None and nickname != "": # @UndefinedVariable
            config.app_window.qmc.operator = nickname
    finally:
        if token_semaphore.available() < 1:
            token_semaphore.release(1)  

def clearCredentials():
    config.logger.info("clearCredentials()")
    # remove credentials from keychain
    if config.app_window is not None and config.app_window.plus_account is not None: # @UndefinedVariable
        try:
            keyring.delete_password(config.app_name,config.app_window.plus_account) # @UndefinedVariable
        except:
            pass
    try:
        token_semaphore.acquire(1)
        config.token = None
        config.app_window.plus_account = None
        config.passwd = None
        config.nickname = None
    finally:
        if token_semaphore.available() < 1:
            token_semaphore.release(1)   

def setKeyring():
    try:
        #HACK set keyring backend explicitly
        if platform.system().startswith("Windows"):
            import keyring # @Reimport
            keyring.set_keyring(keyring.backends.Windows.WinVaultKeyring())   # @UndefinedVariable                  
        elif platform.system() == 'Darwin':
            import keyring # @Reimport
            keyring.set_keyring(keyring.backends.OS_X.Keyring())
        else: # Linux
            try:
                import keyring
                config.logger.debug("controller: keyring.get_keyring() %s",keyring.get_keyring())
                # test if secretstorage dbus is working
                import secretstorage  # @Reimport
                bus = secretstorage.dbus_init()
                res = list(secretstorage.get_all_collections(bus))
                # if yes, import it
                import keyring.backends.SecretService # @Reimport
                ss_keyring = keyring.backends.SecretService.Keyring()
                if ss_keyring.priority:
                    import keyring # @Reimport
                    # if priority is not 0, we set it as keyring system
                    keyring.set_keyring(ss_keyring)
            except Exception as e:
                pass
                #config.logger.error("controller: Linux keyring Exception %s",e)                
        #config.logger.debug("keyring: %s",str(keyring.get_keyring()))
    except Exception as e:
        config.logger.error("controller: keyring Exception %s",e) 
    
# returns True on successful authentification
def authentify():
    config.logger.info("authentify()")        
    try:
        if config.app_window is not None and config.app_window.plus_account is not None: # @UndefinedVariable
            # fetch passwd
            if config.passwd is None:
                setKeyring()
                try:
                    config.passwd = keyring.get_password(config.app_name, config.app_window.plus_account) # @UndefinedVariable
                except:
                    pass
            if config.passwd is None:
                config.logger.debug("connection: -> password not found")
                clearCredentials()
                return False
            else:
                config.logger.debug("connection: -> authentifying %s",config.app_window.plus_account) # @UndefinedVariable
                data = {"email":config.app_window.plus_account,"password": config.passwd} # @UndefinedVariable
                r = postData(config.auth_url,data,False)
                # returns 404: login wrong and 401: passwd wrong
                res = r.json()
                if "success" in res and res["success"]:
                    config.logger.debug("connection: -> authentified, token received")
                    if "result" in res and "user" in res["result"] and "nickname" in res["result"]["user"]:
                        nickname = res["result"]["user"]["nickname"]
                    else:
                        nickname = None
                    setToken(res["result"]["user"]["token"],nickname)
                    return True
                else:
                    config.logger.debug("connection: -> authentification failed")
                    if "error" in res:
                        config.app_window.sendmessage(res["error"]) # @UndefinedVariable
                    clearCredentials()
                    return False
    except requests.exceptions.RequestException as e:
        config.logger.error("connection: -> RequestException: %s",e)
        raise(e)
    except Exception as e:
        config.logger.debug("connection: -> Exception: %s",e)
        clearCredentials()
        raise(e)

def getHeaders(authorized=True,decompress=True):
    os,os_version = config.app_window.get_os() # @UndefinedVariable
    headers = {'user-agent': 'Artisan/' + __version__ + " (" + os + "; " + os_version + ")"}
    if authorized:
        token = getToken()
        if token is not None:
            headers["Authorization"] = "Bearer " + token
    if decompress:
        headers["Accept-Encoding"] = "deflate, compress, gzip" # identity should not be in here!
    return headers
    
def sendData(url,data,verb):
    if verb == "POST":
        return postData(url,data)
    else:
        return putData(url,data)
    
# TODO: implement!    
def putData(url,data):
    pass

def postData(url,data,authorized=True,compress=config.compress_posts):
    config.logger.info("connection:postData(%s,_data_,%s)",url,authorized)
#    config.logger.debug("connection: -> data: %s)",data) # don't log POST data as it might contain credentials!
    jsondata = json.dumps(data).encode("utf8")
    config.logger.debug("connection: -> size %s",len(jsondata))
    headers = getHeaders(authorized,decompress=False)
    headers["Content-Type"] = "application/json"
    if compress and len(jsondata) > config.post_compression_threshold:        
        postdata = gzip.compress(jsondata)
        config.logger.debug("connection: -> compressed size %s",len(postdata))
        headers["Content-Encoding"] = "gzip"
    else:
        postdata = jsondata
    r = requests.post(url,
            headers = headers,
            data    = postdata, 
            verify  = config.verify_ssl,
            timeout = (config.connect_timeout,config.read_timeout))
    config.logger.debug("connection: -> status %s",r.status_code)
    config.logger.debug("connection: -> time %s",r.elapsed.total_seconds())
    if authorized and r.status_code == 401: # authorisation failed
        config.logger.debug("connection: -> session token outdated (404)")
        # we re-authentify by renewing the session token and try again
        if authentify():
            headers = getHeaders(authorized,compress=compress) # recreate header with new token
            r = requests.post(url,
                    headers = headers,
                    data    = postdata, 
                    verify  = config.verify_ssl,
                    timeout = (config.connect_timeout,config.read_timeout))
            config.logger.debug("connection: -> status %s",r.status_code)
            config.logger.debug("connection: -> time %s",r.elapsed.total_seconds())
    return r

def getData(url,authorized=True):
    config.logger.info("getData(%s,%s)",url,authorized)
    headers = getHeaders(authorized)
#    config.logger.debug("connection: -> request headers %s",headers)
    r = requests.get(url,
        headers = headers,
        verify  = config.verify_ssl,
        timeout = (config.connect_timeout,config.read_timeout))
    config.logger.debug("connection: -> status %s",r.status_code)
#    config.logger.debug("connection: -> headers %s",r.headers)
    config.logger.debug("connection: -> time %s",r.elapsed.total_seconds())
    if authorized and r.status_code == 401: # authorisation failed
        config.logger.debug("connection: -> session token outdated (404) - re-authentify")
        # we re-authentify by renewing the session token and try again
        authentify()
        headers = getHeaders(authorized) # recreate header with new token
        r = requests.get(url,
                 headers = headers,
                 verify  = config.verify_ssl,
                 timeout = (config.connect_timeout,config.read_timeout))
        config.logger.debug("connection: -> status %s",r.status_code)
#        config.logger.debug("connection: -> headers %s",r.headers)
        config.logger.debug("connection: -> time %s",r.elapsed.total_seconds())
    try:
        config.logger.debug("connection: -> size %s",len(r.content))
#        config.logger.debug("connection: -> data %s",r.json())
    except:
        pass
    return r
