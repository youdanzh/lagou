#Youdan zhang 2019 CuseHack
#Jiaqi Li
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from collections import defaultdict
from string import punctuation
from heapq import nlargest
from PIL import Image
import pytesseract

filename = input("Please enter the Full Filename\n")
text=pytesseract.image_to_string(Image.open(filename))
newfile = input("Please enter the text saving directory and filename (eg:/Users/zhangyoudan/Desktop/news.txt) \n")
with open(newfile, 'wt') as f:
    print(text, file=f)

stopwords = set(stopwords.words('english') + list(punctuation))
max_cut = 0.8
min_cut = 0.1
#ignore the max annd main freq
##compute freq func
def compute_frequencies(word_sent):
    freq = defaultdict(int)
    for c in word_sent:
        for word in c:
            if word not in stopwords:
                freq[word] += 1
    a = float(max(freq.values()))
    for w in list(freq.keys()):
        freq[w] = freq[w]/a
        if freq[w] >= max_cut or freq[w] <= min_cut:
               del freq[w]
#if the article too short
    return freq
#summarize by freq
def summarize(text, num):
    sents = sent_tokenize(text)
    assert num <= len(sents)
    word_sent = [word_tokenize(s.lower()) for s in sents]
    freq = compute_frequencies(word_sent)
    ranking = defaultdict(int)
    for i, word in enumerate(word_sent):
        for w in word:
            if w in freq:
                ranking[i] += freq[w]
    sents_idx = rank(ranking, n)
    return [sents[j] for j in sents_idx]
#ranking freq
def rank(ranking, n):
    return nlargest(n, ranking, key=ranking.get)
#main
if __name__ == '__main__':
    with open(newfile, "r") as myfile:
        text = myfile.read().replace('\n','')
    res = summarize(text, 2)
    for i in range(len(res)):
        print(res[i])
