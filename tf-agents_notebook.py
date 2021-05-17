# %% [markdown]
#### todo:
# - fix parallel envoriments
# - use correct policy batch size for ppo
# - use greedy policy to test (what is "eager mode"?)
# - organize folders created by modules
# - use original network numbers
# - replace print with logging in py_env
# - change num_parallel_environments
# %% [markdown]
## import modules
import logging
import tensorflow as tf
from IPython import get_ipython

import backtest_tse.backtesting_tse as backtest
from config import config
from env_tse.py_env_trading import TradingPyEnv
from model.models import TradeDRLAgent
from preprocess_tse_data import preprocess_data

logging.basicConfig(format="%(message)s", level=logging.INFO)

# %% [markdown]
## Preprocess data
df_train, df_trade = preprocess_data()

# %% [markdown]
## Create the envoriments
information_cols = ["daily_variance", "change", "log_volume"]

logging.info(f'TensorFlow version: {tf.version.VERSION}')
logging.info(f"List of available [GPU] devices:\n{tf.config.list_physical_devices('GPU')}")


class TrainEvalPyEnv(TradingPyEnv):
    def __init__(self):
        super().__init__(
            df=df_train,
            daily_information_cols=information_cols,
            patient=True,
            random_start=False,
            cache_indicator_data=False #todo: delete if needed,
            )


class TestPyEnv(TradingPyEnv):
    def __init__(self):
        super().__init__(
            df=df_trade,
            daily_information_cols=information_cols,
            cache_indicator_data=False,
            discrete_actions=True,
            shares_increment=10,
            patient=True,
            random_start=False,)

# %% todo: delete - test the envirement
# environment = TestPyEnv()
# utils.validate_py_environment(environment, episodes=2)

# %% [markdown]
## Agent
tf_agent = TradeDRLAgent().get_agent(
    py_env=TrainEvalPyEnv,
)

# %% [markdown]
## Train
# tf_agents.system.multiprocessing.enable_interactive_mode()

# %%
TradeDRLAgent().train_PPO(
    root_dir="./" + config.TRAINED_MODEL_DIR,
    py_env=TrainEvalPyEnv,
    tf_agent=tf_agent,
    collect_episodes_per_iteration=1,
    policy_checkpoint_interval=500000,
    num_iterations = 30,
    use_tf_functions=False
    )

# %% [markdown]
## Predict
df_account_value, df_actions = TradeDRLAgent().predict_trades(py_test_env=TestPyEnv)

# %% [markdown]
## Trade info
logging.info(f"Model actions:\n{df_actions.head()}")
logging.info(f"Account value data shape: {df_account_value.shape}:\n{df_account_value.head(10)}")

# %% [markdown]
## Backtest stats & plots
backtest.backtest_tse_trades(df_account_value, "^TSEI", config.START_TRADE_DATE, config.END_DATE)
# %%