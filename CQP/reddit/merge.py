import io, os
import re
from lxml import etree
from xml.sax.saxutils import escape

meta = ['id', 'author', 'author_flair_css_class', 'author_flair_text', 'controversiality', 'created_utc', 'decade',
        'distinguished', 'edited', 'gilded', 'link_id', 'month', 'parent_id', 'retrieved_on', 'score', 'stickied',
        'subreddit', 'subreddit_id', 'ups', 'year']


def text2dict(text):
    """
    <text author="Saotome84" author_flair_css="" author_flair_text="None" controversiality="0" created_utc="1533052789"
    distinguished="None" edited="" gilded="0" link_id="t3_938g8w" parent_id="t1_e3c2s09" retrieved_on="1536927861"
    score="1" stickied="False" subreddit="TsundereSharks" subreddit_id="t5_2zhuq" ups="" year="2018" month="7" decade="2010">
    """
    out = '<text'
    text = re.sub('\t', '', text)
    fields = re.sub('="( )+', '="', text).strip('<text ').strip('>').replace('=" "', '=""').split('" ')
    for i in fields:
        k = i.split('=')[0]
        if k not in meta:
            raise ValueError('Key not found')
        if k == 'author_flair_css_class':
            k = 'author_flair_css'
        v = i.split('=')[-1]
        v = v.replace('"', '').strip()
        if not v:
            v = '_'
        out += f' {k}="{v}"'
    out += '>'
    return out


in_dir = 'data' + os.sep + 'final_reddit'
out_dir = 'data'
out = ''

for filename in os.listdir(in_dir):
    if not filename.startswith('RC'):
        continue

    # if filename != 'RC_2020_1_ss.sgml':
    #     continue

    changed = ''
    with io.open(in_dir+os.sep+filename, encoding='utf-8') as f:
        lines = f.read()

        lines = re.sub('</text>\n</s>\n\n', '</text>\n', lines)
        lines = re.sub('([^>])\n</p>', '\1\n</s>\n</p>', lines)
        lines = re.sub('<p>\n([^<])', '<p>\n<s>\n\1', lines)

        lines = lines.split('\n')

        for line in lines:

            if '\t' in line:
                if '<text ' in line:
                    line = re.sub('\t', '', line)
                    changed += line + '\n'
                    continue
                if '' in line:
                    line = re.sub('', '\t', line)
                    line = re.sub('\t+', '\t', line)
                if '&gt' in line:
                    line = re.sub('&gt', '&gt;', line)
                if '&lt' in line:
                    line = re.sub('&lt', '&lt;', line)
                # if '&' in line:
                #     line = re.sub('&[^g|^l]', '&amp;', line)
                line = re.sub('&amp([^;])', '&amp;\1', line)

                if '<' in line:
                    new = []
                    fields = line.split('\t')
                    for x in fields:
                        if '<' in x:
                            x = x.replace('<', '&lt;')
                        new.append(x)
                    line = '\t'.join(new)
            elif line.startswith('<text '):
                # if line.startswith('<text id="esghxoa" author="Princess_Parabellum"'):
                #     a = 1
                line = text2dict(line)
            changed += line + '\n'

    out += changed

    re.sub('"_"><s>\n', '', out)
    re.sub('\n\n', '\n', out)
    re.sub('">\n<s>\n', '', out)

with io.open(out_dir+os.sep+'reddit_2020.sgml', 'w', encoding='utf-8') as f:
    f.write(out)

print('Done!')
