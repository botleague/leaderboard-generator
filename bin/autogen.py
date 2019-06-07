import os
import sys
import time
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


def main():
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')

    # Don't need Firestore for HTML dev
    os.environ['SHOULD_USE_FIRESTORE'] = 'false'

    from leaderboard_generator.config import config

    # Catch up with unwatched changes
    generate()

    path = config.root_dir
    event_handler = AutoGenTrigger()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


def in_html_dir(path):
    from leaderboard_generator.config import config
    in_static = path.startswith(config.static_dir)
    in_templates = path.startswith(config.template_dir)
    ret = in_static or in_templates
    return ret


def generate():
    from leaderboard_generator.generate_site import generate
    generate()


class AutoGenTrigger(FileSystemEventHandler):
    def __init__(self):
        super(AutoGenTrigger, self).__init__()
        self.last_gen_time = -1

    def on_moved(self, event):
        super(AutoGenTrigger, self).on_moved(event)

        what = 'directory' if event.is_directory else 'file'
        logging.debug("Moved %s: from %s to %s", what, event.src_path,
                      event.dest_path)

    def on_created(self, event):
        super(AutoGenTrigger, self).on_created(event)

        what = 'directory' if event.is_directory else 'file'
        logging.debug("Created %s: %s", what, event.src_path)

    def on_deleted(self, event):
        super(AutoGenTrigger, self).on_deleted(event)

        what = 'directory' if event.is_directory else 'file'
        logging.debug("Deleted %s: %s", what, event.src_path)

    def on_modified(self, event):
        super(AutoGenTrigger, self).on_modified(event)

        what = 'directory' if event.is_directory else 'file'
        logging.debug("Modified %s: %s", what, event.src_path)
        if event.is_directory:
            return
        if not in_html_dir(event.src_path):
            return
        if any(x in event.src_path for x in ['___jb']):
            return

        if self.last_gen_time == -1 or time.time() - self.last_gen_time > 5:
            logging.info("Modified %s: %s", what, event.src_path)
            generate()
            self.last_gen_time = time.time()


if __name__ == '__main__':
    main()
