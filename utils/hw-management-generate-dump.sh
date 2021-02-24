#!/bin/bash

# see SONiC generate_dump script for potential invokations

dump_path=/tmp/hw-mgmt-dump
allow_disruptive_hwdump=false

while [ ! -z "$1" ]; do
   case $1 in
      -a) allow_disruptive_hwdump=true;;
   esac
   shift
done

runcmd() {
   echo ":: BEGIN CMD: $@"
   "$@"
   echo ":: END CMD: $@"
}

dumpfile() {
   local filename="$1"
   echo ":: BEGIN FILE: $filename"
   cat "$filename"
   if [ "$(tail -c 1 "$filename")" != "\n" ]; then
      echo
   fi
   echo ":: END FILE: $filename"
}

{
   runcmd arista dump
   runcmd arista syseeprom
   runcmd arista show platform reboot-cause -a -H
   runcmd arista show platform environment
   runcmd arista show chassis summary

   for cachefile in $(find /run/platform_cache/arista -type f); do
      dumpfile $cachefile
   done

   dumpfile /proc/scd

   runcmd losetup -l
   runcmd lsblk -o NAME,LABEL,FSTYPE,FSSIZE,FSUSED,FSAVAIL,SIZE,RO,TYPE,VENDOR,MODEL,SERIAL,ALIGNMENT,MOUNTPOINT
   runcmd fdisk -l "/dev/$(lsblk -no pkname "$(df | awk '/\/host$/ {print $1}')")"

} > $dump_path
