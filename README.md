## Automatic wafer dipper 


This project includes 2 modules to automate semiconductor research lab.

**(1) WaferDipper_Controller**

This provides a UI on PC to interface the Arduino controller of a custom-made 
wafer etching machine. Refer to the readme under that folder for more details 
about the construction of the etching machine and the code for Arduino.  

**(2) CommSignal_Arduino**

This module allows you to send signals read from Arduino controller to users via Slack or email. 
It can also be modified into a 2-way communication i.e. in case you want to control the 
research instrument via Arduino or just configuring the Arduino itself.


