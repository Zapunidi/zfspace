#!/bin/bash
# Must be run from this directory
# Deleting everything created by init script

# Simultaneously destroy all associated zfs and main zpool
sudo /sbin/zpool destroy zfspace_test

# Destroy write-protected mountpoint along with all temporary data
yes|rm -R temp