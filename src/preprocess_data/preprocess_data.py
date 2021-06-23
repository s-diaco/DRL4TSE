"""preprocess data before using it"""
import logging

import pandas as pd
from stockstats import StockDataFrame as Sdf

from preprocess_data import csv_data, custom_columns


def add_technical_indicator(
    data: pd.DataFrame,
    tech_indicator_list: list
) -> pd.DataFrame:
    """
    calcualte technical indicators
    add technical inidactors using "stockstats" package

    Parameters:
            data (df): pandas dataframe
            tech_indicator_list (list): list of stockstats indicators

    Returns: 
            df (pd.DataFrame): data with indicators
    """
    df = data.copy()
    stock = Sdf.retype(df.copy())
    unique_tickers = stock.tic.unique()

    for indicator in tech_indicator_list:
        indicator_df = pd.DataFrame()
        for unique_ticker in unique_tickers:
            try:
                temp_indicator = stock[stock.tic ==
                                       unique_ticker][indicator]
                temp_indicator = pd.DataFrame(temp_indicator)
                indicator_df = indicator_df.append(
                    temp_indicator, ignore_index=True
                )
            except Exception as e:
                logging.error(e)
        df[indicator] = indicator_df
    return df


def new_column_from_client_func(client_func, data):
    '''
    Create "series" from a given function and dataframe

            Parameters:
                    client_func (callable): function used to create the column
                    data (pd.DataFrame): data used to calculate new columns

            Returns:
                    column (pd.Series): calculated column

            Raises:
                    TypeError: if the column type is not pd.Series
    '''
    # TODO check if there are any Nan or inf values in new column
    column = client_func(data)
    if isinstance(column, pd.Series):
        return column
    else:
        raise TypeError(f'Type of return value for "{str(client_func)}" \
            func should be "pd.Series"')


def add_user_defined_features(data: pd.DataFrame) -> pd.DataFrame:
    '''
    Add data from functions in 'user_calculated_columns.py'.

            Parameters:
                    data (pd.DataFrame): data used to calculate new columns

            Returns:
                    data (pd.DataFrame): the updated dataframe
    '''
    logging.info(f'Adding custom columns')
    for i in dir(custom_columns):
        item = getattr(custom_columns, i)
        if callable(item):
            # add new column to dataframe
            try:
                data[str(item)] = new_column_from_client_func(item, data)
            except:
                logging.info(f'Add column "{str(item)}": unsuccessful!')
    return data


def preprocess_data(tic_list, start_date, end_date,
                    field_mappings, baseline_filed_mappings,
                    csv_file_info, tec_indicators) -> pd.DataFrame:
    """preprocess data before using"""

    # if not os.path.exists("./" + config.DATA_SAVE_DIR):
    #    os.makedirs("./" + config.DATA_SAVE_DIR)
    # if not os.path.exists("./" + config.TRAINED_MODEL_DIR):
    #    os.makedirs("./" + config.TRAINED_MODEL_DIR)
    # if not os.path.exists("./" + config.TENSORBOARD_LOG_DIR):
    #    os.makedirs("./" + config.TENSORBOARD_LOG_DIR)
    # if not os.path.exists("./" + config.RESULTS_DIR):
    #    os.makedirs("./" + config.RESULTS_DIR)

    # from config.py start_date is a string
    logging.info(f'Train start date: {start_date}')
    # from config.py end_date is a string
    logging.info(f'Train end date: {end_date}')
    logging.info(f'Tickers: {tic_list}')
    data_loader = csv_data.CSVData(
        start_date=start_date,
        end_date=end_date,
        ticker_list=tic_list,
        csv_dirs=csv_file_info["dir_list"],
        baseline_file_name=csv_file_info["baseline_file_name"],
        has_daily_trading_limit=csv_file_info["has_daily_trading_limit"],
        use_baseline_data=csv_file_info["use_baseline_data"],
        baseline_filed_mappings=baseline_filed_mappings,
        baseline_date_column_name=csv_file_info["baseline_date_column_name"]
        )
    raw_df = data_loader.fetch_data(
        field_mappings = field_mappings,
        date_column=csv_file_info["date_column_name"])

    # Preprocess Data
    processed_data = add_technical_indicator(
        data=raw_df,
        tech_indicator_list=tec_indicators
    )

    processed_data = add_user_defined_features(
        processed_data
    )

    logging.info(f'Preprocessed data (tail): \n {processed_data.tail()}')
    logging.info(f'Sample size: {len(processed_data)}')
    logging.info(f'Training column names: {processed_data.columns}')

    return processed_data