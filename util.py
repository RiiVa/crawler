import json
import string
import re
from nltk.tokenize import word_tokenize
import random
import numpy as np


vocabulary = set([])
doc_names = set([])
tuples = []

def read(jsonName):
    #cargar
    file = open(jsonName, 'rt')
    data = json.load(file)
    for item in data['item']:
        #tokenizar
        tokens = word_tokenize(item['content'])
        #minuscula
        tokens = [t.lower() for t in tokens]
        words = [w for w in tokens if w.isalpha()]
        document_voc = set([])

        for w in words:
            vocabulary.add(w)
            document_voc.add(w)

        doc_names.add(item['url'])
        tuples.append((item['url'], document_voc))



def create_term_document_matrix(line_tuples, document_names, vocab):
	vocab_to_id = dict(zip(vocab, range(0, len(vocab))))
	docname_to_id = dict(zip(document_names, range(0, len(vocab))))
	matrix = np.zeros([len(vocab), len(document_names)])

	for document, tokens in line_tuples:
		column_id = docname_to_id.get(document, None)
		if column_id is None:
			continue
		for word in tokens:
			row_id = vocab_to_id.get(word, None)
			if row_id is None:
				continue
				matrix[row_id, column_id] += 1
	return matrix
  # END SOLUTION


def compute_cosine_similarity(vector1, vector2):
	num = np.dot(vector1, vector2)
	den1 = np.sqrt((vector1**2).sum())
	den2 = np.sqrt((vector2**2).sum())
	return num / (den1 * den2)

def rank_plays(target_play_index, term_document_matrix, similarity_fn):
	m, n = term_document_matrix.shape
	sims = np.zeros(n)
	v_tgt = get_column_vector(term_document_matrix, target_play_index)
	for i in range(n):
		v_doc = get_column_vector(term_document_matrix, i)
		sims[i] = similarity_fn(v_tgt, v_doc)
	sims_sort = np.argsort(-sims)
	return sims_sort

def get_row_vector(matrix,idx):
	return matrix[idx,:]

def get_column_vector(matrix,idx):
	return matrix[:,idx]

read('items.json')
print('Computing term document matrix...')
td_matrix = create_term_document_matrix(tuples, doc_names, vocabulary)

random_idx = random.randint(0, len(doc_names)-1)
ranks = rank_plays(random_idx, td_matrix, compute_cosine_similarity)
for idx in range(0, 1000):
	name = ranks[idx]
	print('%d: %s' % (idx+1, doc_names[name]))