import os

import yaml
from binstar_client import Conflict

from sync import sync

FROM = 'conda-forge'
TO = 'vpython'


def main(requirements_path):
    with open(requirements_path, 'rt') as f:
        package_list = yaml.safe_load(f)

    token = os.getenv('BINSTAR_TOKEN')

    for package in package_list:
        print(package['name'])
        try:
            sync(FROM, TO, package['name'], token, to_label='main')
        except Conflict:
            print('Skipping because of a conflict anaconda.org')


if __name__ == '__main__':
    main('vp_copy.yaml')
