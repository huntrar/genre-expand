#!/usr/bin/env python
""" expand-genre - Expand ID3 genre metadata using Wikipedia

    written by Hunter Hammond (huntrar@gmail.com)
"""

from __future__ import absolute_import, print_function
import argparse as argp
import os
import sys

import eyed3
from six import PY2, iteritems
from six.moves import input
import wikipedia

from . import __version__

ARTIST_SEARCH_LIMIT = 3  # Number of pages to search per artist
FOUND_GENRES = {}  # Cache for artists and genres

MAX_LEVEL = 1000  # Maximum depth of directories to recurse

SPACE = '\n\n'


def get_parser():
    """Parse command-line arguments."""
    parser = argp.ArgumentParser(description='expand ID3 genre metadata')
    parser.add_argument('-d', '--search-dir', type=str, required=True,
                        help='directory to search')
    parser.add_argument('-r', '--recursive', action='store_true',
                        help='recursively search directories')
    parser.add_argument('-l', '--level', type=int, default=MAX_LEVEL,
                        help='depth of directories to recurse')
    parser.add_argument('-f', '--force', action='store_true',
                        help='do not prompt user ever')
    parser.add_argument('-s', '--force-save', action='store_true',
                        help='save files without prompt')
    parser.add_argument('-m', '--missing-only', action='store_true',
                        help='only expand missing genres')
    parser.add_argument('-q', '--quiet', action='store_true',
                        help='suppress status and error messages')
    parser.add_argument('-v', '--version', action='store_true',
                        help='display current version')
    return parser


def walk_level(search_dir, level):
    """os.walk with a level parameter."""
    search_dir = search_dir.rstrip(os.path.sep)
    assert os.path.isdir(search_dir)
    num_sep = search_dir.count(os.path.sep)
    for root, dirs, files in os.walk(search_dir):
        yield root, dirs, files
        num_sep_this = root.count(os.path.sep)
        if num_sep + level <= num_sep_this:
            del dirs[:]


def expand_genres(args):
    """Uses Wikipedia and eyed3 ID3 tagging to expand MP3 metadata."""
    for paths in walk_level(args['search_dir'], args['level']):
        # Load audio files by artist name, allowing MP3 only
        files = [x for x in paths[2] if x.endswith('.mp3')]
        audio_files = {}
        for file in files:
            filename = '{}/{}'.format(paths[0].rstrip('/'), file)
            audio_file = eyed3.load(filename)
            if not audio_file:
                continue

            artist = audio_file.tag.artist
            if not artist:
                continue

            genre = audio_file.tag.genre
            genre_name = ''
            if genre:
                genre_name = genre.name

            # If user chose missing only then skip songs with existing genres
            if genre_name and args['missing_only']:
                continue

            if artist not in audio_files:
                # Initialize audio file list with old genre name, if any
                audio_files[artist] = [genre_name]
            audio_files[artist].append(audio_file)

        # Find genres for each artist, first item in songs list is old genre
        for artist, songs in audio_files.iteritems():
            if artist in FOUND_GENRES:
                modify_songs(args, artist, songs[1:], FOUND_GENRES[artist], found_already=True)
                continue

            if not args['quiet']:
                print('Artist: {}\tOld Genre: {}'.format(artist, songs[0]))
            genres = find_genres(args, artist)
            if not genres:
                if not args['quiet']:
                    print('No new genres found for {}.'.format(artist))
                    print(SPACE)
                FOUND_GENRES[artist] = None
                continue

            modify_songs(args, artist, songs[1:], join_genres(genres))


def join_genres(genres):
    """Trim and join genres to 255 characters."""
    return ';'.join(genres)[:255]


def find_genres(args, artist):
    """Use Wikipedia to find genres for an artist.


       Pages are searched for Genre keywords and music-related titles
       If more than one music related title exists user is asked to choose
    """
    genres = []
    searched = set()
    for page in [x for x in find_pages(artist) if x]:
        if not args['quiet']:
            print('Searching page on {}'.format(page.title))
        searched.add(page.title)
        genres = filter_genres(args, page.html())
        if genres and confirm_genres(args, artist, genres):
            break
        else:
            genres = []
    else:
        for page in [x for x in find_pages(artist, failed=True) if x]:
            if page.title in searched:
                continue
            if not args['quiet']:
                print('Searching page on {}'.format(page.title))
            genres = filter_genres(args, page.html())
            if genres and confirm_genres(args, artist, genres):
                break
            else:
                genres = []

    return genres


def confirm_genres(args, artist, genres):
    """Allow user to confirm a new genre label."""
    if any((args['force_save'], args['force'])):
        return True
    inp = input('Label {} as {}?\n: '.format(artist, ';'.join(genres)))
    return 'y' in inp.lower()


def find_pages(artist, failed=False):
    """Find Wikipedia pages related to an artist.

       If search results contain more than one music keyword the user is
       asked to choose between the results.
       If a page is not chosen or we fail to find a genre we let Wikipedia
       choose one to ARTIST_SEARCH_LIMIT pages per artist.
    """
    valid_titles = ['artist', 'singer', 'rapper', 'music', 'band']
    if not failed:
        choices = [x.lower() for x in wikipedia.search(artist)]
        valid_choices = []
        for i, entry in enumerate(choices):
            # Always append the first choice of search results
            if i == 0 or any(x in entry for x in valid_titles):
                valid_choices.append(entry)

        if not valid_choices:
            valid_choices = choices[:ARTIST_SEARCH_LIMIT]

        return [choose_page(valid_choices)]

    # Attempt to identify a genre after a failure or lack of pages
    page = None
    try:
        page = wikipedia.page(artist)
    except wikipedia.exceptions.DisambiguationError as err:
        choices = [x.lower() for x in str(err).split('\n')]
        valid_choices = []
        for choice in choices:
            if any(x in choice for x in valid_titles):
                valid_choices.append(choice)

        return [wikipedia.page(x) for x in valid_choices]
    return [page]


def choose_page(choices):
    """Allow user to choose a page by displaying topics.

       If there is only a single choice that one is returned.
    """
    if len(choices) == 1:
        return wikipedia.page(choices[0])
    if choices:
        inp = input('Is the topic {} or none?\n: '.format(', '.join(choices)))
        for choice in choices:
            if inp in choice:
                return wikipedia.page(choice)
    return None


def filter_genres(args, html):
    """Filter Wikipedia HTML string for genre metadata."""
    genres = []
    if not html:
        return genres

    try:
        genre_string = html.split('Genres')[1].split('<th')[0]
        if not genre_string:
            return genres
    except IndexError:
        if 'Genres' not in html:
            if not args['quiet']:
                sys.stderr.write('No genre found on page.\n')
            return genres

    while '">' in genre_string:
        genre_string = '">'.join(genre_string.split('">')[1:])
        genres.append(genre_string.split('<')[0].strip())
    return [x for x in genres if x]


def modify_songs(args, artist, songs, new_genres, found_already=False):
    """Modify an artist's songs with new genres."""
    if not new_genres:
        return

    if songs:
        # Confirm or cancel modification if genre already set to something
        old_genre = songs[0].tag.genre
        old_genre_name = ''
        if old_genre:
            old_genre_name = old_genre.name

        if old_genre_name == new_genres:
            if not args['quiet'] and not found_already:
                print('New and old genre match; moving on...')
                print(SPACE)

            cache_artist(artist, new_genres)
            return

        if old_genre_name and not any((args['force_save'], args['force'])):
            if artist not in FOUND_GENRES or (artist in FOUND_GENRES and not FOUND_GENRES[artist]):
                inp = input('Really change {}\'s genre from {} to {}?\n: '.format(artist, old_genre_name, new_genres))
                if 'y' not in inp.lower():
                    FOUND_GENRES[artist] = None
                    if not args['quiet']:
                        print(SPACE)
                    return

        cache_artist(artist, new_genres)

        if not args['quiet']:
            print('Artist: {}\tNew Genre: {}'.format(artist, new_genres))
        for song in songs:
            song.tag.genre = eyed3.id3.Genre(new_genres)
            if not args['quiet']:
                print('Saving {}... '.format(song.tag.title))
            try:
                song.tag.save()
            except Exception as err:
                if not args['quiet']:
                    sys.stderr.write('Error during saving: {}\n'.format(str(err)))

    if not args['quiet']:
        print(SPACE)


def cache_artist(artist, new_genres):
    """Cache newly identified genres in FOUND_GENRES."""
    if artist not in FOUND_GENRES:
        FOUND_GENRES[artist] = new_genres


def command_line_runner():
    """Handle command-line interaction."""
    parser = get_parser()
    args = vars(parser.parse_args())

    if args['version']:
        print(__version__)
        return

    eyed3.log.setLevel("ERROR")

    if args['level'] == MAX_LEVEL and not args['recursive']:
        # Set level to 0 for a non-recursive search
        args['level'] = 0

    expand_genres(args)


if __name__ == '__main__':
    command_line_runner()
