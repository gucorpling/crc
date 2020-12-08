import io, os


def return_label(line):
    if line.startswith('</text'):
        return '/text', 'close'
    elif line.startswith('</p'):
        return '/p', 'close'
    elif line.startswith('</s'):
        return '/s', 'close'
    elif line.startswith('<text'):
        return 'text', 'open'
    elif line.startswith('<p'):
        return 'p', 'open'
    elif line.startswith('<s'):
        return 's', 'open'


stack = []
with io.open('data/reddit_2020.sgml', encoding='utf-8') as f:
    lines = f.read().split('\n')

    for i, line in enumerate(lines):
        # if i == 155732:
        #     a = 1
        if i != len(lines) - 1:
            if line == '</text>' and not lines[i+1].startswith('<text '):
                raise ValueError(f'Lines between <text> and </text>, Error at Line {i+1}')
        if line.startswith('<'):
            label, state = return_label(line)
            if state == 'open':
                stack.append((label, state))
            else:
                try:
                    last = stack.pop()
                except:
                    raise ValueError(f'Error in Line {i+1}')

                if last[0] not in label or last[-1] == state:
                    raise ValueError(f'Format error between <{last}> and <{label}> in Line {i+1}')

print('Done!')
