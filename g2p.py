# -*- coding: utf-8 -*-
"""
g2p.py
~~~~~~~~~~

This script converts Korean graphemes to romanized phones and then to pronunciation.

    (1) graph2phone: convert Korean graphemes to romanized phones
    (2) phone2prono: convert romanized phones to pronunciation
    (3) graph2phone: convert Korean graphemes to pronunciation

Usage:  $ python g2p.py '스물 여덟째 사람'
        (NB. Please check 'rulebook_path' before usage.)

Yejin Cho (ycho@utexas.edu)
Jaegu Kang (jaekoo.jk@gmail.com)
Hyungwon Yang (hyung8758@gmail.com)
Yeonjung Hong (yvonne.yj.hong@gmail.com)

Created: 2016-08-11
Last updated: 2019-01-31 Yejin Cho

* Key updates made:
    - G2P Performance test available ($ python g2p.py test)
    - G2P verbosity control available


Update by Cardroid6
"""

import datetime as dt
import math
import optparse
import re
from typing import List, Union

# Option
parser = optparse.OptionParser()
parser.add_option(
    "-v",
    action="store_true",
    dest="verbose",
    default="False",
    help="This option prints the detail information of g2p process.",
)

(options, args) = parser.parse_args()
verbose = options.verbose


class Phone:
    def __init__(
        self,
        cv_type: str,
        position: str,
        hangul: str,
        symbol: str,
    ):
        self._cv_type = cv_type
        self._position = position
        self._hangul = hangul
        self._symbol = symbol

    @property
    def cv_type(self):
        return self._cv_type

    @property
    def position(self):
        return self._position

    @property
    def hangul(self):
        return self._hangul

    @property
    def symbol(self):
        return self._symbol


class RuleBook:
    def __init__(self, rules, phns: List[Phone]):
        self._rules = []
        self._hangul_dict = {}
        self._symbol_dict = {}

        for rule in phns:
            self._rules.append(rule)

    @property
    def rules(self):
        return self._rules

    @property
    def hangul_dict(self):
        return self._hangul_dict

    @property
    def symbol_dict(self):
        return self._symbol_dict


def writefile(body, fname):
    with open(fname, "w", encoding="utf-8") as f:
        for line in body:
            f.write("{}\n".format(line))


def read_phonebook(phone_book_path):
    lines = []
    with open(phone_book_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    phn_list = []
    hangul_dict = {}
    symbol_dict = {}

    for line in lines:
        line = line.strip()
        if line == "":
            continue

        tokens = line.split("\t")
        # C/V_Type Position Hangul Symbol
        cv_type = tokens[0]
        position = tokens[1]
        hangul = tokens[2]
        symbol = tokens[3]

        phn = Phone(cv_type, position, hangul, symbol)

        phn_list.append(phn)
        hangul_dict[phn.hangul] = phn
        symbol_dict[phn.symbol] = phn

    return phn_list, hangul_dict, symbol_dict


def read_rulebook(rule_book_path):
    lines = []
    with open(rule_book_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    rule_in = []
    rule_out = []

    for line in lines:
        line = line.strip()

        if line != "":
            if line[0] != "#":
                IOlist = line.split("\t")
                rule_in.append(IOlist[0])
                if IOlist[1]:
                    rule_out.append(IOlist[1])
                else:  # If output is empty (i.e. deletion rule)
                    rule_out.append("")

    return rule_in, rule_out


def read_testset(testset_path):
    lines = []
    with open(testset_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    test_in = []
    test_out = []

    for line in lines:
        line = line.strip()

        if line != "" and line[0] != "#":
            IOlist = line.split("\t")
            test_in.append(IOlist[0])
            if IOlist[1]:
                test_out.append(IOlist[1])
            else:  # If output is empty (i.e. deletion rule)
                test_out.append("")

    return test_in, test_out


def is_hangul(charint):
    hangul_init = 44032
    hangul_fin = 55203
    return charint >= hangul_init and charint <= hangul_fin


def check_char_type(var_list):
    #  1: whitespace
    #  0: hangul
    # -1: non-hangul
    checked = []
    for i in range(len(var_list)):
        if var_list[i] == 32:  # whitespace
            checked.append(1)
        elif is_hangul(var_list[i]):  # Hangul character
            checked.append(0)
        else:  # Non-hangul character
            checked.append(-1)
    return checked


def graph2phone(graphs: Union[str, bytes]):
    # Encode graphemes as utf8
    if isinstance(graphs, bytes):
        try:
            graphs = graphs.decode("utf-8")
        except AttributeError:
            pass

    integers = []
    for i in range(len(graphs)):
        integers.append(ord(graphs[i]))

    # Romanization (according to Korean Spontaneous Speech corpus; 성인자유발화코퍼스)
    phones = ""
    ONS = [
        "k0",
        "kk",
        "nn",
        "t0",
        "tt",
        "rr",
        "mm",
        "p0",
        "pp",
        "s0",
        "ss",
        "oh",
        "c0",
        "cc",
        "ch",
        "kh",
        "th",
        "ph",
        "h0",
    ]
    NUC = [
        "aa",
        "qq",
        "ya",
        "yq",
        "vv",
        "ee",
        "yv",
        "ye",
        "oo",
        "wa",
        "wq",
        "wo",
        "yo",
        "uu",
        "wv",
        "we",
        "wi",
        "yu",
        "xx",
        "xi",
        "ii",
    ]
    COD = [
        "",
        "kf",
        "kk",
        "ks",
        "nf",
        "nc",
        "nh",
        "tf",
        "ll",
        "lk",
        "lm",
        "lb",
        "ls",
        "lt",
        "lp",
        "lh",
        "mf",
        "pf",
        "ps",
        "s0",
        "ss",
        "oh",
        "c0",
        "ch",
        "kh",
        "th",
        "ph",
        "h0",
    ]

    # Pronunciation
    idx = check_char_type(integers)
    iElement = 0
    while iElement < len(integers):
        if idx[iElement] == 0:  # not space characters
            base = 44032
            df = int(integers[iElement]) - base
            iONS = int(math.floor(df / 588)) + 1
            iNUC = int(math.floor((df % 588) / 28)) + 1
            iCOD = int((df % 588) % 28) + 1

            s1 = "-" + ONS[iONS - 1]  # onset
            s2 = NUC[iNUC - 1]  # nucleus

            if COD[iCOD - 1]:  # coda
                s3 = COD[iCOD - 1]
            else:
                s3 = ""
            tmp = s1 + s2 + s3
            phones = phones + tmp

        elif idx[iElement] == 1:  # space character
            tmp = "#"
            phones = phones + tmp

        phones = re.sub("-(oh)", "-", phones)
        iElement += 1
        tmp = ""

    # 초성 이응 삭제
    phones = re.sub("^oh", "", phones)
    phones = re.sub("-(oh)", "", phones)

    # 받침 이응 'ng'으로 처리 (Velar nasal in coda position)
    phones = re.sub("oh-", "ng-", phones)
    phones = re.sub("oh([# ]|$)", "ng", phones)

    # Remove all characters except Hangul and syllable delimiter (hyphen; '-')
    phones = re.sub(r"(\W+)\-", "\\1", phones)
    phones = re.sub(r"\W+$", "", phones)
    phones = re.sub(r"^\-", "", phones)
    return phones


def phone2prono(phones, rule_in, rule_out):
    # Apply g2p rules
    for pattern, replacement in zip(rule_in, rule_out):
        # print pattern
        phones = re.sub(pattern, replacement, phones)
        prono = phones
    return prono


def add_phone_boundary(phones):
    # Add a comma (,) after every second alphabets to mark phone boundaries
    ipos = 0
    newphones = ""
    while ipos + 2 <= len(phones):
        if phones[ipos] == "-":
            newphones = newphones + phones[ipos]
            ipos += 1
        elif phones[ipos] == " ":
            ipos += 1
        elif phones[ipos] == "#":
            newphones = newphones + phones[ipos]
            ipos += 1

        newphones = newphones + phones[ipos] + phones[ipos + 1] + ","
        ipos += 2

    return newphones


def add_space(phones):
    ipos = 0
    newphones = ""
    while ipos < len(phones):
        if ipos == 0:
            newphones = newphones + phones[ipos] + phones[ipos + 1]
        else:
            newphones = newphones + " " + phones[ipos] + phones[ipos + 1]
        ipos += 2

    return newphones


def graph2prono(graphs, rule_in, rule_out):
    romanized = graph2phone(graphs)
    romanized_bd = add_phone_boundary(romanized)
    prono = phone2prono(romanized_bd, rule_in, rule_out)

    prono = re.sub(",", " ", prono)
    prono = re.sub(" $", "", prono)
    prono = re.sub("#", "-", prono)
    prono = re.sub("-+", "-", prono)

    prono_prev = prono
    identical = False
    loop_cnt = 1

    if verbose:
        print("=> Romanized: " + romanized)
        print("=> Romanized with boundaries: " + romanized_bd)
        print("=> Initial output: " + prono)

    while not identical:
        prono_new = phone2prono(re.sub(" ", ",", prono_prev + ","), rule_in, rule_out)
        prono_new = re.sub(",", " ", prono_new)
        prono_new = re.sub(" $", "", prono_new)

        if re.sub("-", "", prono_prev) == re.sub("-", "", prono_new):
            identical = True
            prono_new = re.sub("-", "", prono_new)
            if verbose:
                print("\n=> Exhaustive rule application completed!")
                print("=> Total loop count: " + str(loop_cnt))
                print("=> Output: " + prono_new)
        else:
            if verbose:
                print("\n=> Rule applied for more than once")
                print("cmp1: " + re.sub("-", "", prono_prev))
                print("cmp2: " + re.sub("-", "", prono_new))
            loop_cnt += 1
            prono_prev = prono_new

    return prono_new


def test_g2p(rule, testset):
    (testin, testout) = read_testset(testset)
    cnt = 0
    body = []
    for idx in range(0, len(testin)):
        print("Test item #: " + str(idx + 1) + "/" + str(len(testin)))
        item_in = testin[idx]
        item_out = testout[idx]
        ans = graph2phone(item_out)
        ans = re.sub("-", "", ans)
        ans = add_space(ans)

        (rule_in, rule_out) = rule
        pred = graph2prono(item_in, rule_in, rule_out)

        if pred != ans:
            print("G2P ERROR:  [result] " + pred + "\t\t\t[ans] " + item_in + " [" + item_out + "] " + ans)
            cnt += 1
        else:
            body.append("[result] " + pred + "\t\t\t[ans] " + item_in + " [" + item_out + "] " + ans)

    print("Total error item #: " + str(cnt))
    writefile(body, "good.txt")


def run_g2p(graph, rule):
    (rule_in, rule_out) = rule
    return graph2prono(graph, rule_in, rule_out)


def run_test(rule, testset):
    print("[ G2P Performance Test ]")
    beg = dt.datetime.now()

    test_g2p(rule, testset)

    end = dt.datetime.now()
    print("Total time: ")
    print(end - beg)


# Usage:
if __name__ == "__main__":
    rule = read_rulebook("rulebook.txt")

    if args[0] == "test":  # G2P Performance Test
        run_test(rule, "testset.txt")

    else:
        graph = args[0]
        prono = run_g2p(graph, rule)
        print(prono)
