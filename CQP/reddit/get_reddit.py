#!/usr/bin/python
# -*- coding: utf-8 -*-

import json, sys, re, os, io, time, requests
# import praw
# import pandas as pd
import datetime as dt
# from praw import Reddit
import csv, tempfile, random
from glob import glob
from langdetect import detect, DetectorFactory
from collections import defaultdict
# from postprocess import exec_via_temp, tree_tag

PY3 = sys.version_info[0] == 3

def get_subreddits(file):
    html = io.open(file, encoding='utf-8').read()
    res = re.findall(r'<a href="[\w\W]+?" rel="nofollow">/r/(\w+?)</a><br>', html)
    cleaned = [x for x in res if 'Porn' not in x or 'porn' not in x]
    return cleaned


def get_pushshift_data(sub=None, before=None, after=None, ids=None, getSubmissions=True, getComments=False, limit=500):
    suffix = ''
    searchType = 'submission'
    if getComments or not getSubmissions:
        searchType = 'comment'
    if before is not None:
        suffix += '&before='+str(before)
    if after is not None:
        suffix += '&after=' + str(after)
    if sub is not None:
        suffix += '&subreddit!=Porn'
    if ids is not None:
        suffix += '&ids=' + ','.join(ids)

    url = f'https://api.pushshift.io/reddit/{searchType}/search/'+'?size='+str(limit)+suffix
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
    # text = re.sub(r'<p>(\s*)\*([^\n]*?[^*\n]\s*)</p>',r'\1<item>\2</item>',text)
    # text = re.sub(r'((\s*<item>.*?</item>\s*\n?)+)',r'\n<list type="unordered">\1\n</list>',text)
    # Hyperlinks
    text = re.sub(r'\[(.*?)\]\((.*?)\)',r'',text)

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


def search_comments(comments, columns, year, month, decade, spaces_so_far, seen_id):
    spaces = 0
    this_post = ''
    for comment in comments:
        if comment['id'] in seen_id:
            continue
        seen_id.append(comment['id'])
        cur_post = '<text'
        body = comment['body']
        body = re.sub('''[^&…;äé0-9a-zA-Z ="'_<>\n\t,./$:?@!\[\]+#\|()*%`-~\\-\^-]''', '', body)
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
                        if field and isinstance(field, str):
                            field = field.replace('"', '')
                        cur_post += f' {col}="{field}"'
                cur_post += f' year="{year}" month="{month}" decade="{decade}">\n'
                cur_post = re.sub('''[^&…;äé0-9a-zA-Z ="'_<>\n\t,./$:?@!\[\]+#\|()*%`-~\\-\^-]''', '', cur_post)
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
months = [str(i+1) for i in range(12)]
years = ['2018', '2019', '2020']

list_subreddits = get_subreddits('listofsubreddits.html')
out_dir = 'data' + os.sep + 'out'

for year in years:
    for month in months:
        if year == '2020' and int(month) > 11:
            continue
        elif year == '2018' and int(month) <= 6:
            continue
        file_dir = out_dir + os.sep + f'RC_{year}_{month}.sgml'
        # if f'{year}-{month}' != '2019-8':
        #     continue
        print(f'{year}-{month}')

        # if os.path.exists(file_dir):
        #     continue
        out_file = io.open(file_dir, 'w', encoding='utf-8')

        decade = "2010" if year.startswith("201") else "2020"
        spaces_so_far = 0
        this_post = ''
        seen_id = []
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
        columns = ['id', 'author', 'author_flair_css_class', 'author_flair_text', 'controversiality', 'created_utc',
                   'distinguished', 'edited', 'gilded', 'link_id', 'parent_id', 'retrieved_on', 'score',
                   'stickied', 'subreddit', 'subreddit_id', 'ups']

        print(f'Start searching comments from {year}-{month}...')
        start_time = time.time()
        # get 500 comments
        (comments_tmp, prev_end_date) = get_pushshift_data(sub=sub, before=start_epoch+100, after=start_epoch, getComments=True, limit=500)
        comments = comments_tmp['data']
        cur_spaces, cur_post = search_comments(comments, columns, year, month, decade, spaces_so_far, seen_id)

        spaces_so_far += cur_spaces
        this_post += cur_post
        out_file.write(cur_post)

        # if not finished, continue
        while prev_end_date is not None:
            if spaces_so_far > max_spaces_per_slice:
                break
            (comments_tmp, prev_end_date) = get_pushshift_data(sub=sub, before=end_epoch, after=prev_end_date-1, getComments=True, limit=500)
            if prev_end_date is not None:
                # submissions.extend(submissions_tmp['data'])
                comments = comments_tmp['data']
                cur_spaces, cur_post = search_comments(comments, columns, year, month, decade, spaces_so_far, seen_id)
                if cur_spaces == 0:
                    # sub = ','.join(random.choices([x for x in list_subreddits if x not in sub_list], k=30))
                    # prev_end_date = start_epoch
                    break
                spaces_so_far += cur_spaces
                this_post += cur_post
                out_file.write(cur_post)

        end_time = time.time()
        print(f'Time cost: {int(end_time - start_time)}s')

        print(spaces_so_far)

        # out_file.write(this_post)
        out_file.close()
