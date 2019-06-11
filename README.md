# Goal
Protex aims at providing a flexible, extensible and interfaced way to remove
TeX macros from a TeX/LaTeX document while keeping the mapping of position from
cleaned text to source. This should make it easier to apply different language
checkers to the plain text and convert the plain text position to source
positions.
When possible the resulting file should also be a reasonably readable text file
(no big blanks, no strange holes...).

# Non-goal

This project won't try to parse TeX in a complex way. The cleaning has to be
extensible, but nor recursive, neither Turing complete as TeX is itself.

# Principle

A command prototype set is first built from the default *commands.json*,
updated by the user *~/.commands.json* (if it exists) and then all the
*commands.json* files found in the file tree from root to the current
directory.

A command prototype tell the parser how many arguments at maximum take the
command and how to use them. There are four sections in *commands.json* files.
The three below consist in a list of special prototype:
* `print_name`: the command take no argument and is replace by its name (ex: `\phi`, `\sum`)
* `print_one`: the command take one argument and print it unchanged
* `discard`: the command take up to 100 arguments and print nothing
The fourth section is `other` and have a mapping as value. The
mapping is of the form `{<command_name>: [<# max args>, <template>]}`.
The template is a string where everything will be printed as is but:
* `%0` will be replace with the command name
* `%1` will be replaced with the first argument (and so on for `%2`, `%3` etc without limit)
* `%%` will be replaced with a raw `%`
* `%` followed by anything else will not be replaced

When parsing the TeX source, the argument collection end as soon as one of
those conditions is fulfilled:
* the max number of arguments have been reached
* the next token is a blank
* the next token is a "word" of more than one letter (a word a sequence of
  contiguous everything that is neither whitespace nor a special thing in TeX
  (comments, commands, curly brackets, square bracket), be carefull,
  punctuation like "." is a valid one letter word that can be the last argument
  of a command)
* the last argument was a non bracketed one letter "word"

Those rules can seem a bit convoluted but if you have a valid TeX document and
valid command prototypes, the result should be what you expect.

# Installation

From source: in the folder of this README run `pip install .` in a terminal.
With pip directly: run `pip install -U protex`

# Usage

See the command line help by running `protex` or `python -m protex`.

# Notes

The requirements.txt is only for development and test, not for normal usage.
There are no dependencies at all.
