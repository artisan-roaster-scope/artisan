#
# ABOUT
# MQTT support for Artisan

# LICENSE
# This program or module is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 2 of the License, or
# version 3 of the License, or (at your option) any later version. It is
# provided for educational purposes and is distributed in the hope that
# it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
# the GNU General Public License for more details.

# AUTHOR
# Marko Luther, 2026


import platform
import json
import logging
import jmespath
import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion, MQTTProtocolVersion
from PyQt6.QtWidgets import QApplication
from typing import Any, Final, TYPE_CHECKING

if TYPE_CHECKING:
    from artisanlib.main import ApplicationWindow # pylint: disable=unused-import
    from paho.mqtt.reasoncodes import ReasonCodes
    from paho.mqtt.properties import Properties
    from paho.mqtt.client import DisconnectFlags

from artisanlib.util import fromCtoFstrict, fromFtoCstrict

_log: Final[logging.Logger] = logging.getLogger(__name__)

class mqttport:
    """ this class handles the communications with all the MQTT devices"""

    KEYRING_SERVICE: Final[str] = 'artisan.mqtt'
    CHANNELS:Final[int] = 12 # maximal number of MQTT channels
    PROTOCOL_VERSIONS:Final[dict[int, MQTTProtocolVersion]] = {
        0: mqtt.MQTTv31,
        1: mqtt.MQTTv311,
        2: mqtt.MQTTv5
    }
    PROTOCOL_VERSION_LABELS:Final[dict[int, str]] = {
        0: 'MQTT v3.1',
        1: 'MQTT v3.1.1',
        2: 'MQTT v5'
    }
    SUPPORTED_TRANSPORT:list[str] = ['TCP', 'WebSockets']

    __slots__ = [ 'aw', '_logging', 'protocol_version', 'transport', 'tls', 'default_host', 'host', 'port', 'user', 'password',
            'connect_timeout', 'keepalive', 'topic', 'channel_topics', 'channel_nodes', 'channel_modes', 'channel_node_expressions', 'readings', 'client' ]

    def __init__(self, aw:'ApplicationWindow') -> None:
        super().__init__()
        self.aw = aw

        self._logging:bool = False # device logging flag

        self.protocol_version:int = 1 # 0:MQTTv31, 1: MQTTv311 (default), 2: MQTTv5
        self.transport:int = 0  # 0:'tcp' (default, use port 1883 or 8883 with TLS) or 1:'websockets' (use port 443) # self.SUPPORTED_TRANSPORT
        self.tls:bool = False
        self.default_host:Final[str] = '127.0.0.1'
        self.host:str = self.default_host # MQTT broker address
        self.port:int = 1883 # the TCP port
        self.user:str = ''
        self.password:str = ''
        self.connect_timeout:float = 3 # in seconds (default 5s)
        self.keepalive:int = 2 # in seconds (default 60s)
        self.topic:str = '/#' # main topic subscription
        # channels
        self.channel_topics:list[str] = ['']*self.CHANNELS  # optional individual topic subscription
        self.channel_nodes:list[str] = ['']*self.CHANNELS   # data selectors (jmespath format)
        self.channel_node_expressions:list[jmespath.parser.ParsedResult|None] = [None]*self.CHANNELS # compiled jmespath data selectors
        self.channel_modes:list[str] = ['C']*self.CHANNELS  # temperature mode; one of '', 'C' or 'F'

        # MQTT data
        self.readings:list[float] = [-1.0]*self.CHANNELS # last data received per channel

        self.client:mqtt.Client|None = None



    #################################################################
    # paho callbacks


    def on_connect_handler(self, client:mqtt.Client, _userdata:Any, _flags:dict[str, Any], status:'ReasonCodes', _properties:'Properties|None') -> None:
        if status == 0:
            _log.debug('MQTT connected')
            self.aw.sendmessageSignal.emit(QApplication.translate('Message', '{} connected').format('MQTT'),True,None)

            # subscribe to main topic
            res:int
            if self.topic.strip() != '':
                _log.debug('subscribing to main topic %s', self.topic)
                try:
                    res,_ = client.subscribe(self.topic)
                    if res != 0:
                        _log.debug('subscribing to %s failed', self.topic)
                except Exception as e: # pylint: disable=broad-except
                    self.aw.qmc.adderror(QApplication.translate('Error Message','MQTT failed to subscribe to {0}: {1}').format(self.topic, e))
            # subscribe to input topics
            input_topics = [topic.strip() for topic in self.channel_topics if topic.strip() != '']
            if len(input_topics) > 0:
                _log.debug('subscribing to input topics %s', input_topics)
                try:
                    res,_ = client.subscribe([(topic, 0) for topic in input_topics])
                    if res != 0:
                        _log.debug('subscribing to %s failed', input_topics)
                except Exception as e: # pylint: disable=broad-except
                    _log.error(e)
        else:
            _log.debug('MQTT failed to connect to %s. Error: %s', self.host, status)
            self.aw.qmc.adderror(QApplication.translate('Error Message','MQTT failed to connect to {0}: {1}').format(self.host,status))

    def on_disconnect_handler(self, _client:mqtt.Client, _userdata:Any, _disconnect_flags:'DisconnectFlags|None', status:'ReasonCodes', _properties:'Properties|None') -> None:
        _log.debug('MQTT disconnected: %s', status.getName()) # type:ignore[no-untyped-call]
        self.aw.sendmessageSignal.emit(QApplication.translate('Message', '{} disconnected').format('MQTT'),True,None)

    def on_subscribe_handler(self, _client:mqtt.Client, _userdata:Any, _mid:int, reason_code_list:'list[ReasonCodes]', _properties:'Properties') -> None:
        _log.debug('on_subscribe_handler: %s', [(rc.getId(rc.getName()), rc.getName()) for rc in reason_code_list]) # type:ignore[no-untyped-call]
        for rc in reason_code_list:
            name = rc.getName() # type:ignore[no-untyped-call]
            if rc.getId(name) != 0: # type:ignore[no-untyped-call]
                self.aw.qmc.adderror(QApplication.translate('Error Message','MQTT subscribe error: {0}').format(name))


    def on_message_handler(self, _client:mqtt.Client, _userdata:Any, message:mqtt.MQTTMessage) -> None:
        try:
            received_data = json.loads(message.payload.decode('utf-8')) # Decode bytes, then deserialize JSON
            if self._logging:
                _log.debug('received_data:\n%s', json.dumps(received_data, indent=3))
                if mqtt.topic_matches_sub(self.topic, message.topic):
                    _log.debug('message for main topic %s received', self.topic)

            self.update_data(received_data, message.topic)

        except json.JSONDecodeError:
            _log.debug('Received non-JSON message from %s', message.topic)



    #################################################################
    #

    # renders the given data as JSON string and publishes it to the given topic on the connected broker
    def publish(self, topic:str, data:Any, device_logging:bool) -> None:
        _log.debug('publish(%s,%s)', topic, data)
        if self.client is None:
            # if not connected we start the client (which will automatically subscribe to the configured topics)
            self.start(device_logging)
        if self.client is not None and self.client.is_connected():
            self.client.publish(topic, json.dumps(data), qos=0, retain=False)


    #################################################################
    #

    def reset_readings(self) -> None:
        _log.debug('reset_readings()')
        self.readings = [-1.0]*self.CHANNELS

    def compile_node_expressions(self) -> None:
        for i, node in enumerate(self.channel_nodes):
            try:
                self.channel_node_expressions[i] = jmespath.compile(node)
            except Exception:  # pylint: disable=broad-except
                self.channel_node_expressions[i] = None

    def update_data(self, data:Any, topic:str) -> None:
        for i, channel_topic in enumerate(self.channel_topics):
            node_expression:jmespath.parser.ParsedResult|None = self.channel_node_expressions[i]
            res:float|None = None
            if (node_expression is not None and
                (mqtt.topic_matches_sub(channel_topic, topic) or (mqtt.topic_matches_sub(self.topic, topic) and channel_topic == ''))):
                try:
                    res = node_expression.search(data)
                except Exception:  # pylint: disable=broad-except
                    pass # formula might fail, like applying avg() to None result
            elif node_expression is None and mqtt.topic_matches_sub(channel_topic, topic): # empty node string, but topic matches the channel topic
                # assume the data is just a string containing a single float
                try:
                    res = float(data)
                except Exception as e:  # pylint: disable=broad-except
                    _log.debug(e)
            if res is not None:
                val:float = float(res)
                # convert temperature scale
                if self.channel_modes[i] == 'C' and self.aw.qmc.mode == 'F':
                    val = fromCtoFstrict(val)
                elif self.channel_modes[i] == 'F' and self.aw.qmc.mode == 'C':
                    val = fromFtoCstrict(val)
                # register converted reading
                self.readings[i] =  val

#
    def store_credentials(self) -> None:
        if self.user != '':
            try:
                import keyring
                keyring.set_password(self.KEYRING_SERVICE, self.user, self.password)
                _log.debug('keyring set MQTT password (%s)', self.user)
            except Exception as e: # pylint: disable=broad-except
                _log.debug('Failed to save MQTT keyring password: %s', e)
                if (not platform.system().startswith('Windows') and platform.system() != 'Darwin'):
                    err_msg = QApplication.translate('Plus', ('Keyring Error: Ensure that gnome-keyring is installed.'))
                else:
                    err_msg = QApplication.translate('Message', ('Error: Failed to store MQTT password'))
                self.aw.sendmessageSignal.emit(err_msg, True, None)

    def load_credentials(self) -> None:
        if self.user != '':
            try:
                import keyring
                passwd:str|None = keyring.get_password(self.KEYRING_SERVICE, self.user)
                if passwd is None:
                    self.password = ''
                    _log.debug('keyring failed to retrieve MQTT password (%s)', self.user)
                    err_msg = QApplication.translate('Message', ('Error: failed to retrieve MQTT password'))
                    self.aw.sendmessageSignal.emit(err_msg, True, None)
                else:
                    self.password = passwd
                _log.debug('keyring loaded MQTT password (%s)', self.user)
            except Exception as e: # pylint: disable=broad-except
                _log.debug('Failed to retrieve MQTT keyring password: %s', e)
                err_msg = QApplication.translate('Message', ('Error: failed to retrieve MQTT password'))
                self.aw.sendmessageSignal.emit(err_msg, True, None)

    def clear_credentials(self) -> None:
        if self.user != '':
            try:
                import keyring
                keyring.delete_password(self.KEYRING_SERVICE, self.user)
                _log.debug('keyring cleared MQTT credentials (%s)', self.user)
            except Exception as e:  # pylint: disable=broad-except
                _log.debug('Failed to clear MQTT keyring password: %s', e)
                err_msg = QApplication.translate('Message', ('Error: failed to clear MQTT password'))
                self.aw.sendmessageSignal.emit(err_msg, True, None)

#

    def start(self, device_logging:bool) -> None:
        _log.debug('starting MQTT')
        self._logging = device_logging

        # clear readings
        self.reset_readings()

        # compile node expressions
        self.compile_node_expressions()

        # create mqtt client object and configure it
        if self.PROTOCOL_VERSIONS[self.protocol_version] == mqtt.MQTTv5: # MQTTv5
            self.client = mqtt.Client( # Xtype:ignore[call-arg]
                callback_api_version = CallbackAPIVersion.VERSION2,
                protocol = self.PROTOCOL_VERSIONS[self.protocol_version],
                transport = self.SUPPORTED_TRANSPORT[self.transport].lower()) # type:ignore[arg-type] # clean_session parameter not support for MQTTv5 clients
        else:
            self.client = mqtt.Client( # Xtype:ignore[call-arg]
                callback_api_version = CallbackAPIVersion.VERSION2,
                protocol = self.PROTOCOL_VERSIONS[self.protocol_version],
                transport = self.SUPPORTED_TRANSPORT[self.transport].lower(), # type:ignore[arg-type]
                clean_session = True) # if client_id is not set a random number is generated and clean_session needs to be True

        # configure
        if self.tls:
            self.client.tls_set()
        if self.user != '':
            self.client.username_pw_set(self.user, self.password)
        # set paho callbacks
        self.client.on_connect = self.on_connect_handler # type:ignore[assignment]
        self.client.on_disconnect = self.on_disconnect_handler # type:ignore[assignment]
        self.client.on_subscribe = self.on_subscribe_handler # type:ignore[assignment]
        self.client.on_message = self.on_message_handler
        # connect
        if self.protocol_version == 2: # MQTTv5
            self.client.connect(self.host, self.port, self.keepalive, clean_start = True)
        else:
            self.client.connect(self.host, self.port, self.keepalive)
        # start client loop .loop_start()
        self.client.loop_start()
        _log.debug('MQTT started')

    def stop(self) -> None:
        _log.debug('stopping MQTT')
        if self.client is not None:
            if self.client.is_connected():
                self.client.disconnect()
            # stop client loop
            self.client.loop_stop()
        # release mqtt client object
        self.client = None
        _log.debug('MQTT stopped')
