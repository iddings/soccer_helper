from argparse import ArgumentParser, FileType
import logging

from soccer_helper import SoccerHelper, Config

parser = ArgumentParser('soccer_helper')

parser.add_argument('-c', '--credentials', type=FileType('r'))
parser.add_argument('-s', '--settings', type=FileType('r'))
parser.add_argument('--verbose', action='store_true', default=False)

args = parser.parse_args()

logging.root.setLevel(logging.INFO if args.verbose else logging.WARNING)

config = Config.fromJSONFiles(settings_file=args.settings, credentials_file=args.credentials)

SoccerHelper(config).run()
