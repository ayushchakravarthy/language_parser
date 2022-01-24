#!/usr/bin/env bash

python main.py \
--pos \
--dataset scan \
--split mcd2 \
--num_runs 5 \
--batch_size 256 \
--num_epochs 250 \
--model_type sep-transformer \
--d_model 256 \
--nhead 8 \
--n_layers 2 \
--dim_feedforward 512 \
--dropout 0.1 \
--learning_rate 0.0001 \
--results_dir sep-transformer \
--out_data_file train_sep_enc_mcd2 \
--out_attn_wts train_sep_enc_mcd2_attn_maps \
--checkpoint_path ../weights/sep-transformer/scan/defaults_sep_enc_mcd2.pt \
--checkpoint_every 4 \
--record_loss_every 20