# Goal
Protex aims at providing a flexible, extensible and interfaced way to remove TeX
macros from a TeX/LaTeX document while keeping the mapping from cleaned texte to
source.  This should make it easier to apply different language checkers to the
plain text and convert the plain text position to source positions.

# Non-goal

This project won't try to parse TeX in a complex way. The cleaning has to be
extensible, but nor recursive, neither Turing complete as TeX is itself.

# Principle

The mapping found in *commands.json* lists commands to be recognised and
their call structures. Arguments will be rendered using a simple template format
so that most information from the TeX document can be kept.  The template won't
allow complex computing and won't be applied recursively.

If a command is not found in the *commands.json* file it will be assumed that it
take one argument that should be printed as is (ex: `section` from LaTeX fit
this case perfectly).

A per-project file *.protex.json* updates the definitions from
*commands.json* if available.

# Notes

The requirements.txt is only for development and test, not for normal usage.
