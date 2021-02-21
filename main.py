#! /usr/bin/env python3

import argparse

parser = argparse.ArgumentParser(description='Simple bomberman')

parser.add_argument('-p', '--pygame', dest='pygame', default=False,
                    action='store_true', help='Use pygame')
parser.add_argument('-b', '--brython', dest='brython', default=False,
                    action='store_true', help='Use brython, serving files')

args = parser.parse_args()

if args.pygame:
    from bomberman.backend.pygame.main import main
    main()
