# -*- coding: utf-8 -*-
import json
import os
import sys

UTF8_BOM = b'\xef\xbb\xbf'


def rename_dirs(work_dir):
    back_data = {}
    back_file = os.path.join(work_dir, 'back.json')
    if os.path.isfile(back_file):
        with open(back_file, 'rb') as f:
            back_data = f.read()
            back_data = json.loads(back_data[back_data.find(b'{'):].decode('utf-8'))
    reverse = len(back_data.keys()) > 0

    i = 0
    dirs = os.listdir(work_dir)
    for d in dirs:
        fd = os.path.join(work_dir, d)
        if os.path.isdir(fd):
            if reverse:
                os.rename(os.path.join(work_dir, d), os.path.join(work_dir, back_data[d]))
            else:
                os.rename(fd, os.path.join(work_dir, '%d' % i))
                back_data[i] = d
                i += 1

    if reverse:
        os.remove(back_file)
    else:
        with open(back_file, 'wb') as f:
            f.write(UTF8_BOM + json.dumps(back_data, ensure_ascii=False, indent=True).encode('utf-8'))

    print('%s rename done!' % ('Direct' if not reverse else 'Reverse'))


if __name__ == '__main__':
    rename_dirs(sys.argv[1])
