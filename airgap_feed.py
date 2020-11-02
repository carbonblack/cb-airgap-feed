#!/usr/bin/env python

import argparse
import json
import os
import re
import requests
import shutil
import sys
from typing import Dict, Optional, List

# noinspection PyBroadException
try:
    from requests.packages.urllib3.exceptions import InsecureRequestWarning, InsecurePlatformWarning
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
except Exception:
    pass


def get_api_token() -> str:
    import psycopg2
    conn = psycopg2.connect("dbname=cb port=5002")
    cur = conn.cursor()
    cur.execute("select auth_token from cb_user where global_admin is true order by id limit 1;")
    token = cur.fetchone()[0]
    token = re.sub("^'|'$", "", token)
    return token


def get_feed(headers: Dict, name: str) -> Optional[Dict]:
    # if the port is something other than 443 change below
    url = "https://127.0.0.1:443/api/v1/feed"
    feeds = requests.get(url, headers=headers, verify=False)
    feeds.raise_for_status()
    for feed in feeds.json():
        if feed['name'].lower() == name.lower():
            return feed
    return None 


def build_cli_parser(description: str = "VMware Carbon Black EDR Airgap Feeds import/export utility") \
        -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description)
    return parser


def main(argv: List) -> int:
    parser = build_cli_parser()
    commands = parser.add_subparsers(help="Commands", dest="command")

    default_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "feeds")

    import_command = commands.add_parser("import", help="Import feeds from disk")
    import_command.add_argument("-f", "--folder", help="Folder to import", default=default_folder, required=False)

    export_command = commands.add_parser("export", help="Export feeds to disk")
    export_command.add_argument("-f", "--folder", help="Folder to export to", default=None, required=True)

    args = parser.parse_args(args=argv)

    mode = args.command

    if hasattr(args, "folder"):
        folder = args.folder
    else:
        # use location of script
        folder = os.path.dirname(os.path.abspath(__file__))

    header = {'X-Auth-Token': get_api_token()}

    # if the port is something other than 443 change below
    url = "https://127.0.0.1:443/api/v1/feed"

    errors = 0
    if mode == 'import':
        print(f'Importing Threat Intelligence feeds from {folder}')

        for root, sub_dirs, files in os.walk(folder):
            for temp_file in files:
                if temp_file.endswith('.json'):
                    filepath = os.path.join(root, temp_file)
                    print(f'filepath = {filepath}')

                    feed_url = f"file://{filepath}"
                    data = {'feed_url': feed_url,
                            'validate_server_cert': False,
                            'manually_added': True}

                    file_json = json.loads(open(filepath).read())
                    feed_name = file_json['feedinfo']['name']
                    feed = get_feed(header, feed_name)
                    if feed is not None:
                        feed_id = feed['id']
                        print(f"Feed {feed_name} already exists, attempting update")
                        feed.update({"feed_url": feed_url, "manually_added": True})
                        feed_update = requests.put(f"{url}/{feed_id}", data=json.dumps(feed), headers=header,
                                                   verify=False)
                        if feed_update.status_code == 200:
                            print(f"Updated {feed_name}")
                        else:
                            print(f"Failed to update {feed_name} (error {feed_update.status_code})")
                            errors += 1
                    else:
                        feed_update = requests.post(url, data=json.dumps(data), headers=header, verify=False)
                        if feed_update.status_code == 200:
                            print(f"Added feed {feed_name}")
                        else:
                            print(f"Failed to add feed {feed_name} (error {feed_update.status_code})")
                            errors += 1
    else:
        export_path = os.path.join(folder, "feeds")
        print(f'Exporting Threat Intelligence Feeds to {export_path}')

        try:
            os.makedirs(export_path)
        except OSError:
            pass  # probably due to folder already existing

        try:
            shutil.copy(os.path.abspath(__file__), folder)
        except shutil.SameFileError:
            pass

        cert = ("/etc/cb/certs/carbonblack-alliance-client.crt",
                "/etc/cb/certs/carbonblack-alliance-client.key")

        export_feeds = ['abusech', 'Bit9AdvancedThreats', 'alienvault',
                        'CbCommunity', 'Bit9EarlyAccess', 'Bit9SuspiciousIndicators', 'Bit9EndpointVisibility',
                        'fbthreatexchange', 'CbKnownIOCs', 'sans', 'mdl', 'ThreatConnect', 'tor', 'attackframework']

        feeds = requests.get(url, headers=header, verify=False)
        feeds.raise_for_status()

        for feed in feeds.json():
            feed_url = feed.get('feed_url', None)
            feed_name = str(feed.get('name', ""))
            print(f"Checking feed {feed_name} at {feed_url}")
            if feed_url and 'http' in feed_url and feed_name in export_feeds:
                try:
                    response = requests.get(url=feed_url, cert=cert)
                    response.raise_for_status()
                    fn = os.path.join(export_path, feed_name + ".json")
                    f = open(fn, "w+")
                    try:
                        print(f"Exporting feed {feed_name} to {fn}")
                        f.write(json.dumps(response.json()))
                    except Exception as e:
                        print(f'Error writing to {feed_name}: {e}')
                        errors += 1
                except Exception as e:
                    print(f'Could not export feed {feed_name}: {e}')
                    errors += 1

    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
