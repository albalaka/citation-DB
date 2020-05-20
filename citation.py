#!/usr/bin/env python3

import sys
from scholarly import scholarly
import time
from tqdm import tqdm
import pickle as pkl

from stem import Signal
from stem.control import Controller
import requests

proxies = {'http': 'socks5://127.0.0.1:9050',
           'https': 'socks5://127.0.0.1:9050'}
scholarly.use_proxy(**proxies)


def refresh_socket():
    print(requests.get('https://ident.me', proxies=proxies).text)
    with Controller.from_port(port=9051) as c:
        c.authenticate()
        c.signal(Signal.NEWNYM)
    print(requests.get('https://ident.me', proxies=proxies).text)


# RL - reinforcement learning
# CF - catastrophic forgetting
# STS - semantic textual similarity
# NLI - natural language inference (same as recognizing textual entailment)
# MC - machine comphrehension
# MT - machine translation
# SDS - Spoken dialogue system
all_tags = ["ML",
            "RL", "genetic programming", "meta learning", "game theory", "regret minimization",
            "multi agent", "multi task",

            "continual learning", "CF",
            "transfer learning",

            "IR",
            "logic",  "symbolic", "relational reasoning", "inductive learning",

            "transformer",

            "NLP", "LM", "NLG",
            "QA", "QG", "STS", "paraphrase identification",
            "NLI", "MC", "MT", "abstractive summarization",

            "VQA",

            "CV", "image captioning",

            "SLU", "ASR", "SDS",

            "XAI",
            ]


def slow_down(i):
    for i in range(i, 0, -1):
        sys.stdout.write("\r")
        sys.stdout.write("{:2d} seconds remaining.".format(i))
        sys.stdout.flush()
        time.sleep(1)


class publication_query(object):
    def __init__(self, query):
        # slow_down(10)
        self.search_result = scholarly.search_pubs(query)
        # slow_down(10)

    def next_result(self):
        # slow_down(10)
        try:
            result = next(self.search_result).fill()
        except Exception:
            print("Try again in an hourish")
            print(time.strftime("%H:%M:%S", time.localtime()))
            return None
        print(result)
        # slow_down(10)
        return result


class publication(object):
    def __init__(self, pub, read=False, notes=None, tags=None):
        self.bib = pub.bib
        self.bib['title'] = self.bib['title'].replace('"', "'")
        self.cited_by = []
        self.cites_to = []
        self.read = read
        if tags:
            self.tags = tags
        else:
            self.tags = []
        if notes:
            self.notes = notes
        else:
            self.notes = ""
        try:
            self.ID = pub.id_scholarcitedby
        except:
            self.ID = pub.url_scholarbib
        citedby = pub.get_citedby()
        for c in citedby:
            try:
                self.cited_by.append(c.id_scholarcitedby)
            except:
                self.cited_by.append(c.url_scholarbib)

    def add_tags(self, tags):
        for t in tags:
            self.tags.append(t)

    def add_notes(self, note):
        self.notes.append(note)

    def set_read(self, read):
        self.read = read

    def has_tag(self, tag):
        if tag in self.tags:
            return True
        return False

    def view(self):
        print("TAGS: {}".format(self.tags))
        print("Notes: {}".format(self.notes))


class citation_DB(object):
    def __init__(self):
        self.citations = {}

    def add_publication(self, c):
        assert(type(c) == publication)
        ID = c.ID
        print("Currently adding ID: {}".format(c.ID))
        assert(ID not in self.citations.keys()
               ), "This citation already exists?"
        self.citations[ID] = {"publication": c, "title": c.bib['title']}

        for paper in self.citations:
            # check if this item has been cited by another paper
            if paper in self.citations[ID]['publication'].cited_by:
                self.citations[paper]['publication'].cites_to.append(ID)
                print("Found citation from {} to {}".format(
                    self.citations[paper]['title'], self.citations[ID]['title']))
            # check if this item cites a paper in our citations
            if ID in self.citations[paper]['publication'].cited_by:
                self.citations[ID]['publication'].cites_to.append(paper)
                print("Found citation from {} to {}".format(self.citations[ID]['title'],
                                                            self.citations[paper]['title']))

    def view_citation_network(self):
        for ID, paper in self.citations.items():
            no_citations = True
            for c in paper['publication'].cites_to:
                no_citations = False
                print(
                    "{}\n\t---> {}".format(paper['title'], self.citations[c]['title']))
            if no_citations:
                print("{} does not cite any other papers".format(
                    paper['title']))
            print()

    def view_citation_network_with_tag(self, tag):

        print("Papers tagged with {}".format(tag))
        for ID, paper in self.citations.items():
            paper_has_tag = False
            if paper['publication'].has_tag(tag):
                paper_has_tag = True

            cites_to = []
            citation_has_tag = False
            for c in paper['publication'].cites_to:
                if paper_has_tag:
                    cites_to.append(
                        [self.citations[c]['title'], self.citations[c]['publication'].tags])
                else:
                    if self.citations[c]['publication'].has_tag(tag):
                        citation_has_tag = True
                        cites_to.append(
                            [self.citations[c]['title'], self.citations[c]['publication'].tags])

            # print(paper['title'])
            # print(paper_has_tag)
            if paper_has_tag:
                print("{}\n\thas tags: {}".format(
                    paper['title'], paper['publication'].tags))
            elif citation_has_tag:
                for title, tags in cites_to:
                    print("\t--->{} has tags: {}".format(title, tags))
            if paper_has_tag or citation_has_tag:
                print()

    def view_untagged(self):
        print("Untagged Papers")
        for ID, paper in self.citations.items():
            if not paper['publication'].tags:
                print(paper['title'])

    def view_all_citations(self):
        for paper in self.citations.values():
            print(paper['title'])
            if paper['publication'].tags:
                print("\t{}".format(paper['publication'].tags))

    def add_tags_notes_to_publication(self, title, tags, notes):
        found = False
        for paper in self.citations.values():
            if paper['title'].lower() == title.lower():
                paper['publication'].add_tags(tags)
                paper['publication'].add_notes(notes)
                save_DB(self)
                found = True
                print("Updated {}".format(paper['title']))
        if not found:
            print()
            print("{} NOT FOUND IN DB".format(title))
            print()

    def view_single(self, title):
        for paper in self.citations.values():
            if paper['title'].lower() == title.lower():
                paper['publication'].view()


def save_DB(DB, save_path='citation_DB.pkl'):
    with open(save_path, "wb") as f:
        pkl.dump(DB, f)


def load_DB(load_path='citation_DB.pkl'):
    with open(load_path, "rb") as f:
        DB = pkl.load(f)
    return DB


def view_DB(load_path="citation_DB.pkl"):
    DB = load_DB(load_path)
    DB.view_all_citations()


def view_DB_citation_network(load_path="citation_DB.pkl"):
    DB = load_DB(load_path)
    DB.view_citation_network()


def view_DB_citation_network_with_tag(tag, load_path="citation_DB.pkl"):
    DB = load_DB(load_path)
    DB.view_citation_network_with_tag(tag)


def add_publication_from_GS(query, DB_path="citation_DB.pkl", tags=None, notes=None, read=False):
    DB = load_DB(DB_path)
    refresh_socket()
    pubs = publication_query(query.lower())
    correct_result = False
    while not correct_result:
        # slow_down(10)
        res = pubs.next_result()
        if not res:
            return
        answer = None
        while answer not in ("yes", "no"):
            answer = input("Enter yes or no: ")
            if answer == "yes":
                correct_result = True
        # slow_down(10)

    # slow_down(10)
    pub = publication(res, read=read, notes=notes, tags=tags)
    # slow_down(10)
    DB.add_publication(pub)
    save_DB(DB, save_path=DB_path)
    # slow_down(1200+(len(pub.cited_by)//2))
