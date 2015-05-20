#!/bin/bash

clear


# Global variables
user=$(whoami)
break="=============================================="


echo
echo
echo "Hello Hack3rcon%!"
echo
echo $break
echo
echo "Good moring, "$user
echo
echo $break
echo $break
ping -c3 google.com
echo
echo "Ping complete."
read -p "Press <enter> to continue."

ifconfig

rm tmp 2>/dev/null # 2>/dev/null hide output to user

