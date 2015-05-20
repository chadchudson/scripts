#!/bin/bash
clear 

rm robots.txt tmp 2>/dev/null

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

wget -q $domain/robots.txt
# awk example
cat robots.txt | grep 'Disallow' | awk '{print $2}' > tmp

# or

# cut example
# cat robots.txt | grep 'Disallow' | cut -d ' ' -f2 > tmp_cut

firefox &
sleep 4

# Read a list and open each line in a new tab
for i in $(cat tmp); do
     firefox -new-tab http://www.$domain$i &
     sleep 1
done

