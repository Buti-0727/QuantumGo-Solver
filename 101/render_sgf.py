#!/usr/bin/env python3
import sys
import re
from pathlib import Path

SGF_LETTERS = "abcdefghjklmnopqrst"

def sgf_to_idx(coord):
    return (SGF_LETTERS.index(coord[0]), SGF_LETTERS.index(coord[1]))

def parse_sgf(sgf):
    ab = re.findall(r'AB((?:\[[a-z]{2}\])*)', sgf)
    aw = re.findall(r'AW((?:\[[a-z]{2}\])*)', sgf)
    moves = re.findall(r';([BW])\[([a-z]{2})\]', sgf)
    
    stones = {}
    for grp in ab:
        for c in re.findall(r'\[([a-z]{2})\]', grp):
            stones[sgf_to_idx(c)] = 'X'
    for grp in aw:
        for c in re.findall(r'\[([a-z]{2})\]', grp):
            stones[sgf_to_idx(c)] = 'O'
    for color, c in moves:
        stones[sgf_to_idx(c)] = '1' if color == 'B' else '2'
    return stones

def render(stones, size=19):
    print('   ' + ' '.join(SGF_LETTERS[:size]))
    for r in range(size):
        row = []
        for c in range(size):
            row.append(stones.get((c, r), '.'))
        print(f'{SGF_LETTERS[r]:2} ' + ' '.join(row))

if __name__ == '__main__':
    sgf = Path(sys.argv[1]).read_text()
    stones = parse_sgf(sgf)
    render(stones)
