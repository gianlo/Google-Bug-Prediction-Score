#!/bin/python

from __future__ import print_function

import os
import math
import datetime
import subprocess
import csv
import optparse



def get_output(cmd):
    return subprocess.check_output(cmd)

command_option = None

def str2time(v):
    return datetime.datetime.strptime(v, "%Y-%m-%d")
    
def daydifference(after, before):
    return (str2time(before)-str2time(after)).days

def text2date(line):
    date = line[8:18]
    if date[0] == "2":
        return date
    
def getdates(lines):
    datelist = []
    for line in lines:
        h = line.find("Date:")
        if h != -1:
            date = text2date(line)
            if date is not None:
                datelist.append(date)
    return datelist
        
def get_gitlog(path):
    command = ["git", "log", "--date=short", '--', path]
    text = get_output(command).decode("utf-8")
    lines = text.split("\n")
    return lines

def google_score(duration, existing):
    ti = 0
    if (existing != 0):
        ti = duration*1.0 / existing
    return 1.0 / (1.0+math.exp((-12.0*ti)+12.0))

def calc_fix_score(datelist):
    if len(datelist) < 1:
        return 0
    first_commit_date = datelist[len(datelist)-1]
    existing_days = daydifference(first_commit_date, datetime.date.today().isoformat())
    score = 0
    for date in datelist:
        duration = daydifference(first_commit_date, date)
        score += google_score(duration, existing_days)
    return score

def calc_score_from_path(path):
    lines = get_gitlog(path)
    datelist = getdates(lines)
    score = calc_fix_score(datelist)
    return score

def remove_unused_ext(path):
    global command_option
    if command_option.extension is None:
        return path
    ext = "." + command_option.extension
    index = path.find(ext)
    if index == -1:
        return None
    else:
        return path

def remove_git_directory(path):
    index = path.find(".git")
    if index == -1:
        return path
    else:
        return None

def remove_unused_path(path):
    path = remove_unused_ext(path)
    if path is not None:
        path = remove_git_directory(path)
    return path


def get_file_pathes(root):
    filelist = []
    for dpath, dnames, fnames in os.walk(root):
        if not remove_git_directory(dpath):
            continue
        for fname in fnames:
            path = os.path.join(dpath, fname)
            need_path = remove_unused_path(path)
            if need_path is not None:
	            filelist.append(need_path)
    return filelist

def get_package_pathes(root):
    packagelist = []
    for dpath, dnames, fnames in os.walk(root):
        for dname in dnames:
            path = os.path.join(dpath, dname)
            path = remove_git_directory(path)
            if path is not  None:
                packagelist.append(path)
    return packagelist

def get_pathes(root):
    global command_option
    f_package = command_option.package
    if f_package:
        list = get_package_pathes(root)
    else:
        list = get_file_pathes(root)
    return list

def parse_option():
    parser = optparse.OptionParser()
    parser.add_option("-t", "--target", dest="target",
        default=".",
        help="target path to analyse")
    parser.add_option("-p", "--package", dest="package", action="store_true",
        default=False, help="analyse not for file but package")
    parser.add_option("-e", "--extension", dest="extension",
        default=None, help="extension restriction (used only --package==False)")
    options, remainder = parser.parse_args()
    print( 'target    :', options.target)
    print( 'package   :', options.package)
    print( 'extension :', options.extension)
    global command_option
    command_option = options
    return options

print("=====start======")
options = parse_option()
outputfile = "bugfix_score.csv"
with open(outputfile, "wt", newline='') as ofi:
    writercsv = csv.writer(ofi)
    print("Retrieving files...")
    filelist = get_pathes(options.target)
    print("Scoring files...")
    os.chdir(options.target)
    for f in filelist:
        try:
            score = calc_score_from_path(f)
            if score > 0:
                print( f, score)
            writercsv.writerow([f, score])
        except:
            continue
    
print("=====end======")

