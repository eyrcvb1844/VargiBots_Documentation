Introduction
============

This project we have worked on is set in an automated warehouse setting where essential packages are required to be sent out to different parts of the city. Heavy focus has been given to the aspect of automation. The ware house consists of two robotic arms, as the requirements are sent to the warehouse, one robotic arm will identify the packages from a shelf and place them on a conveyor belt and the other robotic arm at the end of the conveyor belt will pick these objects from the conveyor and place them into bins. Each bin represents a destination for the package. As packages are sent out from the warehouse, there will also be alerts sent to the user via email notifying them about the package being shipped from the warehouse.

The orders have been taken from MQTT topic with the use of ros-iot action server, and then further processing of these orders taken has been done one by one in the action client, as it receives them through a rostopic, where the action server publishes the orders as they come.

The inventory is maintained in the action client node. The action client node sends the ur5#1 arm (first robotic arm) the necessary commands to pick the boxes up with respect to the priority of the order, with coordinates of the box on the shelf, if the order is available; else the information of the failure of order is conveyed.

Following this the ur5#1 arm picks the appropriate box up and places it on the conveyor belt, and tells which priority box is being sent to ur5#2 (second robotic arm). It also sends information that a specific order has been dispatched.

The ur5#2 picks the box from the conveyor as the conveyor stops when the box reaches under the vacuum gripper and drops it into the bin mentioning the same priority as that of the box. It also sends information that the order has been shipped.

All these information are published comprehensively on Google Sheets, this data is used to auto send users email alerts using Google Apps Script. Dashboard sheet, and the same is used for presenting all relevant details on the Dashboard Website. 

Team Members:
Aniruddha Mandal, Anish Konar, Chirantan Ganguly, Sagnik Nayak from University of Calcutta

Video
-----

.. raw:: html
    
   <iframe width="100%" height="400" src="https://www.youtube.com/embed/QIGFrAWsTJA" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>
