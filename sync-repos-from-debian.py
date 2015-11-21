#!/usr/bin/python

# Copyright 2015 Jonathan Riddell <jr@jriddell.org>
# May be copied under the GNU GPLv2 or later

# Script to ensure all the repos in Debian pkg-kde Git are in Neon
# It'll get the list from the git.debian website, add any that are
# missing to gitolite-admin/conf then clone those archives from
# git.debian and mirror them into the new neon one
#
# To Do:
# make it work with a given archive
# make it not fail when cloning empty debian archives
# make it add hooks

import urllib2
import re
import subprocess
import os

def debug(string):
    print string

# for some reason our git server doesn't like % in tag names
def removeInvalidTags():
    debug("in removeInvalidTags()")
    proc = subprocess.Popen(['git', 'tag', '-l'],stdout=subprocess.PIPE)
    while True:
        line = proc.stdout.readline()
        if '%' in line:
            debug("found a bad tag: " + line)
            subprocess.check_call(["git", "tag", "-d", line.rstrip()])
        if line == "":
            break

response = urllib2.urlopen('http://anonscm.debian.org/cgit/pkg-kde/')

debianRepositories = []
for line in response:
    if line.find('sublevel-repo') > 0:
        out = re.split(".*title='pkg-kde/(.*)' href='", line)
        debianRepositories.append(str(out[1]))

debug(str(debianRepositories))

if not os.path.isdir("gitolite-admin"):
    subprocess.check_call(["git", "clone", "neon:gitolite-admin"])
    os.chdir("gitolite-admin")
else:
    os.chdir("gitolite-admin")
    subprocess.check_call(["git", "pull"])

neonRepositories = []
with open("conf/gitolite.conf") as f:
    for line in f:
        out = re.split("repo (.*)", line)
        if len(out) > 2:
            debug(out[1])
            neonRepositories.append(out[1])

f = open("conf/gitolite.conf", 'a')

for repo in debianRepositories:
    if repo in neonRepositories:
        debug(repo + " is in neon repo")
    else:
        debug(repo + " not in neon repo")
        f.write("repo " + repo + "\n")
        f.write("    RW+     =   @all\n\n")
subprocess.check_call(["git", "commit", "-a", "-m 'sync repos with debian'"])
subprocess.check_call(["git", "push"])

os.chdir("..")

for repo in debianRepositories:
#    if repo not in neonRepositories:
        subprocess.check_call(["git", "clone", "debian:"+repo])
        repoName = repo.split("/")[-1]
        os.chdir(repoName)
        removeInvalidTags()
        subprocess.check_call(["git", "push", "--mirror", "neon:"+repo])
        os.chdir("..")
        subprocess.check_call(["rm", "-rf", repoName])
