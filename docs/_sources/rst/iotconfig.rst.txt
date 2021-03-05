Config, msg and Action Files
============================

pkg_ros_iot_bridge/config/config_pyiot.yaml
-------------------------------------------

:server_url:            URL of mqtt broker     
:server_port:           Port no. of hive mqtt server
:sub_order_topic:       Topic on which orders are published        
:qos:                   Quality of sevice
:sub_cb_ros_topic:      Topic on which orders are published after getting it from mqtt topic
:spread_sheet_id1:      Google sheet id on which Inventory, dispatched and shipped orders and Dashboard is maintained
:spread_sheet_id2:      Google sheet id of e-yantra

pkg_ros_iot_bridge/msg/msgMqttSub.msg
-------------------------------------

:timestamp: msg type: ``time``

:topic: msg type: ``string``

:message: msg type: ``string``

pkg_ros_iot_bridge/action/msgRosIot.action
------------------------------------------

goal
++++
:protocol: type: ``string`` - It contains the goal protocol like mqtt or http
:mode: type: ``string`` - It contains the goal mode
:topic: type: ``string`` - It contains the goal type
:message: type: ``string`` - It contains the message of the goal

result
++++++
:flag_success: type: ``boolean`` - If the goal is successfully processed, it will send True otherwise False

feedback
++++++++
:percentage_complete: type: ``int8`` - Percentage of goal processed will be sent as feedback