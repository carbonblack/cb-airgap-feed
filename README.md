# cb-airgap-feed

## NOTE

This project will no longer be maintained. Starting with EDR version 7.5.0, the cb-airgap-feed script will be incorporated into the EDR distribution. It will work the same way, using the same command-line options, and will be called `/usr/share/cb/cbfeed_airgap`.

## Description

This tool helps customers import VMware Carbon Black EDR-provided threat intelligence feeds into 
EDR servers installed inside an isolated network. This script will export a subset of the Cb Collective 
Defense Cloud Threat Intelligence Feeds into a set of JSON files which can then be copied and imported 
into an airgapped EDR server.

The following feeds are supported by this tool:

* abuse.ch Indicators of Compromise
* Malware Domain List
* Tor exit nodes
* Carbon Black Advanced Threat Indicators
* Carbon Black Community Feed
* Carbon Black Early Access Feed
* Carbon Black Suspicious Indicators
* Carbon Black Endpoint Visibility Feed
* Carbon Black Known IOC Feed
* SANS Threat Hunting Feed
* AlienVault Open Threat Exchange
* Facebook Threat Exchange TLP White Indicators
* ThreatConnect
* MITRE ATT&CK Feed

Other Cb Collective Defense Cloud feeds are not able to be exported as they require
the target EDR server to be online and actively communicating with the Collective
Defense Cloud.


## Usage

To use this tool, you will need two EDR servers, one with access to the Internet
and the Cb Collective Defense Cloud (the "source"), and one that is disconnected from the Internet
(the "destination"). The first server will run the script in "export" mode to download the 
feeds from the Cb Collective Defense Cloud and save them to a local directory. This directory
is then burned to CD, copied to USB, or otherwise transferred to the "destination" server
through a secure means. The folder includes a copy of the script plus the contents of all
the feeds exported from the Cb Collective Defense Cloud.

Once the folder arrives on the destination server, the script is then run in "import" mode
to import the feed contents into the isolated EDR server. This process can be 
repeated on a regular basis to keep the copies of the feeds on the "destination" server
in sync with the feeds from the Cb Collective Defense Cloud.

## Step-by-Step Instructions

1. Run the `airgap_feeds.py` script on the "source" system with a `-f` argument indicating
   the folder where the feeds should be saved. This folder could be on a mounted USB stick, or
   a temporary directory that will be burned to CD-ROM. For example:
   
        # ./airgap_feeds.py export -f /tmp/blah
        exporting threat intelligence feeds to /tmp/blah
        ...
        # cp -rp /tmp/blah /media/USB
        # umount /media/USB

2. Copy the files to your destination server.

3. Change into the directory containing the script and `feeds` folder that you copied from the 
   "source" server.

4. Run the `airgap_feeds.py` script on the "destination" system in "import" mode. For example:

        # ./airgap_feeds.py import
        importing threat intelligence feeds from /media/USB
        ...

## Support

1. View all API and integration offerings on the [Developer Network](https://developer.carbonblack.com/) along with reference documentation, video tutorials, and how-to guides.
2. Use the [Developer Community Forum](https://community.carbonblack.com/t5/Developer-Relations/bd-p/developer-relations) to discuss issues and get answers from other API developers in the Carbon Black Community.
3. Report bugs and change requests to [Carbon Black Support](http://carbonblack.com/resources/support/).

