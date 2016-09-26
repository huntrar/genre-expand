#!/usr/bin/env python
"""Expand ID3 genre metadata of MP3 files using Wikipedia."""

import os
import sys

import eyed3
import wikipedia

ARTIST_SEARCH_LIMIT = 3  # Number of pages to search per artist
FOUND_GENRES = {}  # Cache for artists and genres


def expand_genres(dir):
    """Uses Wikipedia and eyed3 ID3 tagging to expand MP3 metadata."""
    for paths in os.walk(dir):
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

            if artist not in audio_files:
                # Initialize audio file list with old genre name, if any
                genre = audio_file.tag.genre
                genre_name = ''
                if genre:
                    genre_name = genre.name
                audio_files[artist] = [genre_name]
            audio_files[artist].append(audio_file)

        # Find genres for each artist, first item in songs list is old genre
        for artist, songs in audio_files.iteritems():
            if artist in FOUND_GENRES:
                modify_songs(artist, songs[1:], FOUND_GENRES[artist])
                continue

            print('Artist: {}\tOld Genre: {}'.format(artist, songs[0]))
            genres = find_genres(artist)
            if not genres:
                print('No new genres found for {}.'.format(artist))
                FOUND_GENRES[artist] = None
                print('\n\n\n')
                continue

            modify_songs(artist, songs[1:], ';'.join(genres))


def find_genres(artist):
    """Use Wikipedia to find genres for an artist.
    
    
       Pages are searched for Genre keywords and music-related titles
       If more than one music related title exists user is asked to choose
    """
    genres = []
    searched = set()
    for page in find_pages(artist):
        print('Page title: {}'.format(page.title))
        searched.add(page.title)
        genres = filter_genres(page.html())
        if genres and confirm_genres(artist, genres):
            break
    else:
        for page in find_pages(artist, failed=True):
            if page.title in searched:
                continue
            print('Page title: {}'.format(page.title))
            genres = filter_genres(page.html())
            if genres and confirm_genres(artist, genres):
                break

    return genres



def confirm_genres(artist, genres):
    """Allow user to confirm a new genre label."""
    inp = raw_input('Label {} as {}?\n: '.format(artist, ';'.join(genres)))
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
        inp = raw_input('Is the topic {} or none?\n: '.format(', '.join(choices)))
        for choice in choices:
            if inp in choice:
                return wikipedia.page(choice)
    return None


def filter_genres(html):
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
            sys.stderr.write('No genre found on page.\n')
            return genres

    while '">' in genre_string:
        genre_string = '">'.join(genre_string.split('">')[1:])
        genres.append(genre_string.split('<')[0].strip())
    return [x for x in genres if x]


def modify_songs(artist, songs, new_genres):
    """Modify an artist's songs with new genres."""
    if not new_genres:
        return

    if songs:
        # Confirm modification if genre already set to something
        old_genre = songs[0].tag.genre
        old_genre_name = ''
        if old_genre:
            old_genre_name = old_genre.name

        if old_genre_name:
            if artist in FOUND_GENRES and FOUND_GENRES[artist]:
            inp = raw_input('Really change {}\'s genre from {} to {}?\n: '.format(artist, old_genre_name, new_genres))
            if 'y' not in inp.lower():
                FOUND_GENRES[artist] = None
                print('\n\n\n')
                return
        
        if artist not in FOUND_GENRES:
            # Cache newly identified genres to FOUND_GENRES
            FOUND_GENRES[artist] = new_genres

        for song in songs:
            song.tag.genre = eyed3.id3.Genre(new_genres)
            print('Saving {}'.format(song.tag.title))
            song.tag.save()
    print('\n\n\n')

                
if __name__ == '__main__':
    if not len(sys.argv) > 1:
        print('You must enter a directory name.')
    else:
        eyed3.log.setLevel("ERROR")
        expand_genres(sys.argv[1])
