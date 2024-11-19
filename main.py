import pandas as pd
import numpy as np
import random
import matplotlib.pyplot as plt
import argparse
from textwrap import dedent
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
import os.path
import warnings

# silence future warnings
warnings.simplefilter(action='ignore', category=FutureWarning)


# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']


# global setting holder
global_settings = {
    'service': None,
    'SPREADSHEET_ID': None,
    'section_name': None,
    'df_students': None,
    'df_pairs': None,
    'df_protected': None,
    'round_num': None,
    'mode': None,
    'game_settings': None,
    'game_abbrev': None,
    'residual_student': None,
    'id_to_name': None,
    'today': pd.Timestamp.now().strftime('%Y-%m-%d'),
    'extra_price_plot_lines': {}
}


def col_num_to_letters(n):
    """Convert a positive integer to its corresponding column letter."""
    string = ""
    while n > 0:
        n, remainder = divmod(n - 1, 26)
        string = chr(65 + remainder) + string
    return string

def clean_input(input_str):
    """Input command with cleaning"""
    instr = input(input_str)
    return ''.join([c for c in instr if c.isalnum()]).strip().lower()


def convert_to_serializable(obj):
    """
    Recursively convert NumPy data types to native Python types.
    """
    if isinstance(obj, np.ndarray):
        return [convert_to_serializable(o) for o in obj]
    elif isinstance(obj, (list, tuple)):
        return [convert_to_serializable(o) for o in obj]
    elif isinstance(obj, dict):
        return {k: convert_to_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif pd.isnull(obj):
        return ''
    else:
        return obj

def demand_and_profits(p1, p2):
    # Demand functions
    mode = global_settings['mode']
    total_demand = 100
    cost = global_settings['game_settings']['c']
    s1_market_share, s2_market_share = 0, 0
    if mode == 'bertrand':
        # Market share depends inversely on price
        slope = global_settings['game_settings']['alpha']
        # winner takes all
        if p1 < p2:
            s1_market_share = np.clip(1 - slope * p1 / total_demand, 0, 1.0)
            s2_market_share = 0
        elif p1 > p2:
            s1_market_share = 0
            s2_market_share = np.clip(1 - slope * p2 / total_demand, 0.0, 1.0)
        else:
            s1_market_share = s2_market_share = np.clip((1 - slope * p1 / total_demand) / (2.0), 0.0, 0.5)
    elif mode == 'hotelling':
        # low transport hotelling. NE c+t, monopoly = v/2
        t = global_settings['game_settings']['t']
        v = global_settings['game_settings']['v']
        # u1(xM) = u2(xM)
        xM = (-p1 + p2 + 100 * t) / (2 * t)
        # u1(xA0) = 0
        xA0 = (v - p1) / t
        # u2(xB0) = 0
        xB0 = 100 - (v - p2) / t
        
        if xA0 < xB0:
            s1_market_share = np.clip(xA0 / 100, 0.0, 1.0)
            s2_market_share = np.clip((100 - xB0) / 100, 0.0, 1.0)
        else:
            s1_market_share = np.clip(xM, 0, 100) / 100
            s2_market_share = 1.0 - s1_market_share    
        
    else:
        raise ValueError("Invalid mode.")

    # Profits
    s1_profit = s1_market_share * (p1 - cost) * total_demand
    s2_profit = s2_market_share * (p2 - cost) * total_demand
    
    # Return profits rounded to 1 decimal
    s1_profit = round(s1_profit, 1)
    s2_profit = round(s2_profit, 1)
    # and shares in percentage
    s1_market_share = f"{s1_market_share:.1%}"
    s2_market_share = f"{s2_market_share:.1%}"

    return (s1_market_share, s1_profit), (s2_market_share, s2_profit)

def register_section(section_name, section_sheet_id):
    """Register a section with the given name and sheet ID."""
    # load the settings
    if os.path.exists('settings.pickle'):
        with open('settings.pickle', 'rb') as settings_file:
            settings = pickle.load(settings_file)
    else:
        settings = {}
        
    # Register the section
    settings[section_name] = section_sheet_id
    # Save the settings
    with open('settings.pickle', 'wb') as settings_file:
        pickle.dump(settings, settings_file)
    print(f"Section {section_name} registered with sheet ID {section_sheet_id}.")
    return

def load_section_settings():
    """Load the section settings."""
    if os.path.exists('settings.pickle'):
        with open('settings.pickle', 'rb') as settings_file:
            settings = pickle.load(settings_file)
    else:
        settings = {}
    return settings

def prompt_for_section(settings):
    """Prompt the user to select a section."""
    print("Select a section:")
    for i, section_name in enumerate(settings.keys()):
        print(f"{i + 1}. {section_name}")
    while True:
        section_index = input("Enter the section number: ")
        try:
            section_index = int(section_index)
            if section_index < 1 or section_index > len(settings):
                raise ValueError
            break
        except ValueError:
            print("Invalid section number. Please enter a valid section number.")
    section_index -= 1
    section_name = list(settings.keys())[section_index]
    section_sheet_id = settings[section_name]
    global_settings['section_name'] = section_name
    global_settings['SPREADSHEET_ID'] = section_sheet_id
    return 

def load_students():
    """Load the student data from the Google Sheet."""
    service = global_settings['service']
    SPREADSHEET_ID = global_settings['SPREADSHEET_ID']
    sheet_name = 'Pricing'
    result = service.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID,
                                                 range=f'{sheet_name}!A2:B').execute()
    values = result.get('values', [])

    if not values:
        raise ValueError('No data found in Pricing.')
    
    # Make sure that that all other cells in the sheet are empty
    service.spreadsheets().values().clear(
        spreadsheetId=SPREADSHEET_ID, range=f'{sheet_name}!C2:Z1000', body={}
    ).execute()
    
    # Make sure that all of our other sheets are empty
    for _sheet_name in ['Rival Prices', 'Market Shares', 'Profits', 'GameResults']:
        update_range = f'{_sheet_name}!A2:Z1000' if _sheet_name != 'GameResults' else f'{_sheet_name}!A1:Z1000'
        service.spreadsheets().values().clear(
            spreadsheetId=SPREADSHEET_ID, range=update_range, body={}
        ).execute()

    # Create a DataFrame of students
    df_students = pd.DataFrame(values, columns=['Name', 'ID'])
    global_settings['df_students'] = df_students
    
    # Initialize cumulative profits
    df_protected = df_students.copy()
    df_protected['student_round'] = 0
    df_protected['Total Profit'] = 0

    # For each round, add columns for 'Rival Price', 'Market Share', 'Profit'
    for round_num in range(1, 11):
        df_protected[f'Round{round_num}_RivalPrice'] = ''
        df_protected[f'Round{round_num}_MarketShare'] = ''
        df_protected[f'Round{round_num}_Profit'] = ''
    
    df_protected.set_index('ID', inplace=True)    
    
    global_settings['df_protected'] = df_protected
    
    return

def pair_students(student_list=None):
    """Randomly pair students."""
    df_students = global_settings['df_students']
    if student_list is None:
        # Randomly pair students
        student_list = df_students['ID'].tolist()
        
    random.shuffle(student_list)

    pairs = []
    residual_student = None
    df_protected = global_settings['df_protected']

    while len(student_list) >= 2:
        p1 = student_list.pop()
        p2 = student_list.pop()
        # Set the rounds to all allocated students to 1
        df_protected.loc[p1, 'student_round'] = 1
        df_protected.loc[p2, 'student_round'] = 1
        pairs.append((p1, p2))

    # If one student is left, pair with an existing student
    if len(student_list) == 1:
        residual_student = student_list.pop()
        df_protected.loc[residual_student, 'student_round'] = 1
        # Randomly select an existing student to pair with
        allocated_students = [p[0] for p in pairs] + [p[1] for p in pairs]
        allocated_student = random.choice(allocated_students)
        pairs.append((residual_student, allocated_student))

    # Create a mapping from ID to Name
    id_to_name = dict(zip(df_students['ID'], df_students['Name']))
    global_settings['id_to_name'] = id_to_name

    # Build pairs DataFrame
    pair_data = []
    for pair in pairs:
        residual = residual_student in pair
        pair_data.append({
            'Student1_ID': pair[0],
            'Student1_Name': id_to_name.get(pair[0], ''),
            'Student2_ID': pair[1],
            'Student2_Name': id_to_name.get(pair[1], ''),
            'Residual': residual
        })
    df_pairs = pd.DataFrame(pair_data)
    global_settings['df_pairs'] = df_pairs
    global_settings['residual_student'] = residual_student
    return

def plot_student_pairs():
     
    # Make a folder for the plots
    if not os.path.exists('plots'):
        os.makedirs('plots')
    
    # Make a subfolder for the section
    section_name = global_settings['section_name']
    if not os.path.exists(f'plots/{section_name}'):
        os.makedirs(f'plots/{section_name}')
    game_abbrev = global_settings['game_abbrev']
    today = global_settings['today']
    fig_dir = f'plots/{section_name}/{game_abbrev}_{today}'
    if not os.path.exists(fig_dir):
        os.makedirs(fig_dir)
        
    
    # get the data sets
    df_pairs = global_settings['df_pairs'].copy()
    df_prices = get_prices()
    df_protected = global_settings['df_protected']
    mode = global_settings['mode']
    
    df_pairs['total_profit'] = df_pairs['Student1_ID'].map(df_protected['Total Profit']) + \
        df_pairs['Student2_ID'].map(df_protected['Total Profit'])
    df_pairs.sort_values('total_profit', ascending=False, inplace=True)
    df_pairs.reset_index(drop=True, inplace=True)

    # Generate line plots
    rounds = list(range(1, 11))
    for index, pair in df_pairs.iterrows():
        s1_id = pair['Student1_ID']
        s2_id = pair['Student2_ID']
        s1_name = pair['Student1_Name']
        s2_name = pair['Student2_Name']

        # Get prices and profits for s1
        s1_prices = []
        s1_profits = []
        for r in rounds:
            price_col_name = f'Price_{r}'
            price = df_prices.loc[df_prices['ID'] == s1_id, price_col_name].values
            if len(price) == 0 or pd.isna(price[0]):
                continue
            s1_prices.append(price[0])
            profit = pd.to_numeric(df_protected.loc[s1_id, f'Round{r}_Profit'], errors='coerce')
            s1_profits.append(profit)

        # Get prices and profits for s2
        s2_prices = []
        s2_profits = []
        for r in rounds:
            price_col_name = f'Price_{r}'
            price = df_prices.loc[df_prices['ID'] == s2_id, price_col_name].values
            if len(price) == 0 or pd.isna(price[0]):
                continue
            s2_prices.append(price[0])
            profit = pd.to_numeric(df_protected.loc[s2_id, f'Round{r}_Profit'], errors='coerce')
            s2_profits.append(profit)

        s1_name_short = s1_name.split()[0]
        s2_name_short = s2_name.split()[0]
        
        # Plot prices and profits side by sides
        fig, axs = plt.subplots(1, 2, figsize=(15, 5))
        axs[0].plot(range(1, 1 + len(s1_prices)), s1_prices, label=f'{s1_name_short}', linestyle='solid')
        axs[0].plot(range(1, 1 + len(s2_prices)), s2_prices, label=f'{s2_name_short}', linestyle='dashed')
        axs[0].set_xlabel('Round')
        axs[0].set_ylabel('Price')
        axs[0].set_title(f'Prices for {s1_name} and {s2_name}')
        axs[0].legend()
        
        axs[1].plot(range(1, 1+ len(s1_profits)), s1_profits, label=f'{s1_name_short}', linestyle='solid')
        axs[1].plot(range(1, 1 + len(s2_profits)), s2_profits, label=f'{s2_name_short}', linestyle='dashed')
        axs[1].set_xlabel('Round')
        axs[1].set_ylabel('Profit')
        axs[1].set_title(f'Profits for {s1_name} and {s2_name}')
        axs[1].legend()
        plt.tight_layout()
        s1_name_clean = s1_name.replace(' ', '_').lower()
        s2_name_clean = s2_name.replace(' ', '_').lower()
        plt.savefig(os.path.join(fig_dir, f'rank_{index+1:d}_{s1_name_clean}_{s2_name_clean}.png'))
        plt.close('all')
    
    # Add a plot of the average price per round
    avg_prices = []
    for r in rounds:
        prices = df_prices[f'Price_{r}']
        avg_price = prices.mean()
        avg_prices.append(avg_price)
    plt.figure(figsize=(10, 5))
    plt.plot(rounds, avg_prices, label='Average Price', linestyle='solid', linewidth=2)
    extra_plots = global_settings['extra_price_plot_lines']
    palette = {
        'NE': 'red',
        'Monopoly': 'green'
    }
    for label, price in extra_plots.items():
        plt.axhline(y=price, linestyle='--', label=label, color=palette.get(label, 'black'))
    plt.xlabel('Round')
    plt.ylabel('Price')
    plt.title('Average Price per Round')
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(fig_dir, 'average_prices.png'))
    return
        

def load_service():
    """Load the Google Sheets service."""
    # Authenticate and get the service
    creds = None
    # The file token.pickle stores the user's access and refresh tokens.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If no valid credentials, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for next time
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('sheets', 'v4', credentials=creds)
    global_settings['service'] = service
    return


def prepare_update_request(sheet_name: str, data: pd.DataFrame) -> dict:
    """Prepare an update request for a results sheet from an input data frame.

    Args:
        sheet_name (str): The name of the sheet to update.
        data (pd.DataFrame): A dataframe including name, id, and all the columns to update.

    Returns:
        dict: A dictionary representing the update request.
    """
    # Make sure that 'Name' and 'ID' are the first columns
    data = data[['Name', 'ID'] + [col for col in data.columns if col not in ['Name', 'ID']]].copy()
    
    export_data = data.values.tolist()
    # Convert data types to serializable formats
    export_data = convert_to_serializable(export_data)

    # Determine the column letter
    col_letter = col_num_to_letters(data.shape[1])

    # Prepare the range, starting from row 2 (since row 1 is headers)
    end_row = data.shape[0] + 1  # since header is row 1
    range_name = f'{sheet_name}!A2:{col_letter}{end_row}'

    # Create the update request body
    request = {
        'range': range_name,
        'values': export_data
    }
    return request

def execute_batch_update(update_requests):
    """Execute a batch update with the collected update requests.

    Args:
        update_requests (list): A list of update request dictionaries.
    """
    service = global_settings['service']
    SPREADSHEET_ID = global_settings['SPREADSHEET_ID']

    body = {
        'valueInputOption': 'RAW',
        'data': update_requests
    }
    service.spreadsheets().values().batchUpdate(
        spreadsheetId=SPREADSHEET_ID,
        body=body
    ).execute()


def get_prices()->pd.DataFrame:
    # Read all the pricing data
    df_protected = global_settings['df_protected']
    service = global_settings['service']
    SPREADSHEET_ID = global_settings['SPREADSHEET_ID']
    sheet_name = 'Pricing'
    start_row = 2
    end_row = 1 + df_protected.shape[0]
    start_col = 'A'
    end_cols = 'L'
    results = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=f'{sheet_name}!{start_col}{start_row}:{end_cols}{end_row}'
    ).execute()
    values = results.get('values', [])
        
    if not values:
        print('No price data found.')
        return
    
    

    # Create a DataFrame for prices
    df_prices = pd.DataFrame(values)
    cols = ['Name', 'ID'] + [f'Price_{i}' for i in range(1, df_prices.shape[1] - 1)]
    df_prices.columns = cols
    # reindex to all prices
    full_cols = ['Name', 'ID'] + [f'Price_{i}' for i in range(1, 11)]
    df_prices = df_prices.reindex(columns=full_cols).fillna(np.nan)
    # Make sure that all price columns are numeric
    for i in range(1, 11):
        df_prices[f'Price_{i}'] = pd.to_numeric(df_prices[f'Price_{i}'], errors='coerce')
    return df_prices

def advance_round(hard=False):
    """Advance to the next round

    Args:
        hard (bool, optional): if False will only progress student pairs that have submitted prices.
            If True, will use previous prices as current choice for missing inputs and will coalece
            all students to the same round. Defaults to False.
    """
    round_num = global_settings['round_num']
    df_protected = global_settings['df_protected']
    
    df_prices = get_prices()
     
    # Check if we have pairs assigned
    df_pairs = global_settings['df_pairs']
    if df_pairs is None:
        students_in_game = df_prices.dropna(subset=['Price_1'])['ID'].tolist()
        pair_students(students_in_game)
        df_pairs = global_settings['df_pairs']     
   
    # determine the current binding round
    binding_round = df_protected.loc[(df_protected['student_round'] > 0), 'student_round'].min()
    binding_round = 1 if binding_round is None else binding_round
    binding_round = max(min(binding_round, 10), 1)
    
    update_price_positions = []
    # Process each pair
    for _, pair in df_pairs.iterrows():
        s1_id = pair['Student1_ID']
        s2_id = pair['Student2_ID']
        residual = pair['Residual']
        
        # Get the current round of the students
        source_pair_round = df_protected.loc[s1_id, 'student_round']
        # Determine how many rounds are we going to process
        if not hard:
            rounds = [source_pair_round]
        else:
            rounds = range(source_pair_round, binding_round + 1)
            
        for pair_round in rounds:
            # Then we check if they both have inputed prices for their current round
            price_col_name = f'Price_{pair_round}'
            
            
            # Get prices for both students
            s1_price = df_prices.loc[df_prices['ID'] == s1_id, price_col_name].values
            s2_price = df_prices.loc[df_prices['ID'] == s2_id, price_col_name].values

            if len(s1_price) == 0 or pd.isna(s1_price[0]):
                s1_price = None 
            else:
                s1_price = s1_price[0]
            if len(s2_price) == 0 or pd.isna(s2_price[0]):
                s2_price = None
            else:
                s2_price = s2_price[0]
                
            if (s1_price is None or s2_price is None) and not hard:
                continue
            else:
                if s1_price is None:
                    s1_price = df_prices.loc[df_prices['ID'] == s1_id, f'Price_{pair_round - 1}'].values[0]
                    # add the price back to df_prices for updating
                    df_prices.loc[df_prices['ID'] == s1_id, price_col_name] = s1_price
                    update_price_positions.append((s1_id, pair_round, s1_price))
                if s2_price is None:
                    s2_price = df_prices.loc[df_prices['ID'] == s2_id, f'Price_{pair_round - 1}'].values[0]
                    # add the price back to df_prices for updating
                    df_prices.loc[df_prices['ID'] == s2_id, price_col_name] = s2_price
                    update_price_positions.append((s2_id, pair_round, s2_price))
             
            (s1_market_share, s1_profit), (s2_market_share, s2_profit) = demand_and_profits(s1_price, s2_price)

            # Update df_protected for s1
            df_protected.loc[s1_id, f'Round{pair_round}_RivalPrice'] = s2_price
            df_protected.loc[s1_id, f'Round{pair_round}_MarketShare'] = s1_market_share
            df_protected.loc[s1_id, f'Round{pair_round}_Profit'] = s1_profit
            df_protected.loc[s1_id, 'Total Profit'] += s1_profit
            df_protected.loc[s1_id, 'student_round'] += 1
            
            if not residual: 
                # Update df_protected for s2
                df_protected.loc[s2_id, f'Round{pair_round}_RivalPrice'] = s1_price
                df_protected.loc[s2_id, f'Round{pair_round}_MarketShare'] = s2_market_share
                df_protected.loc[s2_id, f'Round{pair_round}_Profit'] = s2_profit
                df_protected.loc[s2_id, 'Total Profit'] += s2_profit
                df_protected.loc[s2_id, 'student_round'] += 1

    # Update pending prices
    if len(update_price_positions) > 0:
        data = []
        df_students = global_settings['df_students']
        ids = df_students['ID'].tolist()
        for id_value, round_num, value in update_price_positions:
            row_number = ids.index(id_value) + 2
            col_letter = col_num_to_letters(round_num + 2)
            sheet_name = 'Pricing'
            cell_range = f'{sheet_name}!{col_letter}{row_number}'
            data.append({
                'range': cell_range,
                'values': [[value]]
            })
            
            body = {
                'valueInputOption': 'RAW',
                'data': data
            }
            service = global_settings['service']
            spreadsheet_id = global_settings['SPREADSHEET_ID']
            result = service.spreadsheets().values().batchUpdate(
                spreadsheetId=spreadsheet_id, body=body).execute()
        
    # make sure that df_protected is updated
    global_settings['df_protected'] = df_protected.copy()
    df_protected = df_protected.reset_index(drop=False)
    # Update only the relevant column in each sheet
    # update rival prices
    update_requests = []
    keep = ['Name', 'ID'] + [x for x in df_protected.columns if 'RivalPrice' in x]
    data = df_protected[keep]
    update_requests.append(prepare_update_request('Rival Prices', data))
    # update market shares
    keep = ['Name', 'ID'] + [x for x in df_protected.columns if 'MarketShare' in x]
    data = df_protected[keep]
    update_requests.append(prepare_update_request('Market Shares', data))
    # update profits
    keep = ['Name', 'ID'] + [x for x in df_protected.columns if '_Profit' in x] + ['Total Profit']
    data = df_protected[keep]
    update_requests.append(prepare_update_request('Profits', data))
    execute_batch_update(update_requests)
    return

def show_pairs():
    """Show the assigned pairs."""
    df_pairs = global_settings['df_pairs']
    if df_pairs is None:
        print("No pairs have been assigned.")
        return
    print("-----------------------")
    print("--- Assigned Pairs ---")
    for _, row in df_pairs.iterrows():
        if not row['Residual']:
            print(f"{row['Student1_Name']} - {row['Student2_Name']}")
        else:
            print(f"{row['Student1_Name']} - Residual - {row['Student2_Name']}")
    print("-----------------------")
    return

def update_game_results():
    """Update the game results sheet."""
    service = global_settings['service']
    SPREADSHEET_ID = global_settings['SPREADSHEET_ID']
    df_pairs = global_settings['df_pairs']
    df_protected = global_settings['df_protected']
    df_results = df_pairs.copy()
    df_results['Student1_TotalProfit'] = df_results['Student1_ID'].map(df_protected['Total Profit'])
    df_results['Student2_TotalProfit'] = df_results['Student2_ID'].map(df_protected['Total Profit'])

    # Write df_results to a new sheet
    new_sheet_name = 'GameResults'

    # Check if 'GameResults' sheet already exists
    sheets_metadata = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
    sheet_names = [sheet['properties']['title'] for sheet in sheets_metadata['sheets']]
    if new_sheet_name not in sheet_names:
        # Create the sheet
        requests = [{
            'addSheet': {
                'properties': {
                    'title': new_sheet_name,
                }
            }
        }]
        body = {
            'requests': requests
        }
        response = service.spreadsheets().batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
            body=body).execute()
        
    # Make sure that the sheet is empty
    service.spreadsheets().values().clear(spreadsheetId=SPREADSHEET_ID, range=f'{new_sheet_name}!A1:Z1000', body={}).execute()
        
    # Cleanup the results
    df_results.drop(columns=['Residual'], inplace=True)
    # drop the ids
    df_results.drop(columns=['Student1_ID', 'Student2_ID'], inplace=True)
    # Rename the columns
    df_results.rename(columns={'Student1_Name': 'Student 1', 'Student2_Name': 'Student 2',
                                 'Student1_TotalProfit': 'Student 1 Total Profit', 'Student2_TotalProfit': 'Student 2 Total Profit'}, inplace=True)
    # compute total market profits
    df_results['Total Market Profits'] = df_results['Student 1 Total Profit'] + df_results['Student 2 Total Profit']
    # Round profits to the nearest decimal
    df_results['Student 1 Total Profit'] = df_results['Student 1 Total Profit'].round(1)
    df_results['Student 2 Total Profit'] = df_results['Student 2 Total Profit'].round(1)
    
    # Sort by total market profits
    df_results.sort_values('Total Market Profits', ascending=False, inplace=True)

    # Write df_results to the new sheet
    results_values = [df_results.columns.tolist()] + df_results.values.tolist()
    body = {
        'values': results_values
    }
    service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID, range=f'{new_sheet_name}!A1',
        valueInputOption='RAW', body=body).execute()
    return

def show_rankings(save=False):
    df_protected = global_settings['df_protected'].copy()
    
    # Show the top-five students by total profit
    df_protected.sort_values('Total Profit', ascending=False, inplace=True)
    print(
        "----------------------\n"
        "\nTop 5 students by total profit:\n",
        f"{df_protected[['Name', 'Total Profit']].head(5)}\n"
    )
    
    # Show the top 5 pairs by total profit
    if global_settings['df_pairs'] is None:
        print("No pairs have been assigned.")
        return
    df_pairs = global_settings['df_pairs'].copy()
    df_pairs['total_profit'] = df_pairs['Student1_ID'].map(df_protected['Total Profit']) + \
        df_pairs['Student2_ID'].map(df_protected['Total Profit'])
    df_pairs.sort_values('total_profit', ascending=False, inplace=True)
    print(
        "\nTop 5 pairs by total profit:\n",
        f"{df_pairs[['Student1_Name', 'Student2_Name', 'total_profit']].head(5)}\n"
    )
    print("----------------------")
    
    if save:
        output_dir = './game_results/'
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        section_name = global_settings['section_name']
        game_abbrev = global_settings['game_abbrev']
        today = pd.Timestamp.now().strftime('%Y-%m-%d')
        df_protected.to_csv(f'{output_dir}/{section_name}_{game_abbrev}_{today}_indiv_profits.csv', index=False)
        df_pairs.to_csv(f'{output_dir}/{section_name}_{game_abbrev}_{today}_pair_profits.csv', index=False)
        
    return

def main():
    """Main function to run the game app."""
    # Load the service
    load_service()
    
    # Get the settings
    settings = load_section_settings()
    
    if len(settings) == 0:
        print("No sections registered. Please register your section first usng the --register option.")
        raise ValueError("No sections registered.")

    # The ID of the spreadsheet.
    prompt_for_section(settings)
    
    # Read the student data from 'Pricing'
    load_students()

    # Ask to start the game and select mode
    section_name = global_settings['section_name']
    print(f"Starting game for section {section_name}")

    mode = clean_input("Select game mode:\n"
                 "(a) Homogenous Bertrand \n"
                 "(b) Hotelling \n"
                 ).lower()
    
    if mode not in ['a', 'b']:
        print("Invalid mode selected.")
        raise ValueError("Invalid mode selected.")
    
    if mode == 'a':
        alpha = clean_input("Choose the demand slope parameter alpha (or press Enter for default 1): ")
        if len(alpha) == 0:
            alpha = 1
        else:
            alpha = float(alpha)
            
        c = clean_input("Choose the marginal cost c (or press Enter for default 0): ")
        if len(c) == 0:
            c = 0
        else:
            c = float(c)
        global_settings['game_settings'] = {'alpha': alpha, 'c': c}
        global_settings['game_abbrev'] = f'bertrand_alpha{alpha}_c{c}'
        global_settings['extra_price_plot_lines'] = {
            'NE': c,
            'Monopoly': (100 + c) / 2.0 
        }
    elif mode == 'b':
        setting = clean_input("Choose a Hotelling Setup:\n"
                              "(a) High transport cost (t=1, c=0, v=200)\n"
                              "(b) Low transport cost (t=.5, c=0, v=200)\n"
                              "(c) Custom\n")
        if setting not in ['a', 'b', 'c']:
            print("Invalid setting selected.")
            raise ValueError("Invalid setting selected.")
        if setting == 'c':
            t = clean_input("Choose the transport cost t (or press Enter for default 1): ")
            if len(t) == 0:
                t = 1
            else:
                t = float(t)
            c = clean_input("Choose the marginal cost c (or press Enter for default 0): ")
            if len(c) == 0:
                c = 0
            else:
                c = float(c)
            v = clean_input("Choose the location of the firms v (or press Enter for default 4): ")
            if len(v) == 0:
                v = 4
            else:
                v = float(v)
            global_settings['game_settings'] = {'t': t, 'c': c, 'v': v}
            global_settings['extra_price_plot_lines'] = {
                'NE': c + 100 * t,
            }
        elif setting == 'a':
            # Monopoly price is 150, NE is 100
            t = 1
            c = 0
            v = 200
            global_settings['game_settings'] = {'t': t, 'c': c, 'v': v}
            global_settings['extra_price_plot_lines'] = {
                'NE': c + 100 * t,
                'Monopoly': 150
            }
        elif setting == 'b':
            # monopoly price is 175, NE is 50
            t = .5
            c = 0
            v = 200
            global_settings['game_settings'] = {'t': t, 'c': c, 'v': v}
            global_settings['extra_price_plot_lines'] = {
                'NE': c + 100 * t,
                'Monopoly': 175
            }
        global_settings['game_abbrev'] = f'hotelling_t{t}_c{c}_v{v}' 
    
    mode_map = {
        'a': 'bertrand',
        'b': 'hotelling',
    }
    mode = mode_map[mode]
    global_settings['mode'] = mode



    # Game loop
    round_num = 1
    while True:
        global_settings['round_num'] = round_num
        # Get the current binding student round
        df_protected = global_settings['df_protected']
        binding_round = df_protected.loc[(df_protected['student_round'] > 0), 'student_round'].min()
        binding_round = 1 if np.isnan(binding_round) else binding_round
        if binding_round > 10:
            print("All rounds have been completed.")
            break
        print(f"\n[{section_name}] - Round {round_num} - Binding Round {binding_round}\n"
              "--------")
        option = clean_input("Select option: \n"
                       "(a) update profits and move to next round (soft)\n"
                       "(b) force update, setting missing prices to previous input (hard)\n"
                       "(c) see current rankings\n"
                       "(d) show assigned pairs\n"
                       "(e) end game \n").lower()
        if option not in ['a', 'b', 'c', 'd', 'e']:
            print("Invalid option selected.")
            continue
        elif option == 'e':
            print("Game ended.")
            break
        elif option == 'd':
            show_pairs()
            continue
        elif option == 'c':
            show_rankings()
            continue
        elif option == 'b':
            advance_round(hard=True)
        elif option == 'a':
            advance_round(hard=False)
        else:
            print("Invalid option selected.")
            continue
        
        round_num += 1

    # After the game ends
    # Create an additional sheet with matched pairs and total profits
    update_game_results()
     
    # print the highest profit student and the highest profit pair
    show_rankings(save=True)
    
    # Create a DataFrame for the pairs and total profits
    plot_student_pairs()
    return

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=dedent("""
    ===== Dynamic Pricing Lab Interface =====
    This script controls the update of the Google Sheets for the Dynamic Pricing Lab.
    
    ---- Setup ---- 
    Before class, you must register your section sheet using
    
    python main.py --register "Section Name" "Section Sheet ID"
    
    Where "Section Name" is the name of the section and "Section Sheet ID" is the ID of the Google Sheet,
    which is the string in the URL after 'https://docs.google.com/spreadsheets/d/' and before '/edit'.
    See the README.md file for more information.
   
    ---- Running the Game ----
    To run the game, simply run
    python main.py
    
    The script will ask you which section to run the game for and the proceed to select a game mode.
    By default each game runs 10 rounds, but you can exit at any time.
    Plots of prices and profits will be generated for each pair of students and stored in the 'plots' folder, 
    with a subfolder for each section.

    ---- Game Modes ----
    The game offers the following modes of play:
    
    a) Homogenous product duopolies with zero marginal cost (Bertrand):
        In this game the lowest price firms takes the market and faces a market share function
            s(p) = 1 - alpha * p
        alpha can be configured within the game and defaults to one. The monopoly price 1/2 * alpha
        and the NE is p = 0.
        
    b) Hotelling model:
        Consumers are uniformly distributed on the [0, 1] line with linear transport cost t, firms have
        marginal cost c and are located at the edgest of the line. The market share function is
            s_1(p_1, p_2) = 1/2 + (p_1 - p_2) / (200 * t)
        and the NE is p_1 = p_2 = c + 100 * t. 
    
    
    In all games the total demand is set to 100.

    """), formatter_class=argparse.RawTextHelpFormatter)
    
    parser.add_argument("--register", type=str, nargs=2,
                        help="register a section with the given name and sheet ID")
    args = parser.parse_args()
    
    if args.register:
        section_name, section_sheet_id = args.register
        register_section(section_name, section_sheet_id)
    else:
        main()  
        
# End of main.py
    
    
