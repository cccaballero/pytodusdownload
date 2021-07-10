import argparse
import concurrent.futures
import os
import pickle
import re
import sys

import requests
from tqdm import tqdm
from todus import client
from todus.s3 import get_real_url

user_config_dir = os.path.join(os.path.expanduser('~'), '.pys3download')
token_path = os.path.join(user_config_dir, 'token.pickle')
os.makedirs(user_config_dir, exist_ok=True)

exitapp = False # flag for stopping download threads

def _dir_path(string):
    if os.path.isdir(string):
        return string
    else:
        raise NotADirectoryError(string)

def _normalize_phone_number(phone_number: str) -> str:
    phone_number = phone_number.lstrip("+").replace(" ", "")
    return "53" + re.match(r"(53)?(\d{8})", phone_number).group(2)

def parse_links_file(links_file):
    links = []
    with open(links_file, 'r') as f:
        lines = f.readlines()
    for line in lines:
        if line:
            link, file_name = line.split('\t')
            links.append({'link': link.strip(), 'file_name': file_name.strip()})
    return links


def get_todus_token(todus_client, force_new=False):

    if not force_new:
        try:
            with open(token_path, 'rb') as handle:
                token = pickle.load(handle)
                return token
        except:
            print('Warning, Could not load an existent token, obtaining new one....')

    phone_number = _normalize_phone_number(input('Your phone number:\n'))
    todus_client.request_code(phone_number)
    code = input('sms code:\n')
    password = todus_client.validate_code(phone_number, code)
    token = todus_client.login(phone_number, password)

    try:
        with open(token_path, 'wb') as handle:
            pickle.dump(token, handle, protocol=3)
    except:
        print('Warning, could not load save the obtained token')

    return token


def fetch_or_resume(todus_client, token, url, filename, output_dir):

    url = get_real_url(token, url)

    headers = {
        "User-Agent": "ToDus {} HTTP-Download".format(todus_client.version_name),
        "Authorization": "Bearer {}".format(token),
    }

    with open(os.path.join(output_dir, filename), 'ab') as f:
        pos = f.tell()
        if pos:
            headers['Range'] = f'bytes={pos}-'

        try:
            response = todus_client.session.get(url, headers=headers, stream=True)
            response.raise_for_status()
        except requests.exceptions.Timeout:
            print('{filename} ERROR: Request Timeout'.format(filename=filename))
            return
        except requests.exceptions.TooManyRedirects:
            print('{filename} ERROR: Too many redirects'.format(filename=filename))
            return
        except requests.exceptions.HTTPError as err:
            print('{filename} ERROR: {err}'.format(filename=filename, err=err))
            return
        except requests.exceptions.RequestException as e:
            print('{filename} ERROR: Unknown Error'.format(filename=filename))
            return

        total_size_in_bytes= int(response.headers.get('content-length', 0))
        block_size = 1024 #1 Kibibyte
        progress_bar = tqdm(total=total_size_in_bytes+pos, unit='iB', unit_scale=True, desc=filename)
        progress_bar.update(pos)

        for data in response.iter_content(block_size):
            if exitapp:
                break
            progress_bar.update(len(data))
            f.write(data)

    progress_bar.close()
    if exitapp:
        print("Download interrupted")
    elif total_size_in_bytes+pos != 0 and progress_bar.n != total_size_in_bytes+pos:
        print("ERROR, something went wrong")

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument(
        'links_file',
        type=argparse.FileType('r'),
        help='File containing ToDus download links'
    )
    parser.add_argument(
        '--output-dir',
        type=_dir_path,
        default=os.getcwd(),
        help='Directory where files will be downloaded'
    )
    parser.add_argument(
        '--max-threads',
        type=int,
        default=1,
        help='Maximum number of concurrent downloads (Default: 1)'
    )
    parser.add_argument(
        '--new-token',
        action="store_true",
        help='Force obtaining a new token'
    )
    args = parser.parse_args()
    links_file_path = args.links_file.name
    args.links_file.close()


    todus_client = client.ToDusClient()
    token = get_todus_token(todus_client, force_new=args.new_token)
    files_to_download = parse_links_file(links_file_path)

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.max_threads) as executor:
        for file_to_download in files_to_download:
            executor.submit(fetch_or_resume,
                            todus_client,
                            token,
                            file_to_download['link'],
                            file_to_download['file_name'],
                            args.output_dir)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        exitapp = True
        sys.exit(1)