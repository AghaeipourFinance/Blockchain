# Original block reward for miners was 50 BTC
start_block_reward = 50
# 210000 is around every 4 years with a 10 minute block interval
reward_interval = 210_000

def max_money():
    # 50 BTC = 5 000 000 000 Satoshis
    current_reward = 50 
    total = 0
    while current_reward > 0:
        total += reward_interval * current_reward
        current_reward /= 2
    return total


print("Total BTC to ever be created:", max_money(), "Satoshis")