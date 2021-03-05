#!/usr/bin/env python

# ROS Node - Action Server - IoT ROS Bridge

import rospy
import actionlib
import threading
import requests
import datetime

# Message Class that is used by ROS Actions internally
from pkg_ros_iot_bridge.msg import msgRosIotAction
# Message Class that is used for Goal Messages
from pkg_ros_iot_bridge.msg import msgRosIotGoal
# Message Class that is used for Result Messages
from pkg_ros_iot_bridge.msg import msgRosIotResult
# Message Class that is used for Feedback Messages
from pkg_ros_iot_bridge.msg import msgRosIotFeedback

# Message Class for MQTT Subscription Messages
from pkg_ros_iot_bridge.msg import msgMqttSub

# Custom Python Module to perfrom MQTT Tasks
from pyiot import iot

orders_dict = {}

class IotRosBridgeActionServer:
    '''
        This is the class for the Action Server which acts as a ROS-IoT Bridge

        Receives the orders as MQTT requests, sends to the action client for processing and publishes the orders on the spreadsheet. 
        Receives Goals from the client for publishing data on the spreadsheets after processing them.
        Publishes data on the spreadsheet through HTTP requests.
        
        :param _as: Action Server Object
        :param _config_mqtt_server_url: url of the hive mqtt server
        :param _config_mqtt_server_port: port of the hive mqtt server
        :param _config_mqtt_qos: mqtt quality of service
        :param _config_sub_order_topic: the mqtt topic on which orders are received
        :param _config_mqtt_sub_cb_ros_topic: the topic on which orders are sent to other ros nodes
        :param _config_google_apps_script: Apps Script deployment id of our google sheet
        :param _config_eyrc_google_apps_script: Apps Script deployment id of google sheet of eyrc
    '''

    def __init__(self):
        """
        Initializes the Action Server.
        Reads and Stores IoT Configuration data from Parameter Server.
        It initializes the subcriber that receives order from MQTT topic and also defines the publisher to the rostopic /ros_iot_bridge/mqtt/sub.
        """

        # Initialize the Action Server
        self._as = actionlib.ActionServer('/action_ros_iot',
                                          msgRosIotAction,
                                          self.on_goal,
                                          self.on_cancel,
                                          auto_start=False)

        #     * self.on_goal - It is the fuction pointer which points to a function which will be called
        #                      when the Action Server receives a Goal.

        #     * self.on_cancel - It is the fuction pointer which points to a function which will be called
        #                      when the Action Server receives a Cancel Request.

        # Read and Store IoT Configuration data from Parameter Server
        param_config_iot = rospy.get_param('config_iot')
        self._config_mqtt_server_url = param_config_iot['mqtt']['server_url']
        self._config_mqtt_server_port = param_config_iot['mqtt']['server_port']
        self._config_mqtt_qos = param_config_iot['mqtt']['qos']
        self._config_mqtt_sub_cb_ros_topic = param_config_iot['mqtt']['sub_cb_ros_topic']
        self._config_sub_order_topic = param_config_iot['mqtt']['sub_order_topic']

        self._config_google_apps_script = param_config_iot['google_apps']['spread_sheet_id1']
        # self._config_eyrc_google_apps_script=param_config_iot['google_apps']['spread_sheet_id2']

        rospy.set_param('/online_order_config/mqtt_unique_id', 'axaKcGsN')

        # Initialize ROS Topic Publication
        # Incoming message from MQTT Subscription will be published on a ROS Topic (/ros_iot_bridge/mqtt/sub).
        # ROS Nodes can subscribe to this ROS Topic (/ros_iot_bridge/mqtt/sub) to get messages from MQTT Subscription.
        self._handle_ros_pub = rospy.Publisher(
            self._config_mqtt_sub_cb_ros_topic, msgMqttSub)

        # self.mqtt_sub_callback() function will be called when there is a message from MQTT Subscription.
        ret = iot.mqtt_subscribe_thread_start(self.mqtt_sub_callback,
                                              self._config_mqtt_server_url,
                                              self._config_mqtt_server_port,
                                              self._config_sub_order_topic,
                                              self._config_mqtt_qos)
        if(ret == 0):
            rospy.loginfo("MQTT Subscribe Thread Started")
        else:
            rospy.logerr("Failed to start MQTT Subscribe Thread")

        # Start the Action Server
        self._as.start()

        rospy.loginfo("Started ROS-IoT Bridge Action Server.")

    def mqtt_sub_callback(self, client, userdata, message):
        '''
            This is a callback function for the MQTT Subscription which receives orders.
            It then publishes the orders to the rostopic /ros_iot_bridge/mqtt/sub for processing.
            It also publishes the Incoming Orders to the spreadsheet using HTTP protocol.
            It stores all the data of orders in a dictionary orders_dict with order id as key.

            :param message: the message received from mqtt topic
        '''

        global orders_dict
        payload = str(message.payload.decode("utf-8"))

        print("[MQTT SUB CB] Message: ", payload)
        print("[MQTT SUB CB] Topic: ", message.topic)

        msg_mqtt_sub = msgMqttSub()
        msg_mqtt_sub.timestamp = rospy.Time.now()
        msg_mqtt_sub.topic = message.topic
        msg_mqtt_sub.message = payload
        order = eval(payload)
        orders_dict[order["order_id"]] = order

        #publisher
        self._handle_ros_pub.publish(msg_mqtt_sub) 
        order_cost = {"Clothes": [150, "LP"], "Medicine": [450, "HP"], "Food": [250, "MP"]}
        parameters = {"id": "IncomingOrders", "Team Id": "VB#1844", "Unique Id": "axaKcGsN", "Order ID": order["order_id"], "Order Date and Time": order["order_time"],	"Item": order["item"],
                      "Priority": order_cost[order["item"]][1], "Order Quantity": order["qty"],	"City": order["city"], "Longitude": order["lon"], "Latitude": order["lat"],	"Cost": order_cost[order["item"]][0], "Quantity": 1}
        URL1 = "https://script.google.com/macros/s/" + \
            self._config_google_apps_script + "/exec"
        # URL2 = "https://script.google.com/macros/s/" + self._config_eyrc_google_apps_script + "/exec"
        requests.get(URL1, params=parameters)
        # requests.get(URL2, params=parameters)

    def on_goal(self, goal_handle):
        '''
            This function will be called when Action Server receives a Goal.
            It sends the goal to process_goal for further processing

            :param goal_handle: goal_handle: the goal received from the action client
        '''

        goal = goal_handle.get_goal()

        rospy.loginfo("Received new goal from Client")
        rospy.loginfo(goal)

        # Validate incoming goal parameters
        if(goal.protocol == "http"):

            if((goal.mode == "inv") or (goal.mode == "disp") or (goal.mode == "ship") or (goal.mode == "fail")):
                goal_handle.set_accepted()

                # Start a new thread to process new goal from the client (For Asynchronous Processing of Goals)
                # 'self.process_goal' - is the function pointer which points to a function that will process incoming Goals
                thread = threading.Thread(name="worker",
                                          target=self.process_goal,
                                          args=(goal_handle,))
                thread.start()

            else:
                goal_handle.set_rejected()
                return

        else:
            goal_handle.set_rejected()
            return

    def process_goal(self, goal_handle):
        '''
            This function is called as a separate thread to process Goal.
            
            It receives the status of the package (like dispatched or shipped) and its order id.
            Types(modes) of goals:
                1. inv: It receives the inventory as a string of dictionaries separated by ";". It splits the string, stores them in a list and converts them into dictionaries. Then it is published to the Inventory sheet one by one.
                2. disp: It receives the order id when it is dispatched. It searches the order from the order list(orders_dict) and publishes it to the OrdersDispatched sheet.
                3. ship: It receives the order id when it is shipped. It searches the order from the order list(orders_dict) and publishes it to the OrdersShipped sheet.
                4. fail: It receives the order id when it is not present in the inventory and sends the status NO in both OrdersDispatched and OrdersShipped sheets.

            :param goal_handle: the goal received from the action client
        '''

        global orders_dict
        flag_success = False
        result = msgRosIotResult()

        goal_id = goal_handle.get_goal_id()
        rospy.loginfo("Processing goal : " + str(goal_id.id))

        goal = goal_handle.get_goal()
        x = datetime.datetime.now()
        d = x.strftime("%d")
        m = x.strftime("%m")
        y = x.strftime("%Y")
        h = x.strftime("%H")
        mi = x.strftime("%M")
        s = x.strftime("%S")
        dt = "{}/{}/{} {}:{}:{}".format(d, m, y, h, mi, s)

        # Goal Processing
        if(goal.mode != "inv"):
            temp = orders_dict[goal.message]
            order_cost = {"Clothes": [150, "LP", 5], "Medicine": [
                450, "HP", 1], "Food": [250, "MP", 3]}
            parameters = {"id": "", "Team Id": "VB#1844", "Unique Id": "axaKcGsN", "Item": temp["item"], "Priority": order_cost[temp["item"]][1], "Cost": order_cost[temp["item"]][0],
                          "Order ID": goal.message, "Order Date and Time": temp["order_time"], "City": temp["city"], "Order Quantity": temp["qty"], "Longitude": temp["lon"], "Latitude": temp["lat"], "Dispatch Quantity": 1,
                          "Dispatch Status": "YES", "Dispatch Date and Time": dt, "Shipped Quantity": 1, "Shipped Status": "YES", "Shipped Date and Time": dt, "Estimated Time of Delivery": ""}
            deli = x + datetime.timedelta(days=order_cost[temp["item"]][2])
            d = deli.strftime("%d")
            m = deli.strftime("%m")
            y = deli.strftime("%Y")
            parameters["Estimated Time of Delivery"] = "{}/{}/{}".format(
                d, m, y)
        URL1 = "https://script.google.com/macros/s/" + \
            self._config_google_apps_script + "/exec"
        # URL2 = "https://script.google.com/macros/s/" + self._config_eyrc_google_apps_script + "/exec"

        if(goal.protocol == "http"):
            rospy.logwarn("HTTP")

            if(goal.mode == "inv"):
                inv_list = goal.message.split(";")
                for i in inv_list:
                    inv_dict = eval(i)
                    requests.get(URL1, params=inv_dict)
            elif(goal.mode == "disp"):
                parameters["id"] = "OrdersDispatched"
                requests.get(URL1, params=parameters)
                # requests.get(URL2, params=parameters)
            elif(goal.mode == "ship"):
                parameters["id"] = "OrdersShipped"
                requests.get(URL1, params=parameters)
                # requests.get(URL2, params=parameters)
            elif(goal.mode == "fail"):
                parameters["id"] = "OrdersDispatched"
                parameters["Dispatch Status"] = "NO"
                requests.get(URL1, params=parameters)
                # requests.get(URL2, params=parameters)
                parameters["id"] = "OrdersShipped"
                parameters["Shipped Status"] = "NO"
                requests.get(URL1, params=parameters)
                # requests.get(URL2, params=parameters)

        rospy.loginfo("Send goal result to client")
        if (result.flag_success == True):
            rospy.loginfo("Succeeded")
            goal_handle.set_succeeded(result)
        else:
            rospy.loginfo("Goal Failed. Aborting.")
            goal_handle.set_aborted(result)

        rospy.loginfo("Goal ID: " + str(goal_id.id) + " Goal Processing Done.")

    def on_cancel(self, goal_handle):
        '''
            This function will be called when Goal Cancel request is send to the Action Server
        '''

        rospy.loginfo("Received cancel request.")
        goal_id = goal_handle.get_goal_id()

def main():
    '''
        It is the main function which initializes the node and keeps the node running.
    '''

    rospy.init_node('node_iot_ros_bridge_action_server')
    action_server = IotRosBridgeActionServer()
    rospy.spin()

if __name__ == '__main__':
    main()