
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
from collections import defaultdict
from fuzzywuzzy import fuzz
#from sentence_transformers import SentenceTransformer, util
import Levenshtein

import re
import string
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer  # For stemming
from nltk.stem import WordNetLemmatizer  # For lemmatization
from fuzzywuzzy import fuzz
from itertools import chain

# Make sure to download the stopwords and punkt packages if you haven't already
import nltk
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
    iban_pattern = r'BE\d{2}\s\d{4}\s\d{4}\s\d{4}\s{1,2}[A-Z]{3}'

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


def get_categories():
    def aggregate_dictionaries(*dicts):
        aggregated_dict = defaultdict(set)  # Use a set to automatically handle duplicates

        # Loop through each dictionary
        for dic in dicts:
            for key, values in dic.items():
                aggregated_dict[key].update(values)  # Add values to the set for each key

        # Convert the sets back to lists
        return {key: list(values) for key, values in aggregated_dict.items()}

    categories_belgium = {
        'Groceries': [
            'Fruits', 'Vegetables', 'Dairy and Eggs', 'Meat and Poultry', 'Fish and Seafood',
            'Grains and Bread', 'Canned and Jarred Goods', 'Frozen Foods', 'Condiments and Spices',
            'Snacks and Sweets', 'Beverages', 'Baking Ingredients', 'Colruyt', 'Delhaize',
            'Carrefour', 'Aldi', 'Lidl', 'SPAR', 'Intermarché', 'Bio-Planet', 'Cru', 'DreamBaby',
            'Dreamland', 'OKay', 'OKay Compact'
        ],
        'Utilities': [
            'Electricity', 'Water', 'Gas', 'Sewage', 'Internet', 'Telephone', 'Waste Disposal',
            'Engie Electrabel', 'TotalEnergies', 'Luminus', 'Mega', 'Eneco', 'Octa+', 'Trevion', 'Aspiravi Energy',
            'Bolt', 'Cociter', 'DATS 24', 'Ebem', 'Elegant', 'Energie.be', 'Frank Energie', 'Wind voor "A"'
        ],
        'Rent': [
            'Mortgage Payments', 'Property Taxes', 'Home Maintenance Costs', 'HOA Dues',
            'Belcar Antwerpen', 'Bia Vlaams Brabant', 'Louyet Hainaut', 'Avery Dennison Materials Belgium',
            'Hilti Belgium', 'Louyet Automotive North', 'Trelleborg Wheel Systems – Belgium', 'Global Safety',
            'Chep Benelux', 'Atlas Copco Belgium', 'Bridgestone Aircraft Tire (Europe)', 'nVent Thermal Belgium',
            'Boels Verhuur', 'Rent 4 Less', 'VP Lam Holding', 'Dem Group', 'Vancia Car Lease', 'Arval Belgium',
            'Bandenbedrijf Vandekerckhove', 'Donckers', 'D’Ieteren Lease', 'Forrez International',
            'Atlas Copco Rental Europe', 'Lalemant', 'Van den Dorpe Material Handling', 'Diamond Europe', 'JCB-Belgium',
            'Locadif', 'Lambrecht Nummer een In Banden', 'Koffie F. Rombouts', 'Beliën Neerpelt', 'Stappert Intramet',
            'Grenke Lease', 'Weg Benelux S.A.', 'Reesink Construction Equipment Belgium', 'Directlease',
            'Heidelberg Benelux', 'Leaseplan Fleet Management', 'Alphabet Belgium Long Term Rental', 'ALSO Belgium',
            'Hyundai Construction Equipment Europe', 'Michelin Belux', 'Van Hool', 'Chep Equipment Pooling',
            'Axus Finance', 'Keyence International (Belgium)', 'BERGERAT MONNOYEUR', 'VAB', 'Victaulic Europe BV',
            'Mercedes-Benz Financial Services Belux'
        ],
        'Dining': [
            'Restaurants', 'Cafes', 'Fast Food', 'Takeout', 'Delivery Services',
            'The Jane', 'Hof Van Cleve', 'La Bonne Chère', 'Boury', 'Zilte', 'Ivresse', 'The Jane Antwerp',
            'Hof Van Cleve Kruisem', 'La Bonne Chère Brussels', 'Boury Roeselare', 'Zilte Antwerp', 'Ivresse Uccle'
        ],
        'Entertainment': [
            'Movies', 'Concerts', 'Theater', 'Amusement Parks', 'Sporting Events',
            'Streaming Services', 'Video Games', 'Books', 'Music', 'Dragone', 'Studio 100', 'Kinepolis Group',
            'D&D Productions', 'Woestijnvis', 'Lumière', 'Caviar', 'Eyeworks', 'De Mensen', 'Fobic Films'
        ],
        'Healthcare': [
            'Doctor Visits', 'Pharmacy', 'Health Insurance', 'Dental Care', 'Vision Care',
            'Mental Health Services', 'Medical Equipment', 'Vaccinations',
            'UCB SA', 'Financière de Tubize SA', 'Galapagos NV', 'Fagron NV', 'Ion Beam Applications SA', 'Nyxoah SA',
            'MDxHealth SA', 'Sequana Medical NV', 'Mithra Pharmaceuticals SA', 'Celyad Oncology SA'
        ],
        'Transport': [
            'Fuel', 'Public Transport', 'Car Maintenance', 'Parking Fees', 'Tolls',
            'Car Insurance', 'Ride-Sharing Services', 'H.Essers', 'Sarens', 'Jost Group', 'Deutsche Bahn',
            'Kuehne + Nagel', 'UPS', 'DSV', 'Van Moer', 'SEA-Invest', 'Euroports', 'Tabak Natie', 'Katoen Natie'
        ],
        'Shopping': [
            'Clothing', 'Electronics', 'Home Goods', 'Beauty Products', 'Toys',
            'Books', 'Jewelry', 'Sporting Goods', 'bol.com', 'coolblue.be', 'amazon.com.be', 'Zalando', 'MediaMarkt',
            'Vanden Borre', 'Fnac', 'IKEA', 'H&M', 'Decathlon', 'ZEB', 'JBC', 'Veritas', 'C&A', 'Primark'
        ],
        'Miscellaneous': [
            'Gifts', 'Donations', 'Subscriptions', 'Pet Care', 'Hobbies',
            'Office Supplies', 'Travel Expenses', 'Anheuser-Busch InBev', 'Umicore', 'KBC Group', 'Solvay S.A.', 'Colruyt Group',
            'Ageas', 'Groupe Bruxelles Lambert', 'Viohalco', 'Proximus', 'Bekaert', 'UCB', 'Belfius'
        ],
        'Materials': [
            "Brico",
            "Hubo",
            "Gamma",
            "Mr. Bricolage",
            "Makro",
            "Gedimat",
            "BigMat",
            "Facq",
            "Van Marcke",
            "Sanitairwinkel",
            "Cevo",
            "Cebeo",
            "Desimpel",
            "Willemen Groep",
            "Matériaux Pierret"
        ],
        'Roland Steven': [
            'Steven Roland', 'Roland Steven'
        ],
        'ALLARD BENEDICTE': [
            'BENEDICTE ALLARD', 'ALLARD BENEDICTE'
        ]
    }


    categories_france = {
            'Groceries': [
                'E.Leclerc', 'Carrefour', 'Les Mousquetaires (Intermarché, Netto)', 'Système U', 'Auchan',
                'Casino', 'Lidl', 'Aldi', 'Cora', 'Monoprix'
            ],
            'Utilities': [
                'EDF', 'Engie', 'Veolia', 'TotalEnergies', 'Neoen', 'Rubis', 'Albioma', 'Voltalia',
                'Electricité de Strasbourg', 'Blue Shark Power System'
            ],
            'Rent': [
                'Foncia', 'Citya Immobilier', 'Crédit Agricole Immobilier', 'Declic Immo',
                'Cagepa', 'NCT', 'Orpi', 'Century 21', 'Laforêt', 'Guy Hoquet'
            ],
            'Dining': [
                'The Jane', 'Hof Van Cleve', 'La Bonne Chère', 'Boury', 'Zilte', 'Ivresse', 'Le Meurice',
                'Ambroisie', 'Pierre Gagnaire', 'Le Cinq'
            ],
            'Entertainment': [
                'Live Nation SAS', 'TF1 Production', 'Gérard Drouot Productions', 'Mediawan', 'Mikros Animation',
                'MPC Film & Episodic', 'Superprod', 'Newen Studios', 'Asacha Media Group'
            ],
            'Healthcare': [
                'Sanofi', 'EssilorLuxottica', 'Sartorius Stedim Biotech', 'BioMérieux', 'Ipsen', 'Virbac',
                'Ramsay Générale de Santé', 'Vetoquinol', 'ABIVAX', 'Pharmagest Interactive'
            ],
            'Transport': [
                 'CMA CGM Group', 'DB Schenker', 'GEODIS', 'Kuehne + Nagel', 'STEF Group',
                'Bolloré Group', 'Dachser', 'XPO, Inc.', 'SNCF', 'RATP'
            ],
            'Shopping': [
                 'Amazon.fr', 'Shein.com', 'Cdiscount', 'Leroy Merlin', 'Fnac', 'Darty',
                'Zalando', 'Veepee', 'La Redoute', 'Decathlon'
            ],
            'Miscellaneous': [
                 'TotalEnergies', 'BNP Paribas', 'Axa', 'Crédit Agricole', 'Sanofi',
                'Dior', 'Société Générale', 'Vinci', 'Orange', 'Oréal'
            ],
            'Materials': [
                "BHP Group",
                "Rio Tinto",
                "Vale S.A.",
                "ArcelorMittal",
                "BASF SE",
                "Dow Inc.",
                "DuPont de Nemours, Inc.",
                "Linde plc",
                "Freeport-McMoRan Inc.",
                "Anglo American plc",
                "Nucor Corporation",
                "PPG Industries, Inc.",
                "Ecolab Inc.",
                "CF Industries Holdings, Inc.",
                "International Paper Company",
                "Sealed Air Corporation",
                "Newmont Corporation",
                "Alcoa Corporation",
                "Martin Marietta Materials, Inc.",
                "Sherwin-Williams Company"
            ],
            'Roland Steven': [
                'Steven Roland', 'Roland Steven'
            ],
            'ALLARD BENEDICTE': [
                'BENEDICTE ALLARD', 'ALLARD BENEDICTE'
            ]
        }

    categories_exact_match = {
            'Groceries': [
                "AD DELHAIZE FORE VORST",
                "INTERMARCHE WAVR",
                "BK BIERGES",
                "7792 CO&GO WAVRE",
                "Poissonnerie SU",
                "Pharma Littoral",
                "SM Casino",
                "DELHAIZE WAVRE 4",
                "DELHAIZE OTTIGNI",
                "DELHAIZE LOUVAIN LA NEUVE",
                "SAKF GREZ DOICEA",
                "SALAM SPRL",
                "FABRY FOOD SPRL",
                "GLAWAV",
            ],
            'Utilities': [
                "EDF Luminus SA",
                "IECBW",
                "SODEXO PASS BELGIUM SA",
                "Brutele sc",
                "Proximus",
            ],
            'Other Charges': ["PHOTOMATIQUE",
                "Parking Brussels", "PARKING LLN",
                "Indigo Infra Bel"
            ],
            'Rent': [
            ],
            'Dining': [
                "FONFON",
                "CRF MKT WAVRE",
                "Le Transat",
                "SHOP FRAIS SPRL",
                "Zanzibar Ottignie",
                "CAFE MAISON DU P",
                "Dunkin’ Louvain",
                "Academys Elias",
                "SELECTA",
                "Le Ressac",
                "Resto Zoo",
                "Aquarium",
                "Vending Machine Maximum",
                "One of a Kind",
                "Maison Dandoy",
                "L’Art de Praslin",
                "La Casiere Ath",
                "Dumont Boulanger",
                "Blond Saint-Gi",
                "Noa Wyszegrodzki",
                "Au Chateau Magiq"
            ],
            'Entertainment': [
                "CINESCOPE BVBA",
                "LES IDEES BLEUES",
                "PS BXL NORD COULOIR B REL",
                "Spectacle Le Mans",
                "Bout du Bioparc",
                "Zoo Les Sables",
                "Suntransfers",
                "Ecole Hector - Par dela l Eau",
                "CESAM Nature",
                "BTS WAVRE"
                "Jard",
                "Les Sables",
                "LES IDEES BLEUES"
            ],
            'Healthcare': [
                "CLINIQUE ST-PIER",
                "Clin St Pierre",
                "Multipharm"
            ],
            'Transport': [
                "LUKOIL 120 WAVRE",
                "Q8 109060 WAVRE",
                "ESSO G&V WAVRE",
                "TOTAL NB000556 W WAVRE",
            ],
            'Shopping': [
                "Amazon Mrktplc",
                "La Redoute",
                "Smile&P*FRANCK LANGLAIS",
                "La Boutique de",
                "Kiabi Belgique",
                "Records Sports Ottignie",
                "HANGAR 86"
            ],
            'Materials': [
                "BRICO",
                "Belgian Minerals",
                "Benoit Delhez - Toitures",
                "Mentior Nicolas P2P Mobil",
                "Bigmat - Grez - carrelage",
                "SA CHAURACI",
                "RJ Location",
                "Auctelia",
                "Kordo"
            ],
            'Steven Roland': [
                "Roland Steven",
                "Steven Roland",
                "Services Taxes - Please des Carmes",
                "Beobank - carte Visa New"
            ],
                'Miscellaneous': [
                "Beobank Interest",
                "Services Taxes - Please des Carmes",
                "Beobank - carte Visa New",
                "Services Taxes - Please des Carmes",
                "frais compte-titres",
                "Encaissement interne",
                "crédit"
            ]
        }

    # Aggregate dictionaries
    categories_exact_match = aggregate_dictionaries(categories_exact_match, categories_axa1, categories_axa2, categories_axa3)

    # Aggregate dictionaries
    categories_fuzzy = aggregate_dictionaries(categories_belgium, categories_france)

    return categories_exact_match, categories_fuzzy


# Define a function to categorize the transactions
def categorize_transaction(transaction_df, categories_exact_match, categories_fuzzy):
    '''

    model = SentenceTransformer('paraphrase-MiniLM-L6-v2')

    def bert_match(text, word_list, threshold=0.7):
        text_embedding = model.encode(text)
        matches = []
        for word in word_list:
            word_embedding = model.encode(word)
            cosine_score = util.cos_sim(text_embedding, word_embedding)
            if cosine_score > threshold:
                return True
                #matches.append((word, cosine_score.item()))
        return False

    '''

    def regex_match(text, word_list):
        matches = []
        for word in word_list:
            pattern = re.compile(re.escape(word), re.IGNORECASE)  # Case insensitive
            if pattern.search(text):
                matches.append(word)
        return matches


    def levenshtein_match(text, word_list, threshold=3):
        matches = []
        for word in word_list:
            distance = Levenshtein.distance(word.lower(), text.lower())
            if distance <= threshold:  # Lower distance means a closer match
                return True
                #matches.append((word, distance))
        return False

    def jaccard_similarity(text, word):
        text_set = set(text.lower().split())
        word_set = set(word.lower().split())
        intersection = text_set.intersection(word_set)
        union = text_set.union(word_set)
        return len(intersection) / len(union)

    def jaccard_match(text, word_list, threshold=0.2):
        matches = []
        for word in word_list:
            score = jaccard_similarity(text, word)
            if score >= threshold:
                return True
                #matches.append((word, score))
        return False


    def fuzzy_match(text, word_list, threshold=80):
        matches = []
        for word in word_list:
            match_score = fuzz.partial_ratio(word.lower(), text.lower())
            if match_score >= threshold:
                return True
                #matches.append((word, match_score))
        return False

    from sklearn.feature_extraction.text import CountVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    import numpy as np

    def cosine_match(text, word_list, threshold=0.8):
        vectorizer = CountVectorizer().fit_transform([text] + word_list)
        vectors = vectorizer.toarray()
        csim = cosine_similarity(vectors)

        matches = []
        for i, word in enumerate(word_list):
            if csim[0][i + 1] >= threshold:
                return True
                #matches.append((word, csim[0][i + 1]))  # csim[0] is the text vector
        return False # matches

    # data in : C:\Users\Temp\AppData\Roaming\nltk_data.
    nltk.download('punkt')
    nltk.download('stopwords')
    nltk.download('wordnet')
    #nltk.download('punkt')
    # Preprocessing function
    def preprocess(text, remove_stopwords=True, use_stemming=False, use_lemmatization=True):
        text = text.lower()  # Convert to lowercase
        text = re.sub(f'[{re.escape(string.punctuation)}]', '', text)  # Remove punctuation
        #tokens = word_tokenize(text)  # Tokenize
        tokens = word_tokenize(text, language='french')

        if remove_stopwords:
            #stop_words = set(stopwords.words('english'))
            stop_words = set(stopwords.words('french'))
            tokens = [word for word in tokens if word not in stop_words]

        if use_stemming:
            stemmer = PorterStemmer()
            tokens = [stemmer.stem(word) for word in tokens]
        elif use_lemmatization:
            lemmatizer = WordNetLemmatizer()
            tokens = [lemmatizer.lemmatize(word) for word in tokens]

        return tokens

    # Generate n-grams from text
    def generate_ngrams(tokens, n):
        return [' '.join(tokens[i:i + n]) for i in range(len(tokens) - n + 1)]

    def fuzzy_match_sequences(text, word_list, threshold=70):
        # Preprocess the text
        preprocessed_text = preprocess(text)

        # Generate n-grams (1 to 6 words)
        ngrams = list(chain.from_iterable(generate_ngrams(preprocessed_text, n) for n in range(1, 7)))

        # Preprocess each word in the word list
        preprocessed_words = [preprocess(word) for word in word_list]

        matches = []
        for ngram in ngrams:
            for word_tokens in preprocessed_words:
                word = ' '.join(word_tokens)  # Join the tokens back to a string for fuzzy matching
                match_score = fuzz.partial_ratio(ngram, word)  # Fuzzy match
                if match_score >= threshold:
                    return True
                    #matches.append((ngram, word, match_score))
        return False #matches

    def levenshtein_match_sequence(text, word_list, threshold=3):
        # Preprocess the text
        preprocessed_text = preprocess(text)

        # Generate n-grams (1 to 6 words)
        ngrams = list(chain.from_iterable(generate_ngrams(preprocessed_text, n) for n in range(1, 7)))

        # Preprocess each word in the word list
        preprocessed_words = [preprocess(word) for word in word_list]

        matches = []

        for ngram in ngrams:
            for word_tokens in preprocessed_words:
                word = ' '.join(word_tokens)  # Join the tokens back to a string for fuzzy matching
                distance = Levenshtein.distance(ngram, word)
                #match_score = fuzz.partial_ratio(ngram, word)  # Fuzzy match
                if distance <= threshold:
                    return True
                    #matches.append((ngram, word, match_score))
        return False #matches


    def jaccard_match_sequence(text, word_list, threshold=0.2):
        # Preprocess the text
        preprocessed_text = preprocess(text)

        # Generate n-grams (1 to 6 words)
        ngrams = list(chain.from_iterable(generate_ngrams(preprocessed_text, n) for n in range(1, 7)))

        # Preprocess each word in the word list
        preprocessed_words = [preprocess(word) for word in word_list]

        matches = []

        for ngram in ngrams:
            for word_tokens in preprocessed_words:
                word = ' '.join(word_tokens)  # Join the tokens back to a string for fuzzy matching
                score = jaccard_similarity(ngram, word)
                #match_score = fuzz.partial_ratio(ngram, word)  # Fuzzy match
                if score >= threshold:
                    return True
                    #matches.append((ngram, word, match_score))
        return False #matches


    def cosine_match_sequence(text, word_list, threshold=0.8):
        # Preprocess the text
        preprocessed_text = preprocess(text)

        # Generate n-grams (1 to 6 words)
        ngrams = list(chain.from_iterable(generate_ngrams(preprocessed_text, n) for n in range(1, 7)))

        # Preprocess each word in the word list
        preprocessed_words = [preprocess(word) for word in word_list]

        matches = []

        for ngram in ngrams:
            for word_tokens in preprocessed_words:
                word = ' '.join(word_tokens)  # Join the tokens back to a string for fuzzy matching
                #score = jaccard_similarity(ngram, word)
                vectorizer = CountVectorizer().fit_transform([ngram] + word)
                vectors = vectorizer.toarray()
                csim = cosine_similarity(vectors)
                #match_score = fuzz.partial_ratio(ngram, word)  # Fuzzy match
                for i, word in enumerate(word):
                    if csim[0][i + 1] >= threshold:
                        return True
                        # matches.append((word, csim[0][i + 1]))  # csim[0] is the text vector
        return False #matches


    # Add a new column 'Categorized' with False for all rows
    transaction_df['Categorized'] = False
    transaction_df['Category'] = "Unknown"
    transaction_df['SubCategory'] = "Unknown"

    #communication = row['Communication'].upper()
    #comment = row['comment'].upper()
    #comment = row['Counterparty'].upper()

    ## ----- Match words from categories with full "comment" from transaction -----
    # exact match
    # Initialize results dictionary
    results = {category: {'positive': [], 'negative': []} for category in categories_exact_match}
    sub_categories = []
    # Categorize transactions with exact matches
    for index, row in transaction_df.iterrows():
        for category, keywords in categories_exact_match.items():
            if any(keyword.upper() in row['comment'].upper() for keyword in keywords):
                if float(row['Amount']) > 0:
                    results[category]['positive'].append(float(row['Amount']))
                    if (transaction_df.at[index, 'Categorized'] == True) and (transaction_df.at[index, 'SubCategory'] == "Unknown"):
                        transaction_df.at[index, 'SubCategory'] = category
                    elif (transaction_df.at[index, 'Categorized'] == True) and (transaction_df.at[index, 'SubCategory'] != "Unknown"):
                        transaction_df.at[index, 'SubCategory'] = "{} / {}".format(transaction_df.at[index, 'SubCategory'], category)
                    transaction_df.at[index, 'Categorized'] = True
                    transaction_df.at[index, 'Category'] = category
                else:
                    results[category]['negative'].append(float(row['Amount']))
                    if (transaction_df.at[index, 'Categorized'] == True) & (transaction_df.at[index, 'SubCategory'] == "Unknown"):
                        transaction_df.at[index, 'SubCategory'] = category
                    elif (transaction_df.at[index, 'Categorized'] == True) and (transaction_df.at[index, 'SubCategory'] != "Unknown"):
                        transaction_df.at[index, 'SubCategory'] = "{} / {}".format(transaction_df.at[index, 'SubCategory'], category)
                    transaction_df.at[index, 'Categorized'] = True
                    transaction_df.at[index, 'Category'] = category

    # regex_match exact match
    # Initialize results dictionary
    results_regex = {category: {'positive': [], 'negative': []} for category in categories_exact_match}
    # Categorize transactions with fuzzy matches if not already categorized
    for index, row in transaction_df.iterrows():
        if transaction_df.at[index, 'Categorized'] == False:
            for category, keywords in categories_exact_match.items():
                if regex_match(row['comment'], keywords):
                    if float(row['Amount']) > 0:
                        results_regex[category]['positive'].append(row['Amount'])
                        if (transaction_df.at[index, 'Categorized'] == True) and (
                                transaction_df.at[index, 'SubCategory'] == "Unknown"):
                            transaction_df.at[index, 'SubCategory'] = category
                        elif (transaction_df.at[index, 'Categorized'] == True) and (
                                transaction_df.at[index, 'SubCategory'] != "Unknown"):
                            transaction_df.at[index, 'SubCategory'] = "{} / {}".format(
                                transaction_df.at[index, 'SubCategory'], category)
                        transaction_df.at[index, 'Categorized'] = True
                        transaction_df.at[index, 'Category'] = category
                    else:
                        results_regex[category]['negative'].append(row['Amount'])
                        if (transaction_df.at[index, 'Categorized'] == True) and (
                                transaction_df.at[index, 'SubCategory'] == "Unknown"):
                            transaction_df.at[index, 'SubCategory'] = category
                        elif (transaction_df.at[index, 'Categorized'] == True) and (
                                transaction_df.at[index, 'SubCategory'] != "Unknown"):
                            transaction_df.at[index, 'SubCategory'] = "{} / {}".format(
                                transaction_df.at[index, 'SubCategory'], category)
                        transaction_df.at[index, 'Categorized'] = True
                        transaction_df.at[index, 'Category'] = category


    # fuzzy matching
    # Initialize results dictionary
    results_fuzzy = {category: {'positive': [], 'negative': []} for category in categories_fuzzy}
    # Categorize transactions with fuzzy matches if not already categorized
    for index, row in transaction_df.iterrows():
        if transaction_df.at[index, 'Categorized'] == False:
            for category, keywords in categories_fuzzy.items():
                if fuzzy_match(row['comment'], keywords):
                    if float(row['Amount']) > 0:
                        results_fuzzy[category]['positive'].append(row['Amount'])
                        if (transaction_df.at[index, 'Categorized'] == True) and (
                                transaction_df.at[index, 'SubCategory'] == "Unknown"):
                            transaction_df.at[index, 'SubCategory'] = category
                        elif (transaction_df.at[index, 'Categorized'] == True) and (
                                transaction_df.at[index, 'SubCategory'] != "Unknown"):
                            transaction_df.at[index, 'SubCategory'] = "{} / {}".format(transaction_df.at[index, 'SubCategory'], category)
                        transaction_df.at[index, 'Categorized'] = True
                        transaction_df.at[index, 'Category'] = category
                    else:
                        results_fuzzy[category]['negative'].append(row['Amount'])
                        if (transaction_df.at[index, 'Categorized'] == True) and (
                                transaction_df.at[index, 'SubCategory'] == "Unknown"):
                            transaction_df.at[index, 'SubCategory'] = category
                        elif (transaction_df.at[index, 'Categorized'] == True) and (
                                transaction_df.at[index, 'SubCategory'] != "Unknown"):
                            transaction_df.at[index, 'SubCategory'] = "{} / {}".format(transaction_df.at[index, 'SubCategory'], category)
                        transaction_df.at[index, 'Categorized'] = True
                        transaction_df.at[index, 'Category'] = category


    # levenshtein_match
    # Initialize results dictionary
    results_bert = {category: {'positive': [], 'negative': []} for category in categories_fuzzy}
    # Categorize transactions with fuzzy matches if not already categorized
    for index, row in transaction_df.iterrows():
        if transaction_df.at[index, 'Categorized'] == False:
            for category, keywords in categories_fuzzy.items():
                if levenshtein_match(row['comment'], keywords):
                    if float(row['Amount']) > 0:
                        results_bert[category]['positive'].append(row['Amount'])
                        if (transaction_df.at[index, 'Categorized'] == True) and (
                                transaction_df.at[index, 'SubCategory'] == "Unknown"):
                            transaction_df.at[index, 'SubCategory'] = category
                        elif (transaction_df.at[index, 'Categorized'] == True) and (
                                transaction_df.at[index, 'SubCategory'] != "Unknown"):
                            transaction_df.at[index, 'SubCategory'] = "{} / {}".format(
                                transaction_df.at[index, 'SubCategory'], category)
                        transaction_df.at[index, 'Categorized'] = True
                        transaction_df.at[index, 'Category'] = category
                    else:
                        results_bert[category]['negative'].append(row['Amount'])
                        if (transaction_df.at[index, 'Categorized'] == True) and (
                                transaction_df.at[index, 'SubCategory'] == "Unknown"):
                            transaction_df.at[index, 'SubCategory'] = category
                        elif (transaction_df.at[index, 'Categorized'] == True) and (
                                transaction_df.at[index, 'SubCategory'] != "Unknown"):
                            transaction_df.at[index, 'SubCategory'] = "{} / {}".format(
                                transaction_df.at[index, 'SubCategory'], category)
                        transaction_df.at[index, 'Categorized'] = True
                        transaction_df.at[index, 'Category'] = category

    # jaccard_match
    # Initialize results dictionary
    results_jaccard = {category: {'positive': [], 'negative': []} for category in categories_fuzzy}
    # Categorize transactions with fuzzy matches if not already categorized
    for index, row in transaction_df.iterrows():
        if transaction_df.at[index, 'Categorized'] == False:
            for category, keywords in categories_fuzzy.items():
                if jaccard_match(row['comment'], keywords):
                    if float(row['Amount']) > 0:
                        results_jaccard[category]['positive'].append(row['Amount'])
                        if (transaction_df.at[index, 'Categorized'] == True) and (
                                transaction_df.at[index, 'SubCategory'] == "Unknown"):
                            transaction_df.at[index, 'SubCategory'] = category
                        elif (transaction_df.at[index, 'Categorized'] == True) and (
                                transaction_df.at[index, 'SubCategory'] != "Unknown"):
                            transaction_df.at[index, 'SubCategory'] = "{} / {}".format(
                                transaction_df.at[index, 'SubCategory'], category)
                        transaction_df.at[index, 'Categorized'] = True
                        transaction_df.at[index, 'Category'] = category
                    else:
                        results_jaccard[category]['negative'].append(row['Amount'])
                        if (transaction_df.at[index, 'Categorized'] == True) and (
                                transaction_df.at[index, 'SubCategory'] == "Unknown"):
                            transaction_df.at[index, 'SubCategory'] = category
                        elif (transaction_df.at[index, 'Categorized'] == True) and (
                                transaction_df.at[index, 'SubCategory'] != "Unknown"):
                            transaction_df.at[index, 'SubCategory'] = "{} / {}".format(
                                transaction_df.at[index, 'SubCategory'], category)
                        transaction_df.at[index, 'Categorized'] = True
                        transaction_df.at[index, 'Category'] = category

    # cosine_match
    # Initialize results dictionary
    results_cosine = {category: {'positive': [], 'negative': []} for category in categories_fuzzy}
    # Categorize transactions with fuzzy matches if not already categorized
    for index, row in transaction_df.iterrows():
        if transaction_df.at[index, 'Categorized'] == False:
            for category, keywords in categories_fuzzy.items():
                if cosine_match(row['comment'], keywords):
                    if float(row['Amount']) > 0:
                        results_cosine[category]['positive'].append(row['Amount'])
                        if (transaction_df.at[index, 'Categorized'] == True) and (
                                transaction_df.at[index, 'SubCategory'] == "Unknown"):
                            transaction_df.at[index, 'SubCategory'] = category
                        elif (transaction_df.at[index, 'Categorized'] == True) and (
                                transaction_df.at[index, 'SubCategory'] != "Unknown"):
                            transaction_df.at[index, 'SubCategory'] = "{} / {}".format(
                                transaction_df.at[index, 'SubCategory'], category)
                        transaction_df.at[index, 'Categorized'] = True
                        transaction_df.at[index, 'Category'] = category
                    else:
                        results_cosine[category]['negative'].append(row['Amount'])
                        if (transaction_df.at[index, 'Categorized'] == True) and (
                                transaction_df.at[index, 'SubCategory'] == "Unknown"):
                            transaction_df.at[index, 'SubCategory'] = category
                        elif (transaction_df.at[index, 'Categorized'] == True) and (
                                transaction_df.at[index, 'SubCategory'] != "Unknown"):
                            transaction_df.at[index, 'SubCategory'] = "{} / {}".format(
                                transaction_df.at[index, 'SubCategory'], category)
                        transaction_df.at[index, 'Categorized'] = True
                        transaction_df.at[index, 'Category'] = category


    '''
    # Bert matching
    # Initialize results dictionary
    results_bert = {category: {'positive': [], 'negative': []} for category in categories_fuzzy}
    # Categorize transactions with fuzzy matches if not already categorized
    for index, row in transaction_df.iterrows():
        if transaction_df.at[index, 'Categorized'] == False:
            for category, keywords in categories_fuzzy.items():
                if fuzzy_match(row['comment'], keywords):
                    if float(row['Amount']) > 0:
                        results_bert[category]['positive'].append(row['Amount'])
                        if (transaction_df.at[index, 'Categorized'] == True) and (
                                transaction_df.at[index, 'SubCategory'] == "Unknown"):
                            transaction_df.at[index, 'SubCategory'] = category
                        elif (transaction_df.at[index, 'Categorized'] == True) and (
                                transaction_df.at[index, 'SubCategory'] != "Unknown"):
                            transaction_df.at[index, 'SubCategory'] = "{} / {}".format(
                                transaction_df.at[index, 'SubCategory'], category)
                        transaction_df.at[index, 'Categorized'] = True
                        transaction_df.at[index, 'Category'] = category
                    else:
                        results_bert[category]['negative'].append(row['Amount'])
                        if (transaction_df.at[index, 'Categorized'] == True) and (
                                transaction_df.at[index, 'SubCategory'] == "Unknown"):
                            transaction_df.at[index, 'SubCategory'] = category
                        elif (transaction_df.at[index, 'Categorized'] == True) and (
                                transaction_df.at[index, 'SubCategory'] != "Unknown"):
                            transaction_df.at[index, 'SubCategory'] = "{} / {}".format(
                                transaction_df.at[index, 'SubCategory'], category)
                        transaction_df.at[index, 'Categorized'] = True
                        transaction_df.at[index, 'Category'] = category
    '''

    ## ----- Match words from categories lists with full ngrams from "comment" from transaction -----
    ## ngrams
    # fuzzy matching
    # Initialize results dictionary
    results_fuzzy_seq = {category: {'positive': [], 'negative': []} for category in categories_fuzzy}
    # Categorize transactions with fuzzy matches if not already categorized
    for index, row in transaction_df.iterrows():
        if transaction_df.at[index, 'Categorized'] == False:
            for category, keywords in categories_fuzzy.items():
                if fuzzy_match_sequences(row['comment'], keywords):
                    if float(row['Amount']) > 0:
                        results_fuzzy_seq[category]['positive'].append(row['Amount'])
                        if (transaction_df.at[index, 'Categorized'] == True) and (
                                transaction_df.at[index, 'SubCategory'] == "Unknown"):
                            transaction_df.at[index, 'SubCategory'] = category
                        elif (transaction_df.at[index, 'Categorized'] == True) and (
                                transaction_df.at[index, 'SubCategory'] != "Unknown"):
                            transaction_df.at[index, 'SubCategory'] = "{} / {}".format(
                                transaction_df.at[index, 'SubCategory'], category)
                        transaction_df.at[index, 'Categorized'] = True
                        transaction_df.at[index, 'Category'] = category
                    else:
                        results_fuzzy_seq[category]['negative'].append(row['Amount'])
                        if (transaction_df.at[index, 'Categorized'] == True) and (
                                transaction_df.at[index, 'SubCategory'] == "Unknown"):
                            transaction_df.at[index, 'SubCategory'] = category
                        elif (transaction_df.at[index, 'Categorized'] == True) and (
                                transaction_df.at[index, 'SubCategory'] != "Unknown"):
                            transaction_df.at[index, 'SubCategory'] = "{} / {}".format(
                                transaction_df.at[index, 'SubCategory'], category)
                        transaction_df.at[index, 'Categorized'] = True
                        transaction_df.at[index, 'Category'] = category

    # levenshtein_match
    # Initialize results dictionary
    results_levenshtein = {category: {'positive': [], 'negative': []} for category in categories_fuzzy}
    # Categorize transactions with fuzzy matches if not already categorized
    for index, row in transaction_df.iterrows():
        if transaction_df.at[index, 'Categorized'] == False:
            for category, keywords in categories_fuzzy.items():
                if levenshtein_match_sequence(row['comment'], keywords):
                    if float(row['Amount']) > 0:
                        results_levenshtein[category]['positive'].append(row['Amount'])
                        if (transaction_df.at[index, 'Categorized'] == True) and (
                                transaction_df.at[index, 'SubCategory'] == "Unknown"):
                            transaction_df.at[index, 'SubCategory'] = category
                        elif (transaction_df.at[index, 'Categorized'] == True) and (
                                transaction_df.at[index, 'SubCategory'] != "Unknown"):
                            transaction_df.at[index, 'SubCategory'] = "{} / {}".format(
                                transaction_df.at[index, 'SubCategory'], category)
                        transaction_df.at[index, 'Categorized'] = True
                        transaction_df.at[index, 'Category'] = category
                    else:
                        results_levenshtein[category]['negative'].append(row['Amount'])
                        if (transaction_df.at[index, 'Categorized'] == True) and (
                                transaction_df.at[index, 'SubCategory'] == "Unknown"):
                            transaction_df.at[index, 'SubCategory'] = category
                        elif (transaction_df.at[index, 'Categorized'] == True) and (
                                transaction_df.at[index, 'SubCategory'] != "Unknown"):
                            transaction_df.at[index, 'SubCategory'] = "{} / {}".format(
                                transaction_df.at[index, 'SubCategory'], category)
                        transaction_df.at[index, 'Categorized'] = True
                        transaction_df.at[index, 'Category'] = category

    # jaccard_match
    # Initialize results dictionary
    results_jaccard_seq = {category: {'positive': [], 'negative': []} for category in categories_fuzzy}
    # Categorize transactions with fuzzy matches if not already categorized
    for index, row in transaction_df.iterrows():
        if transaction_df.at[index, 'Categorized'] == False:
            for category, keywords in categories_fuzzy.items():
                if jaccard_match_sequence(row['comment'], keywords):
                    if float(row['Amount']) > 0:
                        results_jaccard_seq[category]['positive'].append(row['Amount'])
                        if (transaction_df.at[index, 'Categorized'] == True) and (
                                transaction_df.at[index, 'SubCategory'] == "Unknown"):
                            transaction_df.at[index, 'SubCategory'] = category
                        elif (transaction_df.at[index, 'Categorized'] == True) and (
                                transaction_df.at[index, 'SubCategory'] != "Unknown"):
                            transaction_df.at[index, 'SubCategory'] = "{} / {}".format(
                                transaction_df.at[index, 'SubCategory'], category)
                        transaction_df.at[index, 'Categorized'] = True
                        transaction_df.at[index, 'Category'] = category
                    else:
                        results_jaccard_seq[category]['negative'].append(row['Amount'])
                        if (transaction_df.at[index, 'Categorized'] == True) and (
                                transaction_df.at[index, 'SubCategory'] == "Unknown"):
                            transaction_df.at[index, 'SubCategory'] = category
                        elif (transaction_df.at[index, 'Categorized'] == True) and (
                                transaction_df.at[index, 'SubCategory'] != "Unknown"):
                            transaction_df.at[index, 'SubCategory'] = "{} / {}".format(
                                transaction_df.at[index, 'SubCategory'], category)
                        transaction_df.at[index, 'Categorized'] = True
                        transaction_df.at[index, 'Category'] = category

    # cosine_match
    # Initialize results dictionary
    results_cosine_seq = {category: {'positive': [], 'negative': []} for category in categories_fuzzy}
    # Categorize transactions with fuzzy matches if not already categorized
    for index, row in transaction_df.iterrows():
        if transaction_df.at[index, 'Categorized'] == False:
            for category, keywords in categories_fuzzy.items():
                if cosine_match_sequence(row['comment'], keywords):
                    if float(row['Amount']) > 0:
                        results_cosine_seq[category]['positive'].append(row['Amount'])
                        if (transaction_df.at[index, 'Categorized'] == True) and (
                                transaction_df.at[index, 'SubCategory'] == "Unknown"):
                            transaction_df.at[index, 'SubCategory'] = category
                        elif (transaction_df.at[index, 'Categorized'] == True) and (
                                transaction_df.at[index, 'SubCategory'] != "Unknown"):
                            transaction_df.at[index, 'SubCategory'] = "{} / {}".format(
                                transaction_df.at[index, 'SubCategory'], category)
                        transaction_df.at[index, 'Categorized'] = True
                        transaction_df.at[index, 'Category'] = category
                    else:
                        results_cosine_seq[category]['negative'].append(row['Amount'])
                        if (transaction_df.at[index, 'Categorized'] == True) and (
                                transaction_df.at[index, 'SubCategory'] == "Unknown"):
                            transaction_df.at[index, 'SubCategory'] = category
                        elif (transaction_df.at[index, 'Categorized'] == True) and (
                                transaction_df.at[index, 'SubCategory'] != "Unknown"):
                            transaction_df.at[index, 'SubCategory'] = "{} / {}".format(
                                transaction_df.at[index, 'SubCategory'], category)
                        transaction_df.at[index, 'Categorized'] = True
                        transaction_df.at[index, 'Category'] = category
    # Print results
    for category, amounts in results.items():
        print(f"Category: {category}")
        try:
            print(f"  Positive Amounts: {sum(amounts['positive'])}")
            print(f"  Negative Amounts: {sum(amounts['negative'])}")
        except:
            print('test')
    print('test')
    return transaction_df

    '''
      # Save results to a new CSV file
      output_df = pd.DataFrame(columns=['Category', 'Positive Amounts', 'Negative Amounts'])
      for category, amounts in results.items():
          output_df = output_df.append({
              'Category': category,
              'Positive Amounts': sum(amounts['positive']),
              'Negative Amounts': sum(amounts['negative'])
          }, ignore_index=True)
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
    iban = re.search(r'(BE\d{2} \d{4} \d{4} \d{4})', text).group(1)
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