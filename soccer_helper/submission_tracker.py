import re
from datetime import datetime
from logging import Logger, getLogger
from time import sleep
from typing import List
from urllib.parse import urlsplit

from praw.exceptions import APIException
from praw.models import Comment
from sqlalchemy.orm import Session

from soccer_helper.context import Context
from soccer_helper.models import TrackedSubmission, TrackedComment, Mirror
from soccer_helper.util import make_permalink

AUTO_MODERATOR = 'AutoModerator'

log: Logger = getLogger(__name__)


class SubmissionTracker:

    def __init__(self, context: Context):
        self._context = context

    def track(self):

        while True:

            now = datetime.now()

            with self._context.data_store.get_session() as session:

                for sub in session.query(TrackedSubmission).all():

                    if sub.track_until <= now:
                        self._context.data_store.enqueue_deletion(sub)
                        continue

                    if not sub.related_comment_id:
                        for comment in self._context.reddit.submission(sub.id).comments:  # type: Comment
                            if comment.author == AUTO_MODERATOR:
                                sub.related_comment_id = comment.id
                                self._context.data_store.mark_updated(sub)
                                break

                    if sub.related_comment_id:
                        self.poll_automod_comment(session, sub)

            sleep(1)

    def poll_automod_comment(self, session: Session, submission: TrackedSubmission):

        automod_comment = self._context.reddit.comment(submission.related_comment_id)
        automod_comment.refresh()

        for comment in automod_comment.replies:  # type: Comment

            reply: TrackedComment = session.query(TrackedComment).filter_by(fullname=comment.fullname).first()

            links: List[Link] = Link.from_comment_body(comment.body)
            reply_lines = []

            for link in links:
                if link.is_mirrorable:
                    existing_mirror: Mirror = session.query(Mirror).filter_by(original_url=link.url).first()
                    title = link.text.replace("*", "")
                    if existing_mirror and existing_mirror.mirror_url:
                        reply_lines.append(
                            f"**[{title} - Mirror (No Pre-Roll Ads)]({existing_mirror.mirror_url})**"
                        )
                    else:
                        reply_lines.append(f"*{title} - Generating Mirror*")
                        if not existing_mirror:
                            session.add(Mirror(
                                original_url=link.url
                            ))

            if reply_lines:

                #  Disabling the mention for now
                #  reply_lines.append("/u/{} please stop using sites with pre-roll ads.".format(comment.author))
                reply_lines.append("*****")
                reply_lines.append("*This action was performed automatically to improve the quality of /r/soccer.*")
                reply_lines.append("*Downvote this and it will be deleted.*")

                reply_body = "\n\n".join(reply_lines)

                if reply:
                    praw_reply: Comment = self._context.reddit.comment(reply.related_comment_id)
                    if praw_reply.score < self._context.config.reply_delete_threshold:
                        log.info("deleting " + make_permalink(praw_reply))
                        praw_reply.delete()
                    if praw_reply.body != reply_body:
                        log.info("updating " + make_permalink(praw_reply))
                        praw_reply.edit(reply_body)
                else:
                    log.info("replying to " + make_permalink(comment))
                    try:
                        reply_comment: Comment = comment.parent().reply(reply_body)
                        session.add(TrackedComment(
                            fullname=comment.fullname,
                            related_comment_id=reply_comment.id,
                            track_until=datetime.now() + self._context.config.time_to_track
                        ))
                    except APIException as e:
                        log.exception('API Exception')
                        match = re.match(r'you are doing that too much\. try again in (\d+) (.*?)\.', e.message)
                        if match:
                            quantity = int(match.group(1))
                            multipliers = {"seconds": 1, "minutes": 60}
                            if match.group(2) in multipliers:
                                delay = (quantity * multipliers[match.group(2)]) + 60
                            else:
                                delay = 60*10
                            log.warn(f"Rate Limited: waiting {delay} seconds.")
                            sleep(delay)
                            log.info("resuming.")


class Link:

    def __init__(self, text: str, url: str):
        self.text = text
        self.url = url

    @property
    def is_mirrorable(self) -> bool:
        split_url = urlsplit(self.url)
        return 'dailymotion.com' in split_url.netloc.lower()

    @staticmethod
    def from_comment_body(body: str) -> List['Link']:
        return [Link(*m) for m in re.findall(r'\[(.*?)\]\((.*?)\)', body)]
