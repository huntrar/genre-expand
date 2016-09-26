genre-expand
===============================================================

Expand ID3 genre metadata using Wikipedia
-----------------------------------------

Update or replace ID3 genre metadata of MP3 files using data extracted from Wikipedia. Can recursively expand metadata of music directories with or without the need for user confirmation. Allows for topic disambiguation by the user to improve precision, as well as the option to only fill in missing genres.

Installation
------------

::

    pip install genre-expand

or

::

    pip install git+https://github.com/huntrar/genre-expand.git#egg=genre-expand

or

::

    git clone https://github.com/huntrar/genre-expand
    cd genre-expand
    python setup.py install


Usage
-----

::

    usage: genre_expand.py [-h] -d SEARCH_DIR [-r] [-l LEVEL] [-f] [-s] [-m] [-q]
                           [-v]

    expand ID3 genre metadata

    optional arguments:
      -h, --help            show this help message and exit
      -d SEARCH_DIR, --search-dir SEARCH_DIR
                            directory to search
      -r, --recursive       recursively search directories
      -l LEVEL, --level LEVEL
                            depth of directories to recurse
      -f, --force           do not prompt user ever
      -s, --force-save      save files without prompt
      -m, --missing-only    only expand missing genres
      -q, --quiet           suppress status and error messages
      -v, --version         display current version

Author
------

-  Hunter Hammond (huntrar@gmail.com)

Notes
-----

- Choosing the 'force' option will remove the need for prompts, but will also avoid making changes where a choice is ambiguous. If you want to disambiguate topics but skip other confirmations, use the 'force save' option.
- The 'missing only' option is available for only expanding tags with missing genre metadata, preventing overwrites of existing genres.
