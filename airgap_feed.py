import json
import logging
import os

import cbapi.example_helpers as cbhelper
import requests
from cbapi.response import *

log = logging.getLogger(__name__)



#
# The MIT License (MIT)
#
# Copyright (c) 2015 Bit9 + Carbon Black
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
# -----------------------------------------------------------------------------
#
# Zachary Estep 2017


class CbFeedShipper(object):

    def __init__(self, cbapi=None, force_override=None, verbose=None):
        self.cbapi = cbapi
        self.force_override = force_override
        self.verbose = True if verbose else False

    def import_folder(self, folder):
        #Feed queries seem to be broken
        feeds = {feed.name: feed for feed in self.cbapi.select(Feed).all()}
        print(feeds)
        for root, subdirs, files in os.walk(folder):
            for file in files:
                filepath = os.path.join(root, file)
                feed_url = "file://%s" % filepath
                filejson = json.loads(open(filepath).read())
                feedname = filejson['feedinfo']['name']
                feed = feeds.get(feedname, None)
                if feed is not None and not self.force_override:
                    print("Skipping... {} (already existed)".format(feedname))
                else:
                    # create a feed if one didn't exist
                    feed = feed if feed else self.cbapi.create(Feed)
                    feed.name = feedname
                    feed.feed_url = feed_url
                    feed.validate_server_cert = False
                    feed.manually_added = True
                    feed.enabled = True
                    feed.save()
                    feed.refresh()
                    print(feed)

    def export_feeds(self,outdir,cert=None):

        log.info("export_feeds: outdir = {} , cert = {}".format(outdir, cert))

        if cert is None:
            cert = ("/etc/cb/carbonblack-alliance-client.crt", "/etc/cb/carbonblack-alliance-client.key")

        export_feeds = ['abusech', 'Bit9AdvancedThreats', 'alienvault',
                        'CbCommunity', 'Bit9EarlyAccess', 'Bit9SuspiciousIndicators', 'Bit9EndpointVisibility',
                        'fbthreatexchange', 'iconmatching', 'CbKnownIOCs', 'sans', 'mdl', 'ThreatConnect', 'tor', 'attackframework']

        export_feeds = map(lambda f: self.cbapi.select(Feed).where("name:" + f).first(), export_feeds)
        export_feeds = filter(lambda f: not f.feed_url.startswith("file:/"), export_feeds)

        for feed in export_feeds:
            response = requests.get(url=feed.feed_url,cert=cert).json()
            log.debug(response)
            log.info("Trying to export feed {} , url {} ".format(feed.name, feed.feed_url))
            file = open(os.path.join(outdir, feed.name + ".json"), "w+")
            file.write(json.dumps(response))


def main():
    parser = cbhelper.build_cli_parser()
    parser.add_argument("--folder", dest="folder",
                        help="Input Folder where Cb Threat Intelligence Feed JSON files are stored", required=True)
    parser.add_argument("--force-override", dest="override", help="Force update of existing feeds", required=False,
                        default=False)
    parser.add_argument("--mode", dest="mode", help="import or export", required=True)
    parser.add_argument("--cert", dest="cert", help="cert",required=False,default=None)
    parser.add_argument("--key", dest="key",help="key",required=False,default=None)

    args = parser.parse_args()

    cbapi = cbhelper.get_cb_response_object(args)

    shipper = CbFeedShipper(cbapi=cbapi, force_override=args.override, verbose=args.verbose)

    print("[+] Processing folder: {}\n".format(args.folder))

    if args.mode == "export":
        shipper.export_feeds(outdir=args.folder,cert=(args.cert,args.key) if args.cert and args.key else None)
    else:
        shipper.import_folder(folder=args.folder)


if __name__ == "__main__":

    logging.getLogger().setLevel(logging.DEBUG)

    main()

