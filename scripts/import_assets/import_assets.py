import argparse
import csv
import ipaddress
import json
from urllib.parse import urljoin

import requests
from requests.exceptions import HTTPError

DEFAULT_API_URL = 'https://se-api.holmsecurity.com/v2/'
"""
This code importing csv files including information about assets and creates assets in the holm-api endpoint. 
"""


def read_and_create_assets(args):
    """
    Reads data from CSV file and posts it as JSON to the API.
    """
    with open(args.csv_path, 'r') as csv_file:
        csv_reader = csv.reader(csv_file)
        for row in csv_reader:
            dict_fields, ip = prep_dict_fields(row)
            try:
                post_asset_request(args, dict_fields)
                print(
                    f"{dict_fields['name']} with the ip {ip} was added successfully"
                )
            except HTTPError as err:
                errors = json.loads(err.response.content)["errors"]
                print(f"The asset could not be added because: {errors}")


def prep_dict_fields(row):
    ip = row[5]
    asset_type = get_asset_type(ip)
    name = row[0]
    business_impact = row[1]
    details = row[2]
    hosts_personal_data = row[4]
    tags = [t for t in row[3].split('|') if t]
    dict_fields = {
        "name": name,
        "type": asset_type,
        "tags": tags,
        "details": details or None,
        "business_impact": business_impact or 'neutral'
    }
    if hosts_personal_data != '':
        dict_fields['hosts_personal_data'] = str_to_bool(hosts_personal_data)
    else:
        dict_fields['hosts_personal_data'] = False

    if asset_type == 'network':
        dict_fields.update({"ip_range": ip})
    else:
        dict_fields.update({"ip": ip})

    return dict_fields, ip


def str_to_bool(s):
    if s in ['true', 'True']:
        return True
    elif s in ['false', 'False']:
        return False
    else:
        raise ValueError


def get_asset_type(ip):
    try:
        result = ipaddress.ip_network(ip, strict=False)
        if "/32" in str(result):
            try:
                ipaddress.ip_address(ip)
                return "host"
            except:
                pass
        else:
            return "network"
    except ValueError:
        return None


def post_asset_request(args, dict_fields):
    url = urljoin(args.url, 'net-assets')
    json_data = json.dumps(dict_fields)
    headers = {
        "Authorization": f"TOKEN {args.key_token}",
        "Content-Type": "application/json"
    }
    response = requests.post(url=url, data=json_data, headers=headers)
    response.raise_for_status()
    return response


def get_args():
    parser = argparse.ArgumentParser(description='API key of the sc account')
    parser.add_argument('-p',
                        '--csv-path',
                        help='Path to the CSV file',
                        required=True)
    parser.add_argument('-k',
                        '--key-token',
                        type=str,
                        help='Token needed to access sc-dev',
                        required=True)
    parser.add_argument(
        '-u',
        '--url',
        help=f"API URL to use, default is set to {DEFAULT_API_URL}",
        default=DEFAULT_API_URL)

    return parser.parse_args()


if __name__ == '__main__':
    args = get_args()
    asset_data = read_and_create_assets(args)
