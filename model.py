import inspect
if not hasattr(inspect, 'getargspec'):
    def getargspec(func):
        sig = inspect.signature(func)
        args = []
        varargs = None
        varkw = None
        defaults = ()
        for param in sig.parameters.values():
            if param.kind == param.VAR_POSITIONAL:
                varargs = param.name
            elif param.kind == param.VAR_KEYWORD:
                varkw = param.name
            else:
                args.append(param.name)
                if param.default is not param.empty:
                    defaults += (param.default,)
        return args, varargs, varkw, defaults
    inspect.getargspec = getargspec

from flask import Flask, request, render_template, jsonify
import inspect
import pymorphy2
import re
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from nltk.corpus import stopwords
from translate import Translator

app = Flask(__name__)

# Синонимы
def get_synonyms(word, morph):
    parsed_word = morph.parse(word)[0]
    synonyms = set()
    for form in parsed_word.lexeme:
        synonyms.add(form.word)
    return list(synonyms)

# Лемматизация с синонимами
def lemmatize_text(text, morph, en_stopwords):
    text = text.lower()
    text = re.sub(r'\W', ' ', text)
    words = text.split()
    lemmatized_text_with_synonyms = []
    skip_next = False
    for i, word in enumerate(words):
        if skip_next:
            skip_next = False
            continue
        lemmatized_word = morph.parse(word)[0].normal_form
        if lemmatized_word not in en_stopwords:
            lemmatized_text_with_synonyms.append(lemmatized_word)
            synonyms = get_synonyms(lemmatized_word, morph)
            lemmatized_text_with_synonyms.extend(synonyms)
    return ' '.join(lemmatized_text_with_synonyms)

# Система обратной связи
def update_rating(game_name, new_rating, data):
    if game_name in data['Name'].values:
        idx = data.index[data['Name'] == game_name].tolist()[0]
        total_rating = data.at[idx, 'Rating'] * data.at[idx, 'RatingCount']
        data.at[idx, 'RatingCount'] += 1
        total_rating += new_rating
        data.at[idx, 'Rating'] = total_rating / data.at[idx, 'RatingCount']
        data.to_csv('teambuilding.csv', index=False)

# Перевод
def translate_text(text, src_lang='ru', dest_lang='en'):
    translator = Translator(from_lang=src_lang, to_lang=dest_lang)
    translated_text = translator.translate(text)
    return translated_text

morph = pymorphy2.MorphAnalyzer()
en_stopwords = stopwords.words('english')

data = pd.read_csv('teambuilding.csv', delimiter=',', quotechar='"')
data['text'] = data['Name'].astype(str) + ' ' + data['Type'].astype(str) + ' ' + data['Group'].astype(str) + ' ' + data['!Active'].astype(str)
data['text'] = data['text'].apply(lambda x: lemmatize_text(x, morph, en_stopwords))

vectorizer = TfidfVectorizer()
tfidf_matrix = vectorizer.fit_transform(data['text'])

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/recommend', methods=['POST'])
def recommend():
    team_description = request.form['description']
    translated_description = translate_text(team_description)
    description_lemmatized = lemmatize_text(translated_description, morph, en_stopwords)
    description_tfidf = vectorizer.transform([description_lemmatized])
    cosine_similarities = cosine_similarity(description_tfidf, tfidf_matrix).flatten()
    related_docs_indices = cosine_similarities.argsort()[-1:-6:-1]
    recommended_activities = data.iloc[related_docs_indices]
    recommended_activities_sorted = recommended_activities.sort_values(by='Rating', ascending=False)
    recommended_activities_dict = recommended_activities_sorted[['Name', 'Instruction', 'Rating', 'Type', 'Active']].to_dict(orient='records')
    return jsonify(recommended_activities_dict)

@app.route('/rate', methods=['POST'])
def rate():
    game_name = request.form['game_name']
    new_rating = float(request.form['rating'])
    update_rating(game_name, new_rating, data)
    return jsonify({"status": "success"})

if __name__ == '__main__':
    app.run(debug=False)
