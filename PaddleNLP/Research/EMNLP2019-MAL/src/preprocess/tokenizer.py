#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2018 Baidu.com, Inc. All Rights Reserved
#

"""
File: tokenizer.py
Author: xionghao(xionghao05@baidu.com)
Date: 2018/7/6 下午5:17
"""
# coding=utf-8
# Copyright 2018 The Tensor2Tensor Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import collections
import sys
import glob
import unicodedata
import six
import logging
from six.moves import range  # pylint: disable=redefined-builtin

# Conversion between Unicode and UTF-8, if required (on Python2)
_native_to_unicode = (lambda s: s.decode("utf-8")) if six.PY2 else (lambda s: s)

# This set contains all letter and number characters.
_ALPHANUMERIC_CHAR_SET = set(
    six.unichr(i) for i in range(sys.maxunicode)
    if (unicodedata.category(six.unichr(i)).startswith("L") or
        unicodedata.category(six.unichr(i)).startswith("N")))


def encode(text):
    """Encode a unicode string as a list of tokens.

    Args:
      text: a unicode string
    Returns:
      a list of tokens as Unicode strings
    """
    if not text:
        return []
    ret = []
    token_start = 0
    # Classify each character in the input string
    is_alnum = [c in _ALPHANUMERIC_CHAR_SET for c in text]
    for pos in range(1, len(text)):
        if is_alnum[pos] != is_alnum[pos - 1]:
            token = text[token_start:pos]
            if token != u" " or token_start == 0:
                ret.append(token)
            token_start = pos
    final_token = text[token_start:]
    ret.append(final_token)
    return ret


def decode(tokens):
    """Decode a list of tokens to a unicode string.

    Args:
      tokens: a list of Unicode strings
    Returns:
      a unicode string
    """
    token_is_alnum = [t[0] in _ALPHANUMERIC_CHAR_SET for t in tokens]
    ret = []
    for i, token in enumerate(tokens):
        if i > 0 and token_is_alnum[i - 1] and token_is_alnum[i]:
            ret.append(u" ")
        ret.append(token)
    return "".join(ret)


def _read_filepattern(filepattern, max_lines=None, split_on_newlines=True):
    """Reads files matching a wildcard pattern, yielding the contents.

    Args:
      filepattern: A wildcard pattern matching one or more files.
      max_lines: If set, stop reading after reading this many lines.
      split_on_newlines: A boolean. If true, then split files by lines and strip
          leading and trailing whitespace from each line. Otherwise, treat each
          file as a single string.

    Yields:
      The contents of the files as lines, if split_on_newlines is True, or
      the entire contents of each file if False.
    """
    filenames = sorted(glob.glob(filepattern))
    lines_read = 0
    for filename in filenames:
        with open(filename, 'r') as f:
            if split_on_newlines:
                for line in f:
                    yield line.strip()
                    lines_read += 1
                    if max_lines and lines_read >= max_lines:
                        return

            else:
                if max_lines:
                    doc = []
                    for line in f:
                        doc.append(line)
                        lines_read += 1
                        if max_lines and lines_read >= max_lines:
                            yield "".join(doc)
                            return
                    yield "".join(doc)

                else:
                    yield f.read()


def corpus_token_counts(
        text_filepattern, corpus_max_lines, split_on_newlines=True):
    """Read the corpus and compute a dictionary of token counts.

    Args:
      text_filepattern: A pattern matching one or more files.
      corpus_max_lines: An integer; maximum total lines to read.
      split_on_newlines: A boolean. If true, then split files by lines and strip
          leading and trailing whitespace from each line. Otherwise, treat each
          file as a single string.

    Returns:
      a dictionary mapping token to count.
    """
    counts = collections.Counter()
    for doc in _read_filepattern(
            text_filepattern,
            max_lines=corpus_max_lines,
            split_on_newlines=split_on_newlines):
        counts.update(encode(_native_to_unicode(doc)))

    return counts


def vocab_token_counts(text_filepattern, max_lines):
    """Read a vocab file and return a dictionary of token counts.

    Reads a two-column CSV file of tokens and their frequency in a dataset. The
    tokens are presumed to be generated by encode() or the equivalent.

    Args:
      text_filepattern: A pattern matching one or more files.
      max_lines: An integer; maximum total lines to read.

    Returns:
      a dictionary mapping token to count.
    """
    ret = {}
    for i, line in enumerate(
            _read_filepattern(text_filepattern, max_lines=max_lines)):
        if "," not in line:
            logging.warning("Malformed vocab line #%d '%s'", i, line)
            continue

        token, count = line.rsplit(",", 1)
        ret[_native_to_unicode(token)] = int(count)

    return ret
