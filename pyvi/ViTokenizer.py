import sys
import os
import codecs
import pickle
import re
import string
import unicodedata as ud

UPPER = "[" + "".join([
    "A-Z",
    "ÀÁẢÃẠ",
    "ĂẰẮẲẴẶ",
    "ÂẦẤẨẪẬ",
    "Đ",
    "ÈÉẺẼẸ",
    "ÊỀẾỂỄỆ",
    "ÌÍỈĨỊ",
    "ÒÓỎÕỌ",
    "ÔỒỐỔỖỘ",
    "ƠỜỚỞỠỢ",
    "ÙÚỦŨỤ",
    "ƯỪỨỬỮỰ",
    "ỲÝỶỸỴ"
]) + "]"
LOWER = UPPER.lower()
W = "[" + UPPER[1:-1] + LOWER[1:-1] + "]"  # upper and lower

class ViTokenizer:
    bi_grams = set()
    tri_grams = set()
    model_file = 'models/pyvi.pkl'
    if sys.version_info[0] == 3:
        model_file = 'models/pyvi3.pkl'

    with codecs.open(os.path.join(os.path.dirname(__file__), 'models/words.txt'), 'r', encoding='utf-8') as fin:
        for token in fin.read().split('\n'):
            tmp = token.split(' ')
            if len(tmp) == 2:
                bi_grams.add(token)
            elif len(tmp) == 3:
                tri_grams.add(token)
    with open(os.path.join(os.path.dirname(__file__), model_file), 'rb') as fin:
        model = pickle.load(fin)

    @staticmethod
    def word2features(sent, i, is_training):
        word = sent[i][0] if is_training else sent[i]

        features = {
            'bias': 1.0,
            'word.lower()': word.lower(),
            #   'word[-3:]': word[-3:],
            #   'word[-2:]': word[-2:],
            'word.isupper()': word.isupper(),
            'word.istitle()': word.istitle(),
            'word.isdigit()': word.isdigit(),
        }
        if i > 0:
            word1 = sent[i - 1][0] if is_training else sent[i - 1]
            features.update({
                '-1:word.lower()': word1.lower(),
                '-1:word.istitle()': word1.istitle(),
                '-1:word.isupper()': word1.isupper(),
                '-1:word.bi_gram()': ' '.join([word1, word]).lower() in ViTokenizer.bi_grams,
            })
            if i > 1:
                word2 = sent[i - 2][0] if is_training else sent[i - 2]
                features.update({
                    '-2:word.tri_gram()': ' '.join([word2, word1, word]).lower() in ViTokenizer.tri_grams,
                })
                #    else:
                #        features['BOS'] = True

        if i < len(sent) - 1:
            word1 = sent[i + 1][0] if is_training else sent[i + 1]
            features.update({
                '+1:word.lower()': word1.lower(),
                '+1:word.istitle()': word1.istitle(),
                '+1:word.isupper()': word1.isupper(),
                '+1:word.bi_gram()': ' '.join([word, word1]).lower() in ViTokenizer.bi_grams,
            })
            if i < len(sent) - 2:
                word2 = sent[i + 2][0] if is_training else sent[i + 2]
                features.update({
                    '+2:word.tri_gram()': ' '.join([word, word1, word2]).lower() in ViTokenizer.tri_grams,
                })
                #    else:
                #        features['EOS'] = True

        return features

    @staticmethod
    def sent2features(sent, is_training):
        return [ViTokenizer.word2features(sent, i, is_training) for i in range(len(sent))]

    @staticmethod
    def sylabelize(text):
        text = ud.normalize('NFC', text)

        specials = [
            r"=\>",
            r"==>",
            r"->",
            r"\.{2,}",
            r"-{2,}",
            r">>",
            r"\d+x\d+",  # dimension: 3x4
            r"v\.v\.\.\.",
            r"v\.v\.",
            r"v\.v",
            r"°[CF]"
        ]
        digit = [
            r"\d+(?:\.\d+)+,\d+",     # e.g. 4.123,2
            r"\d+(?:\.\d+)+",         # e.g. 60.542.000
            r"\d+(?:,\d+)+",          # e.g. 100,000,000
            r"\d+(?:[\.,_]\d+)?",     # 123
        ]
        phone = [
            r"\d{2,}-\d{3,}-\d{3,}"       # e.g. 03-5730-2357
                                          # very careful, it's easy to conflict with datetime
        ]
        name = [
            r"\d+[A-Z]+\d+",
            r"\d+[A-Z]+"  # e.g. 4K
        ]
        email = "([a-zA-Z0-9_.+-]+@([a-zA-Z0-9-]+\.)+[a-zA-Z0-9-]+)"
        #web = "^(http[s]?://)?(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+$"
        web = "\w+://[^\s]+"
        datetime = [
            # date
            r"\d{1,2}\/\d{1,2}\/\d+",     # e.g. 02/05/2014
            r"\d{1,2}\/\d{1,4}",          # e.g. 02/2014
                                          #   [WIP] conflict with number 1/2 (a half)
            r"\d{1,2}-\d{1,2}-\d+",       # e.g. 02-03-2014
            r"\d{1,2}-\d{1,4}",           # e.g. 08-2014
                                          #   [WIP] conflict with range 5-10 (from 5 to 10)
            r"\d{1,2}\.\d{1,2}\.\d+",     # e.g. 20.08.2014
            r"\d{4}\/\d{1,2}\/\d{1,2}",   # e.g. 2014/08/20
            r"\d{2}:\d{2}:\d{2}"          # time
                                          # e.g. 10:20:50 (10 hours, 20 minutes, 50 seconds)
        ]
        word = "\w+"
        non_word = "[^\w\s]"
        abbreviations = [
            r"[A-ZĐ]+&[A-ZĐ]+",  # & at middle of word (e.g. H&M)
            r"T\.Ư",  # dot at middle of word
            f"{UPPER}+(?:\.{W}+)+\.?",
            f"{W}+['’]{W}+",  # ' ’ at middle of word
            # e.g. H'Mông, xã N’Thôn Hạ
            r"[A-ZĐ]+\.(?!$)",  # dot at the end of word
            r"Tp\.",
            r"Mr\.", "Mrs\.", "Ms\.",
            r"Dr\.", "ThS\.", "Th.S", "Th.s",
            r"e-mail",            # - at middle of word
            r"\d+[A-Z]+\d*-\d+",  # vehicle plates
            # e.g. 43H-0530
            r"NĐ-CP"
        ]

        patterns = []
        patterns.extend(specials)
        patterns.extend(abbreviations)
        patterns.extend([web, email])
        patterns.extend(phone)
        patterns.extend(datetime)
        patterns.extend(name)
        patterns.extend(digit)
        patterns.extend([non_word, word])

        patterns = "(" + "|".join(patterns) + ")"
        if sys.version_info < (3, 0):
            patterns = patterns.decode('utf-8')
        tokens = re.findall(patterns, text, re.UNICODE)

        return text, [token[0] for token in tokens]

    @staticmethod
    def tokenize(str):
        text, tmp = ViTokenizer.sylabelize(str)
        if len(tmp) == 0:
            return str
        labels = ViTokenizer.model.predict([ViTokenizer.sent2features(tmp, False)])
        output = tmp[0]
        for i in range(1, len(labels[0])):
            if labels[0][i] == 'I_W' and tmp[i] not in string.punctuation and\
                            tmp[i-1] not in string.punctuation and\
                    not tmp[i][0].isdigit() and not tmp[i-1][0].isdigit()\
                    and not (tmp[i][0].istitle() and not tmp[i-1][0].istitle()):
                output = output + '_' + tmp[i]
            else:
                output = output + ' ' + tmp[i]
        return output

    @staticmethod
    def spacy_tokenize(str):
        text, tmp = ViTokenizer.sylabelize(str)
        if len(tmp) == 0:
            return str
        labels = ViTokenizer.model.predict([ViTokenizer.sent2features(tmp, False)])
        token = tmp[0]
        tokens = []
        spaces = []
        for i in range(1, len(labels[0])):
            if labels[0][i] == 'I_W' and tmp[i] not in string.punctuation and\
                            tmp[i-1] not in string.punctuation and\
                    not tmp[i][0].isdigit() and not tmp[i-1][0].isdigit()\
                    and not (tmp[i][0].istitle() and not tmp[i-1][0].istitle()):
                token = token + '_' + tmp[i]
            else:
                tokens.append(token)
                token = tmp[i]
        tokens.append(token)
#        text = re.sub("\s\s+" , " ", text)
#        print(tmp)
        i = 0
        for token in tokens:
            i = i + len(token)
            
#            print("{}:{}:{}".format(token,text[i], i))
            if i < len(text) and text[i] == ' ':
                spaces.append(True)
                i += 1
            else:
                spaces.append(False)
               
        return tokens, spaces#[True]*len(tokens)


def spacy_tokenize(str):
    return ViTokenizer.spacy_tokenize(str)


def tokenize(str):
    return ViTokenizer.tokenize(str)

