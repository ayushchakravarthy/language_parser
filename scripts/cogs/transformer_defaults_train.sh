#!/usr/bin/env bash
#SBATCH -p localLimited
#SBATCH -A ucdavis
#SBATCH --mem=1G
#SBATCH --time=100:00:00
#SBATCH --gres=gpu:1
#SBATCH -c 2
#SBATCH --output=logs/cogs/transformer_def_train.txt

export HOME=`getent passwd $USER | cut -d':' -f6`
export PYTHONUNBUFFERED=1
echo Running on $HOSTNAME

source /home/akchak/.bashrc
source /home/akchak/.bashrc
conda activate lp


python main.py \
--dataset cogs
--split train \
--num_runs 1 \
--batch_size 32 \
--num_epochs 100 \
--model_type transformer \
--d_model 12 \
--nhead 2 \
--num_encoder_layers 2 \
--num_decoder_layers 2 \
--dim_feedforward 20 \
--dropout 0.1 \
--learning_rate 0.001 \
--results_dir transformer \
--out_data_file train_defaults \
--out_attn_wts train_defaults_attn_maps \
--checkpoint_path weights/transformer/cogs/defaults_train.pt \
--checkpoint_every 1 \
--record_loss_every 10
