
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

from datetime import datetime

# Define function to extract transaction type
def extract_transaction_type(comment):
    if "Achat par carte" in comment:
        return "Achat par carte"
    elif "Virement" in comment:
        return "Virement"
    elif "Ordre permanent" in comment:
        return "Virement"
    elif "souscription de titres" in comment:
        return "Souscription de titres"
    elif "Achat automatique" in comment:
        return "Souscription de titres"
    elif "Retrait d'espèces" in comment:
        return "Retrait d'espèces"
    elif "Paiement des frais" in comment:
        return "Redevance"
    elif "Contribution compte à vue" in comment:
        return "Redevance"
    elif "Encaissement interne du crédit" in comment:
        return "Prêts hypothécaire"
    else:
        return ""


# Define function to extract communication
def extract_communication(comment):
    # Define the regex pattern for ref bank
    communication = r'Communication:'
    # Search for all ref bank patterns in the text
    communication_matches = re.findall(communication, comment)
    # find text between communication and ref bank
    if communication_matches:
        # Regular expression to match text after 'Communication:' until the end of the line
        pattern = r"Communication:\s*(.+)"
        # Find the first match
        match = re.search(pattern, comment)
        # If a match is found, print it
        if match:
            return match.group(1)
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
    #match_hundreds = re.search(r"[+-]\d{1,3}(,\d{2})", comment).group(0)
    #match_hundreds_amount = re.search(r'[+-]\d{1,3}(,\d{2})', match_hundreds).group(0)
    #match_thousands = re.search(r"[+-]?\d{1,3}(\.\d{3})*,\d{2}", comment).group(0)
    #match_thousands_amount = re.search(r'[+-]?\d{1,3}(\.\d{3})*,\d{2}', match_thousands).group(0)
    match_millions = re.search(r"[+-]\d{1,3}(\.\d{3})*,\d{2}", comment).group(0)
    #if throusand
    if match_millions is not None:
        match_millions_amount = re.search(r'[+-]\d{1,3}(\.\d{3})*,\d{2}', match_millions).group(0).replace(".", "").replace(",", ".")
        sign = match_millions_amount[0:1]
        return f"-{match_millions_amount[1:]}" if sign == '-' else match_millions_amount[1:]
    print("Error: no amount found for comment '{}".format(comment))
    return 0


def extract_counterparty(comment):
    # Define the regex pattern
    iban_pattern = r'Communication:\s'
    # Search for all patterns in the text
    iban_matches = re.findall(iban_pattern, comment)

    if iban_matches:
        # Get the firstmatch
        iban_match = iban_matches[0]
        # Cut the text from the first pattern onwards, including the pattern itself
        cut_text_before_iban = comment[:comment.index(iban_match)]
        # print(f"Last IBAN match found: {iban_match}")
        # print(f"Text after last IBAN match: {cut_text_after_iban}")
        lines = cut_text_before_iban.split('\n')
        if len(lines) > 2:
            joined_text = "\n".join(lines[1:])
            return joined_text
        else:
            return lines[1]

    if ("Achat par carte" in comment) or ("Virement" in comment):
        lines = comment.split('\n')
        cpt_text = lines[1]
        # Regex pattern to find 'de' followed by a space and any digit(s)
        pattern = r'de\s\d+'
        # Find all matches
        matches = re.findall(pattern, cpt_text)
        if matches:
            return ""
        else:
            return lines[1]

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
            'Dreamland', 'OKay', 'OKay Compact', "DELHAIZE", "AD DELHAIZE",
            "COLRUYT", "Bartolas Event"
        ],
        'Utilities': [
            'Electricity', 'Water', 'Gas', 'Sewage', 'Internet', 'Telephone', 'Waste Disposal',
            'Engie Electrabel', 'TotalEnergies', 'Luminus', 'Mega', 'Eneco', 'Octa+', 'Trevion', 'Aspiravi Energy',
            'Bolt', 'Cociter', 'DATS 24', 'Ebem', 'Elegant', 'Energie.be', 'Frank Energie', 'Wind voor "A"',
            "Luminus", "Proximus", "Voo", "INBW"
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
            'Hof Van Cleve Kruisem', 'La Bonne Chère Brussels', 'Boury Roeselare', 'Zilte Antwerp', 'Ivresse Uccle',
            "BK BIERGES", "Maison du prieur", "Barbuston", "DE STOKKE BV", "L IGLOO", "Le Canott",
            "LE RESSAC", "JOURDON CECILE", "CHAT AVENTURIERS"
        ],
        'Entertainment': [
            'Movies', 'Concerts', 'Theater', 'Amusement Parks', 'Sporting Events',
            'Streaming Services', 'Video Games', 'Books', 'Music', 'Dragone', 'Studio 100', 'Kinepolis Group',
            'D&D Productions', 'Woestijnvis', 'Lumière', 'Caviar', 'Eyeworks', 'De Mensen', 'Fobic Films',
            "Cinescope LLN", "O'GLISS PARK", "JARD ATTRACTIONS", "O'GLISS PARK"
        ],
        'Healthcare': [
            'Doctor Visits', 'Pharmacy', 'Health Insurance', 'Dental Care', 'Vision Care',
            'Mental Health Services', 'Medical Equipment', 'Vaccinations',
            'UCB SA', 'Financière de Tubize SA', 'Galapagos NV', 'Fagron NV', 'Ion Beam Applications SA', 'Nyxoah SA',
            'MDxHealth SA', 'Sequana Medical NV', 'Mithra Pharmaceuticals SA', 'Celyad Oncology SA',
            "Pharmacie", "Smits"
        ],
        'Transport': [
            'Fuel', 'Public Transport', 'Car Maintenance', 'Parking Fees', 'Tolls',
            'Car Insurance', 'Ride-Sharing Services', 'H.Essers', 'Sarens', 'Jost Group', 'Deutsche Bahn',
            'Kuehne + Nagel', 'UPS', 'DSV', 'Van Moer', 'SEA-Invest', 'Euroports', 'Tabak Natie', 'Katoen Natie',
            "ESSO", "LUKOIL", "TOTAL", "Shell", "SANEF", "SNCB"
        ],
        'Shopping': [
            'Clothing', 'Electronics', 'Home Goods', 'Beauty Products', 'Toys',
            'Books', 'Jewelry', 'Sporting Goods', 'bol.com', 'coolblue.be', 'amazon.com.be', 'Zalando', 'MediaMarkt',
            'Vanden Borre', 'Fnac', 'IKEA', 'H&M', 'Decathlon', 'ZEB', 'JBC', 'Veritas', 'C&A', 'Primark'
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
            "Matériaux Pierret",
            "BigMat", "BELGIAN MINERALS", "BRICO", "BWT", "ZiwaPool",
            "MISTER MINIT", "VELDDRIEL COMBIFIT", "RJLocation"
        ],
        'Miscellaneous': [
            'Gifts', 'Donations', 'Subscriptions', 'Pet Care', 'Hobbies',
            'Office Supplies', 'Travel Expenses', 'Anheuser-Busch InBev', 'Umicore', 'KBC Group', 'Solvay S.A.', 'Colruyt Group',
            'Ageas', 'Groupe Bruxelles Lambert', 'Viohalco', 'Proximus', 'Bekaert', 'UCB', 'Belfius'
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
            'Miscellaneous': [
                 'TotalEnergies', 'BNP Paribas', 'Axa', 'Crédit Agricole', 'Sanofi',
                'Dior', 'Société Générale', 'Vinci', 'Orange', 'Oréal'
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

def remove_headers_footers(text):
    # Define the transaction pattern
    #transaction_pattern = r'(\d{2}-\d{2}-\d{4})\s+(\d{4})\s+'
    transaction_pattern = r'\d{2}-\d{2}.*\d{2}-\d{2}'
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

        # remove other headers
        start_header = re.search(r"compte à vue\s+(\S+)", header_text).group(0)
        end_header = header_text[-26:]
        # Constructing the regular expression dynamically
        pattern = re.escape(start_header) + r".*?" + re.escape(end_header)
        # Using re.sub to remove everything from start_header to end_header
        remaining_text = re.sub(pattern, '\n', remaining_text, flags=re.DOTALL)

        # remove pdf date
        remaining_text = remaining_text.replace(matched_date, "").strip()

        # find balances
        #match_beginning_footer = re.search(r'Solde actuel [+-]\d{1,3}(\.\d{3})*,\d{2}', remaining_text)
        #if match_beginning_footer:
            # remove header info
            #footer_text = remaining_text[match_beginning_footer.end():].strip()

        # remove footer
        # Try to find "Solde actuel" first
        # Dynamically build the regex pattern using the variable
        match_footer = re.escape(current_balance) + r".*"
        #match_footer = re.search(r"{}".format(current_balance_amount), remaining_text)
        if match_footer:
            # Use re.sub to remove everything from the start_string onward
            remaining_text = re.sub(match_footer, '', remaining_text, flags=re.DOTALL)
        else:
            try:
                remaining_text = re.sub(r"Messages personnels.*", '', remaining_text, flags=re.DOTALL)
            except:
                print("error: footer couldn't be removed")
        return remaining_text
    return text


def split_transactions(remaining_text):
    final_list = []
    pattern = r'(?<=\n)\d{2}-\d{2}\s'
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
input_folder_path = input_folder_path.replace('\\', '/')
language = os.getenv('LANGUAGE')
if language != "French":
    print('Warning: nltk packages are in French. It can be easily changed though, lookup and change parameter "language=french"')
#input_folder_path = 'E:/LaptopBackUp/Administrative/Banques/Fortis/Commun/2024/test/'
#input_folder_path = 'D:/LaptopBackUp/Administrative/Banques/Axa/BE10 7506 7495 9104/extraits/2024'

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
    #client_name = re.search(r'M M ALLARD - ROLAND', text).group()
    #client_number = re.search(r'N° client : (\d+ \d+)', text).group(1)
    iban = re.search(r'(BE\d{2} \d{4} \d{4} \d{4})', text).group(1)
    bic = re.search(r'BIC (\w+)', text).group(1)

    # find current year
    pattern_year = r"Extrait de compte \d{4}"
    match_year = re.search(pattern_year, text)
    if match_year:
        current_year = match_year.group(0)
        current_year = current_year[-4:]
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


    # keep track of account balance
    #if current_balance_date not in dic_balances:
    #    dic_balances[current_balance_date] = current_balance_amount
    #else:
    #    print('test')

    ## remove headers and footer
    remaining_text = remove_headers_footers(text)

    # Loop through each ignored sentences and remove it from the remaining text
    #for line in custom_text_remove:
    #    remaining_text = remaining_text.replace(line, "").strip()

    # Define the regex pattern to remove
    #regex_pattern = [r'Tél\. 02 762 20 00 - Card Stop: 078 170 170 - www\.bnpparibasfortis\.be\d+/\d+',
    #           r"Tél\. \d{2} \d{3} \d{2} \d{2} - Card Stop: \d{3} \d{3} \d{3} - www\.bnpparibasfortis\.be\d+/\d+"]
    #for pattern in regex_pattern:
    #    remaining_text = re.sub(pattern, '', remaining_text)

    # split transactions
    final_transaction_list.extend(split_transactions(remaining_text))

# convert transaction list to df
transaction_df = pd.DataFrame(columns=['date', 'trans_id', 'comment'])
for i, el in enumerate(final_transaction_list):
    transaction_id += 1
    ## Find date in the format "dd-mm"
    pattern = r"\b\d{2}-\d{2}\b"
    # Search for the first occurrence of any date pattern
    try:
        matched_date = re.search(pattern, el).group()
    except:
        matched_date = re.search(r"\d{2}-\d{2}", el).group()
    # get year: Convert the string to a datetime object and extract the year
    #date_year = datetime.strptime(current_balance_date, "%d-%m-%Y").year

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
transaction_df['trans_id'] = transaction_df.index

#errors_output_file = os.path.join(input_folder_path, 'error_transaction.csv')
#try:
#    error_transaction.to_csv(
#        errors_output_file,
#        index=False,
#        sep=',',
#        encoding='utf-8-sig',
#    )
#except:
#    print("error permmission denied: 'error_transaction.csv' seems to be already open, please close the file")
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
#transaction_df['Counterparty'] = ""
'''
# Convert 'date' column to datetime format
transaction_df['date'] = pd.to_datetime(transaction_df['date'], format='%d-%m-%Y')
# Sort the DataFrame by 'date' in ascending order
transaction_df = transaction_df.sort_values(by='date')
# Reset the index if desired
transaction_df.reset_index(drop=True, inplace=True)
'''

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