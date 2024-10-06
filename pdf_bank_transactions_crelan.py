
'''
Improvements:
- regex is hard coded: pattern = r'Tél\. 02 762 20 00 - Card Stop: 078 170 170 - www\.bnpparibasfortis\.be\d+/\d+'
        remaining_text = re.sub(pattern, '', remaining_text)
'''

from PyPDF2 import PdfReader
import pandas as pd
import re
# Load PDF
import os
from dotenv import load_dotenv
from pathlib import Path
from matching_algos import *
import xlsxwriter

from datetime import datetime

# Define function to extract transaction type
def extract_transaction_type(comment):
    if "Achat par carte" in comment:
        return "Achat par carte"
    elif "contactless" in comment:
        return "Achat par carte"
    elif "eCommerce" in comment:
        return "Achat par carte"
    elif "charge crédits" in comment:
        return "Prêts hypothécaire"
    elif "Virement" in comment:
        return "Virement"
    elif " Paiement instantané" in comment:
        return "Virement"
    elif ("Paiement" in comment) or (" Achat carburant Bancontact" in comment):
        return "Achat par carte"
    elif "ordre permanent" in comment:
        return "ordre permanent"
    elif "Versement" in comment:
        return "Virement"
    elif "Mouvement" in comment:
        return "Souscription de titres"
    elif "Achat automatique" in comment:
        return "Souscription de titres"
    elif "Investissement" in comment:
        return "Souscription de titres"
    elif " Souscription épargne" in comment:
        return "Souscription de titres"
    elif "Retrait" in comment:
        return "Retrait d'espèces"
    elif "Tenue de compte" in comment:
        return "Redevance"
    elif "Contribution compte à vue" in comment:
        return "Redevance"
    elif "Encaissement interne du crédit" in comment:
        return "Prêts hypothécaire"
    else:
        return ""


# Define function to extract communication
def extract_communication(comment):
    lines = comment.split('\n')
    try:
        return lines[1]
    except:
        return lines


def process_transaction(row):
    comment = row['comment']
    transaction_type = row['transaction type']
    lines = comment.split('\n')
    if transaction_type == "Achat par carte":
        return lines[1]


# Define function to extract amount
def extract_amount_v1(comment):
    amount_line = [line for line in comment.split('\n') if any(char.isdigit() for char in line)]
    if amount_line:
        amount_pattern = r',\d{2} [+-]'
        #amount_match = re.search(amount_pattern , trans)
        # Extract the amount and clean up the value (e.g., remove "+" or "-")
        amount = amount_line[-1].split()[-1].replace('+', '').replace('-', '')
        return f"-{amount}" if '-' in amount_line[-1] else amount
    return ""


def extract_amount(comment):
    match_millions = re.search(r'[+-]\d{1,3}(\.\d{3})*,\d{2}', comment)
    #if throusand
    if match_millions is not None:
        match_millions = match_millions.group(0)
        match_millions_amount = re.search(r'[+-]\d{1,3}(\.\d{3})*,\d{2}', match_millions).group(0).replace(".", "").replace(",", ".")
        sign = match_millions_amount[0:1]
        return f"-{match_millions_amount[1:]}" if sign == '-' else match_millions_amount[1:]
    print("Error: no amount found for comment '{}".format(comment))
    return 0


def extract_counterparty(comment):
    # Define the regex pattern
    iban_pattern = r'Vers\s'
    # Search for all patterns in the text
    iban_matches = re.findall(iban_pattern, comment)
    if iban_matches:
        # Get the firstmatch
        iban_match = iban_matches[0]
        # Cut the text from the first pattern onwards, including the pattern itself
        cut_text_after_iban = comment[comment.index(iban_match):]
        return cut_text_after_iban
    else:
        # Define the regex pattern for ref bank
        ref_bank_pattern = r'carte\sn°\s'

        # Search for all ref bank patterns in the text
        ref_bank_matches = re.findall(ref_bank_pattern, comment)
        if ref_bank_matches:
            # Get the first ref bank match
            ref_bank_match = ref_bank_matches[0]
            # Find the end index of the last IBAN match
            #ref_bank_end_index = comment.index(ref_bank_match) + len(ref_bank_match)
            # Cut the text from the end of the last IBAN pattern onwards (not including the IBAN itself)
            cut_text_after_iban = comment[comment.index(ref_bank_match):]
            #cut_text_after_ref_bank = comment[ref_bank_match:].strip()
            return cut_text_after_iban
        #print("No patterns found in the text.")
        return ""


def remove_headers_footers(text):
    # Define the transaction pattern
    #transaction_pattern = r'(\d{2}-\d{2}-\d{4})\s+(\d{4})\s+'
    transaction_pattern = r'\b\d+\s\d{2}/\d{2}\b'
    # Search for the first occurrence of the transaction pattern
    match = re.search(transaction_pattern, text)

    if match:
        # remove header info
        header_text = text[:match.start()]
        # Split by the newline character
        header_lines = header_text.split('\n')
        # Remove empty strings and print the results
        header_lines = [headers.strip() for headers in header_lines if headers.strip()]

        # Keep text from the match onward
        remaining_text = text[match.start():]
    else:
        remaining_text = text
    # remove other headers
    #start_header = re.search(r"Nouveau solde au\s+", remaining_text).group(0)
    #end_header = header_text[-26:]
    # Constructing the regular expression dynamically
    try:
        pattern = re.escape("Nouveau solde au") + r".*?" + re.escape("Mouvement Valeur Montant")
        # Using re.sub to remove everything from start_header to end_header
        remaining_text = re.sub(pattern, '\n', remaining_text, flags=re.DOTALL)
    except:
        print("no sub header")

    try:
        remaining_text = re.sub(r"Les sommes déposées.*", '', remaining_text, flags=re.DOTALL)
    except:
        print("error: footer couldn't be removed")

    return remaining_text


def split_transactions(remaining_text):
    final_list = []
    pattern = r'\b\d+\s\d{2}/\d{2}\b'

    # Split the text using the updated pattern
    splitted_text = re.split(pattern, remaining_text)
    # Print each part after splitting
    for idx, part in enumerate(splitted_text, 1):
        final_list.append(f"{idx}: {part.strip()}\n")
        print(f"{idx}: {part.strip()}\n")

    # Remove empty strings and print the results
    return [transaction.strip() for transaction in final_list if transaction.strip()]


# Load the .env file
load_dotenv()
# Access the PDF_FILES_PATH variable
input_folder_path = os.getenv('PDF_FILES_PATH')
language = os.getenv('LANGUAGE')
if language != "French":
    print('Warning: nltk packages are in French. It can be easily changed though, lookup and change parameter "language=french"')

pdf_folder = Path(input_folder_path)
transaction_id = 0
final_transaction_list = []
#error_transaction = pd.DataFrame(columns=['date', 'trans_id', 'comment'])
error_amount = pd.DataFrame(columns=['comment', 'amount'])
dic_balances = {}
# Loop through all PDFs in the folder
for pdf_file in pdf_folder.glob('*.pdf'):
    # Open and process each PDF
    print(f'Processing file: {pdf_file}')
    # Create a PdfReader object
    reader = PdfReader(pdf_file)
    # Extracting information (for example, the number of pages)
    num_pages = len(reader.pages)

    # Extract text
    pdf_text = ''
    for page in reader.pages:
        if not page.extract_text():
            print("error: pdf '{}' cannot be read, it's probably a pure image".format(pdf_file))
        else:
            pdf_text += page.extract_text()

    text = pdf_text
    # Extract client information
    try:
        iban = re.search(r'([A-Z]{2}\d{2}\s+\d{4}\s+\d{4}\s+\d{4})', text).group(1)
        bic = re.search(r'BIC: (\w+)', text).group(1)
    except:
        print("Couldn't retrieve IBAN and BIC")

    # find current year
    # Regex pattern to match the year
    pattern = r'Extrait:\s*\d{1,2}/(\d{4})'
    # Find the first match
    match = re.search(pattern, text)
    # Extract the year if a match is found
    if match:
        current_year = match.group(1)
    else:
        # Regex pattern to match the year
        pattern = r'Nouveau\s+solde\s+au\s+\d{1,2}/\d{1,2}/(\d{4})'
        # Find the first match
        match = re.search(pattern, text)
        # Extract the year if a match is found
        if match:
            current_year = match.group(1)
        else:
            current_year = "9999"

    try:
        # Extract current and previous balance
        # Define the pattern
        pattern = r'Solde\s+précédent\s+au\s+\d{1,2}/\d{1,2}/(\d{4})'
        # Find the first matching line and store it in a variable
        matching_line = next((line for line in text.splitlines() if re.search(pattern, line)), None)
        # get date
        date_pattern = r'\d{1,2}/\d{1,2}/(\d{4})'
        # Find the first match
        old_balance_date = re.search(date_pattern, matching_line).group(0)

        match_millions = re.search(r"-?\s?\d{1,3}(\.\d{3})*,\d{2}", matching_line).group(0)
        if match_millions is not None:
            match_millions_amount = re.search(r'-?\s?\d{1,3}(\.\d{3})*,\d{2}', match_millions).group(0).replace(".",
                                                                                                                "").replace(
                ",", ".")
            sign = match_millions_amount[0:1]
            previous_balance_amount = f"-{match_millions_amount[1:]}" if sign == '-' else match_millions_amount[1:]


        # Extract current and previous balance
        # Define the pattern
        pattern = r'Nouveau\s+solde\s+au\s+\d{1,2}/\d{1,2}/(\d{4})'
        # Find the first matching line and store it in a variable
        matching_line = next((line for line in text.splitlines() if re.search(pattern, line)), None)
        # get date
        date_pattern = r'\d{1,2}/\d{1,2}/(\d{4})'
        # Find the first match
        current_balance_date = re.search(date_pattern, matching_line).group(0)
        match_millions = re.search(r"-?\s?\d{1,3}(\.\d{3})*,\d{2}", matching_line).group(0)
        if match_millions is not None:
            match_millions_amount = re.search(r'-?\s?\d{1,3}(\.\d{3})*,\d{2}', match_millions).group(0).replace(".", "").replace(",", ".")
            sign = match_millions_amount[0:1]
            current_balance_amount = f"-{match_millions_amount[1:]}" if sign == '-' else match_millions_amount[1:]

        # keep track of account balance
        if current_balance_date not in dic_balances:
            dic_balances[current_balance_date] = current_balance_amount
        else:
            print('test')
        if old_balance_date not in dic_balances:
            dic_balances[old_balance_date] = previous_balance_amount
        else:
            print('test')
    except:
        print("not able to retrieve account balance")
    ## remove headers and footer
    remaining_text = remove_headers_footers(text)

    # split transactions
    final_transaction_list.extend(split_transactions(remaining_text))

# convert transaction list to df
transaction_df = pd.DataFrame(columns=['date', 'trans_id', 'comment'])
for i, el in enumerate(final_transaction_list):
    if len(el) > 4:
        transaction_id += 1
        ## Find date in the format "dd-mm"
        # Search for the first occurrence of any date pattern
        #dates = re.findall(r'\b\d{2}/\d{2}\b', el)
        try:
            matched_date = re.search(r'\b\d{2}/\d{2}\b', el).group()
        except:
            try:
                matched_date = re.search(r'\d{2}-\d{2}', el).group()
            except:
                matched_date = '01/01'
        # get year: Convert the string to a datetime object and extract the year
        #date_year = datetime.strptime(current_balance_date, "%d-%m-%Y").year

        transaction_date = "{}/{}".format(matched_date, str(current_year))
        transaction_df = pd.concat([transaction_df,
                                       pd.DataFrame([{'date': transaction_date,
                                                      'trans_id': transaction_id,
                                                      'comment': el}])],
                                      ignore_index=True)

# Convert 'date' column to datetime format
transaction_df['date'] = pd.to_datetime(transaction_df['date'], format='%d/%m/%Y')
# Sort the DataFrame by 'date' in ascending order
transaction_df = transaction_df.sort_values(by='date')
# Reset the index if desired
transaction_df.reset_index(drop=True, inplace=True)
transaction_df['trans_id'] = transaction_df.index

transaction_output_file = os.path.join(input_folder_path, 'transactions.csv')
try:
    transaction_df.to_csv(
        transaction_output_file,
        index=False,
        sep=',',
        encoding='utf-8-sig',
    )
except:
    print("error permmission denied: 'transactions.csv' seems to be already open, please close the file")


# Apply the extraction functions to create the new columns
transaction_df['transaction type'] = transaction_df['comment'].apply(extract_transaction_type)
transaction_df['Communication'] = transaction_df['comment'].apply(extract_communication)
#transaction_df['Communication'] = transaction_df.apply(process_transaction, axis=1)
transaction_df['Amount'] = transaction_df['comment'].apply(extract_amount)
transaction_df['Counterparty'] = transaction_df['comment'].apply(extract_counterparty)


# Display or save the result
# os.path.join(os.path.dirname(pdf_path)
output_file_path = os.path.join(input_folder_path, 'transactions_enriched.csv')
transaction_df.to_csv(output_file_path, index=False)
if transaction_df.empty:
    print("No transaction found")

# Export the 'comments' column to a text file
transaction_df['comment'].to_csv(os.path.join(input_folder_path, 'comments_GPT.txt'), index=False, header=False)

# Apply the categorization function to the DataFrame
categories_exact_match, categories_fuzzy = get_categories()

transaction_df = categorize_transaction(transaction_df, categories_exact_match=categories_exact_match, categories_fuzzy=categories_fuzzy)

output_file_path = os.path.join(input_folder_path, 'transactions_enriched_categorized.csv')
transaction_df.to_csv(output_file_path, index=False)

# convert 'Amount' from string to float
transaction_df['Amount'] = pd.to_numeric(transaction_df['Amount'], errors='coerce')

transaction_df_pos = transaction_df[transaction_df['Amount'] >= 0]
# print
output_file_path = os.path.join(input_folder_path, 'transactions_enriched_categorized_pos_amounts.csv')
transaction_df_pos.to_csv(output_file_path, index=False)

#transaction_df = transaction_df[~(transaction_df['Amount'] >= 0)]
transaction_df_neg = transaction_df[transaction_df['Amount'] < 0]
# print
output_file_path = os.path.join(input_folder_path, 'transactions_enriched_categorized_neg_amounts.csv')
transaction_df_neg.to_csv(output_file_path, index=False)

'''
# Given that your data is already in df, we now create the pivot table
pivot_table = pd.pivot_table(transaction_df, values='Amount', index=['Category', 'Counterparty'], aggfunc='sum')
output_file_path = os.path.join(input_folder_path, 'transactions_enriched_pivot.xlsx')
# Save the pivot table to an Excel file
with pd.ExcelWriter(output_file_path, engine='xlsxwriter') as writer:
    # Write the original DataFrame to one sheet
    transaction_df.to_excel(writer, sheet_name='Original Data', index=False)

    # Write the pivot table to another sheet
    pivot_table.to_excel(writer, sheet_name='Pivot Table')

print("Pivot table created and saved to pivot_output.xlsx")
'''
print(f"File successfully converted and saved to {output_file_path}")