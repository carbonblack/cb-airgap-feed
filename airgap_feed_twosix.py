#!/usr/bin/env python
# Zach Estep
import argparse
import json
import os
import re
import shutil
import sys

import requests

# use subcommands, copy script into destination folder , update readme
# make export include script, and feeds
# export

try:
    from requests.packages.urllib3.exceptions import InsecureRequestWarning, InsecurePlatformWarning
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
except:
    pass


def get_api_token():
    import psycopg2
    conn = psycopg2.connect("dbname=cb port=5002")
    cur = conn.cursor()
    cur.execute("select auth_token from cb_user where global_admin is true order by id limit 1;")
    token = cur.fetchone()[0]
    token = re.sub("^'|'$", "", token)
    return token


def feed_exists(headers, name):
    # if the port is something other than 443 change below
    url = "https://127.0.0.1:443/api/v1/feed"
    feeds = requests.get(url, headers=headers, verify=False)
    feeds.raise_for_status()
    for feed in feeds.json():
        if feed['name'].lower() == name.lower():
            return True

    return False


def build_cli_parser(description="Cb Airgap Feeds import/export Utility"):
    parser = argparse.ArgumentParser(description=description)
    return parser


def main(argv):
    parser = build_cli_parser()
    commands = parser.add_subparsers(help="ExIm Commands", dest="command")

    import_command = commands.add_parser("import", help="Import feeds from disk")
    import_command.add_argument("-f", "--folder", help="Folder to import", default=None, required=False)

    export_command = commands.add_parser("export", help="Export feeds to disk")
    export_command.add_argument("-f", "--folder", help="Folder to export to", default=None, required=True)

    args = parser.parse_args(args=argv)
    print (args)

    mode = args.command

    folder = args.folder if args.folder else "./"

    folder = re.sub("\/$", "", folder)
    header = {'X-Auth-Token': get_api_token()}
    # if the port is something other than 443 change below
    url = "https://127.0.0.1:443/api/v1/feed"
    if mode == 'import':
        for root, subdirs, files in os.walk(folder):
            for tempfile in files:
                filepath = os.path.join(root, tempfile)
                print ('filepath = %s' % filepath)
                feed_url = "file://%s" % filepath
                data = {'feed_url': feed_url,
                        'validate_server_cert': False,
                        'manually_added': True,
                        }
                filejson = json.loads(open(filepath).read())
                if feed_exists(header, filejson['feedinfo']['name']):
                    print ("Skipping... %s (already existed)" % (filejson['feedinfo']['name']))
                else:
                    feedupdate = requests.post(url, data=json.dumps(data), headers=header, verify=False)
                    if feedupdate.status_code == 200:
                        print ("Added... %s" % (filejson['feedinfo']['name']))
                    else:
                        print ("Failed... %s (Error Code: %s)" % (filejson['feedinfo']['name'], feedupdate.status_code))

    else:
        print 'export mode chosen'
        exportpath = os.path.join(folder,"feeds")
        try:
            os.mkdir(folder)
            os.mkdir(exportpath)
            shutil.copy(os.path.abspath(__file__), folder)
        except OSError as os_error:
            pass  # probbably due to folder already existing
        cert = ("/etc/cb/certs/carbonblack-alliance-client.crt", "/etc/cb/certs/carbonblack-alliance-client.key")

        export_feeds = ['abusech', 'Bit9AdvancedThreats', 'alienvault',
                        'CbCommunity', 'Bit9EarlyAccess', 'Bit9SuspiciousIndicators', 'Bit9EndpointVisibility',
                        'fbthreatexchange', 'iconmatching', 'CbKnownIOCs', 'sans', 'mdl', 'ThreatConnect', 'tor']

        url = "https://127.0.0.1:443/api/v1/feed"
        feeds = requests.get(url, headers=header, verify=False)
        feeds.raise_for_status()
        for feed in feeds.json():
            feed_url = feed.get('feed_url', None)
            feed_name = feed.get('name', "").encode('ASCII')
            if feed_url and 'http' in feed_url and feed_name in export_feeds:
                feed_name = feed.get('name').encode('ASCII')
                try:
                    response = requests.get(url=feed_url, cert=cert)
                    fn = os.path.join(exportpath, feed_name + ".json")
                    print(fn)
                    f = open(fn, "w+")
                    try:
                        f.write(json.dumps(response.json()))
                    except Exception as e:
                        print(e)
                        print( 'failed to write for %s' % feed_name )
                except Exception as e:
                    print(e)
                    print('could not export feed_name %s' % feed_name)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
