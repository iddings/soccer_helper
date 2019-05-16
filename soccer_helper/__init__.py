from multiprocessing import Process
import logging
import signal

from soccer_helper.submission_tracker import SubmissionTracker
from soccer_helper.config import Config
from soccer_helper.context import Context
from soccer_helper.models import Base
from soccer_helper.subreddit_tracker import SubredditTracker
from soccer_helper.video_handler import VideoHandler

root = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setFormatter(
    logging.Formatter(
        fmt="%(asctime)s : %(name)s : %(levelname)s - %(message)s",
        datefmt='%Y-%m-%d %H:%M:%S'
    )
)
root.addHandler(handler)
root.setLevel(logging.INFO)


class SoccerHelper:

    def __init__(self, config: Config):
        self._config = config

    def run(self):

        context: Context = Context.from_config(self._config)

        Base.metadata.create_all(context.data_store.engine)

        #original_sigint_handler = signal.signal(signal.SIGINT, signal.SIG_IGN)

        submission_tracker_proc = Process(target=SubmissionTracker(context).track)
        video_handler_proc = Process(target=VideoHandler(context).run)

        submission_tracker_proc.start()
        video_handler_proc.start()

        #signal.signal(signal.SIGINT, original_sigint_handler)

        SubredditTracker(context).track()

        submission_tracker_proc.join()
        video_handler_proc.join()
