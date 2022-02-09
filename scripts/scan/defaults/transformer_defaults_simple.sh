#!/usr/bin/env bash

python main.py \
--dataset scan \
--split simple \
--num_runs 1 \
--batch_size 256 \
--num_epochs 150 \
--model_type transformer \
--d_model 256 \
--nhead 8 \
--n_layers 2 \
--dim_feedforward 512 \
--dropout 0.1 \
--learning_rate 0.001 \
--results_dir transformer \
--out_data_file train_defaults_simple \
--out_attn_wts train_defaults_simple_attn_maps \
--checkpoint_path ../weights/transformer/scan/defaults_simple.pt \
--checkpoint_every 4 \
--record_loss_every 20