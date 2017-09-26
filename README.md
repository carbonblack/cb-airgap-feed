# cb-airgap-feed
import/export threat intelligence feed(s) from file(s) - CbR

There are two versions of this utility:
1) airgap_feed.py

Uses modern cbapi - requires installation of new dependencies on Cbr.

2) airgap_feeds_twosix.py

Uses requests lib to hit rest endpoints 'by hand'. Runs on python 2.6.6 w/o 
any additional dependencies.

arguments: --folder - the relative path of the folder to import/export into/from
--mode the mode of operation, one of 'import' or 'export'.

python airgap_feed.py --folder tmp --mode export
python arigap_feeds_twosix.py --fold tmp --mode import


