import logging
import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
from tqdm import tqdm

from margin_grid_trader.account import MarginAccountSimulator
from margin_grid_trader.trader import LongShortTrader

logging.basicConfig(level=logging.DEBUG,
                    format='%(message)s',
                    handlers=[
                        logging.StreamHandler(),
                        logging.FileHandler(
                            filename='app.log',
                            mode='w')])
# format='%(name)s - %(levelname)s - %(message)s'
# format='%(asctime)s - %(message)s'
# datefmt='%d-%b-%y %H:%M:%S'


def simulate(interval):
    # Constants
    initial_base_currency = 1000
    best_wallet = -9999

    trader_params_df = LongShortTrader.get_random_trader_population(
        n_traders=1, step_lo=0.0035, step_hi=0.01, ratio_lo=0.001, ratio_hi=0.1)
    trader_params_df.at[0, "step"] = 0.02  # TODO for debug
    trader_params_df.at[0, "ratio"] = 0.01  # TODO for debug

    for i in tqdm(range(len(trader_params_df))):
        account = MarginAccountSimulator(initial_base_currency)
        account.update(0, interval[0])

        single_trader_params = trader_params_df.loc[i]
        trader = LongShortTrader(
            acc=account, initial_price=interval[0], step=single_trader_params['step'],
            order_pair_size_ratio=single_trader_params['ratio'])

        for j, price in enumerate(interval[1:]):
            account.update(j + 1, price)
            trader.update(j + 1, price)

        wallet = account.get_investment_value(interval[-1])
        borrow = account.get_borrowed_value(interval[-1])
        trader_params_df.at[i, 'wallet'] = wallet
        trader_params_df.at[i, 'borrow'] = borrow
        trader_params_df.at[i, 'n_trades'] = account.get_trade_count()

        if wallet > best_wallet:
            saved_trader = trader
            saved_account = account
            best_wallet = wallet
            best_borrow = borrow

    print(saved_trader)
    print(f"best_wallet {best_wallet}")
    print(f"best_borrow {best_borrow}")

    grid = saved_trader.grid_manager.get_grid_list()
    plot_results(saved_account, grid)

    plot_histograms(trader_params_df, x='step', y='ratio', n_bins=10)

    return trader_params_df


def plot_histograms(df, x, y, n_bins=10):
    # https://plotly.com/python/2D-Histogram/
    fig = px.density_heatmap(df, x=x, y=y, nbinsx=n_bins, nbinsy=n_bins, text_auto=True)
    fig.show()

    fig = px.density_heatmap(df, x=x, y=y, z="wallet", histfunc="avg", nbinsx=n_bins, nbinsy=n_bins, text_auto=True)
    fig.show()

    fig = px.density_heatmap(df, x=x, y=y, z="borrow", histfunc="avg", nbinsx=n_bins, nbinsy=n_bins, text_auto=True)
    fig.show()

    fig = px.density_heatmap(df, x=x, y=y, z="n_trades", histfunc="avg", nbinsx=n_bins, nbinsy=n_bins, text_auto=True)
    fig.show()


def plot_scatter():
    pass
    # print(self.trader_params)
    # print(self.trader_params.iloc[self.trader_params['wallet'].argmax()])
    # # https://www.statology.org/matplotlib-scatterplot-color-by-value/
    # plt.scatter(self.trader_params.step,
    #             self.trader_params.stop_loss_coef,
    #             s=50,
    #             c=self.trader_params.wallet,
    #             cmap='gray')
    # plt.xlabel("step")
    # plt.ylabel("stop_loss_coef")
    # plt.show()


def plot_results(account: MarginAccountSimulator, grid=None):
    fig, axs = plt.subplots(3)
    if grid is not None:
        axs[0].set_yticks(grid, minor=True)
    axs[0].yaxis.grid(True, which='minor')

    # axs[0].set_xticks(account.market_actions, minor=True) TODO need this
    # axs[0].xaxis.grid(True, which='minor')
    axs[0].xaxis.grid(True, which='both')

    axs[0].plot(account.price_timeline)

    axs[1].plot(account.wallet_timeline)  # , label=trader.label)
    axs[1].xaxis.grid(True, which='both')

    axs[2].plot(account.borrowed_value_timeline)  # , label=trader.label)
    axs[2].xaxis.grid(True, which='both')

    plt.legend()
    plt.show()


def main():
    df = pd.read_csv('../data/BTCUSDT-1m-2021.csv')
    # TODO use high/low values instead close
    ts = df.iloc[:, 4].to_numpy()

    simulate(ts)


if __name__ == '__main__':
    main()
