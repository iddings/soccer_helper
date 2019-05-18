from datetime import datetime
from logging import getLogger, Logger
from time import sleep

from praw.models import Submission

from soccer_helper.context import Context
from soccer_helper.models import TrackedSubmission
from soccer_helper.util import make_permalink

log: Logger = getLogger(__name__)


class SubredditTracker:

    def __init__(self, context: Context):
        self._context: Context = context
        self._subreddit: Submission = context.reddit.subreddit(context.config.subreddit)

    def track(self):
        log.info("tracking " + self._subreddit.display_name)
        for submission in self._subreddit.stream.submissions(skip_existing=True):  # type: Submission
            if submission.link_flair_text in self._context.config.link_flair_names:
                with self._context.data_store.get_session() as session:
                    log.info(f"new submission: {make_permalink(submission)}")
                    session.add(TrackedSubmission(
                        fullname=submission.fullname,
                        track_until=datetime.now() + self._context.config.time_to_track
                    ))