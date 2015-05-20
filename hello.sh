#!/bin/bash
_dow="$(date +"%A")"
echo "Hello $(whoami)!"
echo "The date today is $(date)"
echo "Today is $_dow"
echo "Again, today is (date +"%A")"