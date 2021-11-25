# Training script

import os
import json
import pickle

import torch
import torch.nn as nn
import torch.optim as optim

from data import build_cogs, build_scan
from models.models import *
from test import test


def train(run, args):
    # CUDA 
    use_cuda = torch.cuda.is_available()
    device = torch.device("cuda:0" if use_cuda else "cpu")

    # Data 
    if args.dataset == 'scan':
        SRC, TRG, train_data, dev_data, test_data = build_scan(
            args.split,
            args.batch_size,
            device=device
        )
    elif args.dataset == 'cogs':
        SRC, TRG, train_data, train_100_data, dev_data, test_data, gen_data =  build_cogs(
            args.batch_size,
            device=device
        )
    # vocab
    src_vocab_size = len(SRC.vocab.stoi)
    trg_vocab_size = len(TRG.vocab.stoi)
    pad_idx = SRC.vocab[SRC.pad_token]
    assert TRG.vocab[TRG.pad_token] == pad_idx


    # Model
    if args.model_type == "language_parser":
        model = LanguageParser(
            src_vocab_size,
            trg_vocab_size,
            args.d_model,
            args.nhead,
            args.ffn_exp,
            args.num_parts,
            args.num_decoder_layers,
            args.dim_feedforward,
            args.dropout,
            pad_idx,
            device
        )
    elif args.model_type == "transformer":
        model = Transformer(
            src_vocab_size,
            trg_vocab_size,
            args.d_model,
            args.nhead,
            args.num_encoder_layers,
            args.num_decoder_layers,
            args.dim_feedforward,
            args.dropout,
            pad_idx,
            device
        )
    elif args.model_type == "transformer_default":
        model = TransformerDefault(
            args.num_encoder_layers,
            args.num_decoder_layers,
            args.d_model,
            args.nhead,
            src_vocab_size,
            trg_vocab_size,
            pad_idx,
            device,
        )
    print(f"Model size: {sum(p.numel() for p in model.parameters())}")
    if args.load_weights_from is not None:
        model.load_state_dict(torch.load(args.load_weights_from))
    if run == 0:
        print(model)
    model = model.to(device)
    model.train()

    # Loss Function
    loss_fn = nn.CrossEntropyLoss(ignore_index=pad_idx)
    loss_fn = loss_fn.to(device)

    # Optimizer
    params = model.parameters()
    optimizer = optim.Adam(params, lr=args.learning_rate)

    # Setup things to record
    loss_data = []
    train_accs = []
    dev_accs = []
    test_accs = []
    if args.dataset == 'cogs':
        gen_accs = []
    best_dev_acc = float('-inf')

    # Training Loop
    for epoch in range(args.num_epochs):
        if args.dataset == 'cogs':
            if args.split == 'train':
                for iter, batch in enumerate(train_data):
                    optimizer.zero_grad()
                    if args.model_type != "transformer_default":
                        out, attn_wts = model(batch.src, batch.trg)
                    else:
                        out = model(batch.src, batch.trg)
                    loss = loss_fn(out.view(-1, trg_vocab_size), batch.trg.view(-1))
                    loss.backward()
                    optimizer.step()
                    # Record Loss
                    if iter % args.record_loss_every == 0:
                        loss_datapoint = loss.data.item()
                        print(
                            'Run:', run,
                            'Epochs: ', epoch,
                            'Iter: ', iter,
                            'Loss: ', loss_datapoint
                        )
                        loss_data.append(loss_datapoint)

                # Checkpoint
                if epoch % args.checkpoint_every == 0:
                    # Checkpoint on train data
                    print("Checking training accuracy...")
                    train_acc = test(train_data, model, pad_idx, device, args)
                    print("Training accuracy is ", train_acc)
                    train_accs.append(train_acc)

                    # Checkpoint on development data
                    print("Checking development accuracy...")
                    dev_acc = test(dev_data, model, pad_idx, device, args)
                    print("Development accuracy is ", dev_acc)
                    dev_accs.append(dev_acc)

                    # Checkpoint on test data
                    print("Checking test accuracy...")
                    test_acc = test(test_data, model, pad_idx, device, args)
                    print("Test accuracy is ", test_acc)
                    test_accs.append(test_acc)

                    print('Checking generalization accuracy...')
                    gen_acc = test(gen_data, model, pad_idx, device, args)
                    print("Generalization accuracy is ", gen_acc)
                    gen_accs.append(gen_acc)

                # Write stats file
                results_path = 'results/%s/%s/%s' % (args.results_dir, args.dataset, args.split)
                if not os.path.isdir(results_path):
                    os.mkdir(results_path)
                stats = {'loss_data':loss_data,
                         'train_accs':train_accs,
                         'dev_accs':dev_accs,
                         'test_accs':test_accs}
                results_fn = '%s/%s%d.json' % (results_path,args.out_data_file,run)
                attn_file = '%s/%s%d.pickle' % (results_path, args.out_attn_wts, run)
                with open(results_fn, 'w') as f:
                    json.dump(stats, f)
        
                # Write attn weights to pickle file

                if args.model_type != "transformer_default":
                    with open(attn_file, 'wb') as f:
                        pickle.dump(attn_wts, f)

                # Save model weights
                if run == 0: #first run only
                    if dev_acc > best_dev_acc: # use dev to decide to save
                        best_dev_acc = dev_acc
                        if args.checkpoint_path is not None:
                            torch.save(model.state_dict(),
                                       args.checkpoint_path)
            elif args.split == 'train-100':
                for iter, batch in enumerate(train_100_data):
                    optimizer.zero_grad()
                    if args.model_type != "transformer_default":
                        out, attn_wts = model(batch.src, batch.trg)
                    else:
                        out = model(batch.src, batch.trg)
                    loss = loss_fn(out.view(-1, trg_vocab_size), batch.trg.view(-1))
                    loss.backward()
                    optimizer.step()
                    # Record Loss
                    if iter % args.record_loss_every == 0:
                        loss_datapoint = loss.data.item()
                        print(
                            'Run:', run,
                            'Epochs: ', epoch,
                            'Iter: ', iter,
                            'Loss: ', loss_datapoint
                        )
                        loss_data.append(loss_datapoint)

                # Checkpoint
                if epoch % args.checkpoint_every == 0:
                    # Checkpoint on train data
                    print("Checking training accuracy...")
                    train_acc = test(train_data, model, pad_idx, device, args)
                    print("Training accuracy is ", train_acc)
                    train_accs.append(train_acc)

                    # Checkpoint on development data
                    print("Checking development accuracy...")
                    dev_acc = test(dev_data, model, pad_idx, device, args)
                    print("Development accuracy is ", dev_acc)
                    dev_accs.append(dev_acc)

                    # Checkpoint on test data
                    print("Checking test accuracy...")
                    test_acc = test(test_data, model, pad_idx, device, args)
                    print("Test accuracy is ", test_acc)
                    test_accs.append(test_acc)

                    print('Checking generalization accuracy...')
                    gen_acc = test(gen_data, model, pad_idx, device, args)
                    print("Generalization accuracy is ", gen_acc)
                    gen_accs.append(gen_acc)


                # Write stats file
                results_path = 'results/%s/%s/%s' % (args.results_dir, args.dataset, args.split)
                if not os.path.isdir(results_path):
                    os.mkdir(results_path)
                stats = {'loss_data':loss_data,
                         'train_accs':train_accs,
                         'dev_accs':dev_accs,
                         'test_accs':test_accs}
                results_fn = '%s/%s%d.json' % (results_path,args.out_data_file,run)
                attn_file = '%s/%s%d.pickle' % (results_path, args.out_attn_wts, run)
                with open(results_fn, 'w') as f:
                    json.dump(stats, f)
        
                # Write attn weights to pickle file

                if args.model_type != "transformer_default":
                    with open(attn_file, 'wb') as f:
                        pickle.dump(attn_wts, f)

                # Save model weights
                if run == 0: #first run only
                    if dev_acc > best_dev_acc: # use dev to decide to save
                        best_dev_acc = dev_acc
                        if args.checkpoint_path is not None:
                            torch.save(model.state_dict(),
                                       args.checkpoint_path)
        elif args.dataset == 'scan':
            for iter, batch in enumerate(train_data):
                optimizer.zero_grad()
                if args.model_type != "transformer_default":
                    out, attn_wts = model(batch.src, batch.trg)
                else:
                    out = model(batch.src, batch.trg)
                loss = loss_fn(out.view(-1, trg_vocab_size), batch.trg.view(-1))
                loss.backward()
                optimizer.step()
                # Record Loss
                if iter % args.record_loss_every == 0:
                    loss_datapoint = loss.data.item()
                    print(
                        'Run:', run,
                        'Epochs: ', epoch,
                        'Iter: ', iter,
                        'Loss: ', loss_datapoint
                    )
                    loss_data.append(loss_datapoint)

            # Checkpoint
            if epoch % args.checkpoint_every == 0:
                # Checkpoint on train data
                print("Checking training accuracy...")
                train_acc = test(train_data, model, pad_idx, device, args)
                print("Training accuracy is ", train_acc)
                train_accs.append(train_acc)

                # Checkpoint on development data
                print("Checking development accuracy...")
                dev_acc = test(dev_data, model, pad_idx, device, args)
                print("Development accuracy is ", dev_acc)
                dev_accs.append(dev_acc)

                # Checkpoint on test data
                print("Checking test accuracy...")
                test_acc = test(test_data, model, pad_idx, device, args)
                print("Test accuracy is ", test_acc)
                test_accs.append(test_acc)

            # Write stats file
            results_path = 'results/%s/%s/%s' % (args.results_dir, args.dataset, args.split)
            if not os.path.isdir(results_path):
                os.mkdir(results_path)
            stats = {'loss_data':loss_data,
                     'train_accs':train_accs,
                     'dev_accs':dev_accs,
                     'test_accs':test_accs}
            results_fn = '%s/%s%d.json' % (results_path,args.out_data_file,run)
            attn_file = '%s/%s%d.pickle' % (results_path, args.out_attn_wts, run)
            with open(results_fn, 'w') as f:
                json.dump(stats, f)
        
            # Write attn weights to pickle file

            if args.model_type != "transformer_default":
                with open(attn_file, 'wb') as f:
                    pickle.dump(attn_wts, f)

            # Save model weights
            if run == 0: #first run only
                if dev_acc > best_dev_acc: # use dev to decide to save
                    best_dev_acc = dev_acc
                    if args.checkpoint_path is not None:
                        torch.save(model.state_dict(),
                                   args.checkpoint_path)
        else:
            assert args.dataset not in ['scan', 'cogs'], "Unknown split"