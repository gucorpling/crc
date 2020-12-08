'''
Corpus: State of the Union Address
Created by: Yilun Zhu
The Project Gutenberg EBook of Complete State of the Union Addresses,
from 1790 to 2020
Website: http://stateoftheunion.onetwothree.net/index.shtml
'''

import io, os, sys, tempfile, subprocess
import stanza


def gen_meta():
    return 0


PY3 = sys.version_info[0] == 3

def exec_via_temp(input_text, command_params, workdir=""):
    temp = tempfile.NamedTemporaryFile(delete=False)
    exec_out = ""
    try:
        if PY3:
            # try:
            temp.write(input_text.encode("utf8"))
            # except:
            # 	temp.write(input_text)
        else:
            temp.write(input_text)
        temp.close()

        command_params = [x if x != 'tempfilename' else temp.name for x in command_params]
        if workdir == "":
            proc = subprocess.Popen(command_params, stdout=subprocess.PIPE,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
            (stdout, stderr) = proc.communicate()
        else:
            proc = subprocess.Popen(command_params, stdout=subprocess.PIPE,stdin=subprocess.PIPE,stderr=subprocess.PIPE,cwd=workdir)
            (stdout, stderr) = proc.communicate()

        exec_out = stdout
    except Exception as e:
        print(e)
    finally:
        os.remove(temp.name)
        if PY3:
            try:
                exec_out = exec_out.decode("utf8").replace("\r","")
            except:
                pass
        return exec_out

raw_dir = 'data.txt'
out_dir = 'to2020.txt'
articles = ''

nlp = stanza.Pipeline('en', processors='tokenize')

with io.open(raw_dir, encoding='utf-8') as f:
    cur_article = []
    line_count = 0
    skip = 0
    sent = ''

    lines = f.read().split('\n')
    for i, line in enumerate(lines):
        if not line:
            if not sent:
                continue
            cur_article.append(sent)
            doc = nlp(sent)
            tok_sents = [[word.text for word in sentence.words] for sentence in doc.sentences]
            tt_path = os.path.abspath(os.path.join("..", "ttagger"))
            cmd = [tt_path + os.sep + "cmd" + os.sep + "tree-tagger",
                   "-token", "-lemma", "-no-unknown", "-hyphen-heuristics",
                   ".."+os.sep+"ttagger" + os.sep + "lib" + os.sep + "english.par", "tempfilename"]
            for tokenized in tok_sents:
                tagged = "<s>\n" + exec_via_temp('\n'.join(tokenized), cmd) + "</s>\n"
                articles += tagged
            sent = ''
        elif line.startswith('**'):
            if cur_article:
                articles += '</text>\n'
                cur_article = []
                line_count = 0
        elif line == 'State of the Union Address':
            name = lines[i+1]
            short_name = name.split()[-1]
            date = lines[i+2]
            year, month, day = date.split()[-1], date.split()[0], date.split()[1].strip(',')
            decade = '2020s' if year.startswith('202') else '2010s'
            headline = f'<text id="{short_name.lower()}_{year}" name="{name}" short_name="{short_name}" party="None" decade="{decade}" year="{year}" month="{month}" day="{day}">\n'
            articles += headline

            skip = 2
        elif skip > 0:
            skip -= 1
        else:
            sent += line

        line_count += 1

articles += '</text>\n'
with io.open(out_dir, 'w', encoding='utf-8') as f:
    f.write(articles)
print('Done!')
