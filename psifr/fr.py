"""Utilities for working with free recall data."""

import pandas as pd


def check_data(df):
    """Run checks on free recall data.

    Parameters
    ----------
    df : pandas.DataFrame
        Contains one row for each trial (study and recall). Must have fields:
            subject : number or str
                Subject identifier.
            list : number
                List identifier. This applies to both study and recall trials.
            trial_type : str
                Type of trial; may be 'study' or 'recall'.
            position : number
                Position within the study list or recall sequence.
            item : str
                Item that was either presented or recalled on this trial.
    """

    # check that all fields are accounted for
    columns = ['subject', 'list', 'trial_type', 'position', 'item']
    for col in columns:
        assert col in df.columns, f'Required column {col} is missing.'

    # only one column has a hard constraint on its exact content
    assert df['trial_type'].isin(['study', 'recall']).all(), (
        'trial_type for all trials must be "study" or "recall".')


def merge_lists(study, recall, merge_keys=None, list_keys=None, position_key='position'):
    """Merge study and recall events together for each list.

    Parameters
    ----------
    study : pandas.DataFrame
        Information about all study events. Should have one row for
        each study event.

    recall : pandas.DataFrame
        Information about all recall events. Should have one row for
        each recall attempt.

    merge_keys : list, optional
        Columns to use to designate events to merge. Default is
        ['subject', 'list', 'item'], which will merge events related to
        the same item, but only within list.

    list_keys : list, optional
        Columns that apply to an entire list, as opposed to specific
        study events. These columns will still be defined for
        intrusions even though they have no corresponding study event.

    position_key : str, optional
        Column indicating the position of each item in either the study
        list or the recall sequence.

    Returns
    -------
    merged : pandas.DataFrame
        Merged information about study and recall events. Each row
        corresponds to one unique input/output pair.

        The following columns will be added:
        input : int
            Position of each item in the input list (i.e., serial
            position).
        output : int
            Position of each item in the recall sequence.
        recalled : bool
            True for rows with an associated recall event.
        repeat : int
            Number of times this recall event has been repeated (0 for
            the first recall of an item).
        intrusion : bool
            True for recalls that do not correspond to any study event.
    """

    if merge_keys is None:
        merge_keys = ['subject', 'list', 'item']

    # get running count of number of times each item is recalled in each list
    recall.loc[:, 'repeat'] = recall.groupby(merge_keys).cumcount()

    # set keys to define the level of recall at items within list
    if list_keys is not None:
        merge_keys += list_keys

    # get just the fields to use in the merge
    recall = recall[merge_keys + ['position', 'repeat']]

    # merge information from study and recall trials
    merged = pd.merge(study, recall, left_on=merge_keys, right_on=merge_keys,
                      how='outer')

    # position from study events indicates input position;
    # position from recall events indicates output position
    merged = merged.rename(columns={position_key + '_x': 'input',
                                    position_key + '_y': 'output'})

    # field to indicate whether a given item was recalled
    merged.loc[:, 'recalled'] = merged['output'].notna().astype('bool')

    # field to indicate whether a given recall was an intrusion
    merged.loc[:, 'intrusion'] = merged['input'].isna().astype('bool')

    # fix repeats field to define for non-recalled items
    merged.loc[merged['repeat'].isna(), 'repeat'] = 0
    merged = merged.astype({'repeat': 'int'})
    return merged