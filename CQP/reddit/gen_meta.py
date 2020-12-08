import io, os, time
import re


meta = ['id', 'author', 'author_flair_css', 'author_flair_text', 'controversiality', 'created_utc', 'decade',
        'distinguished', 'edited', 'gilded', 'link_id', 'month', 'parent_id', 'retrieved_on', 'score', 'stickied',
        'subreddit', 'subreddit_id', 'ups', 'year']


def text2dict(text):
    """
    <text author="Saotome84" author_flair_css="" author_flair_text="None" controversiality="0" created_utc="1533052789"
    distinguished="None" edited="" gilded="0" link_id="t3_938g8w" parent_id="t1_e3c2s09" retrieved_on="1536927861"
    score="1" stickied="False" subreddit="TsundereSharks" subreddit_id="t5_2zhuq" ups="" year="2018" month="7" decade="2010">
    """
    if '\t' in text:
        raise ValueError('Illegible format.')
    out_dict = {}
    text = re.sub('\t', '', text)
    fields = re.sub('="( )+', '="', text).strip('<text ').strip('>').replace('=" "', '=""').split('" ')
    for i in fields:
        k = i.split('=')[0]
        if k == 'author_flair_css_class':
            k = 'author_flair_css'
        v = i.split('=')[-1].strip('"')
        v = v.replace('"', '')

        if k not in meta:
            raise ValueError(f'The key does not exist. The line is {text}')
        if not v:
            v = '_'
        out_dict[k] = v
    return out_dict


meta_file_dir = 'data' + os.sep + 'reddit2020_meta.tab'
in_file_dir = 'data' + os.sep + 'reddit_2020.sgml'

with io.open(meta_file_dir, 'w', encoding='utf-8') as outfile:
    headline = '\t'.join(meta)
    # outfile.write(f'{headline}\n')

    with io.open(in_file_dir, encoding='utf-8') as f:
        # print(filename)
        start_time = time.time()

        for c, line in enumerate(f.read().split('\n')):
            if line.startswith('<text '):
                meta_dict = text2dict(line)
                try:
                    meta_line = '\t'.join([meta_dict[i] for i in meta])
                except:
                    raise ValueError(f'Line in {c}')
                outfile.write(f'{meta_line}\n')
    end_time = time.time()
    print(f'Time cost: {int(end_time-start_time)}s')
