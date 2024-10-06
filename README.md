# Bank PDF Transactions to XLS Converter

## Overview

This app is designed to convert your PDF bank transactions, extracted from your bank website, into Excel (`.xls`) files. Currently, the app supports transactions from Axa, Crelan, Belfius and Fortis banks.

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
- Belfius

## Installation
    
- clone the repo
- Install **_requirements.txt_**:
  in your env `pip install -r /path/to/requirements.txt`
- install ntlk corpora:
  `python -m nltk.downloader all` (https://www.nltk.org/data.html)
  
## Procedure

- The full following procedure could be fully automated using an OpenAi api.

### Summary of Instructions:
1. **Edit the `.env`** file for the folder path where your PDFs are located.
2. **Run the relevant script** for your bank (Axa, Crelan, Belfius or Fortis).
3. **Enrich categories** using GPT for custom categorizations for comments.
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
   - For Belfius: `pdf_bank_transactions_belfius.py`

   Example:
   ```bash
   python pdf_bank_transactions_axa.py

### B) Enrich Custom Categories with GPT

1. **Extract comments**:

   After running the script, a file `comments_GPT.txt` is generated in the source folder 
   including all transactions' comments.

2. **Use GPT for categorization**:

    Open ChatGPT, load the .txt file, and send the following prompt (customize it by adding your own categories, such as your name):
   
```
    from the file attached, can you identify all businesses, companies, names and person, and add them (as they are without correction) as lists in the dictionary of categories:

   - Groceries: Transactions at supermarkets, grocery stores, etc.
   - Utilities: Payments for electricity, water, gas, etc.
   - Rent: Payments for rent or deposits for housing.
   - Dining: Transactions at restaurants, cafes, etc.
   - Entertainment: Payments for movies, concerts, etc.
   - Healthcare: Payments for pharmacies, clinics, etc.
   - Transport: Payments for fuel, public transport, etc.
   - Shopping: Transactions at retail stores, online shopping, etc.
   - Materials: transactions at DIY stores, handiwork, renovation equipment, garden...
   - "FirstName LastName":
   - Miscellaneous: Any other transactions that don’t fit into the above categories.
```

   Verify the lists values and categories suggested by GPT and adapt if necessary

### C) Run the Script and Get Results

1. **Enrich the matching dictionary**:

- In the `script matching_algos.py`, enrich your categories from GPT in the dictionaries:
  - 1) `categories_exact_match`: will try to find exact matches from keywords of each category to categorize the transactions
  - 2) `categories_belgium` and `categories_france`: will use matching algorithms to match keywords of each category to categorize the transactions
- Be aware, the matching goes through all categories of the dic so that less important categories must be located at the beginning
of the dictionary and the most important as last keys of the dic.

2. **Re-run the script**:

- After enriching your categories in the dic, run the script again.
- You can reproduce the process several times to refine you dictionaries

3. **Locate the results**:

Find the categorized transactions in the following files:
- transactions_enriched_categorized.csv (all transactions)
- transactions_enriched_categorized_pos_amounts.csv (positive amounts)
- transactions_enriched_categorized_neg_amounts.csv (negative amounts)

Few precisions about the fields in the xls.
Fields related to your transactions:

   - **date**: transaction date
   - **trans_id**: transaction id
   - **comment**: full transaction text
   - **transaction type**: type of transaction
   - **Communication**: communication extracted from your transaction text
   - **Amount**: transaction amount
   - **Counterparty**: transaction's counterparty
     
Additional fields:
   - **exact keyword**: keyword found in category when exact match algo
   - **regex exact keyword**: keyword found in category when exact match regex algo
   - **fuzzy keyword**: keyword found in category when algo matching 
   - **Categorized**: if transaction could be cotegorised
   - **Category**: first category found
   - **SubCategory**: next categories found

4. **Analyse the results**:

Open the xls files (I suggest to open xls split by negative and positive amounts separately),
select all data and insert a pivot table:

![img_1.png](img_1.png)

Ii suggest to use:
- as rows: `Category` and `transaction type`
- as values: `Amount`

![img_2.png](img_2.png)

You can perform deeper analysis using other fields available in the pivot table.
You drilldown on specific transactions and enrich the classification dictionnary if transactions were misclassified.
