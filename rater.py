# -*- coding: utf-8 -*-
import argparse
import os

from PIL import Image, ImageFile

base_dir = os.path.dirname(__file__)
sign_dir = os.path.join(base_dir, 'signs')


def rate(args):
    if not os.path.isfile(args.image_path):
        print('%s is not a file' % args.image_path)
        return
    sign_path = os.path.join(sign_dir, '%s_%02d.png' % (args.sign_style, args.age_rating))
    if not os.path.isfile(sign_path):
        print('Can\'t find sign for %s style and age rating %d: %s' %
              (args.sign_style, args.age_rating, sign_path))
        return

    print('Rating image %s' % args.image_path)
    img = Image.open(args.image_path)

    back = Image.new('RGBA', img.size)
    back.paste(img)

    back = resize_img(args, back)

    sign = Image.open(sign_path)
    offset = get_offset(args, back.size, sign.size)

    back.paste(sign, offset, mask=sign)
    back = back.convert('RGB')

    result_img = os.path.basename(args.image_path).split('.')[0] + '_%02d+.webp' % args.age_rating
    ImageFile.MAXBLOCK = 2 * img.size[0] * img.size[1]
    back.save(os.path.join(os.path.dirname(args.image_path), result_img), 'WebP', quality=95)


def resize_img(args, img):
    if args.new_width is not None and args.new_height is not None:
        new_size = (args.new_width, args.new_height)
    elif args.new_width is not None:
        new_size = (args.new_width, int(img.size[1] * (args.new_width / img.size[0])))
    elif args.new_height is not None:
        new_size = (int(img.size[0] * (args.new_height / img.size[1])), args.new_height)
    else:
        new_size = img.size
    return img.resize(new_size, Image.LANCZOS) if new_size != img.size else img


def get_offset(args, img_size, sign_size):
    offset = (0, 0)
    if args.sign_position == 0:
        offset = (args.sign_offset, args.sign_offset)
    elif args.sign_position == 1:
        offset = (img_size[0] - sign_size[0] - args.sign_offset, args.sign_offset)
    elif args.sign_position == 2:
        offset = (args.sign_offset, img_size[1] - sign_size[1] - args.sign_offset)
    elif args.sign_position == 3:
        offset = (img_size[0] - sign_size[0] - args.sign_offset,
                  img_size[1] - sign_size[1] - args.sign_offset)
    return offset


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Add age rating sign to image'
    )
    parser.add_argument(
        '--age_rating',
        required=False,
        metavar='AGE_RATING',
        default=12,
        type=int
    )
    parser.add_argument(
        '--sign_style',
        required=False,
        metavar='SIGN_STYLE',
        help='File prefix for age rating image file',
        default='default',
        type=str
    )
    parser.add_argument(
        '--sign_position',
        required=False,
        metavar='SIGN_POSITION',
        help='Position of age rating sign: '
             '0 - top-left, 1 - top-rigth, 2 - bottom-left, 3 - bottom-right',
        default='3',
        type=int
    )
    parser.add_argument(
        '--sign_offset',
        required=False,
        metavar='SIGN_OFFSET',
        help='Offset of age rating sign in pixels',
        default='10',
        type=int
    )
    parser.add_argument(
        '--new_width',
        required=False,
        metavar='NEW_WIDTH',
        type=int
    )
    parser.add_argument(
        '--new_height',
        required=False,
        metavar='NEW_HEIGHT',
        type=int
    )
    parser.add_argument(
        'image_path',
        metavar='IMAGE_PATH',
        help='Path to image file',
        type=str
    )
    arguments = parser.parse_args()
    rate(arguments)
