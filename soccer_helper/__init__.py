from multiprocessing import Process
import logging
from typing import Dict

from soccer_helper.submission_tracker import SubmissionTracker
from soccer_helper.config import Config
from soccer_helper.context import Context
from soccer_helper.models import Base
from soccer_helper.subreddit_tracker import SubredditTracker
from soccer_helper.video_handler import VideoHandler

log = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setFormatter(
    logging.Formatter(
        fmt="%(asctime)s : %(name)s : %(levelname)s - %(message)s",
        datefmt='%Y-%m-%d %H:%M:%S'
    )
)
log.addHandler(handler)


class SoccerHelper:

    def __init__(self, config: Config):
        self._config = config

    def run(self):

        context: Context = Context.from_config(self._config)

        Base.metadata.create_all(context.data_store.engine)

        process_targets = {
            "subreddit_tracker": SubredditTracker(context).track,
            "submission_tracker": SubmissionTracker(context).track,
            "video_handler": VideoHandler(context).run
        }

        processes: Dict[str, Process] = {k: Process(target=v) for k, v in process_targets.items()}

        for name, proc in processes.items():
            log.info(f"starting process: {name}")
            proc.start()

        while True:

            try:

                for name in processes:
                    if not processes[name].is_alive():
                        log.info(f"process {name} died. restarting.")
                        processes[name] = Process(target=process_targets[name])
                        processes[name].start()

            except KeyboardInterrupt:
                log.info('exiting.')
                break
