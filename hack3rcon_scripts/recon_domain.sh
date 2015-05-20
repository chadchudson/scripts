#!/bin/bash
clear 

echo
echo
echo -n "Enter a domain: "
read domain

# Check for no response
if [ -z $domain ];then
     echo
     echo "You did not enter a domain name."
     exit
fi

echo "You can follow directions. Starting recon on $domain."
echo
read -p "Press <enter> to continue."

# Update websites from google search on dns report dnsstuff.com dnscolos.com/dnsreport.php(no automate)
firefox &
sleep 4
firefox -new-tab http://www.intodns.com/$domain &
sleep 1
firefox -new-tab http://dnsstuff.com/tools#dnsReport|type=domain&value=$domain & # need to register
firefox -new-tab xxx &
sleep 1
firefox -new-tab xxx &
firefox -new-tab xxx &
sleep 1
firefox -new-tab xxx &
firefox -new-tab xxx &


