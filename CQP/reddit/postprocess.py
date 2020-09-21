import re, io, os, time
import sys, tempfile, subprocess
from tqdm import tqdm
import stanza

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


def tree_tag(sent, nlp):
    doc = nlp(sent)
    toks = '\n'.join([word.text for sentence in doc.sentences for word in sentence.words])

    tt_path = os.path.abspath(os.path.join("ttagger")) + os.sep
    cmd = [tt_path + os.sep + "cmd" + os.sep + "tree-tagger",
           "-token","-lemma","-no-unknown","-hyphen-heuristics","ttagger"+os.sep+"lib"+os.sep+"english.par","tempfilename"]
    tagged = exec_via_temp(toks, cmd)

    return tagged

# tree_tag('What is the airspeed of an unladen swallow?')

nlp = stanza.Pipeline('en', processors='tokenize')

file_dir = 'out'
out_dir = 'processed_reddit'
if not os.path.exists(out_dir):
    os.mkdir(out_dir)
for filename in os.listdir(file_dir):
    # if filename != 'RC_2019_4.sgml':
    #     continue
    if os.path.isfile(out_dir+os.sep+filename):
        continue
    print(filename)
    start_time = time.time()
    with io.open(file_dir+os.sep+filename, encoding='utf-8') as f:
        file = f.read().split('</text>')

        with io.open(out_dir+os.sep+filename, 'w', encoding='utf-8') as out_file:

            for chunk in tqdm(file):
                meta = chunk.split('">\n')[0].strip() + '>\n'
                if meta:
                    out_file.write(meta)

                    p = chunk.split('">\n')[-1].strip().replace('<p>', '').replace('</p>', '')
                    out_file.write('<p>\n')

                    # tagging
                    tagged = tree_tag(p, nlp)
                    out_file.write(tagged)

                    out_file.write('</p>\n')
                    out_file.write('</text>\n')
        # out_file.close()
    end_time = time.time()
    print(f'Time cost: {int(end_time - start_time)}s')
