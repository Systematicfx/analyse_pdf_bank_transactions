
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
    if "BANCONTACT" in comment.upper():
        return "Achat par carte"
    elif "VIREMENT" in comment.upper():
        return "Virement"
    elif "VERSEMENT" in comment.upper():
        return "Virement"
    elif "DOMICILIATION" in comment.upper():
        return "Virement"
    elif "CHARGEMENT DE LA CARTE" in comment.upper():
        return "Virement"
    elif "ORDRE PERMANENT" in comment.upper():
        return "Virement"
    elif "DEPOT" in comment.upper():
        return "Retrait d'espèces"
    elif "RETRAIT" in comment.upper():
        return "Retrait d'espèces"
    elif "FRAIS DE" in comment:
        return "Redevance"
    else:
        return ""


# Define function to extract communication
def extract_communication(comment):
    # Define the regex pattern for ref bank
    communication = r'COMMUNICATION\s:'
    # Search for all ref bank patterns in the text
    communication_matches = re.findall(communication, comment.upper())
    # find text between communication and ref bank
    if communication_matches:
        # Get the firstmatch
        match = communication_matches[0]
        cut_text_after = comment[comment.index(match):]
        # Remove the pattern 'COMMUNICATION:'
        cut_text_after = re.sub(r'COMMUNICATION\s*:', '', cut_text_after)

        ref = r'REFERENCE DU CREANCIER'
        # Search for all ref bank patterns in the text
        ref_matches = re.findall(ref, cut_text_after.upper())
        if ref_matches:
            # Get the firstmatch
            match = ref_matches[0]
            cut_text_before = cut_text_after[:cut_text_after.index(match)]
            return cut_text_before
        else:
            return cut_text_after

    communication = r'VERSEMENT DE\s+[A-Z]{2}\d{2}\s+\d{4}\s+\d{4}\s+\d{4}\s+'
    communication_matches = re.findall(communication, comment.upper())
    # find text between communication and ref bank
    if communication_matches:
        # Regular expression to match text after 'Communication:' until the end of the line
        pattern = r"VERSEMENT DE\s+[A-Z]{2}\d{2}\s+\d{4}\s+\d{4}\s+\d{4}\s\s*(.+)"
        ref_matches = re.findall(pattern, comment.upper())
        if ref_matches:
            # Get the firstmatch
            match = ref_matches[0]
            cut_text_after = comment[comment.upper().index(match):]
            lines = cut_text_after.split('\n')
            return "{}: {}".format(lines[0], lines[1])

    communication = r'VIREMENT\s'
    communication_matches = re.findall(communication, comment.upper())
    # find text between communication and ref bank
    if communication_matches:
        lines = comment.split('\n')
        return "{}: {}".format(lines[len(lines) - 2], lines[len(lines) - 1])
    return ""


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
    match_millions = re.search(r"[+-]\s+\d{1,3}(\.\d{3})*,\d{2}", comment).group(0)
    if match_millions is None:
        match_millions = re.search(r"[+-]\d{1,3}(\.\d{3})*,\d{2}", comment).group(0)
    match_millions = match_millions.replace(' ', '')
    #if throusand
    if match_millions is not None:
        # Remove spaces
        match_millions_amount = re.search(r'[+-]\d{1,3}(\.\d{3})*,\d{2}', match_millions).group(0).replace(".", "").replace(",", ".")
        sign = match_millions_amount[0:1]
        return f"-{match_millions_amount[1:]}" if sign == '-' else match_millions_amount[1:]
    print("Error: no amount found for comment '{}".format(comment))
    return 0


def extract_counterparty(comment):
    bancontact_pattern = r'BANCONTACT ACHAT'
    # Search for all patterns in the text
    bancontact_matches = re.findall(bancontact_pattern, comment.upper())
    if bancontact_matches:
        # Search for all ref bank patterns in the text
        bancontact_matches = re.findall(bancontact_pattern, comment.upper())
        # find text between communication and ref bank
        if bancontact_matches:
            # Regular expression to match text after 'Communication:' until the end of the line
            pattern = r"BANCONTACT ACHAT\s*(.+)"
            # Find the first match
            match = re.search(pattern, comment)
            # If a match is found, print it
            if match:
                line = match.group(1).replace('\n', '')
                line = line.lstrip(' -')
                return re.sub(r'\s{2,}', ' ', line)
    # Define the regex pattern
    iban_pattern = r'\sVERS\s'
    # Search for all patterns in the text
    iban_matches = re.findall(iban_pattern, comment)

    if iban_matches:
        # Get the firstmatch
        iban_match = iban_matches[0]
        # Cut the text from the first pattern onwards, including the pattern itself
        cut_text_after_iban = comment[comment.index(iban_match):]
        # Remove the pattern from the text
        pattern = r'\sVERS\s[A-Z]{2}\d{2}\s+\d{4}\s+\d{4}\s+\d{4}'
        cut_text_after_iban = re.sub(pattern, '', cut_text_after_iban)
        line = cut_text_after_iban.replace('\n', '')
        line = line.lstrip(' -')
        return re.sub(r'\s{2,}', ' ', line)

    # Define the regex pattern
    iban_pattern = r'\sAU NOM DE\s'
    # Search for all patterns in the text
    iban_matches = re.findall(iban_pattern, comment)
    if iban_matches:
        # Get the firstmatch
        iban_match = iban_matches[0]
        # Cut the text from the first pattern onwards, including the pattern itself
        cut_text_after_iban = comment[comment.index(iban_match):]
        # Remove the pattern from the text
        pattern = r'\sAU NOM DE\s'
        cut_text_after_iban = re.sub(pattern, '', cut_text_after_iban)
        line = cut_text_after_iban.replace('\n', '')
        line = line.lstrip(' -')
        return re.sub(r'\s{2,}', ' ', line)

    return ""


def remove_headers_footers(text):
    # Define the transaction pattern
    #transaction_pattern = r'(\d{2}-\d{2}-\d{4})\s+(\d{4})\s+'

    transaction_pattern = r'SOLDE AU\s*\d{2}-\d{2}-\d{4}'
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

    # remove sub-headers
    transaction_pattern = r'\d+\s+\d{2}-\d{2}-\d{4}'
    # Search for the first occurrence of the transaction pattern
    match = re.search(transaction_pattern, remaining_text)
    if match:
        # Keep text from the match onward
        remaining_text = remaining_text[match.start():]

        # remove other headers
        start_header = 'Belfius Banque'
        end_header = re.search(r'----\s+[A-Z]{2}\d{2}\s+\d{4}\s+\d{4}\s+\d{4}\s+-----', remaining_text).group(0)
        # Constructing the regular expression dynamically
        pattern = re.escape(start_header) + r".*?" + re.escape(end_header)
        # Using re.sub to remove everything from start_header to end_header
        remaining_text = re.sub(pattern, '\n', remaining_text, flags=re.DOTALL)

        remaining_text = re.sub(r'-{3,}', '', remaining_text)

    # remove footer
    transaction_pattern = r'SOLDE AU\s*\d{2}-\d{2}-\d{4}'
    # Search for the first occurrence of the transaction pattern
    match = re.search(transaction_pattern, remaining_text)

    if match:
        # remove header info
        remaining_text = remaining_text[:match.start()]
    else:
        try:
            transaction_pattern = r'Belfius Banque'
            # Search for the first occurrence of the transaction pattern
            match = re.search(transaction_pattern, remaining_text)

            if match:
                # remove header info
                remaining_text = remaining_text[:match.start()]
        except:
            print("error: couldn't remove footer")


    return remaining_text


def split_transactions(remaining_text):
    final_list = []
    # Define the regex pattern
    pattern = r'(\d+\s+\d{2}-\d{2}-\d{4})'

    # Use re.split() with the pattern in parentheses to keep the delimiter
    result = re.split(pattern, remaining_text)

    # Remove any empty strings from the list (optional)
    result = [item for item in result if item.strip()]
    # Iterate over the list, taking even and odd index pairs
    concatenated_list = []
    for i in range(0, len(result), 2):
        # Concatenate the current even-indexed string with the following odd-indexed string
        concatenated_string = result[i] + " " + result[i + 1]
        concatenated_list.append(concatenated_string)

    # Remove empty strings and print the results
    return [transaction.strip() for transaction in concatenated_list if transaction.strip()]


# Load the .env file
load_dotenv()
# Access the PDF_FILES_PATH variable
input_folder_path = os.getenv('PDF_FILES_PATH')
input_folder_path = input_folder_path.replace('\\', '/')
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

    # Checking extracted text to find transaction pattern
    #pdf_text[:1000]

    text = pdf_text
    # Extract client information
    #client_name = re.search(r'M M ALLARD - ROLAND', text).group()
    #client_number = re.search(r'N° client : (\d+ \d+)', text).group(1)
    try:
        iban = re.search(r'([A-Z]{2}\d{2}\s+\d{4}\s+\d{4}\s+\d{4})', text).group(1)
        bic = re.search(r'BIC:\s(\w+)', text).group(1)
    except:
        print("Couldn't retrieve IBAN and BIC")

    # Define the regex pattern
    pattern = r'SOLDE AU\s*\d{2}-\d{2}-\d{4}'
    # Search for all patterns in the text
    matches = re.findall(pattern, text)

    if matches:
        # Get the firstmatch
        iban_match = matches[-1]
        # Cut the text from the first pattern onwards, including the pattern itself
        cut_text = text[text.index(iban_match):]
        # find current year
        pattern_year = r'SOLDE AU\s*\d{2}-\d{2}-\d{4}'
        match_year = re.search(pattern_year, text)
        if match_year:
            current_year = match_year.group(0)
            current_year = current_year[-4:]
        else:
            current_year = '9999'
    else:
        current_year = '9999'
    '''
    # Extract current and previous balance
    match_date = re.search(r"Date\s*:\s*\d{2}-\d{2}-\d{4}", text)
    if match_date:
        matched_date = match_date.group()
        current_balance_date = re.search(r'\s*:\s*\d{2}-\d{2}-\d{4}', matched_date).group(0)
    else:
        current_balance_date = "Unknown"

    try:
        current_balance = re.search(r'Solde actuel [+-]\d{1,3}(\.\d{3})*,\d{2}', text).group(0)
        current_balance_amount = re.search(r'[+-]?\d{1,3}(\.\d{3})*,\d{2}', current_balance).group(0)
    except:
        try:
            current_balance = re.search(r'Solde actuel [+-]\d{1,3}(,\d{2})', text).group(0)
            current_balance_amount = re.search(r'[+-]\d{1,3}(,\d{2})', current_balance).group(0)
        except:
            current_balance = re.search(r'Solde actuel [+-]\d{1,3}(\.\d{3})*,\d{2}', text).group(0)
            current_balance_amount = re.search(r'[+-]\d{1,3}(\.\d{3})*,\d{2}', current_balance).group(0)
    try:
        previous_balance = re.search(r'Solde précédent [+-]\d{1,3}(\.\d{3})*,\d{2}', text).group(0)
        previous_balance_amount = re.search(r'[+-]\d{1,3}(\.\d{3})*,\d{2}', previous_balance).group(0)
    except:
        try:
            previous_balance = re.search(r'Solde précédent [+-]\d{1,3}(,\d{2})', text).group(0)
            previous_balance_amount = re.search(r'[+-]\d{1,3}(,\d{2})', previous_balance).group(0)
        except:
            previous_balance = re.search(r'Solde précédent [+-]\d{1,3}(\.\d{3})*,\d{2}', text).group(0)
            previous_balance_amount = re.search(r'[+-]\d{1,3}(\.\d{3})*,\d{2}', previous_balance).group(0)
    '''

    ## remove headers and footer
    remaining_text = remove_headers_footers(text)

    # split transactions
    final_transaction_list.extend(split_transactions(remaining_text))

# convert transaction list to df
transaction_df = pd.DataFrame(columns=['date', 'trans_id', 'comment'])
for i, el in enumerate(final_transaction_list):
    #transaction_id += 1
    ## Find date in the format "dd-mm"
    pattern = r"\b\d{2}-\d{2}\b"
    # Search for the first occurrence of any date pattern
    try:
        matched_date = re.search(pattern, el).group()
    except:
        matched_date = re.search(r"\d{2}-\d{2}", el).group()

    # remove sub-headers
    transaction_pattern = r'\d+\s+\d{2}-\d{2}-\d{4}'
    # Search for the first occurrence of the transaction pattern
    match = re.search(transaction_pattern, el)
    if match:
        transaction_id = match.group()[0:4]
    else:
        transaction_id = i + 1

    transaction_date = "{}-{}".format(matched_date, str(current_year))
    transaction_df = pd.concat([transaction_df,
                                   pd.DataFrame([{'date': transaction_date,
                                                  'trans_id': transaction_id,
                                                  'comment': el}])],
                                  ignore_index=True)

# Convert 'date' column to datetime format
transaction_df['date'] = pd.to_datetime(transaction_df['date'], format='%d-%m-%Y')
# Sort the DataFrame by 'date' in ascending order
transaction_df = transaction_df.sort_values(by='date')
# Reset the index if desired
transaction_df.reset_index(drop=True, inplace=True)

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