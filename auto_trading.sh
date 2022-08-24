#!/bin/bash

conda activate marketwatch

cd /Users/yueyuchen/Documents/Academy/Research/MarketWatch

/Users/yueyuchen/opt/anaconda3/envs/marketwatch/bin/python /Users/yueyuchen/Documents/Academy/Research/MarketWatch/update_data.py

conda activate PaperTrading

cd /Users/yueyuchen/Documents/Academy/Research/PaperTrading

/Users/yueyuchen/opt/anaconda3/envs/PaperTrading/bin/python /Users/yueyuchen/Documents/Academy/Research/PaperTrading/main.py