#!/usr/bin/env python3
# -*- coding: utf-8 -*-
################################################################################
#
# Script that loops forever reading the journal log, and publishes all of the
#  logged detection events -- i.e., the highest confidence detection in each
#  (potentially overlapping) time chunk within each recording interval.
#
# The format of the birdpi logs is as follows:
#  HH:MM:SS---[server][INFO] <startOffset>;<endOffset>-('<scientificName>_<commonName>', <confidence>)
#
################################################################################

import logging
import time

from systemd import journal
from parse import parse


LOG_LEVEL = "WARNING"

UID = 1000          # uid of 'jdn'
WAIT_MSEC = 15000   # currently: 15sec batches, six 3sec chunks, with .5sec overlap


logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger(__name__)

def main():
    j = journal.Reader()
    j.log_level(journal.LOG_INFO)
    j.add_match(_UID=str(UID))
    j.seek_tail()
    j.get_previous()
    logger.debug("Initialized")

    logger.info(f"Following INFO logs for user {UID} starting from most recent logged event")
    while True:
        if j.wait(WAIT_MSEC):
            while True:
                entry = j.get_next()
                if not entry:
                    break
                if 'MESSAGE' in entry:
                    timestamp = entry['__REALTIME_TIMESTAMP']
                    message = entry['MESSAGE']
                    logger.debug(f"{timestamp}: <<<{message}>>>")
                    ret = parse("[server][INFO] {};{}-({}, {})", message)
                    if ret:
                        parts = list(ret)
                        logger.debug(f"parts: {parts}")
                        if len(parts) == 4:
                            names = parts[2].split("_")
                            if len(names) != 2:
                                logger.error(f"Bad names: {parts[2]}")
                                continue
                            scientificName = names[0].lstrip('\'"')
                            commonName = names[1].rstrip('\'"')
                            msgBody = {
                                'start': float(parts[0]),
                                'end': float(parts[1]),
                                'confidence': float(parts[3]),
                                'scientific': scientificName,
                                'common': commonName
                            }
                            print(f"{timestamp}: {msgBody}")
                        else:
                            logger.debug(f"Bad parse: {parts}")
                    else:
                        logger.debug("Message mismatch")
                else:
                    logger.debug("No MESSAGE")
        else:
            time.sleep(0.1)
    logger.debug("Exiting")


if __name__ == "__main__":
    main()
