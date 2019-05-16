from argparse import ArgumentParser, FileType

from soccer_helper import SoccerHelper, Config

parser = ArgumentParser('soccer_helper')

parser.add_argument('-c', '--credentials', type=FileType('r'))
parser.add_argument('-s', '--settings', type=FileType('r'))

args = parser.parse_args()

config = Config.fromJSONFiles(settings_file=args.settings, credentials_file=args.credentials)

SoccerHelper(config).run()
