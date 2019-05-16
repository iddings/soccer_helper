import json
import re
from datetime import datetime
from multiprocessing.pool import Pool
from time import sleep

import requests

from soccer_helper import Context
from soccer_helper.models import Mirror


class VideoHandler:

    def __init__(self, context: Context):
        self._context = context

    def run(self):

        pool = Pool(processes=4)

        try:

            while True:

                with self._context.data_store.get_session() as session:
                    mirrors = session.query(Mirror).filter_by(mirror_url=None, processing=False, skip=False).all()
                    for mirror in mirrors:
                        pool.apply_async(VideoHandler.process_mirror, args=(self._context, mirror.original_url))
                        mirror.processing = True
                        self._context.data_store.mark_updated(mirror)

                sleep(1)

        except KeyboardInterrupt:

            with self._context.data_store.get_session() as session:
                for mirror in session.query(Mirror).all():
                    mirror.processing = False
                    self._context.data_store.mark_updated(mirror)

            pool.terminate()
            pool.join()

    @staticmethod
    def process_mirror(context: Context, url: str):

        with context.data_store.get_session() as session:

            mirror: Mirror = session.query(Mirror).filter_by(original_url=url).first()

            assert mirror

            print('attempting to get ' + url)

            dm_code = re.search(r'dailymotion.com/video/(.*?)$', url, flags=re.IGNORECASE).group(1)

            res = requests.get(f'https://www.dailymotion.com/embed/video/{dm_code}')

            if res.status_code != 200:
                mirror.skip = True
                context.data_store.mark_updated(mirror)
                return

            bad_video = None

            match = re.search(r'var config = (\{.*?\});', res.text.replace("\n", " "))
            if match:

                metadata = json.loads(match.group(1))['metadata']

                if 'error' not in metadata:

                    created = datetime.fromtimestamp(metadata['created_time'])

                    if (datetime.now() - created) <= context.config.upload_window:

                        best_q = max(set(metadata['qualities'].keys()) - {'auto'})
                        info = metadata['qualities'][best_q]

                        for i in info:
                            if i['type'].startswith('video'):
                                bad_video = i['url']

                    else:
                        print('skipping due to old video.')

            if not bad_video:
                mirror.skip = True
                context.data_store.mark_updated(mirror)
                return

            api_url = "https://api.streamable.com/upload"

            print('getting ' + bad_video)

            video = requests.get(bad_video).content

            print('uploading...')

            res = requests.post(
                api_url,
                auth=(context.config.streamable_username, context.config.streamable_password),
                headers={'User-Agent': "helping soccer thrive v1"},
                files={'file': video},
                data={'title': 'video'}
            )

            if res.status_code == 200:
                mirror.mirror_url = 'https://streamable.com/' + res.json()['shortcode']
                context.data_store.mark_updated(mirror)
