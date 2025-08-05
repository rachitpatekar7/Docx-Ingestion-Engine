# rule_embedding.py

import numpy as np
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics.pairwise import cosine_similarity

class RuleEmbedding:
    def __init__(self):
        self.label_encoder = LabelEncoder()
        self.embeddings = {}

    def fit(self, rules):
        """Fit the model to the provided rules."""
        encoded_rules = self.label_encoder.fit_transform(rules)
        self.embeddings = {rule: self._embed_rule(encoded_rule) for rule, encoded_rule in zip(rules, encoded_rules)}

    def _embed_rule(self, encoded_rule):
        """Create a simple embedding for a rule."""
        return np.array([np.sin(encoded_rule), np.cos(encoded_rule)])

    def get_embedding(self, rule):
        """Get the embedding for a specific rule."""
        return self.embeddings.get(rule, None)

    def similarity(self, rule1, rule2):
        """Calculate the cosine similarity between two rules."""
        embedding1 = self.get_embedding(rule1)
        embedding2 = self.get_embedding(rule2)

        if embedding1 is not None and embedding2 is not None:
            return cosine_similarity([embedding1], [embedding2])[0][0]
        return None

    def transform(self, rules):
        """Transform a list of rules into their embeddings."""
        return np.array([self.get_embedding(rule) for rule in rules if self.get_embedding(rule) is not None])