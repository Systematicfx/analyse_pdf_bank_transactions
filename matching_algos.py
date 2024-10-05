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
            'Rent': [
                "AXA Belgium"
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
                "Les Sables"
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
                "DYNEFF BROUZILS",
                "TOTAL NB000556 W WAVRE",
                "Suntransfers"
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
            'Miscellaneous': [
                "PHOTOMATIQUE",
                "Parking Brussels",
                "Beobank Interest",
                "Services Taxes - Please des Carmes",
                "Beobank - carte Visa New",
                "Services Taxes - Please des Carmes",
                "PARKING LLN",
                "Indigo Infra Bel",
                "LES IDEES BLEUES"
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
            'Firstname Lastname': [
                "Lastname Firstname",
                "Firstname Lastname",
                "Services Taxes - Please des Carmes",
                "Beobank - carte Visa New"
            ],
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
        if matches:
            return matches[0]
        else:
            return ""


    def levenshtein_match(text, word_list, threshold=3):
        matches = []
        for word in word_list:
            distance = Levenshtein.distance(word.lower(), text.lower())
            if distance <= threshold:  # Lower distance means a closer match
                return word
                #matches.append((word, distance))
        return ""

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
                return word
                #matches.append((word, score))
        return ""


    def fuzzy_match(text, word_list, threshold=80):
        matches = []
        for word in word_list:
            match_score = fuzz.partial_ratio(word.lower(), text.lower())
            if match_score >= threshold:
                return word
                #matches.append((word, match_score))
        return ""

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
                return word
                #matches.append((word, csim[0][i + 1]))  # csim[0] is the text vector
        return "" # matches

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
                    return word
                    #matches.append((ngram, word, match_score))
        return "" #matches

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
                    return word
                    #matches.append((ngram, word, match_score))
        return "" #matches


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
                    return word
                    #matches.append((ngram, word, match_score))
        return "" #matches


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
                        return word
                        # matches.append((word, csim[0][i + 1]))  # csim[0] is the text vector
        return "" #matches


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
        if "chez 123Inkt - NEDERHORST" in row['comment']:
            print("test")
        for category, keywords in categories_exact_match.items():
            # if any(keyword.upper() in row['comment'].upper() for keyword in keywords):
            for keyword in keywords:
                if keyword.upper() in row['comment'].upper():
                    if float(row['Amount']) > 0:
                        results[category]['positive'].append(float(row['Amount']))
                        if (transaction_df.at[index, 'Categorized'] == True) and (transaction_df.at[index, 'SubCategory'] == "Unknown"):
                            transaction_df.at[index, 'SubCategory'] = category
                        elif (transaction_df.at[index, 'Categorized'] == True) and (transaction_df.at[index, 'SubCategory'] != "Unknown"):
                            transaction_df.at[index, 'SubCategory'] = "{} / {}".format(transaction_df.at[index, 'SubCategory'], category)
                        transaction_df.at[index, 'Categorized'] = True
                        transaction_df.at[index, 'Category'] = category
                        if transaction_df.at[index, 'exact keyword'] == "":
                            transaction_df.at[index, 'exact keyword'] = keyword
                        continue
                    else:
                        results[category]['negative'].append(float(row['Amount']))
                        if (transaction_df.at[index, 'Categorized'] == True) & (transaction_df.at[index, 'SubCategory'] == "Unknown"):
                            transaction_df.at[index, 'SubCategory'] = category
                        elif (transaction_df.at[index, 'Categorized'] == True) and (transaction_df.at[index, 'SubCategory'] != "Unknown"):
                            transaction_df.at[index, 'SubCategory'] = "{} / {}".format(transaction_df.at[index, 'SubCategory'], category)
                        transaction_df.at[index, 'Categorized'] = True
                        transaction_df.at[index, 'Category'] = category
                        if transaction_df.at[index, 'exact keyword'] == "":
                            transaction_df.at[index, 'exact keyword'] = keyword
                        continue

    # regex_match exact match
    # Initialize results dictionary
    results_regex = {category: {'positive': [], 'negative': []} for category in categories_exact_match}
    # Categorize transactions with fuzzy matches if not already categorized
    for index, row in transaction_df.iterrows():
        if "chez 123Inkt - NEDERHORST" in row['comment']:
            print("test")
        if transaction_df.at[index, 'Categorized'] == False:
            for category, keywords in categories_exact_match.items():
                regex_found_match = regex_match(row['comment'], keywords)
                if regex_found_match != "":
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
                        if transaction_df.at[index, 'regex exact keyword'] == "":
                            transaction_df.at[index, 'regex exact keyword'] = regex_found_match
                        continue
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
                        if transaction_df.at[index, 'regex exact keyword'] == "":
                            transaction_df.at[index, 'regex exact keyword'] = regex_found_match
                        continue


    # fuzzy matching
    # Initialize results dictionary
    results_fuzzy = {category: {'positive': [], 'negative': []} for category in categories_fuzzy}
    # Categorize transactions with fuzzy matches if not already categorized
    for index, row in transaction_df.iterrows():
        if transaction_df.at[index, 'Categorized'] == False:
            for category, keywords in categories_fuzzy.items():
                keyword = fuzzy_match(row['comment'], keywords)
                if keyword != "":
                #if fuzzy_match(row['comment'], keywords):
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
                        if transaction_df.at[index, 'fuzzy keyword'] == "":
                            transaction_df.at[index, 'fuzzy keyword'] = keyword
                        continue
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
                        if transaction_df.at[index, 'fuzzy keyword'] == "":
                            transaction_df.at[index, 'fuzzy keyword'] = keyword
                        continue


    # levenshtein_match
    # Initialize results dictionary
    results_bert = {category: {'positive': [], 'negative': []} for category in categories_fuzzy}
    # Categorize transactions with fuzzy matches if not already categorized
    for index, row in transaction_df.iterrows():
        if transaction_df.at[index, 'Categorized'] == False:
            for category, keywords in categories_fuzzy.items():
                keyword = levenshtein_match(row['comment'], keywords)
                if keyword != "":
                #if levenshtein_match(row['comment'], keywords):
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
                        if transaction_df.at[index, 'fuzzy keyword'] == "":
                            transaction_df.at[index, 'fuzzy keyword'] = keyword
                        continue
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
                        if transaction_df.at[index, 'fuzzy keyword'] == "":
                            transaction_df.at[index, 'fuzzy keyword'] = keyword
                        continue

    # jaccard_match
    # Initialize results dictionary
    results_jaccard = {category: {'positive': [], 'negative': []} for category in categories_fuzzy}
    # Categorize transactions with fuzzy matches if not already categorized
    for index, row in transaction_df.iterrows():
        if transaction_df.at[index, 'Categorized'] == False:
            for category, keywords in categories_fuzzy.items():
                keyword = jaccard_match(row['comment'], keywords)
                if keyword != "":
                #if jaccard_match(row['comment'], keywords):
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
                        if transaction_df.at[index, 'fuzzy keyword'] == "":
                            transaction_df.at[index, 'fuzzy keyword'] = keyword
                        continue
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
                        if transaction_df.at[index, 'fuzzy keyword'] == "":
                            transaction_df.at[index, 'fuzzy keyword'] = keyword
                        continue

    # cosine_match
    # Initialize results dictionary
    results_cosine = {category: {'positive': [], 'negative': []} for category in categories_fuzzy}
    # Categorize transactions with fuzzy matches if not already categorized
    for index, row in transaction_df.iterrows():
        if transaction_df.at[index, 'Categorized'] == False:
            for category, keywords in categories_fuzzy.items():
                keyword = cosine_match(row['comment'], keywords)
                if keyword != "":
                #if cosine_match(row['comment'], keywords):
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
                        if transaction_df.at[index, 'fuzzy keyword'] == "":
                            transaction_df.at[index, 'fuzzy keyword'] = keyword
                        continue
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
                        if transaction_df.at[index, 'fuzzy keyword'] == "":
                            transaction_df.at[index, 'fuzzy keyword'] = keyword
                        continue


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
                keyword = fuzzy_match_sequences(row['comment'], keywords)
                if keyword != "":
                #if fuzzy_match_sequences(row['comment'], keywords):
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
                        if transaction_df.at[index, 'fuzzy keyword'] == "":
                            transaction_df.at[index, 'fuzzy keyword'] = keyword
                        continue
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
                        if transaction_df.at[index, 'fuzzy keyword'] == "":
                            transaction_df.at[index, 'fuzzy keyword'] = keyword
                        continue

    # levenshtein_match
    # Initialize results dictionary
    results_levenshtein = {category: {'positive': [], 'negative': []} for category in categories_fuzzy}
    # Categorize transactions with fuzzy matches if not already categorized
    for index, row in transaction_df.iterrows():
        if transaction_df.at[index, 'Categorized'] == False:
            for category, keywords in categories_fuzzy.items():
                keyword = levenshtein_match_sequence(row['comment'], keywords)
                if keyword != "":
                #if levenshtein_match_sequence(row['comment'], keywords):
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
                        if transaction_df.at[index, 'fuzzy keyword'] == "":
                            transaction_df.at[index, 'fuzzy keyword'] = keyword
                        continue
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
                        if transaction_df.at[index, 'fuzzy keyword'] == "":
                            transaction_df.at[index, 'fuzzy keyword'] = keyword
                        continue

    # jaccard_match
    # Initialize results dictionary
    results_jaccard_seq = {category: {'positive': [], 'negative': []} for category in categories_fuzzy}
    # Categorize transactions with fuzzy matches if not already categorized
    for index, row in transaction_df.iterrows():
        if transaction_df.at[index, 'Categorized'] == False:
            for category, keywords in categories_fuzzy.items():
                keyword = jaccard_match_sequence(row['comment'], keywords)
                if keyword != "":
                #if jaccard_match_sequence(row['comment'], keywords):
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
                        if transaction_df.at[index, 'fuzzy keyword'] == "":
                            transaction_df.at[index, 'fuzzy keyword'] = keyword
                        continue
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
                        if transaction_df.at[index, 'fuzzy keyword'] == "":
                            transaction_df.at[index, 'fuzzy keyword'] = keyword
                        continue

    # cosine_match
    # Initialize results dictionary
    results_cosine_seq = {category: {'positive': [], 'negative': []} for category in categories_fuzzy}
    # Categorize transactions with fuzzy matches if not already categorized
    for index, row in transaction_df.iterrows():
        if transaction_df.at[index, 'Categorized'] == False:
            for category, keywords in categories_fuzzy.items():
                keyword = cosine_match_sequence(row['comment'], keywords)
                if keyword != "":
                #if cosine_match_sequence(row['comment'], keywords):
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
                        if transaction_df.at[index, 'fuzzy keyword'] == "":
                            transaction_df.at[index, 'fuzzy keyword'] = keyword
                        continue
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
                        if transaction_df.at[index, 'fuzzy keyword'] == "":
                            transaction_df.at[index, 'fuzzy keyword'] = keyword
                        continue
    '''
    # Print results
    for category, amounts in results.items():
        print(f"Category: {category}")
        try:
            print(f"  Positive Amounts: {sum(amounts['positive'])}")
            print(f"  Negative Amounts: {sum(amounts['negative'])}")
        except:
            print('test')
    print('test')
    '''
    return transaction_df