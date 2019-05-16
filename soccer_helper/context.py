from praw.reddit import Reddit

from soccer_helper.config import Config
from soccer_helper.data_store import DataStore


class Context:

    def __init__(self, config: Config, reddit: Reddit, data_store: DataStore):
        self.config: Config = config
        self.reddit: Reddit = reddit
        self.data_store: DataStore = data_store

    @staticmethod
    def from_config(config: Config) -> 'Context':
        reddit: Reddit = Reddit(
            client_id=config.reddit_client_id,
            client_secret=config.reddit_client_secret,
            password=config.reddit_password,
            user_agent=config.praw_user_agent,
            username=config.reddit_username
        )
        data_store: DataStore = DataStore(config, reddit)
        return Context(config, reddit, data_store)

    def __getstate__(self):
        return self.config

    def __setstate__(self, state: Config):
        prox = Context.from_config(state)
        self.config = prox.config
        self.data_store = prox.data_store
        self.reddit = prox.reddit
