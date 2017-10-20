from dd_model_helper import *
from dd_helper import *
import time

input_default='/home/lca80/Desktop/data/emtell/sept2017/all_m3_CT_and_DS_reports.csv'

def train_save_model(X, Y, X_test, Y_test, vocab2idx, tag_lst, parameters, window_size, \
		target_names, model_path):

	#create graph
	VOCAB_SIZE = len(vocab2idx)
	NUM_OF_CLASSES = len(tag_lst)
	EMBEDDINGS_SIZE = parameters['embedding_size']
	batch_size = 32

	if parameters['nn'] == 'mlp':
		from MLP import MLP
		STATE_SIZE = EMBEDDINGS_SIZE*window_size

		specs = [VOCAB_SIZE, EMBEDDINGS_SIZE, STATE_SIZE, NUM_OF_CLASSES, 1, 'Adam',\
			model_path]
		model = MLP(specs)

	else:
		from RNN import RNN
		STATE_SIZE = window_size

		#specs = [VOCAB_SIZE, EMBEDDINGS_SIZE, STATE_SIZE, NUM_OF_CLASSES, 1, 'GRU', 'SGD',\
		#	'model/comma_clf.model']
		specs = [VOCAB_SIZE, EMBEDDINGS_SIZE, STATE_SIZE, NUM_OF_CLASSES, 1, 'lstm', 'Adagrad',\
			model_path]  #'RMS']  #
		model = RNN(specs)

	print "train:", len(X), " test:", len(X_test), " batch_size:", batch_size
	print "vocabs:", len(vocab2idx), " tags:", len(tag_lst), " len(feature_vec):",len(X[0])
	print parameters['nn'], specs

	#train a model
	t0 = time.time()
	max_iter = 20
	display_every = 5

	model.train(X, Y, X_test, Y_test, batch_size, max_iter, display_every)
	print "time:", time.time() - t0; t0=time.time()

	[clf, vocab2idx, parameters]=load_model(model_path)
	#predict and get scores
	y_pred = clf.predict(X_test, batch_size)
	print get_scores(Y_test, y_pred, target_names = target_names)


def create_models(dd_lst, model_dir):

	#1) get sentences data from dd_lst
	period_lst, comma_lst, heading_lower_lst = get_sentences_data(dd_lst)

	#2) get features and labels for comma clf
	X, Y, X_test, Y_test, vocab2idx, tag_lst, parameters, window_size, target_names = \
        	get_comma_features_labels(comma_lst, period_lst, 6, 3, char_based=False, nn='mlp')  #True)  #

	#3) save parameters
	with open(model_dir + 'comma_clf_parameters.json', 'w') as fj:
	    json.dump(parameters, fj)
	with open(model_dir + 'comma_clf_vocab2idx.json', 'w') as fj:
	    json.dump(vocab2idx, fj)

	#4) train and save model
	train_save_model(X, Y, X_test, Y_test, vocab2idx, tag_lst, parameters, window_size, \
		target_names, model_dir + 'comma_clf.model')

	#5) get features and labels for linebreak clf
	X, Y, X_test, Y_test, vocab2idx, tag_lst, parameters, window_size, target_names = \
		get_linebreak_features_labels(period_lst, 6, 3, char_based=False, nn='mlp')

	#6) save parameters
	with open(model_dir + 'linebreak_clf_parameters.json', 'w') as fj:
	    json.dump(parameters, fj)
	with open(model_dir + 'linebreak_clf_vocab2idx.json', 'w') as fj:
	    json.dump(vocab2idx, fj)

	#7) train and save model
	train_save_model(X, Y, X_test, Y_test, vocab2idx, tag_lst, parameters, window_size, \
		target_names, model_dir + 'linebreak_clf.model')

	#8) save heading_lst
	heading_str = '\n'.join(heading_lower_lst)
	#print len(heading_lower_lst), heading_str[:160]
	with open('model/heading_lower_lst.txt', 'w') as fd:
	    fd.write(heading_str)

	#9) save sentence_len3_lst
	period_len3_lst = filter(lambda s: len(s.split()) < 4, period_lst)
	period_len3_lst = map(lambda s: s.lower(), period_len3_lst )
	period_len3_lst = list(set(period_len3_lst))
	sentence_len3_str = '\n'.join(period_len3_lst)
	with open('model/sentence_len3_lst.txt', 'w') as fd:
	    fd.write(sentence_len3_str)


if __name__ == '__main__':
	import argparse
	import json
	import os

	argparser = argparse.ArgumentParser()

	argparser.add_argument("-i", "--input_csv", dest="input_csv", default=input_default, \
		help="input report data csv file path (default={})".format(input_default))
	argparser.add_argument("-d", "--input_dd_path", dest="input_dd_path", default="dd_lst.json", \
		help="input discharge diagnoses data json file path (default=dd_lst.json)")
	argparser.add_argument("-m", "--model_dir", dest="output_model_dir", default="model/", \
		help="output models directory (default=model/)")
	args = argparser.parse_args()

	try:
		with open ('dd_lst.json') as fj:
		    dd_lst = json.load(fj)
	except:
		data_path = args.input_csv
		file_name = data_path.split('/')[-1]
		dd_lst, _ = extract_dd_raw(data_path)

	if args.output_model_dir == "model/" and not os.path.isdir("model"):
		os.system("mkdir model")

	create_models(dd_lst, args.output_model_dir)
	print "Done!"
	