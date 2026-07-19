import json
import random
import re

# Default dictionary containing synonyms for common film, award, and industry-related terms.
DEFAULT_SYNONYMS = {
    "win": ["secure", "obtain", "claim", "receive", "take home", "capture"],
    "wins": ["secures", "claims", "receives", "takes home", "captures"],
    "won": ["secured", "claimed", "received", "took home", "captured"],
    "nominate": ["propose", "put forward", "name", "select"],
    "nominated": ["proposed", "put forward", "named", "selected"],
    "nomination": ["nod", "selection", "mention"],
    "nominations": ["nods", "selections", "mentions"],
    "award": ["prize", "honor", "laurel", "accolade"],
    "awards": ["prizes", "honors", "laurels", "accolades"],
    "film": ["movie", "feature", "motion picture", "title"],
    "films": ["movies", "features", "motion pictures", "titles"],
    "director": ["filmmaker", "helmer", "director"],
    "star": ["feature", "showcase", "headline"],
    "starred": ["featured", "showcased", "headlined"],
    "release": ["launch", "premiere", "debut"],
    "released": ["launched", "premiered", "debuted"],
    "outstanding": ["exceptional", "distinguished", "remarkable", "stellar"],
    "acclaimed": ["celebrated", "lauded", "renowned", "praised"],
    "prestigious": ["esteemed", "reputable", "distinguished", "celebrated"]
}

class TextParaphraser:
    """
    A local text processing module designed for data augmentation, synonym substitution,
    and syntactic structural rotation.
    """
    def __init__(self, custom_dict_path=None):
        if custom_dict_path:
            try:
                with open(custom_dict_path, "r", encoding="utf-8") as f:
                    self.synonyms = json.load(f)
            except Exception as e:
                print(f"Warning: Could not load custom dictionary ({e}). Using default values.")
                self.synonyms = DEFAULT_SYNONYMS
        else:
            self.synonyms = DEFAULT_SYNONYMS

    def replace_synonyms(self, text: str) -> str:
        """
        Tokenizes input string and substitutes matching terms with synonyms from the dictionary
        while preserving case-sensitivity and suffix punctuation.
        """
        words = text.split()
        new_words = []
        
        for word in words:
            # Isolate suffix punctuation (e.g. commas, periods)
            match_punc = re.search(r'([^\w]*)$', word)
            punc = match_punc.group(1) if match_punc else ''
            clean_word = re.sub(r'[^\w]', '', word)
            clean_word_lower = clean_word.lower()

            if clean_word_lower in self.synonyms:
                candidates = self.synonyms[clean_word_lower]
                replacement = random.choice(candidates)
                
                # Maintain original capitalization profile
                if len(clean_word) > 0:
                    if clean_word.isupper():
                        replacement = replacement.upper()
                    elif clean_word[0].isupper():
                        replacement = replacement[0].upper() + replacement[1:]
                
                new_words.append(replacement + punc)
            else:
                new_words.append(word)
                
        return " ".join(new_words)

    def grammar_rotation(self, text: str) -> str:
        """
        Alters common sentence configurations to modify grammatical patterns.
        """
        # Rotation 1: "Directed by X, the film Y..." -> "The film Y, directed by X..."
        pattern_directed = r"Directed by ([\w\s]+), the film ([\w\s'\-\:\,\.]+)\s*(won|received|was)"
        def rot_directed(match):
            director = match.group(1).strip()
            film = match.group(2).strip()
            action = match.group(3).strip()
            return f"The film {film}, which was directed by {director}, {action}"

        text = re.sub(pattern_directed, rot_directed, text, flags=re.IGNORECASE)

        # Rotation 2: "X won the Y award for Z" -> "The Y award for Z was won by X"
        pattern_won = r"([\w\s]+) won the ([\w\s]+) award for ([\w\s]+)"
        def rot_won(match):
            winner = match.group(1).strip()
            award = match.group(2).strip()
            category = match.group(3).strip()
            return f"The {award} award for {category} was won by {winner}"

        text = re.sub(pattern_won, rot_won, text, flags=re.IGNORECASE)

        return text

    def paraphrase(self, text: str) -> str:
        """
        Performs structural grammar rotation followed by synonym replacements.
        """
        rotated = self.grammar_rotation(text)
        return self.replace_synonyms(rotated)

# Quick demonstration helper
if __name__ == "__main__":
    paraphraser = TextParaphraser()
    
    sample_text = "Directed by Christopher Nolan, the film Oppenheimer won the Best Picture award for Outstanding Achievement."
    print("Original Text:\n", sample_text)
    print("\nParaphrased Text:\n", paraphraser.paraphrase(sample_text))
