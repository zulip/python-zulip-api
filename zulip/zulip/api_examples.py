#!/usr/bin/env python
import os
import zulip

def main():
    zulip_path = os.path.abspath(os.path.dirname(zulip.__file__))
    examples_path = os.path.abspath(os.path.join(zulip_path, 'examples'))
    if os.path.isdir(examples_path):
        print(examples_path)
    else:
        raise OSError("Examples cannot be accessed at {}: Directory does not exist!"
                      .format(examples_path))

if __name__ == '__main__':
    main()
