#!/usr/bin/env python3

import sys
import scholarly
import time
from tqdm import tqdm
import pickle as pkl

proxies = {'http': 'socks5://127.0.0.1:9050',
           'https': 'socks5://127.0.0.1:9050'}
scholarly.scholarly.use_proxy(**proxies)


# RL - reinforcement learning
# CF - catastrophic forgetting
# STS - semantic textual similarity
# NLI - natural language inference (same as recognizing textual entailment)
# MC - machine comphrehension
# MT - machine translation

all_tags = ["ML", "RL", "CF", "transfer learning",
            "multi-task", "continual learning",
            "logic", "transformer", "multi agent",
            "game theory", "regret minimization",
            "relational reasoning", "QA", "inductive learning", "symbolic",
            "CV", "image captioning", "NLP", "ASR", "SLU",
            "sentence pair modeling", "STS", "paraphrase identification",
            "NLI", "MC", "interpretability", "explainability", "MT", "IR", "XAI"]


def slow_down(i):
    for i in range(i, 0, -1):
        sys.stdout.write("\r")
        sys.stdout.write("{:2d} seconds remaining.".format(i))
        sys.stdout.flush()
        time.sleep(1)


class publication_query(object):
    def __init__(self, query):
        slow_down(10)
        self.search_result = scholarly.search_pubs_query(query)
        slow_down(10)

    def next_result(self):
        slow_down(10)
        result = next(self.search_result).fill()
        print(result)
        slow_down(10)
        return result


class publication(object):
    def __init__(self, pub, read=False):
        self.bib = pub.bib
        self.cited_by = []
        self.cites_to = []
        self.tags = []
        try:
            self.ID = pub.id_scholarcitedby
        except:
            self.ID = pub.url_scholarbib
        self.notes = []
        self.read = read
        citedby = pub.get_citedby()
        # for c in tqdm(citedby, total=pub.citedby):
        #     time.sleep(30)
        #     self.cited_by.append(c['id_scholarcitedby'])
        #     time.sleep(30)
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

    def view_all_citations(self):
        for paper in self.citations.values():
            print(paper['title'])

    # def view_single(self, title):
    #     found = False
    #     for paper in self.citations.values():
    #         if


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


def add_publication_from_GS(query, DB_path="citation_DB.pkl", tags=None, notes=None, read=False):
    DB = load_DB(DB_path)

    pubs = publication_query(query.lower())
    correct_result = False
    while not correct_result:
        slow_down(10)
        res = pubs.next_result()
        answer = None
        while answer not in ("yes", "no"):
            answer = input("Enter yes or no: ")
            if answer == "yes":
                correct_result = True
        slow_down(10)

    slow_down(10)
    pub = publication(res, read=read)
    slow_down(10)
    DB.add_publication(pub)
    save_DB(DB, save_path=DB_path)
    slow_down(1800)
