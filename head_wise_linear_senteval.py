import sys
from copy import deepcopy
import os
import argparse
import sklearn


import torch
import numpy as np
from tqdm import tqdm


PATH_BERT = '../pytorch-pretrained-BERT'
sys.path.insert(0, PATH_BERT)


PATH_SENTEVAL = './SentEval'
PATH_TO_DATA = './SentEval/data/'
sys.path.insert(0, PATH_SENTEVAL)
import senteval

from transformer_anatomy.encoder import BERTEncoder, GPTEncoder, GPT2Encoder, TransfoXLEncoder
from transformer_anatomy.single_head_exp import *


if __name__ == '__main__':

    # ====== Generate Embedding of Large Model ====== #
    parser = argparse.ArgumentParser(description='Evaluate BERT')
    parser.add_argument("--device", type=list, default=[0,1,2,3,4,5,6,7])
    parser.add_argument("--batch_size", type=int, default=5000)
    parser.add_argument("--kfold", type=int, default=5)
    parser.add_argument("--usepytorch", type=bool, default=True)
    parser.add_argument("--task_path", type=str, default='./SentEval/data/')
    parser.add_argument("--cache_path", type=str, default='.cache')
    parser.add_argument("--result_path", type=str, default='results/test_probing_head_wise')
    parser.add_argument("--optim", type=str, default='rmsprop')
    parser.add_argument("--cbatch_size", type=int, default=256)
    parser.add_argument("--tenacity", type=int, default=3)
    parser.add_argument("--epoch_size", type=int, default=2)
    parser.add_argument("--model_name", type=str, default='bert-base-uncased') #

    parser.add_argument("--task", type=int, default=0)
    parser.add_argument("--layer", nargs='+', type=int, default=[0, 1])
    parser.add_argument("--head", nargs='+', type=int, default=[0, 1]) #8, 15
    parser.add_argument("--location", type=str, default='head') #8, 15
    parser.add_argument("--head_size", type=int, default=64)
    parser.add_argument("--dropout", type=float, default=0)
    parser.add_argument("--nhid", type=int, default=0)

    args = parser.parse_args()
    args.seed = 123
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    os.environ["CUDA_VISIBLE_DEVICES"] = ','.join(str(x) for x in args.device)

    list_layer = range(args.layer[0], args.layer[1] + 1) if len(args.layer) > 1 else [args.layer[0]]
    list_head = range(args.head[0], args.head[1] + 1) if len(args.head) > 1 else [args.head[0]]
    num_exp = len(list(list_layer)) * len(list_head)

    print("======= Benchmark Configuration ======")
    print("Args: ", args)
    print("Device: ", args.device)
    print("model name: ", args.model_name)
    print("Task: ", tasks[args.task])
    print("location: ", args.location)
    print("Total Exps: ", num_exp)
    print("======================================")

    cnt = 0
    args.task = tasks[args.task]
    if args.model_name in ['bert-base-uncased', 'bert-large-uncased'] :
        model = BERTEncoder(model_name=args.model_name, encode_capacity=args.batch_size)
    elif args.model_name == 'openai-gpt':
        model = GPTEncoder(encode_capacity=args.batch_size)
    elif args.model_name == 'gpt2':
        model = GPT2Encoder(encode_capacity=args.batch_size)
    elif args.model_name == 'transfo-xl-wt103':
        model = TransfoXLEncoder(encode_capacity=args.batch_size)
    else:
        raise ValueError

    with tqdm(total=num_exp, file=sys.stdout) as pbar:
        for layer in list_layer:
            for head in list_head:

                print('\n---------')
                print("L: {}. H: {}.".format(layer, head))
                args.head = head
                args.layer = layer

                exp_result = experiment(model, args.task, deepcopy(args))

                pbar.set_description('P: %d' % (1 + cnt))
                pbar.update(1)
                cnt += 1

                print("** Saving Best Result of Acc: {}.".format(exp_result['acc']))
                save_exp_result(exp_result, args.task)

