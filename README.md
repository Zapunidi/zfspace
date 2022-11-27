# zfspace
Console tool to find occupied pool space in ZFS on Linux.
The tool uses pure python3 with shell commands to collect useful information from ZFS 
and show it in convenient way wit recommendations how to free some space.

## Introduction

ZFS is a non-trivial LVS filesystem with snapshots, reservations, deduplication, filesystems hierarchy and so on. 
Common tools, such as `df` or `ls` can't provide relevant information when you **need to free some space**.
There is an [explanatory article](https://zedfs.com/all-you-have-to-know-about-reading-zfs-disk-usage/) about this.  
  
Snapshots USED space is another puzzle. ZFS only shows space freed by destroying individual snapshot or space 
occupied by all filesystem snapshots. If you add up all USED by the snapshots space, you will **not** get total occupied 
space because there is some space occupied by snapshot combinations. Most people do not comprehend this.  

zfspace tries to analyze space usage and describe it in a human way with recommendations on the things you can do 
to free some space. The snapshot analysis is similar to 
[this tool](https://github.com/mafm/zfs-snapshot-disk-usage-matrix).

## Installation

`pip3 install zfspace`
zfspace doesn't require root priviledges as it is installed in ~/.local/bin/ 

## Usage

Usage: `zfspace [-h] [-V] [-f FILTER] dataset_name`  
Run `zfspace -h` to get more help   
Example: `zfspace mypool/root/`

## Compatibility

zfspace is pure python module installed by pip, so it might work on any Linux with Python3 and pip package manager.
But zfspace has only been tested on Ubuntu 18.04 and Debian 10.

## Development

* You must obey PEP8 formatting rules written in .flake8  
* You must create new versions using bump2version. It simultaneously update several files with new version and 
place a version tag in repository.  
Example:
```bash
bump2version patch
```
or
```bash
bump2version minor
```
* Packet release is based on pyproject.toml. First prepare your environment with:
 ```bash
pip3 install build
```
To build a packet use bump2version first and then go into project directory and run:
 ```bash
python3 -m build --wheel
 ```
Install manually (replace x.x.x with correct version) with:
```bash
pip install dist/zfspace-x.x.x-py3-none-any.whl --force-reinstall
```

## Publishing notes

Twine packet must be installed
```bash
pip3 install twine
```
To publish:
```bash
twine upload dist/zfspace-x.x.x-py3-none-any.whl
```
You will be asked for login and password on PyPi.