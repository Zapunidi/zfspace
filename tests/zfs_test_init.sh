#!/bin/bash
# Must be run from this directory

# Creating directory to play within
mkdir temp

# Creating files for zpool
dd if=/dev/zero of=temp/disk1 count=64 bs=1M
dd if=/dev/zero of=temp/disk2 count=64 bs=1M
dd if=/dev/zero of=temp/disk3 count=64 bs=1M

# Creating zpool of raidz type on these disks with internal mountpoint
sudo /sbin/zpool create -m `pwd`/temp/mnt zfspace_test raidz `pwd`/temp/disk1 `pwd`/temp/disk2 `pwd`/temp/disk3

# Making use of refreservation
sudo /sbin/zfs set refreservation=10M zfspace_test

# Creating children
sudo /sbin/zfs create zfspace_test/child1
sudo /sbin/zfs create zfspace_test/child2

# Setting easy read/write rules
sudo chmod 777 -R temp

# GENERATION 1

# Populate with files
dd if=/dev/urandom of=temp/mnt/par1 count=2 bs=1M
dd if=/dev/urandom of=temp/mnt/child1/file1 count=2 bs=1M
dd if=/dev/urandom of=temp/mnt/child2/file1 count=2 bs=1M

# Make assymetrical snapshots
sudo /sbin/zfs snap zfspace_test@generation1
sudo /sbin/zfs snap zfspace_test/child2@generation1

# GENERATION 2

# Populate with files
dd if=/dev/urandom of=temp/mnt/par2 count=1 bs=1M
dd if=/dev/urandom of=temp/mnt/child1/file2 count=1 bs=1M
dd if=/dev/urandom of=temp/mnt/child2/file2 count=1 bs=1M

# Make assymetrical snapshots
sudo /sbin/zfs snap zfspace_test@generation2
sudo /sbin/zfs snap zfspace_test/child1@generation2

# GENERATION 3

# Removing files
rm temp/mnt/par1
rm temp/mnt/child1/file1
rm temp/mnt/child2/file2

# Make full snapshots
sudo /sbin/zfs snap -r zfspace_test@generation_long_name_for_test3

# GENERATION 4

# Populate with files
dd if=/dev/urandom of=temp/mnt/par4 count=1 bs=1M
dd if=/dev/urandom of=temp/mnt/child1/file4 count=1 bs=1M
dd if=/dev/urandom of=temp/mnt/child2/file4 count=1 bs=1M

# Skipping snapshots

# GENERATION 5

# Populate with files
dd if=/dev/urandom of=temp/mnt/par5 count=2 bs=1M
dd if=/dev/urandom of=temp/mnt/child1/file5 count=1 bs=1M

# Removing files
rm temp/mnt/par2
rm temp/mnt/child1/file2
rm temp/mnt/child2/file1

# Make partial snapshots
sudo /sbin/zfs snap zfspace_test@generation5
sudo /sbin/zfs snap zfspace_test/child1@generation5

# GENERATION 6

# Removing files
rm temp/mnt/par5

# Populate with files
dd if=/dev/urandom of=temp/mnt/par6 count=4 bs=1M
