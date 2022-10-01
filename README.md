# zfspace
Console tool to find occupied pool space in ZFS on Linux.
The tool uses pure python3 with shell commands to collect useful information from ZFS and show in convinient way. 

## Introduction

ZFS is a non-trivial LVS filesystem with snapshots, deduplication, filesystems hierarchy and so on. 
Common tools, such as `dh` or `ls` can't provide relevant information when you **need to free some space**.
There is an [explanatory article](https://zedfs.com/all-you-have-to-know-about-reading-zfs-disk-usage/) about this.
Snapshots USED space is another puzzle. ZFS only shows space freed by destroying individual snapshot or space 
occupied by all filesystem snapshots. If you add up all USED space by the snapshots, you will not get total occupied 
space because there is some space occupied by a snapshot combinations.
zfspace tries to show you these combinations and/or explain where most of your space is used. 
The idea is similar to [this tool](https://github.com/mafm/zfs-snapshot-disk-usage-matrix).

## Installation

`pip3 install zfspace`
zfspace doesn't require root priviledges as it is installed in ~/.local/bin/ 

## Usage

`zfspace <dataset name>`
Example: zfspace mypool/root/
**dataset name** may be a **snapshot name** or **filesystem name**. Clones and volumes may also be supported.

## Compatibility

zfspace is pure python module installed by pip, so it might work on any Linux with Python3 and pip package manager.
But zfspace has only been tested on Ubuntu 18.04 and Ubuntu 20.04.