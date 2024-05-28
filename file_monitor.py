"""
Copyright (C) 2024 James Sawyer
All rights reserved.

This script and the associated files are private 
and confidential property. Unauthorized copying of 
this file, via any medium, and the divulgence of any 
contained information without express written consent 
is strictly prohibited.

This script is intended for personal use only and should 
not be distributed or used in any commercial or public 
setting unless otherwise authorized by the copyright holder. 
By using this script, you agree to abide by these terms.

DISCLAIMER: This script is provided 'as is' without warranty 
of any kind, either express or implied, including, but not 
limited to, the implied warranties of merchantability, 
fitness for a particular purpose, or non-infringement. In no 
event shall the authors or copyright holders be liable for 
any claim, damages, or other liability, whether in an action 
of contract, tort or otherwise, arising from, out of, or in 
connection with the script or the use or other dealings in 
the script.
"""

# -*- coding: utf-8 -*-

import os
import platform
import time
import logging
import inotify.adapters

logging.basicConfig(filename='file_monitor.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def monitor_file_close(directory):
    i = inotify.adapters.Inotify()
    i.add_watch(directory)

    for event in i.event_gen(yield_nones=False):
        (_, type_names, path, filename) = event
        if 'IN_CLOSE_WRITE' in type_names:
            logging.info(f"File closed: {os.path.join(path, filename)}")


def main():
    directory = '/path/to/monitor'
    current_os = platform.system()

    logging.info(f"Operating System: {current_os}")

    while True:
        monitor_file_close(directory)
        time.sleep(1)


if __name__ == "__main__":
    main()
