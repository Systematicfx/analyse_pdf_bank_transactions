
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

# Define function to extract transaction type
def extract_transaction_type(comment):
    if "Paiement par carte de débit" in comment:
        return "Paiement par carte de débit"
    elif "Virement" in comment:
        return "Virement"
    elif "Retrait d'espèces" in comment:
        return "Retrait d'espèces"
    elif "Redevance" in comment:
        return "Redevance"
    elif "Domiciliation" in comment:
        return "Domiciliation"
    else:
        return ""


# Define function to extract communication
def extract_communication(comment):

    test = re.findall("2403041658015445", comment)
    num_matches = len(test)
    if num_matches > 0:
        print("test")
    # Define the regex pattern for ref bank
    communication = r'Communication :'
    # Search for all ref bank patterns in the text
    communication_matches = re.findall(communication, comment)
    # find text between communication and ref bank
    if communication_matches:
        # Get the last match
        communication_match = communication_matches[0]
        # Find the end index of the last communication match
        communication_end_index = comment.index(communication_match) + len(communication_match)
        # Cut the text from the end of the last communication pattern onwards (not including the 'communication' itself)
        cut_text_after_communication = comment[communication_end_index:].strip()
        # Now find all ref_bank patterns in the remaining text
        ref_bank_pattern = r'Référence banque : \d{16}'
        all_ref_bank_matches = re.findall(ref_bank_pattern, cut_text_after_communication)

        if all_ref_bank_matches:
            # Get the last ref_bank match
            last_ref_bank_match = all_ref_bank_matches[-1]
            # Cut the text from the last ref_bank pattern onwards, including the pattern itself
            cut_text_ref_bank = cut_text_after_communication[:cut_text_after_communication.index(last_ref_bank_match)]
            return cut_text_ref_bank
        else:
            return cut_text_after_communication

    lines = comment.split('\n')
    if ("Paiement par carte de débit" in comment) or ("Retrait d'espèces" in comment):
        # Define the regex pattern for bancontact
        bancontact = r'Bancontact'
        # Search for all bancontact patterns in the text
        bancontact_matches = re.findall(bancontact, comment)
        # find text between "apiement" or "retrait" and bancontact

        # Define the regex pattern for Visa Debit
        visa = r'Visa Debit'
        # Search for all bancontact patterns in the text
        visa_matches = re.findall(visa, comment)
        # find text between "apiement" or "retrait" and bancontact
        if bancontact_matches:
            # Get the first match
            bancontact_match = bancontact_matches[0]
            # Find the end index of the last communication match
            bancontact_index = comment.index(bancontact_match)
            # Cut the text
            text_before_bancontact = comment[:bancontact_index].strip()
            # Now find all ref_bank patterns in the remaining text
            lines = text_before_bancontact.split('\n')
            # Join the elements with a newline character
            joined_text = "\n".join(lines[1:])
            return joined_text  # Communication info is usually in the second line
        elif visa_matches:
            # Get the first match
            visa_match = visa_matches[0]
            # Find the end index of the last communication match
            visa_index = comment.index(visa_match)
            # Cut the text
            text_before_visa = comment[:visa_index].strip()
            # Now find all ref_bank patterns in the remaining text
            lines = text_before_visa.split('\n')
            # Join the elements with a newline character
            joined_text = "\n".join(lines[1:])
            return joined_text  # Communication info is usually in the second line
        else:
            return lines[1]
    elif "Virement" in comment:
        for line in lines:
            if "Communication" in line:
                return line.split("Communication : ")[-1]
    else:
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
    # Regex pattern to match amounts that contain a comma with exactly two digits after it and a mandatory "+" or "-" sign
    match_hundreds = re.search(r"([\d]+,\d{2})\s*([-+])", comment)
    match_thousands = re.search(r"\d{1,3}(\.\d{3})*,\d{2}\s*([-+])", comment)
    #if throusand
    if match_hundreds is not None and match_thousands is not None:
        if len(match_thousands.group(0)) > len(match_hundreds.group(0)):
            amount = match_thousands.group(0).replace(".", "").replace(",",
                                                             ".").replace(" {}".format(match_thousands.group(2)), "")  # Remove thousand separators (dots) and convert comma to dot
            sign = match_thousands.group(2)  # Capture the mandatory "+" or "-" sign
            return f"-{amount}" if sign == '-' else amount
        else: # match_hundreds
            amount = match_hundreds.group(1).replace(",", ".")  # Capture the number, replace the comma with a period for decimal
            sign = match_hundreds.group(2)  # Capture the mandatory "+" or "-" sign
            return f"-{amount}" if sign == '-' else amount

    print("Error: no amount found for comment '{}".format(comment))
    return 0


def extract_counterparty(comment):
    # Define the regex pattern for IBAN
    iban_pattern = r'[A-Z]{2}\d{2}\s\d{4}\s\d{4}\s\d{4}\s{1,2}[A-Z]{3}'

    # Search for all IBAN patterns in the text
    iban_matches = re.findall(iban_pattern, comment)
    if iban_matches:
        # Get the last IBAN match
        iban_match = iban_matches[-1]
        # Cut the text from the last IBAN pattern onwards, including the pattern itself
        cut_text_after_iban = comment[comment.index(iban_match):]
        #print(f"Last IBAN match found: {iban_match}")
        #print(f"Text after last IBAN match: {cut_text_after_iban}")

        # Now find all date patterns in the remaining text
        date_pattern = r'\d{2}-\d{2}'
        all_date_matches = re.findall(date_pattern, cut_text_after_iban)

        if all_date_matches:
            # Get the last date match
            last_date_match = all_date_matches[-1]
            # Cut the text from the last date pattern onwards, including the pattern itself
            cut_text_after_date = cut_text_after_iban[:cut_text_after_iban.index(last_date_match)]
            #print(f"Last date pattern found: {last_date_match}")
            #print(f"Text after last date match: {cut_text_after_date}")
            return cut_text_after_date
        else:
            #print("No date patterns found in the text after the last IBAN.")
            return cut_text_after_iban
    else:
        # Define the regex pattern for ref bank
        ref_bank_pattern = r'Référence banque : \d{16}'

        # Search for all ref bank patterns in the text
        ref_bank_matches = re.findall(ref_bank_pattern, comment)
        if ref_bank_matches:
            # Get the last ref bank match
            ref_bank_match = ref_bank_matches[-1]
            # Find the end index of the last IBAN match
            ref_bank_end_index = comment.index(ref_bank_match) + len(ref_bank_match)
            # Cut the text from the end of the last IBAN pattern onwards (not including the IBAN itself)
            cut_text_after_ref_bank = comment[ref_bank_end_index:].strip()
            # Now find all date patterns in the remaining text
            date_pattern = r'\d{2}-\d{2}'
            all_date_matches = re.findall(date_pattern, cut_text_after_ref_bank)

            if all_date_matches:
                # Get the last date match
                last_date_match = all_date_matches[-1]
                # Cut the text from the last date pattern onwards, including the pattern itself
                cut_text_after_date = cut_text_after_ref_bank[:cut_text_after_ref_bank.index(last_date_match)]
                #print(f"Last date pattern found: {last_date_match}")
                #print(f"Text after last date match: {cut_text_after_date}")
                return cut_text_after_date
            else:
                #print("No date patterns found in the text after the last IBAN.")
                return cut_text_after_ref_bank
        #print("No patterns found in the text.")
        return ""

    '''
    # Define the regex patterns
    iban_pattern = r'BE\d{2}\s\d{4}\s\d{4}\s\d{4}\s{1,2}[A-Z]{3}'
    date_pattern = r'\d{2}-\d{2}'

    comment = """Virement en euros via Easy Banking Web 
    Date d'exécution : 30-06-2024
    Communication : 931/3687/38570
    Référence banque : 2406301710212344BE76 3350 5545 9895  EUR
    BBRUBEBB 01-07
    Référence banque : 2406301710212344BE76 8750 5596 9295  USD
    EDF Luminus SA01-07 10,00 -"""

    # Find all matches of the IBAN pattern in the text
    iban_matches = re.findall(iban_pattern, comment)
    #num_matches = len(iban_matches)
    last_match = iban_matches[-1]
    # Find the IBAN-like match
    iban_match = re.search(last_match, comment)

    # Check if an IBAN match is found
    if iban_match:
        # Get the matched IBAN
        iban_value = iban_match.group()

        # Get the start index of the IBAN match
        start_index = iban_match.end()

        # Search for the date pattern after the IBAN match
        # Find all matches of the IBAN pattern in the text
        date_matches = re.findall(date_pattern, comment[start_index:])
        num_date_matches = len(date_matches)
        last_date_match = date_matches[-1]
        # Find the IBAN-like match
        date_match = re.search(last_date_match, comment[start_index:])

        #date_match = re.search(date_pattern, comment[start_index:])

        if date_match:
            # Extract the text between the IBAN and the date
            text_between = comment[start_index:start_index + date_match.start()].strip()
            # Combine the IBAN and the text
            result = f"{iban_value} {text_between}"
            return result
        else:
            return comment[iban_match.start():]
    else:
        return ""

    '''


# Load the .env file
load_dotenv()
# Access dotenv variable
input_folder_path = os.getenv('PDF_FILES_PATH')
language = os.getenv('LANGUAGE')
if language != "French":
    print('Warning: nltk packages are in French. It can be easily changed though, lookup and change parameter "language=french"')

#input_folder_path = 'E:/LaptopBackUp/Administrative/Banques/Fortis/Commun/2021/test/'

custom_text_remove = ['Les dépôts sont éligibles pour la protection. Plus d’informations via votre contact habituel ou sur bnpparibasfortis.be/garantiedepots',
                      'Tél. 02 762 20 00 - Card Stop: 078 170 170 - www.bnpparibasfortis.be3/3']

#reader = PdfReader(pdf_path)

pdf_folder = Path(input_folder_path)
final_transaction_list = []
error_transaction = pd.DataFrame(columns=['date', 'trans_id', 'comment'])
error_amount = pd.DataFrame(columns=['comment', 'amount'])
# Loop through all PDFs in the folder
for pdf_file in pdf_folder.glob('*.pdf'):
    # Open and process each PDF
    print(f'Processing file: {pdf_file}')

    # Create a PdfReader object
    reader = PdfReader(pdf_file)

    # Extracting information (for example, the number of pages)
    num_pages = len(reader.pages)
    #print(f'Number of pages in {pdf_file.name}: {num_pages}')

    # Example: Extract text from all pages
    #for page_num in range(num_pages):
    #    page = reader.pages[page_num]
    #    text = page.extract_text()
    #    print(f'Text from page {page_num + 1} of {pdf_file.name}:\n{text}\n')


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
    client_name = re.search(r'M M ALLARD - ROLAND', text).group()
    client_number = re.search(r'N° client : (\d+ \d+)', text).group(1)
    iban = re.search(r'([A-Z]{2}\d{2} \d{4} \d{4} \d{4})', text).group(1)
    bic = re.search(r'BIC (\w+)', text).group(1)

    # Extract current and previous balance
    try:
        current_balance = re.search(r'Solde actuel au (\d{2}-\d{2}-\d{4}) (\d+,\d{2})', text).groups()
    except:
        current_balance = re.search(r'Solde actuel au (\d{2}-\d{2}-\d{4}) \d{1,3}(\.\d{3})*,\d{2}', text).groups()
    try:
        previous_balance = re.search(r'Solde précédent au (\d{2}-\d{2}-\d{4}) (\d+,\d{2})', text).groups()
    except:
        previous_balance = re.search(r'Solde précédent au (\d{2}-\d{2}-\d{4}) \d{1,3}(\.\d{3})*,\d{2}', text).groups()
    # Define the transaction pattern
    transaction_pattern = r'(\d{2}-\d{2}-\d{4})\s+(\d{4})\s+'

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
        # Loop through each header line and remove it from the remaining text
        for line in header_lines:
            remaining_text = remaining_text.replace(line, "").strip()
        # Loop through each ignored sentences and remove it from the remaining text
        for line in custom_text_remove:
            remaining_text = remaining_text.replace(line, "").strip()
            # remove ignored sentences
        # Define the regex pattern
        regex_pattern = [r'Tél\. 02 762 20 00 - Card Stop: 078 170 170 - www\.bnpparibasfortis\.be\d+/\d+',
                   r"Tél\. \d{2} \d{3} \d{2} \d{2} - Card Stop: \d{3} \d{3} \d{3} - www\.bnpparibasfortis\.be\d+/\d+"]
        for pattern in regex_pattern:
            remaining_text = re.sub(pattern, '', remaining_text)
        #'r\'Tél\\. 02 762 20 00 - Card Stop: 078 170 170 - www\\.bnpparibasfortis\\.be\\d+/\\d+\''
        # Replace the pattern with an empty string
        #for line in custom_regex_remove:
            # Use repr() to get the escaped representation, but strip the outer quotes
            #raw_like_string = repr(line)[1:-1]

            # Replace double backslashes (\\) with single backslashes (\) dynamically
            #raw_like_string = raw_like_string.replace('\\\\', '\\')

            # Prefix with r' and suffix with a single quote to make it look like a raw string
            #final_string = f"r'{raw_like_string}'"
            #remaining_text = remaining_text.replace(final_string, "").strip()
            # Remove the double backslashes
            #line = line.replace('\\\\', '\\')
            # Remove the 'r\' at the start if present
            #if line.startswith("r'"):
            #    line = line[2:]



        # date + id
        transaction_pattern = r'(\d{2}-\d{2}-\d{4})\s+(\d{4})\s+'
        # Split the remaining text based on the transaction pattern
        split_transactions = re.split(transaction_pattern, remaining_text)

        # Remove empty strings and print the results
        split_transactions = [transaction.strip() for transaction in split_transactions if transaction.strip()]

        # find pattern: "..............................................................  0276  "
        sub_transaction_pattern = r'\.+\s*(\d{4})\s*'
        last_date_pattern = r'^(\d{2}-\d{2}-\d{4})$'
        last_trans_id_pattern = r'^(\d{4})$'
        # when a new page code 0276 is not preceded by dot
        # e.g: in 'E:/LaptopBackUp/Administrative/Banques/Fortis/Commun/2024/pdfData (23).pdf'
        end_of_page_pattern = r',\d{2} [+-]'

        for trans in split_transactions:
            # keep last date
            if re.search(last_date_pattern, trans):
                last_date = trans
            if re.search(last_trans_id_pattern, trans):
                last_trans_id = trans
            # if sub_match: we have several transactions that day, we need to split and add them
            sub_match = re.search(sub_transaction_pattern, trans)
            if sub_match:
                #print('test')
                split_sub_transactions = re.split(sub_transaction_pattern, trans)
                final_transaction_list.append(split_sub_transactions[0])
                for i, el in enumerate(split_sub_transactions):
                    if i > 0:
                        if i % 2 != 0:  # This checks if i is odd
                            final_transaction_list.append(last_date)
                            final_transaction_list.append(split_sub_transactions[i])
                            final_transaction_list.append(split_sub_transactions[i + 1])
                            match_end_page = re.search(end_of_page_pattern, split_sub_transactions[i + 1])
                            if match_end_page:
                                split_end_page = re.split(end_of_page_pattern, split_sub_transactions[i + 1])
                                if len(split_end_page) > 2:
                                    print('possible error: 1 transaction stuck in one comment')
                                    error_transaction = pd.concat([error_transaction,
                                               pd.DataFrame([{'date': last_date,
                                                              'trans_id': last_trans_id,
                                                              'comment': split_sub_transactions[i + 1]}])],
                                              ignore_index=True)
                                    #error_transaction = error_transaction.append(
                                    #    {'date': last_date, 'trans_id': last_trans_id,
                                    #     'comment': split_sub_transactions[i + 1]},
                                    #    ignore_index=True)
            else:
                match_end_page = re.search(end_of_page_pattern, trans)
                if match_end_page:
                    split_end_page = re.split(end_of_page_pattern, trans)
                    if len(split_end_page) > 2:
                        print('possible error: 1 transaction stuck in one comment')
                        error_transaction = pd.concat([error_transaction,
                                                       pd.DataFrame([{'date': last_date,
                                                                      'trans_id': last_trans_id,
                                                                      'comment': trans}])],
                                                      ignore_index=True)
                final_transaction_list.append(trans)

# convert transaction list to df
transaction_df = pd.DataFrame(columns=['date', 'trans_id', 'comment'])
for i, el in enumerate(final_transaction_list):
    if i == 0 or i % 3 == 0:
        transaction_df = pd.concat([transaction_df,
                                       pd.DataFrame([{'date': final_transaction_list[i],
                                                      'trans_id': final_transaction_list[i+1],
                                                      'comment': final_transaction_list[i+2]}])],
                                      ignore_index=True)

errors_output_file = os.path.join(input_folder_path, 'error_transaction.csv')
try:
    error_transaction.to_csv(
        errors_output_file,
        index=False,
        sep=',',
        encoding='utf-8-sig',
    )
except:
    print("error permmission denied: 'error_transaction.csv' seems to be already open, please close the file")
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

# Convert 'date' column to datetime format
transaction_df['date'] = pd.to_datetime(transaction_df['date'], format='%d-%m-%Y')
# Sort the DataFrame by 'date' in ascending order
transaction_df = transaction_df.sort_values(by='date')
# Reset the index if desired
transaction_df.reset_index(drop=True, inplace=True)

# Display or save the result
# os.path.join(os.path.dirname(pdf_path)
output_file_path = os.path.join(input_folder_path, 'transactions_enriched.csv')
transaction_df.to_csv(output_file_path, index=False)
if transaction_df.empty:
    print("No transaction found")
# Apply the categorization function to the DataFrame
categories_exact_match, categories_fuzzy = get_categories()
transaction_df['exact keyword'] = ""
transaction_df['regex exact keyword'] = ""
transaction_df['fuzzy keyword'] = ""
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