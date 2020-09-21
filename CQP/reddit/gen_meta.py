import io, os, time


def text2dict(text):
    """
    <text author="Saotome84" author_flair_css="" author_flair_text="None" controversiality="0" created_utc="1533052789"
    distinguished="None" edited="" gilded="0" link_id="t3_938g8w" parent_id="t1_e3c2s09" retrieved_on="1536927861"
    score="1" stickied="False" subreddit="TsundereSharks" subreddit_id="t5_2zhuq" ups="" year="2018" month="7" decade="2010">
    """
    out_dict = {}
    fields = text.strip('<text '). strip('>').split(' ')
    for i in fields:
        k = i.split('=')[0]
        v = i.split('=')[-1].strip('"')
        if not v:
            v = '_'
        out_dict[k] = v
    return out_dict


meta = ['id', 'author', 'author_flair_css', 'author_flair_text', 'controversiality', 'created_utc', 'decade',
        'distinguished', 'edited', 'gilded', 'link_id', 'month', 'parent_id', 'retrieved_on', 'score', 'stickied',
        'subreddit', 'subreddit_id', 'ups', 'year']

meta_file_dir = 'meta.tab'
in_file_dir = 'out'

with io.open(meta_file_dir, 'w', encoding='utf-8') as outfile:
    headline = '\t'.join(meta)
    outfile.write(f'{headline}\n')

    for filename in os.listdir(in_file_dir):
        print(filename)
        start_time = time.time()
        with io.open(in_file_dir + os.sep + filename, encoding='utf-8') as f:
            for line in f.read().split('\n'):
                if line.startswith('<text '):
                    meta_dict = text2dict(line)
                    meta_line = '\t'.join([meta_dict[i] for i in meta])
                    outfile.write(f'{meta_line}\n')
        end_time = time.time()
        print(f'Time cost: {int(end_time-start_time)}s')
