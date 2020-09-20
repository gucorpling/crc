#!/usr/bin/python
# -*- coding: utf-8 -*-

import json, sys, re, os, io, time, requests
import praw
# import pandas as pd
import datetime as dt
from praw import Reddit
import csv, tempfile, random
from glob import glob
from langdetect import detect, DetectorFactory
from collections import defaultdict
# from postprocess import exec_via_temp, tree_tag

PY3 = sys.version_info[0] == 3

def get_subreddits(file):
    html = io.open(file, encoding='utf-8').read()
    res = re.findall(r'<a href="[\w\W]+?" rel="nofollow">/r/(\w+?)</a><br>', html)
    return res


def get_pushshift_data(sub=None, before=None, after=None, ids=None, getSubmissions=True, getComments=False, limit=1000):
    suffix = ''
    searchType = 'submission'
    if getComments or not getSubmissions:
        searchType = 'comment'
    if before is not None:
        suffix += '&before='+str(before)
    if after is not None:
        suffix += '&after=' + str(after)
    if sub is not None:
        suffix += '&subreddit=' + sub
    if ids is not None:
        suffix += '&ids=' + ','.join(ids)

    url = 'https://api.pushshift.io/reddit/search/'+searchType+'?sort=desc&size='+str(limit)+suffix
    print('loading '+url)
    r = requests.get(url)
    try:
        data = json.loads(r.content)
    except:
        data = {'data': {}}
    if len(data['data']) > 0:
        prev_end_date = data['data'][-1]['created_utc']
    else:
        prev_end_date = None
    return (data, prev_end_date)


def escape_reddit(lines):
    lines = re.sub(r'(?<!\\)(\\[nr])+', r' ___NEWLINE__', lines)  # Replace new lines with real newline
    lines = re.sub(r'(?<!\\)\\(["\\/bfnrt])', r' ', lines)  # Remove literal escapes in data
    lines = lines.replace("<","&lt;")
    lines = lines.replace(">","&gt;")
    lines = re.sub(" +"," ",lines)
    return lines


def make_para(text):
    text = text.split("___NEWLINE__")
    text = "</p>\n<p>".join(text)
    text = "<p>" + text + "</p>"
    text = text.replace("<p></p>","").strip()
    # Handle bullets
    text = re.sub(r'<p>(\s*)\*([^\n]*?[^*\n]\s*)</p>',r'\1<item>\2</item>',text)
    text = re.sub(r'((\s*<item>.*?</item>\s*\n?)+)',r'\n<list type="unordered">\1\n</list>',text)
    # Hyperlinks
    text = re.sub(r'\[(.*?)\]\((.*?)\)',r'<ref target="\2">\1</ref>',text)

    text = re.sub(r'\n+</p>', r'</p>', text)

    text = re.sub(r'\n+', ' ', text)

    return text.strip()


def flattenjson(b, delim):
    val = {}
    for i in b.keys():
        if isinstance(b[i], dict):
            get = flattenjson(b[i], delim)
            for j in get.keys():
                val[i + delim + j] = get[j]
        else:
            val[i] = b[i]

    return val


def search_comments(comments, columns, year, month, decade, spaces_so_far):
    spaces = 0
    this_post = ''
    for comment in comments:
        cur_post = '<text'
        body = comment['body']
        lang = ''
        try:
            lang = detect(body)
        except:
            lang = 'unknown'
            continue
        cur_space = body.count(' ')
        if cur_space >= min_length and cur_space <= max_length:
            if lang == 'en':
                for col in columns:
                    a = 1
                    if col not in comment.keys():
                        cur_post += f' {col}=""'
                    else:
                        field = comment[col]
                        cur_post += f' {col}="{field}"'
                cur_post += f' year="{year}" month="{month}" decade="{decade}">\n'
                text = make_para(body)

                cur_post += text + '\n</text>'
                spaces += cur_space

                this_post += cur_post + '\n'

        # if the number of comments is enough, build the doc for that submission
        if spaces_so_far + spaces > max_spaces_per_slice:
            break

    return spaces, this_post


# GHURC settings
min_length = 25
max_length = 500
max_tokens_per_slice = 255000
max_spaces_per_slice = 0.85*max_tokens_per_slice

add_meta_tag = True # Wrap with <meta...
# months = [str(i+1) for i in range(12)]
# years = ['2019', '2020']
years = ['2018']
months = ['7', '8', '9', '10', '11', '12']

list_subreddits = get_subreddits('listofsubreddits.html')
out_dir = 'out'

for year in years:
    for month in months:
        if year == '2020' and int(month) > 9:
            continue
        file_dir = out_dir + os.sep + f'RC_{year}_{month}.sgml'
        # if f'{year}-{month}' != '2019-3':
        #     continue
        print(f'{year}-{month}')

        if os.path.exists(file_dir):
            continue
        out_file = io.open(file_dir, 'w', encoding='utf-8')

        decade = "2010" if year.startswith("201") else "2020"
        spaces_so_far = 0
        this_post = ''
        sub_list = []
        start_epoch = int(dt.datetime(int(year), int(month), 1).timestamp())
        if month == '12':
            end_epoch = int(dt.datetime(int(year)+1, 1, 1).timestamp())
        else:
            end_epoch = int(dt.datetime(int(year), int(month)+1, 1).timestamp())

        # randomly select 30 subreddits
        sub = ','.join(random.choices(list_subreddits, k=30))
        sub_list += sub

        # columns = ['subreddit', 'distinguished', 'subreddit_type', 'subreddit_id', 'stickied', 'gilded', 'author',
        #            'author_flair_text', 'created_utc', 'parent_id', 'score', 'controversiality', 'is_submitter',
        #            'author_cakeday', 'author_flair_css_class', 'link_id', 'retrieved_on', 'id', 'can_gild', 'edited']
        columns = ['author', 'author_flair_css', 'author_flair_text', 'controversiality', 'created_utc',
                   'distinguished', 'edited', 'gilded', 'link_id', 'parent_id', 'retrieved_on', 'score',
                   'stickied', 'subreddit', 'subreddit_id', 'ups']

        print(f'Start searching comments from {year}-{month}...')
        start_time = time.time()
        # get 1000 comments
        (comments_tmp, prev_end_date) = get_pushshift_data(sub=sub, before=end_epoch, after=start_epoch, getComments=True, limit=1000)
        comments = comments_tmp['data']
        cur_spaces, cur_post = search_comments(comments, columns, year, month, decade, spaces_so_far)
        spaces_so_far += cur_spaces
        this_post += cur_post
        out_file.write(cur_post)

        # if not finished, continue
        while prev_end_date is not None:
            if spaces_so_far > max_spaces_per_slice:
                break
            (comments_tmp, prev_end_date) = get_pushshift_data(sub=sub, before=end_epoch, after=prev_end_date-1, getComments=True, limit=1000)
            if prev_end_date is not None:
                # submissions.extend(submissions_tmp['data'])
                comments = comments_tmp['data']
                cur_spaces, cur_post = search_comments(comments, columns, year, month, decade, spaces_so_far)
                spaces_so_far += cur_spaces
                this_post += cur_post
                out_file.write(cur_post)

        while spaces_so_far < max_spaces_per_slice:
            sub = ','.join(random.choices([x for x in list_subreddits if x not in sub_list], k=30))
            sub_list += sub
            (comments_tmp, new_prev_end_date) = get_pushshift_data(sub=sub, before=end_epoch, after=start_epoch,
                                                               getComments=True, limit=1000)
            comments = comments_tmp['data']
            cur_spaces, cur_post = search_comments(comments, columns, year, month, decade, spaces_so_far)
            spaces_so_far += cur_spaces
            this_post += cur_post
            out_file.write(cur_post)

            while new_prev_end_date is not None:
                if spaces_so_far > max_spaces_per_slice:
                    break
                (comments_tmp, new_prev_end_data) = get_pushshift_data(sub=sub, before=end_epoch, after=new_prev_end_date - 1,
                                                                   getComments=True, limit=1000)
                if new_prev_end_data is not None:
                    # submissions.extend(submissions_tmp['data'])
                    comments = comments_tmp['data']
                    cur_spaces, this_post = search_comments(comments, columns, year, month, decade, spaces_so_far)
                    spaces_so_far += cur_spaces
                    this_post += cur_post
                    out_file.write(cur_post)
        end_time = time.time()
        print(f'Time cost: {int(end_time - start_time)}s')

        print(spaces_so_far)

        # out_file.write(this_post)
        out_file.close()
