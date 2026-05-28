import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import accuracy_score
import pickle

# Load dataset
df = pd.read_csv("spam.csv", encoding='latin-1')

# Keep useful columns
df = df[['v1', 'v2']]
df.columns = ['label', 'message']


# Convert labels
df['label'] = df['label'].map({
    'ham': 0,
    'spam': 1
})

# Features and labels
X = df['message']
y = df['label']

# Convert text into numbers
vectorizer = TfidfVectorizer()

X = vectorizer.fit_transform(X)

# Split data
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42
)

# Train model
model = MultinomialNB()

model.fit(X_train, y_train)

# Accuracy
y_pred = model.predict(X_test)

accuracy = accuracy_score(y_test, y_pred)

print("Accuracy:", accuracy)

# Save model
pickle.dump(model, open('model.pkl', 'wb'))
pickle.dump(vectorizer, open('vectorizer.pkl', 'wb'))

print("Model saved successfully!")