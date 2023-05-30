import os
import re

import pandas as pd

from S5.Weather import to_csv, to_parquet


def test_to_parquet(caplog, tmp_path):
    df = pd.DataFrame([400, 500, 600], columns=['Col'])

    to_parquet("Name", df, tmp_path)
    folder_content = os.listdir(tmp_path)

    empty_df = pd.DataFrame()
    to_parquet("Name2", empty_df, tmp_path)

    # Check if there is only one file made
    assert len(folder_content) == 1

    # Check the filename is in the right format
    assert re.fullmatch("Forecast[0-9]{12}Name.parquet", folder_content[0])

    # Check the warning was logged
    assert "Dataframe is empty, skip exporting to parquet." in caplog.text


def test_to_csv(caplog, tmp_path):
    df = pd.DataFrame([400, 500, 600], columns=['Col'])

    to_csv("Name", df, tmp_path)
    folder_content = os.listdir(tmp_path)

    empty_df = pd.DataFrame()
    to_csv("Name2", empty_df, tmp_path)

    # Check if there is only one file made
    assert len(folder_content) == 1

    # Check the filename is in the right format
    assert re.fullmatch(r"Forecast[0-9]{12}Name.csv", folder_content[0])

    # Check the warning was logged
    assert "Dataframe is empty, skip exporting to csv." in caplog.text
