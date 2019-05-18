from dataclasses import dataclass
from datetime import timedelta
from json import load
from typing import TextIO, List


@dataclass(frozen=True)
class Config:

    streamable_username: str
    streamable_password: str

    reddit_username: str
    reddit_password: str
    reddit_client_id: str
    reddit_client_secret: str
    praw_user_agent: str

    subreddit: str
    link_flair_names: List[str]
    time_to_track: timedelta
    upload_window: timedelta
    reply_delete_threshold: int

    max_download_retries: int = 5

    database_uri: str = 'sqlite:////dev/shm/soccer_helper.db'

    @staticmethod
    def fromJSONFiles(settings_file: TextIO, credentials_file: TextIO) -> 'Config':

        try:

            settings = load(settings_file)

            return Config(
                time_to_track=timedelta(**settings.pop('time_to_track')),
                upload_window=timedelta(**settings.pop('upload_window')),
                **settings,
                **load(credentials_file)
            )

        finally:
            settings_file.close()
            credentials_file.close()
