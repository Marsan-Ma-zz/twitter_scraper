# coding: utf-8
import os, json, yaml, requests, jieba, argparse
import re
import numpy as np

from langdetect import detect
from datetime import datetime
from random import random, choice


def gather_raws(args):
    raw = []
    files = ["%s/%s" % (args.source_path, f) for f in os.listdir(args.source_path) if args.lang in f]
    for f in files:
        raw += open(f, 'rt').readlines()
    # print(len(raw), raw[0])
    return raw


def clean_line(line):
    # language detect
    try:
        lang = detect(line)
    except Exception as e:
        lang = 'unknown'
    # remove links
    line = re.sub(r"http\S+", "", line)
    # remove tags
    line = re.sub(r"\@[a-z0-9-_][a-z0-9-_]*", '', line)
    line = re.sub(r"\#[a-z0-9-_][a-z0-9-_]*", '', line)
    # strip multi-spaces, tabs and newlines
    line = re.sub("\s+", ' ', line).strip()
    return line, lang


def dump_cleaned_corpus(args, raw, filename='./corpus/cleaned_corpus.txt'):
    filename = "%s/cleaned_corpus_%s.txt" % (args.result_path, args.lang)
    with open(filename, 'w') as fw:
        for idx in range(len(raw)//2):
            sent1, lang1 = clean_line(raw[2*idx])
            sent2, lang2 = clean_line(raw[2*idx+1])
            if (args.lang == lang1[:2] == lang2[:2]) and (len(sent1) > 10) and (len(sent2) > 10):
                fw.write(sent1+"\n")
                fw.write(sent2+"\n")
            if (idx % 1000) == 0:
                print("dump %i lines @ %s" % (idx, datetime.now()))


if __name__ == '__main__':
    # parser
    parser = argparse.ArgumentParser()
    parser.add_argument('--lang', type=str, required=True, help='language: en/zh/ja')
    parser.add_argument('--source_path', type=str, default='./corpus', help='source data path')
    parser.add_argument('--result_path', type=str, default='./corpus', help='cleared data path')
    args = parser.parse_args()

    # main    
    raw = gather_raws(args)
    dump_cleaned_corpus(args, raw)

