---
layout: single
permalink: /devices/websockets/
title: "WebSockets"
excerpt: "JSON"
header:
  overlay_image: /assets/images/websockets.jpg
  image: /assets/images/websocketso.jpg
  teaser: assets/images/websockets.jpg
---

Artisan supports the communication of JSON over WebSockets.

<figure>
<a href="{{ site.baseurl }}/assets/images/websockets-tab.png">
<img src="{{ site.baseurl }}/assets/images/websockets-tab.png"></a>
    <figcaption>WebSockets tab</figcaption>
</figure>

## WebSocket Devices

There is one main WebSocket device type and 4 extra device, each delivering two channels, thus 10 channels of data in total. 

The WebSocket connection as well as those 10 WebSocket channels are configured in the WebSocket dialog (menu Config >> Port, 7th tab).

The WebSocket endpoint `ws://<host>:<port>/<path>`  is configured via the `<host>`, `<port>` and ´<path>` components.

Connect, reconnect and request timeouts are specified in seconds.

Data request messages have the following general form:

```
{
  <Command>: <Data Request>, 
  <Message ID>: nnnn, 
  <Machine ID>: <ID>
}
```

All node tags can be configured in the WebSocket tab.

The message id, the number `nnn`, is automatically generated. The corresponding response is expected to hold the same message id at its <Message ID> node. Multiple machines can be differentiated via the `<Machine ID>` node with the value taken from the `ID` setting.

If the `Data Request` field is non-empty, a corresponding request for data of the above form is send each sampling interval. This request is expected to be responded by a message holding data for all WebSocket inputs.

If the `Request` field of one WebSocket input channel is non-empty, a corresponding data request message with its field value taken as `<Command>` node value is send each sampling interval. This request is expected to be responded by a message holding data for just this WebSocket input.

Note that requesting the data for all WebSocket inputs in one `Data Request` is usually more efficient.

A data request message as described above is expected to be answered by a response message of the following form

```
{
  <Message ID>: nnnn,
  <Data>: { <node_0> : v0, .., <node_n> : vn} 
}
```

with the message id `nnn` has to correspond to the one of the request message and the `<node_0>`,..,`<node_n>` nodes hold the data for the corresponding WebSocket input channels.


## WebSocket Push Messages

Artisan is listening to two push messages that are received without an explicit request.

- CHARGE Message: `{ <Message>: <CHARGE> }`
- DROP Message: `{ <Message>: <DROP> }`

On receiving the CHARGE message, the CHARGE event is set. On receiving the DROP message, the DROP event is set.

In case Artisan is not yet recording on receiving the CHARGE message and the `START on CHARGE` flag is ticked, the recording is automatically started before the CHARGE event is registered.

In case Artisan is recording on receiving the DROP message and the `OFF on DROP` flag is ticked, the recording is automatically stopped after the DROP event is registered.



## WebSocket Events

Artisan is listening on Event Messages of the format

```
{
  <Message>: <Event>,
  <data>: { <Node> : <Tag>} 
}
```

A message with  a `<Tag>` from the set `<DRY>`, `<FCs>`, `<FCe>`, `<SCs>`, `<SCe>` activates the corresponding event button in Artisan.


## WebSocket Commands

Buttons and sliders can send out `WebSocket Command`s. The following commands in the action description are supported.

Note that WebSocket Command actions can be sequenced by separating them with semicolons like in `{% raw %}sleep(2.5); send({{"command": "keepAlive"}}){% endraw %}`


* `send(<json>)`:  
if the `<json>` text respects the JSON format it is send to the connected WebSocket server
* `sleep(s)` :  
delay processing by `s` seconds (float)
* `read(<json>)`: 
if the `<json>` text respects the JSON format it is send to the connected WebSocket server and the response is bound to the variable `_`
* `button(<expr>) :
sets the last button state to either "pressed" if <expr> evalutes to 1 or True and "normal", otherwise

Example Button Action:
{% raw %}````
read({{"command": "getRoasterState"}});button(_["data"]["state"] == "ready")
```{% endraw %}
Send `getRoasterState` request on button perss and sets the button in "pressed" state if response indicate `ready').

The placeholder `{}` is substituted by the event value in button and slider actions.  However, if the WebSocket Command is used as button or  slider actinon where this substition takes place all regular brackets have to be escaped by duplicating them like in the following example

{% raw %}```
send(
  {{ "command": "setControlParams", 
     "params": {{ "burner": {} }}
  }}
)
```{% endraw %}

The placeholders `{BT}`, `{ET}`, `{time}` substituted in WebSocket Command actions by the current bean temperature (BT), environmental temperature (ET) or the time in seconds (float). Again, if such a placeholder is used in a WebSocket Command, all JSON elements have to be wrapped in an extra set of brackets like in the following example.

```
{% raw %}
send({{"command": "keepAlive", "params": {BT}}})
{% endraw %}
```