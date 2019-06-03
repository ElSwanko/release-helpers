# -*- coding: utf-8 -*-

header_template = '''
[align=center][color=#336699][b][size=24]%(name)s[/size][/b][/color][/align][hr]
[poster=right]%(poster)s[/poster]
[b]Страна:[/b] %(country)s
[b]Жанр:[/b] %(genres)s
[b]Формат:[/b] %(format)s
[b]Тип издания:[/b] [url=%(vgmdb_link)s]%(release)s[/url]
[b]Исполнители:[/b] %(artists)s

[b]Кодек:[/b] %(codec)s
[b]Битрейт:[/b] %(bitrate)s
[b]Тип рипа:[/b] %(rip_type)s

[brc]
'''

footer_template = '''
[color=transparent][size=0]%(header_str)s
[b]Продолжительность:[/b] %(total_time)s
[b]Описание:[/b]
Альбомы в раздаче
%(albums_str)s
[/size][/color]
'''

header_str_template = '''
%(name)s — %(count)s альбомов (%(dates)s) /%(release)s/ %(format)s [%(codec)s|%(bitrate)s|%(rip_type)s] <%(genres)s>'''

single_album_template = '''
[b]Треклист:[/b]
%(tracklist)s

[b]Продолжительность:[/b] %(time)s
%(reports)s
'''

multi_album_template = '''
[hide=%(name)s]
%(cover)s
[b]Трeклист:[/b]
%(tracklist)s

[b]Прoдолжительность:[/b] %(time)s
%(reports)s
[/hide]'''

track_template = '''
[%(time)s] %(num)s. %(artist)s — %(title)s'''

spectrogram_template = '''[url=%(link)s][img]%(thumb)s[/img][/url]'''

show_meta_template = '''[hr][align=center][size=18][b]
%(meta_key)s
[/b][/size][/align][hr]
%(albums_str)s
'''

hide_meta_template = '''[hide=%(meta_key)s]
%(albums_str)s
[/hide][hr]
'''

preview_clips_template = '''
[hr][align=center][b]Несколько клипов для ознакомления:[/b]
%s
[/align][hr]'''

named_clips_template = '''
[hr][hide=Несколько клипов для ознакомления:]
%s[/hide]'''

SPECS_LIMIT = 3
COVER_WIDTH = 400
POSTER_WIDTH = 500
REPO_NAME = 'Folder.auCDtect.txt'
API_AUTH = {
    'token': 'dL6fE5q5GQzEIq5cQi4f',
    'secret_key': 'wXvMKwjoPVjnlppr9LtsIwyU1QgvHLzP5RO'
}
API_TIMEOUT = 30
API_RETRIES = 5

MISC = '_misc_'
UPDATES = '_updates_'
UTF8_BOM = b'\xef\xbb\xbf'

import argparse
import base64
import datetime
import json
import os

import requests
from PIL import Image


def main(args):
    print('Processing directory %s' % args.work_dir)
    check_misc_dirs(args, {})

    base_name = os.path.basename(args.work_dir) + '.json'
    main_path = os.path.join(args.work_dir, base_name)
    misc_path = os.path.join(args.work_dir, MISC, base_name)

    if os.path.isfile(misc_path) and os.path.isfile(main_path):
        merge_files(misc_path, main_path)
    elif os.path.isfile(main_path):
        os.rename(main_path, misc_path)
    elif not os.path.isfile(misc_path):
        print('Data file not found neither in %s no %s' % (misc_path, main_path))
        return

    data_json = open_data_json(misc_path)

    check_misc_dirs(args, data_json)

    if args.clean_images:
        clean_images(data_json)

    clean_data_json(data_json)
    save_data_json(misc_path, data_json)

    check_poster(args, data_json)

    code = header_template % data_json
    code += format_albums(args, data_json)
    code += format_updates(args)
    code += format_clips(args, data_json)
    code += format_footer(data_json)

    code_path = os.path.join(args.work_dir, MISC, data_json['name'] + '.txt')
    if os.path.isfile(code_path):
        os.remove(code_path)
    save_file(code_path, code)
    save_data_json(misc_path, data_json)
    print('Complete bb-code to %s' % code_path)


def open_data_json(path):
    with open(path, 'rb') as f:
        data = f.read()
        return json.loads(data[data.find(b'{'):].decode('utf-8'))


def save_data_json(path, data_json):
    save_file(path, json.dumps(data_json, ensure_ascii=False, indent=True))


def save_file(path, data_str):
    with open(path, 'wb') as f:
        f.write(UTF8_BOM + data_str.encode('utf-8'))


def merge_files(misc_path, main_path):
    misc_json = open_data_json(misc_path)
    main_json = open_data_json(main_path)
    misc_json['albums'].extend(main_json['albums'])
    misc_json['clips'].extend(main_json['clips'])
    save_data_json(misc_path, misc_json)
    os.remove(main_json)
    print('Merged data files: %s into %s' % (main_path, misc_path))


def albums_iterator(albums):
    for album in albums:
        if len(album.get('albums', [])) > 0:
            for child in album['albums']:
                yield child, album
        else:
            yield album, None


def clean_data_json(data_json):
    albums = list(filter(lambda a: len(a['dir']) > 0, data_json['albums']))
    for album, _ in albums_iterator(albums): clean_tracklist(album)
    data_json['albums'] = sorted(albums, key=lambda k: k['dir'])
    data_json['count'] = len(albums)
    data_json['name'] = data_json['name'].strip()
    print('Cleaned up data_json %s' % data_json['name'])


def clean_tracklist(album):
    tracklist = filter(lambda track: track['num'] != '00', album['tracklist'])
    album['tracklist'] = sorted(tracklist, key=lambda k: k['num'])
    print('Cleaned up tracklist in album %s' % album['dir'])


def clean_images(data_json):
    data_json['poster'] = ''
    for album, _ in albums_iterator(data_json['albums']): clean_album_images(album)
    print('Cleaned images in data file %s' % data_json['name'])


def clean_album_images(album):
    album['cover'] = ''
    album['spectrograms'] = []
    print('Cleaned images for album %s' % album['dir'])


def format_albums(args, data_json):
    print('Format albums from data file %s' % data_json['name'])
    albums_str = ''
    meta_keys = sorted(data_json['meta_keys'].keys())
    if len(meta_keys) > 1:
        for key in meta_keys:
            albums = filter_albums_by_meta_key(data_json['albums'], key)
            albums_str += (hide_meta_template if args.hide_meta else show_meta_template) % \
                          {'meta_key': data_json['meta_keys'][key], 'albums_str': process_albums(args, albums)}
    else:
        albums = filter_albums_by_meta_key(data_json['albums'], meta_keys[0])
        albums_str = process_albums(args, albums)
    print('Albums in data file %s formatted' % data_json['name'])
    return albums_str


def filter_albums_by_meta_key(albums, key):
    result = list(filter(lambda album: album['meta_key'] == int(key), albums))
    result = sorted(result, key=lambda k: k['dir'])
    print('Filtered %d albums by meta_key %s' % (len(result), key))
    return result


def process_albums(args, albums):
    print('Processing %d albums' % len(albums))
    if len(albums) == 1:
        print('Processing single album')
        return process_single_album(args, albums[0])
    albums_str = '\n'.join([process_multi_album(args, album) for album in albums])
    print('Processed %d albums' % len(albums))
    return albums_str


def process_multi_album(args, album, parent=None):
    if len(album.get('albums', [])) > 0:
        print('Processing multi-disc album %s of %d discs' % (album['dir'], len(album['albums'])))
        return '\n'.join(['[hide=%s]' % format_dir(album['dir']),
                          '\n'.join([process_multi_album(args, child, album)
                                     for child in sorted(album['albums'], key=lambda k: k['dir'])]), '[/hide]'])
    else:
        print('Processing single-disc album %s' % album['dir'])
        return multi_album_template % {
            'name': format_dir(album['dir']),
            'cover': format_cover(get_cover(args, album, parent)),
            'tracklist': format_tracks(album),
            'time': album['total_time'],
            'reports': format_reports(args, album, parent)
        }


def process_single_album(args, album):
    if len(album.get('albums', [])) > 0:
        print('Processing multi-disc album %s of %d discs' % (album['dir'], len(album['albums'])))
        return '\n'.join([process_multi_album(args, child, album)
                          for child in sorted(album['albums'], key=lambda k: k['dir'])])
    else:
        print('Processing album %s' % album['dir'])
        return single_album_template % {
            'tracklist': format_tracks(album),
            'time': album['total_time'],
            'reports': format_reports(args, album)
        }


def format_dir(dir_name):
    return dir_name.replace('[', '(').replace(']', ')')


def format_tracks(album):
    track_list = ''.join([track_template % track for track in sorted(album['tracklist'], key=lambda k: k['num'])])
    print('Formatted tracklist in album %s' % album['dir'])
    return track_list


def format_cover(cover):
    return '[img=right]%s[/img]' % cover if cover else ''


def get_cover(args, album, parent=None):
    print('Get cover for album %s' % album['dir'])
    if album['cover']:
        print('Got saved cover %s' % album['cover'])
        return album['cover']
    misc_path = os.path.join(get_misc_path(args, album, parent), 'cover.jpg')
    if os.path.isfile(misc_path):
        links = upload_image(misc_path)
        album['cover'] = links['link']
        print('Got cover from misc folder %s' % album['cover'])
        return album['cover']
    album_path = get_album_path(args, album, parent)
    img_path = os.path.join(album_path, 'cover.jpg')
    if os.path.isfile(img_path):
        resize_image(img_path, misc_path)
        links = upload_image(misc_path)
        album['cover'] = links['link']
        print('Got jpg cover from main folder %s' % album['cover'])
        return album['cover']
    img_path = os.path.join(album_path, 'cover.png')
    if os.path.isfile(img_path):
        resize_image(img_path, misc_path, convert=True)
        links = upload_image(misc_path)
        album['cover'] = links['link']
        print('Got png cover from main folder %s' % album['cover'])
        return album['cover']
    print('Cover not found for album %s' % album['dir'])
    return ''


def format_reports(args, album, parent=None):
    print('Format reports for album %s' % album['dir'])
    repo_str = ''
    aucdtect = get_aucdtect_report(args, album, parent)
    if len(aucdtect) > 0:
        repo_str += ''.join(['\n[spoiler=Отчёт auCDtect][pre]',
                             '\n'.join([line for line in aucdtect]), '[/pre][/spoiler]'])
        print('Formatted check report for album %s' % album['dir'])
    specs = get_spectrograms(args, album, parent)
    if len(specs) > 0:
        repo_str += ''.join(['\n[spoiler=Спектрограммы]',
                             ''.join([spectrogram_template % specs[i] for i in
                                      range(0, (SPECS_LIMIT if args.limit_specs else len(specs)))]), '[/spoiler]'])
        print('Formatted spectrograms for album %s' % album['dir'])
    return repo_str


def get_aucdtect_report(args, album, parent=None):
    misc_path = os.path.join(get_misc_path(args, album, parent), REPO_NAME)
    if not os.path.isfile(misc_path):
        main_path = os.path.join(get_album_path(args, album, parent), REPO_NAME)
        if os.path.isfile(main_path):
            os.rename(main_path, misc_path)
        else:
            print('Check report not found for album %s' % album['dir'])
            return []
    print('Found check %s report for album %s' % (misc_path, album['dir']))
    with open(misc_path, 'rb') as f:
        data = f.read()
        lines = data[data.find(b'-'):].decode('utf-16', errors='strict').split('\n')[14:]
        if not args.skip_cdda:
            return lines
        result = []
        while len(lines) > 2:
            record = lines[0:4]
            if record[2].find('MPEG') > 0:
                result.extend(record)
            lines = lines[4:]
        if len(result) == 0:
            result.append('All tracks are CDDA')
        return result


def get_spectrograms(args, album, parent=None):
    print('Get spectrograms for album %s' % album['dir'])
    if len(album['spectrograms']) > 0:
        print('Got saved spectrograms for album %s' % album['dir'])
        return album['spectrograms']
    misc_path = get_misc_path(args, album, parent)
    files = find_spectrograms(misc_path, True)
    if len(files) == 0:
        main_path = get_album_path(args, album, parent)
        main_files = find_spectrograms(main_path, False)
        if len(main_files) == 0:
            print('No spectrograms found for album %s' % album['dir'])
            return []
        else:
            print('Found %d files for album %s' % (len(main_files), album['dir']))
            for file in main_files:
                misc_file = os.path.join(misc_path, file)
                os.rename(os.path.join(main_path, file), misc_file)
                files.append(misc_file)
    album['spectrograms'] = list(map(lambda f: upload_image(f), files))
    print('Got new spectrograms for album %s' % album['dir'])
    return album['spectrograms']


def find_spectrograms(path, join):
    result = list(map(lambda file: os.path.join(path, file) if join else file,
                      filter(lambda file: file.endswith('.Spectrogram.png'), os.listdir(path))))
    print('Found %d spectrograms in path %s' % (len(result), path))
    return result


def format_clips(args, data_json):
    if len(data_json.get('clips', [])) == 0:
        return ''
    clips_str = ''.join(['[url=%(url)s]%(name)s[/url]\n' % clip if args.named_clips
                         else '[yt]%(url)s[/yt] ' % clip for clip in data_json['clips']])
    return (named_clips_template if args.named_clips else preview_clips_template) % clips_str


def format_updates(args):
    updates_dir = os.path.join(args.work_dir, MISC, UPDATES)
    updates = os.listdir(updates_dir)
    if len(updates) == 0:
        return ''
    updates_str = '\n[hr][spoiler=История обновлений]\n'
    for update_file in sorted(updates):
        updates_str += '[spoiler=%s]\n' % os.path.basename(update_file)
        with open(os.path.join(updates_dir, update_file), encoding='utf-8') as f:
            for line in f.readlines():
                updates_str += line
        updates_str += '[/spoiler]\n'
    return updates_str + '[/spoiler]\n'


def format_footer(data_json):
    header_str = header_str_template % data_json
    total_time = datetime.timedelta()
    albums = data_json['albums']
    for album, _ in albums_iterator(albums):
        total_time += parse_time(album['total_time'])
    albums_str = '\n'.join([format_dir(album['dir']) for album in albums[-4:]])
    return footer_template % {
        'header_str': header_str,
        'total_time': total_time.__str__(),
        'albums_str': albums_str
    }


def parse_time(time):
    h, m, s = map(int, time.split(':'))
    return datetime.timedelta(hours=h, minutes=m, seconds=s)


def get_album_path(args, album, parent=None):
    album_path = [args.work_dir]
    if parent:
        album_path.append(parent['dir'])
    album_path.append(album['dir'])
    return os.path.join(*album_path)


def get_misc_path(args, album, parent=None):
    album_path = [args.work_dir, MISC]
    if parent:
        album_path.append(parent['dir'])
    album_path.append(album['dir'])
    return os.path.join(*album_path)


def check_misc_dirs(args, data_json):
    check_dir(os.path.join(args.work_dir, MISC))
    check_dir(os.path.join(args.work_dir, MISC, UPDATES))
    for album, parent in albums_iterator(data_json.get('albums', [])):
        check_dir(get_misc_path(args, album, parent))
    print('Checked misc directories')


def check_dir(misc_dir):
    if not os.path.isdir(misc_dir):
        os.makedirs(misc_dir, exist_ok=True)


def check_poster(args, data_json):
    print('Get poster in data file %s' % data_json['name'])
    if data_json['poster']:
        print('Got saved poster in data file %s' % data_json['name'])
        return
    misc_path = os.path.join(args.work_dir, MISC, 'poster.jpg')
    if not os.path.isfile(misc_path):
        main_path = os.path.join(args.work_dir, 'poster.jpg')
        if os.path.isfile(main_path):
            resize_image(main_path, misc_path)
        else:
            data_json['poster'] = ''
            print('No poster found for data file %s ' % data_json['name'])
            return
    links = upload_image(misc_path)
    data_json['poster'] = links['link']
    print('Found poster for data file %s' % data_json['name'])


def resize_image(img_path, misc_path, new_width=COVER_WIDTH, convert=False):
    img = Image.open(img_path)
    if img.size[0] >= img.size[1]:
        new_size = (new_width, int(img.size[1] * (new_width / img.size[0])))
    else:
        new_size = (int(img.size[0] * (new_width / img.size[1])), new_width)
    print('Resize cover %s from %s to %s' % (img_path, img.size, new_size))
    img = img.resize(new_size, Image.LANCZOS)
    if convert and img.mode == 'RGBA':
        img = img.convert('RGB')
    img.save(misc_path, 'JPEG')
    print('Resized cover in path %s' % misc_path)


def _upload_image(img_path):
    print('Uploaded image in path %s' % img_path)
    return {'link': img_path, 'thumb': img_path}


def upload_image(img_path):
    print('Uploading image in path %s' % img_path)
    with open(img_path, 'rb') as f:
        img = f.read()

    headers = {'Authorization': 'TOKEN ' + API_AUTH['token']}
    data = {'secret_key': API_AUTH['secret_key'], 'image': base64.encodebytes(img)}
    result = {'link': '', 'thumb': ''}
    tries = API_RETRIES
    while tries > 0:
        try:
            response = requests.post('https://api.imageban.ru/v1', data=data, headers=headers, timeout=API_TIMEOUT)
            if response.status_code == 200:
                response = json.loads(response.text, encoding='utf-8')
                if response['status'] == 200:
                    data = response['data']
                    result['link'] = data['link']
                    result['thumb'] = '/'.join(['https:/', data['server'], 'thumbs', data['date'], data['name']])
                    tries = 1
                else:
                    print('Failed to upload image in path %s: %s' % (img_path, response))
            else:
                print('Failed to upload image in path %s: %s' % (img_path, response))
        except Exception as e:
            print('Failed to upload image in path %s, cause: %s' % (img_path, e))
        finally:
            tries -= 1
    print('Uploaded image in path %s: %s' % (img_path, result))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Music release helper')
    parser.add_argument('--clean_images', required=False, action='store_true')
    parser.add_argument('--named_clips', required=False, action='store_true')
    parser.add_argument('--limit_specs', required=False, action='store_true')
    parser.add_argument('--skip_cdda', required=False, action='store_true')
    parser.add_argument('--hide_meta', required=False, action='store_true')
    parser.add_argument('work_dir', type=str)
    arguments = parser.parse_args()
    print(arguments.work_dir)
    main(arguments)
