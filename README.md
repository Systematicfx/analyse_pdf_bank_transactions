# Bank PDF Transactions to XLS Converter

## Overview

This app is designed to convert your PDF bank transactions, extracted from your bank website, into Excel (`.xls`) files. Currently, the app supports transactions from Axa, Crelan, and Fortis banks.

Additionally, the app extracts transaction details such as the "comment" and "counterparty" and automatically categorizes each transaction based on predefined dictionaries of categories. The categorization can be enriched with GPT for custom categories.

Let's be clear: the code is not polished or optimized. It was developed quickly to address the immediate need of analyzing bank transaction PDF files. While the current functionality meets this need, the code could benefit from refactoring to improve its readability, structure, and overall quality.

## Features

- **Convert PDF Transactions**: Converts PDF bank statements into Excel format.
- **Automatic Categorization**: Categorizes transactions based on predefined dictionaries.
- **Custom Category Enrichment with GPT**: Enrich the categorization by adding your own categories using GPT.

## Supported Banks

- Axa
- Crelan
- Fortis

## Procedure

- The full following procedure could be fully automated using an OpenAi api.

### Summary of Instructions:
1. **Edit the `.env`** file for the folder path where your PDFs are located.
2. **Run the relevant script** for your bank (Axa, Crelan, or Fortis).
3. **Enrich categories** by extracting comments and using GPT for custom categorizations.
4. **Update the script** with your new categories and re-run it to get categorized transactions.

### A) Generate Transactions

1. **Update the `.env` file**:
   - Set the `PDF_FILES_PATH` variable to the folder where your PDF bank files are located.
     ```bash
     PDF_FILES_PATH=/path/to/your/pdf/files
     ```

2. **Run the appropriate script for your bank**:
   - For Axa: `pdf_bank_transactions_axa.py`
   - For Crelan: `pdf_bank_transactions_crelan.py`
   - For Fortis: `pdf_bank_transactions_fortis.py`

   Example:
   ```bash
   python pdf_bank_transactions_axa.py
   

Here is the full Bank PDF Transactions to XLS Converter README in .md format:

markdown
Copier le code
# Bank PDF Transactions to XLS Converter

## Overview

This app is designed to convert your PDF bank transactions, extracted from your bank website, into Excel (`.xls`) files. Currently, the app supports transactions from Axa, Crelan, and Fortis banks.

Additionally, the app extracts transaction details such as the "comment" and "counterparty" and automatically categorizes each transaction based on predefined dictionaries of categories. The categorization can be enriched with GPT for custom categories.

## Features

- **Convert PDF Transactions**: Converts PDF bank statements into Excel format.
- **Automatic Categorization**: Categorizes transactions based on predefined dictionaries.
- **Custom Category Enrichment with GPT**: Enrich the categorization by adding your own categories using GPT.

## Supported Banks

- Axa
- Crelan
- Fortis

## Procedure

### A) Generate Transactions

1. **Update the `.env` file**:
   - Set the `PDF_FILES_PATH` variable to the folder where your PDF bank files are located.
     ```bash
     PDF_FILES_PATH=/path/to/your/pdf/files
     ```

2. **Run the appropriate script for your bank**:
   - For Axa: `pdf_bank_transactions_axa.py`
   - For Crelan: `pdf_bank_transactions_crelan.py`
   - For Fortis: `pdf_bank_transactions_fortis.py`

   Example:
   ```bash
   python pdf_bank_transactions_axa.py
   
### B) Enrich Custom Categories with GPT
1. **Extract comments**:

    After running the script, locate the file transactions_enriched_categorized.csv generated in the folder.
    Extract all results from the "comment" column and paste them into a .txt file.

2. **Use GPT for categorization**:

    Open ChatGPT, load the .txt file, and send the following prompt (customize it by adding your own categories, such as your name):
   
    from the file attached, can you identify all businesses, companies, names and person, and add them (as they are without correction) as lists in the dictionary of categories:
   - **Groceries**: Transactions at supermarkets, grocery stores, etc.
   - **Utilities**: Payments for electricity, water, gas, etc.
   - **Rent**: Payments for rent or deposits for housing.
   - **Dining**: Transactions at restaurants, cafes, etc.
   - **Entertainment**: Payments for movies, concerts, etc.
   - **Healthcare**: Payments for pharmacies, clinics, etc.
   - **Transport**: Payments for fuel, public transport, etc.
   - **Shopping**: Transactions at retail stores, online shopping, etc.
   - **Materials**: transactions at DIY stores, handiwork, renovation equipment, garden...
   - **"FirstName LastName"**
   - **Miscellaneous**: Any other transactions that don’t fit into the above categories.

   Verify the lists values and categories suggested by GPT and adapt if necessary

### C) Run the Script and Get Results

1. **Re-run the script**:

- After enriching your categories, run the script again.

2. **Locate the results**:

Find the categorized transactions in the following files:
- transactions_enriched_categorized.csv (all transactions)
- transactions_enriched_categorized_pos_amounts.csv (positive amounts)
- transactions_enriched_categorized_neg_amounts.csv (negative amounts)