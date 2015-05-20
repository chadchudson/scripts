#!/bin/bash
clear 

echo
echo
echo -n "First name: "
read fname

# Check for no response
if [ -z $fname ];then
     echo
     echo "You did not enter a first name."
     exit
fi

echo
echo -n "Last name: "
read lname

# Check for no response
if [ -z $lname ];then
     echo
     echo "You did not enter a last name."
     exit
fi

echo "You can follow directions. Starting recon on $fname $lname."
echo
read -p "Press <enter> to continue."

firefox &
sleep 4
firefox http://www.411.com/name/$fname-$lname/ &
sleep 1
firefox -new-tab http://cvgadget.com/person/$fname/$lname &
firefox -new-tab http://www.peekyou.com/$fname_$lname/ &
sleep 1
firefox -new-tab http://www.addresses.com/people/$fname+$lname &
firefox -new-tab https://pipl.com/search/?q=$fname+$lname&l=&sloc=&in=5 &
sleep 1
firefox -new-tab http://www.spokeo.com/search?q=$fname+$lname &
firefox -new-tab http://www.zabasearch.com/people/$fname+$lname/ &
firefox -new-tab https://www.google.com/?gws_rd=ssl#q=$fname+$lname/ &
firefox -new-tab http://radaris.com/p/$fname/$lname/ &


