"""
CEFR Seviyelerine Göre Kelime Yeniden Etiketleme

Bu script, kelimeleri aşağıdaki kriterlere göre CEFR seviyelerine yeniden etiketler:
- A1: En temel, günlük hayatta sık kullanılan kelimeler (merhaba, ev, su, yemek vb.)
- A2: Temel kelimeler, biraz daha geniş (alışveriş, seyahat, basit fiiller)
- B1: Orta seviye, soyut kavramlar başlıyor (iş, eğitim, duygular)
- B2: İleri kelimeler, akademik ve profesyonel (analiz, strateji, karmaşık fiiller)
- C1: Gelişmiş, nadir kullanılan kelimeler
- C2: Çok nadir, uzman seviye kelimeler
"""

import sqlite3
import os

# Temel CEFR kelime listeleri (İngilizce öğretimi standartlarına göre)
A1_CORE_WORDS = {
    # Selamlaşma & Temel
    'hello', 'hi', 'bye', 'goodbye', 'yes', 'no', 'please', 'thank', 'thanks', 'sorry',
    'name', 'my', 'your', 'i', 'you', 'he', 'she', 'it', 'we', 'they',
    
    # Sayılar
    'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten',
    'zero', 'hundred', 'thousand', 'first', 'second', 'third',
    
    # Renkler
    'red', 'blue', 'green', 'yellow', 'black', 'white', 'orange', 'pink', 'purple', 'brown', 'gray', 'grey',
    
    # Aile
    'mother', 'father', 'mom', 'dad', 'mum', 'sister', 'brother', 'family', 'baby', 'child', 'children',
    'son', 'daughter', 'husband', 'wife', 'parent', 'grandma', 'grandpa', 'grandmother', 'grandfather',
    
    # Ev & Eşyalar
    'house', 'home', 'room', 'door', 'window', 'bed', 'table', 'chair', 'kitchen', 'bathroom',
    'garden', 'floor', 'wall', 'roof', 'key', 'lamp', 'clock', 'phone', 'television', 'tv',
    
    # Yiyecek & İçecek
    'food', 'water', 'milk', 'coffee', 'tea', 'bread', 'rice', 'egg', 'meat', 'fish',
    'chicken', 'fruit', 'apple', 'banana', 'orange', 'vegetable', 'potato', 'tomato', 'cheese', 'butter',
    'sugar', 'salt', 'drink', 'eat', 'hungry', 'thirsty', 'breakfast', 'lunch', 'dinner',
    
    # Vücut
    'body', 'head', 'face', 'eye', 'eyes', 'ear', 'ears', 'nose', 'mouth', 'hand', 'hands',
    'arm', 'arms', 'leg', 'legs', 'foot', 'feet', 'finger', 'hair', 'tooth', 'teeth',
    
    # Zaman
    'time', 'day', 'night', 'morning', 'afternoon', 'evening', 'today', 'tomorrow', 'yesterday',
    'week', 'month', 'year', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday',
    'january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december',
    'hour', 'minute', 'second', 'now', 'later', 'soon', 'always', 'never', 'sometimes',
    
    # Temel Fiiller
    'be', 'is', 'am', 'are', 'was', 'were', 'have', 'has', 'had', 'do', 'does', 'did',
    'go', 'come', 'see', 'look', 'give', 'take', 'make', 'put', 'get', 'say', 'tell',
    'know', 'think', 'want', 'need', 'like', 'love', 'help', 'work', 'play', 'read', 'write',
    'speak', 'listen', 'hear', 'open', 'close', 'start', 'stop', 'run', 'walk', 'sit', 'stand',
    'sleep', 'wake', 'buy', 'sell', 'pay', 'live', 'die', 'born', 'learn', 'teach', 'study',
    
    # Temel Sıfatlar
    'big', 'small', 'long', 'short', 'tall', 'old', 'new', 'young', 'good', 'bad',
    'hot', 'cold', 'warm', 'cool', 'fast', 'slow', 'easy', 'hard', 'happy', 'sad',
    'nice', 'beautiful', 'ugly', 'clean', 'dirty', 'open', 'closed', 'right', 'wrong', 'same', 'different',
    'full', 'empty', 'rich', 'poor', 'cheap', 'expensive', 'free', 'busy', 'ready', 'late', 'early',
    
    # Yer & Yön
    'here', 'there', 'where', 'up', 'down', 'left', 'right', 'in', 'out', 'on', 'off',
    'front', 'back', 'top', 'bottom', 'inside', 'outside', 'near', 'far', 'next', 'behind',
    
    # Ulaşım
    'car', 'bus', 'train', 'plane', 'bike', 'bicycle', 'taxi', 'boat', 'ship', 'road', 'street',
    
    # Diğer Temel
    'man', 'woman', 'boy', 'girl', 'person', 'people', 'friend', 'student', 'teacher', 'doctor',
    'book', 'pen', 'paper', 'school', 'class', 'money', 'job', 'shop', 'store', 'market',
    'city', 'town', 'country', 'world', 'sun', 'moon', 'star', 'sky', 'tree', 'flower',
    'dog', 'cat', 'bird', 'animal', 'weather', 'rain', 'snow', 'wind', 'cloud',
    'thing', 'place', 'way', 'idea', 'problem', 'question', 'answer',
    
    # Ek Temel Kelimeler (sık kullanılan)
    'keep', 'kept', 'find', 'found', 'lose', 'lost', 'win', 'won', 'try', 'use', 'used',
    'call', 'called', 'ask', 'asked', 'wait', 'feel', 'felt', 'seem', 'show', 'turn',
    'leave', 'left', 'bring', 'brought', 'hold', 'held', 'begin', 'began', 'end', 'move',
    'every', 'some', 'any', 'all', 'many', 'much', 'few', 'little', 'more', 'most', 'other',
    'also', 'too', 'very', 'really', 'just', 'only', 'still', 'even', 'well', 'again',
    'about', 'after', 'before', 'between', 'during', 'through', 'under', 'over', 'into', 'without',
    'because', 'if', 'when', 'while', 'until', 'although', 'though', 'since', 'than', 'that', 'this',
    'which', 'who', 'what', 'how', 'why', 'could', 'would', 'should', 'must', 'might', 'can', 'will',
    'being', 'been', 'having', 'doing', 'going', 'coming', 'looking', 'making', 'taking', 'getting',
    'life', 'year', 'years', 'part', 'hand', 'side', 'line', 'word', 'words', 'point',
    'number', 'group', 'home', 'water', 'long', 'each', 'these', 'those', 'such', 'both',
    'own', 'same', 'different', 'another', 'kind', 'sort', 'type', 'lot', 'lots',
    'ago', 'yet', 'already', 'else', 'enough', 'quite', 'rather', 'almost', 'maybe', 'perhaps',
    'let', 'lets', 'got', 'getting', 'went', 'going', 'seen', 'seeing', 'done', 'doing',
    'everything', 'something', 'anything', 'nothing', 'everyone', 'someone', 'anyone', 'nobody',
    'somewhere', 'anywhere', 'everywhere', 'nowhere', 'whenever', 'wherever', 'whatever', 'however',
    'herself', 'himself', 'itself', 'myself', 'yourself', 'themselves', 'ourselves',
    'able', 'possible', 'important', 'sure', 'true', 'real', 'clear', 'certain', 'best', 'better', 'worse', 'worst',
    'ago', 'either', 'neither', 'together', 'alone', 'else', 'away', 'around', 'across', 'along',
    'above', 'below', 'towards', 'forward', 'against', 'beside', 'beyond', 'within',
    'light', 'dark', 'fire', 'air', 'ground', 'earth', 'stone', 'rock', 'wood', 'metal', 'glass', 'plastic',
    'box', 'bag', 'page', 'sign', 'letter', 'email', 'message', 'news', 'story', 'music', 'song', 'film', 'movie',
    'game', 'toy', 'ball', 'card', 'gift', 'present', 'party', 'holiday', 'birthday',
    'chance', 'luck', 'hope', 'fear', 'worry', 'care', 'attention', 'reason', 'cause', 'effect', 'result',
}

A2_CORE_WORDS = {
    # Genişletilmiş Yiyecek
    'salad', 'soup', 'sandwich', 'cake', 'chocolate', 'ice', 'cream', 'pizza', 'pasta', 'noodle',
    'sauce', 'spice', 'pepper', 'onion', 'garlic', 'carrot', 'lettuce', 'cucumber', 'bean', 'pea',
    'grape', 'strawberry', 'lemon', 'melon', 'cherry', 'peach', 'pear', 'pineapple',
    'beef', 'pork', 'lamb', 'turkey', 'duck', 'seafood', 'shrimp', 'lobster', 'crab',
    'juice', 'soda', 'wine', 'beer', 'alcohol', 'bottle', 'glass', 'cup', 'plate', 'bowl', 'fork', 'knife', 'spoon',
    
    # Giyim
    'clothes', 'shirt', 'pants', 'trousers', 'jeans', 'dress', 'skirt', 'jacket', 'coat', 'sweater',
    'shoes', 'boots', 'socks', 'hat', 'cap', 'scarf', 'gloves', 'tie', 'belt', 'bag', 'pocket',
    'button', 'zipper', 'size', 'wear', 'fit', 'fashion', 'style',
    
    # Alışveriş
    'price', 'cost', 'discount', 'sale', 'receipt', 'cash', 'card', 'credit', 'change', 'tip',
    'customer', 'shopping', 'mall', 'department', 'checkout', 'basket', 'cart',
    
    # Seyahat & Turizm
    'travel', 'trip', 'vacation', 'holiday', 'tour', 'tourist', 'passport', 'visa', 'luggage', 'suitcase',
    'hotel', 'reservation', 'booking', 'flight', 'airport', 'station', 'ticket', 'platform',
    'beach', 'mountain', 'lake', 'river', 'sea', 'ocean', 'island', 'desert', 'jungle',
    'map', 'guide', 'camera', 'photo', 'picture', 'souvenir',
    
    # Ev Detay
    'apartment', 'flat', 'building', 'stairs', 'elevator', 'lift', 'balcony', 'terrace', 'basement', 'attic',
    'living', 'dining', 'bedroom', 'guest', 'furniture', 'sofa', 'couch', 'desk', 'shelf', 'drawer',
    'curtain', 'carpet', 'rug', 'mirror', 'fridge', 'refrigerator', 'oven', 'stove', 'microwave', 'dishwasher',
    'washing', 'machine', 'dryer', 'iron', 'vacuum', 'broom', 'mop',
    
    # Sağlık Temel
    'health', 'healthy', 'sick', 'ill', 'pain', 'hurt', 'fever', 'cold', 'flu', 'headache',
    'medicine', 'pill', 'tablet', 'hospital', 'clinic', 'nurse', 'patient', 'appointment', 'check',
    'exercise', 'gym', 'sport', 'fitness', 'diet', 'weight', 'muscle',
    
    # Meslekler
    'job', 'career', 'profession', 'boss', 'manager', 'employee', 'worker', 'colleague', 'team',
    'lawyer', 'engineer', 'scientist', 'artist', 'musician', 'actor', 'writer', 'journalist', 'photographer',
    'chef', 'waiter', 'waitress', 'driver', 'pilot', 'police', 'firefighter', 'soldier', 'farmer',
    'secretary', 'accountant', 'banker', 'salesman', 'mechanic', 'electrician', 'plumber',
    
    # Duygular Genişletilmiş
    'angry', 'afraid', 'scared', 'worried', 'nervous', 'excited', 'surprised', 'bored', 'tired', 'relaxed',
    'proud', 'jealous', 'lonely', 'confused', 'disappointed', 'embarrassed', 'ashamed',
    'emotion', 'feeling', 'mood', 'stress', 'pressure',
    
    # Hobiler
    'hobby', 'interest', 'collection', 'music', 'song', 'dance', 'art', 'paint', 'draw', 'game',
    'movie', 'film', 'theater', 'concert', 'show', 'performance', 'exhibition', 'museum', 'gallery',
    'sport', 'football', 'soccer', 'basketball', 'tennis', 'swimming', 'running', 'cycling', 'hiking',
    'cooking', 'baking', 'gardening', 'fishing', 'camping', 'photography',
    
    # Teknoloji Temel
    'computer', 'laptop', 'tablet', 'smartphone', 'internet', 'website', 'email', 'message', 'text',
    'password', 'username', 'account', 'download', 'upload', 'search', 'click', 'screen', 'keyboard', 'mouse',
    
    # İlişkiler
    'relationship', 'boyfriend', 'girlfriend', 'couple', 'wedding', 'marriage', 'divorce', 'single', 'partner',
    'neighbor', 'guest', 'visitor', 'stranger', 'enemy', 'classmate', 'roommate',
    
    # Fiiller Genişletilmiş
    'arrive', 'leave', 'return', 'enter', 'exit', 'cross', 'pass', 'reach', 'turn', 'move',
    'carry', 'bring', 'send', 'receive', 'deliver', 'order', 'pack', 'unpack',
    'cook', 'bake', 'fry', 'boil', 'mix', 'cut', 'slice', 'chop', 'pour', 'serve',
    'wash', 'clean', 'dry', 'fix', 'repair', 'break', 'damage', 'destroy',
    'choose', 'decide', 'plan', 'prepare', 'organize', 'arrange', 'cancel', 'postpone',
    'invite', 'accept', 'refuse', 'apologize', 'forgive', 'blame', 'complain', 'suggest', 'recommend',
    'promise', 'agree', 'disagree', 'argue', 'discuss', 'explain', 'describe', 'mention',
    'remember', 'forget', 'recognize', 'realize', 'understand', 'wonder', 'guess', 'suppose', 'expect', 'hope', 'wish',
    'try', 'attempt', 'succeed', 'fail', 'win', 'lose', 'compete', 'practice', 'improve',
    'save', 'spend', 'waste', 'earn', 'borrow', 'lend', 'owe', 'afford',
}

B1_CORE_WORDS = {
    # İş & Kariyer
    'business', 'company', 'corporation', 'organization', 'industry', 'factory', 'manufacture',
    'office', 'department', 'branch', 'headquarters', 'meeting', 'conference', 'presentation',
    'interview', 'resume', 'application', 'hire', 'employ', 'promote', 'resign', 'retire', 'fire', 'layoff',
    'salary', 'wage', 'income', 'bonus', 'benefit', 'insurance', 'pension', 'contract', 'agreement',
    'deadline', 'schedule', 'shift', 'overtime', 'vacation', 'leave',
    'client', 'customer', 'supplier', 'partner', 'competitor', 'stakeholder',
    'project', 'task', 'assignment', 'responsibility', 'duty', 'goal', 'objective', 'target',
    'report', 'document', 'file', 'folder', 'memo', 'proposal', 'budget',
    
    # Eğitim İleri
    'education', 'university', 'college', 'degree', 'diploma', 'certificate', 'qualification',
    'course', 'lecture', 'seminar', 'workshop', 'curriculum', 'syllabus',
    'exam', 'test', 'quiz', 'assignment', 'homework', 'essay', 'thesis', 'dissertation',
    'grade', 'score', 'pass', 'fail', 'graduate', 'undergraduate', 'postgraduate', 'scholarship',
    'professor', 'lecturer', 'tutor', 'mentor', 'dean', 'principal',
    'research', 'study', 'experiment', 'laboratory', 'theory', 'hypothesis', 'conclusion',
    'knowledge', 'skill', 'ability', 'talent', 'intelligence', 'creativity',
    
    # Sağlık İleri
    'treatment', 'therapy', 'surgery', 'operation', 'injection', 'vaccine', 'prescription',
    'symptom', 'diagnosis', 'condition', 'disease', 'illness', 'infection', 'virus', 'bacteria',
    'allergy', 'asthma', 'diabetes', 'cancer', 'heart', 'blood', 'pressure', 'cholesterol',
    'mental', 'physical', 'psychological', 'emotional', 'anxiety', 'depression',
    'recovery', 'rehabilitation', 'prevention', 'cure', 'heal',
    'specialist', 'surgeon', 'therapist', 'psychiatrist', 'psychologist',
    
    # Hukuk & Toplum
    'law', 'legal', 'illegal', 'crime', 'criminal', 'victim', 'witness', 'evidence', 'proof',
    'court', 'judge', 'jury', 'trial', 'verdict', 'sentence', 'prison', 'jail',
    'police', 'officer', 'detective', 'investigation', 'arrest', 'charge', 'accuse', 'guilty', 'innocent',
    'right', 'freedom', 'justice', 'equality', 'discrimination', 'racism', 'sexism',
    'government', 'politics', 'politician', 'election', 'vote', 'democracy', 'republic',
    'parliament', 'congress', 'senate', 'minister', 'president', 'prime',
    'policy', 'regulation', 'rule', 'ban', 'permit', 'license',
    'citizen', 'immigrant', 'refugee', 'nationality', 'identity',
    
    # Çevre
    'environment', 'nature', 'ecology', 'ecosystem', 'climate', 'global', 'warming',
    'pollution', 'waste', 'trash', 'garbage', 'recycle', 'reuse', 'reduce',
    'energy', 'power', 'electricity', 'fuel', 'oil', 'gas', 'coal', 'nuclear', 'solar', 'wind',
    'renewable', 'sustainable', 'conservation', 'protection', 'endangered', 'extinct',
    'forest', 'rainforest', 'jungle', 'wildlife', 'species', 'habitat',
    'atmosphere', 'ozone', 'carbon', 'emission', 'greenhouse',
    
    # Medya & İletişim
    'media', 'news', 'newspaper', 'magazine', 'article', 'headline', 'reporter', 'editor',
    'broadcast', 'channel', 'program', 'series', 'episode', 'documentary',
    'advertisement', 'commercial', 'promotion', 'marketing', 'brand', 'logo',
    'social', 'network', 'platform', 'content', 'post', 'share', 'like', 'comment', 'follow', 'subscribe',
    'information', 'data', 'statistics', 'survey', 'poll', 'opinion', 'view',
    'publish', 'print', 'distribute', 'circulate',
    
    # Finans
    'finance', 'financial', 'economy', 'economic', 'market', 'stock', 'share', 'bond', 'investment',
    'bank', 'account', 'savings', 'loan', 'mortgage', 'debt', 'credit', 'interest', 'rate',
    'tax', 'income', 'profit', 'loss', 'revenue', 'expense', 'cost', 'fee', 'charge',
    'currency', 'exchange', 'dollar', 'euro', 'pound', 'yen',
    'inflation', 'recession', 'growth', 'decline', 'crisis',
    
    # Soyut Kavramlar
    'concept', 'theory', 'principle', 'philosophy', 'logic', 'reason', 'argument',
    'opinion', 'perspective', 'viewpoint', 'attitude', 'belief', 'value', 'moral', 'ethics',
    'culture', 'tradition', 'custom', 'heritage', 'identity', 'diversity',
    'society', 'community', 'population', 'generation', 'trend', 'phenomenon',
    'advantage', 'disadvantage', 'benefit', 'drawback', 'consequence', 'impact', 'effect', 'influence',
    'cause', 'result', 'outcome', 'solution', 'alternative', 'option', 'choice',
    'opportunity', 'challenge', 'obstacle', 'difficulty', 'issue', 'matter', 'concern',
    'success', 'failure', 'achievement', 'progress', 'development', 'improvement',
    'quality', 'quantity', 'standard', 'level', 'degree', 'extent', 'range', 'scope',
    
    # Fiiller B1
    'achieve', 'accomplish', 'complete', 'fulfill', 'obtain', 'acquire', 'gain',
    'develop', 'establish', 'create', 'produce', 'generate', 'provide', 'supply', 'offer',
    'maintain', 'preserve', 'protect', 'defend', 'support', 'assist', 'contribute',
    'increase', 'decrease', 'grow', 'expand', 'extend', 'reduce', 'limit', 'restrict',
    'compare', 'contrast', 'distinguish', 'identify', 'define', 'classify', 'categorize',
    'analyze', 'examine', 'investigate', 'explore', 'discover', 'reveal', 'demonstrate', 'prove',
    'consider', 'evaluate', 'assess', 'judge', 'determine', 'conclude',
    'communicate', 'express', 'convey', 'indicate', 'imply', 'suggest', 'propose',
    'influence', 'affect', 'shape', 'transform', 'convert', 'adapt', 'adjust', 'modify',
    'require', 'demand', 'insist', 'urge', 'encourage', 'motivate', 'inspire', 'persuade', 'convince',
    'prevent', 'avoid', 'escape', 'survive', 'recover', 'overcome',
    'represent', 'reflect', 'symbolize', 'illustrate', 'portray',
    'connect', 'link', 'relate', 'associate', 'combine', 'integrate', 'separate', 'divide', 'split',
    'organize', 'structure', 'arrange', 'coordinate', 'manage', 'handle', 'deal', 'cope',
}

B2_CORE_WORDS = {
    # Akademik & Bilimsel
    'academic', 'scholarly', 'intellectual', 'theoretical', 'empirical', 'analytical', 'critical',
    'methodology', 'framework', 'paradigm', 'criterion', 'criteria', 'parameter', 'variable',
    'hypothesis', 'thesis', 'proposition', 'assumption', 'premise', 'inference', 'deduction', 'induction',
    'correlation', 'causation', 'regression', 'deviation', 'distribution', 'proportion', 'ratio',
    'phenomenon', 'observation', 'interpretation', 'implication', 'significance', 'validity', 'reliability',
    'abstract', 'concrete', 'tangible', 'intangible', 'subjective', 'objective',
    'comprehensive', 'extensive', 'intensive', 'thorough', 'rigorous', 'systematic', 'coherent',
    
    # İş Profesyonel
    'strategy', 'strategic', 'tactic', 'tactical', 'initiative', 'implementation', 'execution',
    'innovation', 'entrepreneurship', 'startup', 'venture', 'merger', 'acquisition', 'partnership',
    'revenue', 'turnover', 'margin', 'overhead', 'capital', 'asset', 'liability', 'equity',
    'forecast', 'projection', 'estimate', 'assessment', 'valuation', 'appraisal',
    'optimization', 'efficiency', 'productivity', 'performance', 'benchmark', 'metric', 'indicator',
    'stakeholder', 'shareholder', 'investor', 'entrepreneur', 'executive', 'consultant',
    'negotiate', 'bargain', 'compromise', 'collaborate', 'delegate', 'supervise', 'oversee',
    'restructure', 'downsize', 'outsource', 'streamline', 'consolidate',
    
    # Hukuk & Yönetim İleri
    'legislation', 'regulation', 'statute', 'amendment', 'constitution', 'jurisdiction',
    'litigation', 'prosecution', 'defendant', 'plaintiff', 'attorney', 'counsel', 'advocate',
    'compliance', 'enforcement', 'sanction', 'penalty', 'liability', 'obligation', 'provision',
    'bureaucracy', 'administration', 'governance', 'sovereignty', 'autonomy', 'federation',
    'diplomacy', 'treaty', 'alliance', 'coalition', 'summit', 'negotiation', 'mediation', 'arbitration',
    'ideology', 'doctrine', 'manifesto', 'propaganda', 'rhetoric', 'discourse',
    
    # Psikoloji & Sosyoloji
    'psychology', 'sociology', 'anthropology', 'behavior', 'behaviour', 'cognition', 'perception',
    'consciousness', 'subconscious', 'unconscious', 'instinct', 'intuition', 'impulse',
    'personality', 'temperament', 'character', 'trait', 'disposition', 'tendency',
    'motivation', 'incentive', 'stimulus', 'response', 'reaction', 'reflex',
    'trauma', 'phobia', 'obsession', 'compulsion', 'addiction', 'disorder',
    'therapy', 'counseling', 'intervention', 'rehabilitation', 'recovery',
    'prejudice', 'stereotype', 'bias', 'assumption', 'perception', 'misconception',
    'conformity', 'deviation', 'norm', 'expectation', 'sanction',
    
    # Teknoloji İleri
    'algorithm', 'encryption', 'authentication', 'authorization', 'infrastructure', 'architecture',
    'interface', 'protocol', 'bandwidth', 'latency', 'scalability', 'compatibility',
    'database', 'server', 'cloud', 'virtual', 'simulation', 'automation', 'robotics',
    'artificial', 'intelligence', 'machine', 'learning', 'neural', 'network',
    'cybersecurity', 'malware', 'virus', 'hacking', 'breach', 'vulnerability',
    'innovation', 'disruption', 'transformation', 'digitalization', 'modernization',
    
    # Çevre İleri
    'sustainability', 'biodiversity', 'deforestation', 'desertification', 'erosion', 'degradation',
    'contamination', 'emission', 'discharge', 'effluent', 'residue', 'toxin', 'pollutant',
    'renewable', 'non-renewable', 'alternative', 'conventional', 'fossil',
    'conservation', 'preservation', 'restoration', 'mitigation', 'adaptation',
    'ecosystem', 'biosphere', 'habitat', 'niche', 'food chain', 'predator', 'prey',
    
    # Ekonomi İleri
    'macroeconomics', 'microeconomics', 'fiscal', 'monetary', 'aggregate', 'domestic',
    'inflation', 'deflation', 'stagflation', 'recession', 'depression', 'prosperity',
    'commodity', 'derivative', 'futures', 'option', 'portfolio', 'diversification',
    'subsidy', 'tariff', 'quota', 'embargo', 'sanction', 'protectionism',
    'privatization', 'nationalization', 'deregulation', 'liberalization',
    'monopoly', 'oligopoly', 'cartel', 'conglomerate', 'multinational',
    
    # Sıfatlar B2
    'sophisticated', 'elaborate', 'intricate', 'complex', 'complicated', 'convoluted',
    'profound', 'superficial', 'trivial', 'significant', 'substantial', 'marginal', 'negligible',
    'explicit', 'implicit', 'inherent', 'intrinsic', 'extrinsic', 'fundamental', 'underlying',
    'prevalent', 'predominant', 'prominent', 'conspicuous', 'obscure', 'subtle', 'nuanced',
    'plausible', 'feasible', 'viable', 'sustainable', 'pragmatic', 'hypothetical', 'speculative',
    'ambiguous', 'vague', 'precise', 'accurate', 'approximate', 'tentative', 'definitive',
    'controversial', 'contentious', 'disputed', 'unanimous', 'consensual',
    'unprecedented', 'inevitable', 'imminent', 'impending', 'prospective', 'retrospective',
    'contemporary', 'conventional', 'traditional', 'innovative', 'revolutionary', 'radical',
    
    # Fiiller B2
    'articulate', 'elaborate', 'elucidate', 'clarify', 'specify', 'stipulate', 'designate',
    'encompass', 'comprise', 'constitute', 'entail', 'necessitate', 'warrant', 'justify',
    'scrutinize', 'scrutinise', 'monitor', 'audit', 'verify', 'validate', 'corroborate', 'substantiate',
    'hypothesize', 'postulate', 'conjecture', 'speculate', 'presume', 'infer', 'deduce',
    'synthesize', 'integrate', 'consolidate', 'unify', 'harmonize', 'reconcile', 'align',
    'diminish', 'minimize', 'mitigate', 'alleviate', 'exacerbate', 'aggravate', 'intensify',
    'perpetuate', 'sustain', 'uphold', 'reinforce', 'undermine', 'jeopardize', 'compromise',
    'facilitate', 'expedite', 'accelerate', 'impede', 'hinder', 'obstruct', 'inhibit', 'constrain',
    'allocate', 'distribute', 'disperse', 'concentrate', 'accumulate', 'deplete', 'exhaust',
    'advocate', 'endorse', 'sanction', 'denounce', 'condemn', 'criticize', 'critique',
    'transcend', 'surpass', 'exceed', 'outweigh', 'predominate', 'prevail', 'supersede',
}

C1_CORE_WORDS = {
    'aberration', 'abhorrent', 'abrogate', 'abstemious', 'abstruse', 'accentuate', 'accolade',
    'acrimony', 'admonish', 'adroit', 'adversarial', 'aesthetic', 'affable', 'aggrandize',
    'alacrity', 'altruism', 'amalgamate', 'ameliorate', 'anachronism', 'antithesis', 'apathy',
    'apprehension', 'arbitrary', 'archaic', 'arduous', 'articulate', 'ascertain', 'assiduous',
    'audacious', 'auspicious', 'austere', 'avarice', 'benevolent', 'beseech', 'blatant',
    'bolster', 'bombastic', 'brevity', 'burgeon', 'cacophony', 'candid', 'capricious',
    'catalyst', 'caustic', 'circumspect', 'clandestine', 'clemency', 'coalesce', 'cogent',
    'commensurate', 'compendium', 'complacent', 'conciliatory', 'concomitant', 'condone',
    'confluence', 'congenial', 'conjecture', 'connoisseur', 'consecrate', 'conspicuous',
    'consummate', 'contentious', 'contingent', 'contrite', 'conundrum', 'conventional',
    'copious', 'corroborate', 'credulous', 'culminate', 'cursory', 'cynical', 'debilitate',
    'decorum', 'deferential', 'defunct', 'deleterious', 'delineate', 'demeanor', 'denounce',
    'deprecate', 'deride', 'desultory', 'deter', 'detrimental', 'diatribe', 'dichotomy',
    'didactic', 'diffident', 'digress', 'diligent', 'discern', 'discreet', 'discrete',
    'disdain', 'disparage', 'disparate', 'disseminate', 'dissonance', 'divergent', 'doctrine',
    'dogmatic', 'dubious', 'duplicity', 'ebullient', 'eclectic', 'edify', 'efficacy',
    'egalitarian', 'egregious', 'elicit', 'eloquent', 'elucidate', 'emancipate', 'embellish',
    'empirical', 'emulate', 'endemic', 'enervate', 'engender', 'enigmatic', 'enmity',
    'ephemeral', 'epitome', 'equanimity', 'equivocal', 'eradicate', 'erroneous', 'erudite',
    'eschew', 'esoteric', 'espouse', 'ethereal', 'euphemism', 'evanescent', 'exacerbate',
    'exculpate', 'exemplary', 'exhaustive', 'exigent', 'exonerate', 'expedient', 'explicit',
    'extenuate', 'extraneous', 'extricate', 'facetious', 'facilitate', 'fallacious', 'fastidious',
    'fathom', 'fecund', 'felicitous', 'fervent', 'flagrant', 'fledgling', 'florid', 'foment',
    'forestall', 'formidable', 'fortuitous', 'fractious', 'frugal', 'furtive', 'galvanize',
}

def get_db_path():
    """Veritabanı yolunu al."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(os.path.dirname(script_dir), 'app.db')

def calculate_word_difficulty(word, pos=None, length=None):
    """Kelime zorluğunu hesapla."""
    word_lower = word.lower().strip()
    
    # Geçersiz karakterler varsa C1 yap (www, sayılar vb.)
    if not word_lower.isalpha():
        return 'C1'
    
    # Çok kısa kelimeler (2 harf altı) - muhtemelen kısaltma
    if len(word_lower) < 2:
        return 'C1'
    
    # Önce bilinen listelerde ara - SADECE bu listeler A1 olabilir
    if word_lower in A1_CORE_WORDS:
        return 'A1'
    if word_lower in A2_CORE_WORDS:
        return 'A2'
    if word_lower in B1_CORE_WORDS:
        return 'B1'
    if word_lower in B2_CORE_WORDS:
        return 'B2'
    if word_lower in C1_CORE_WORDS:
        return 'C1'
    
    # Liste dışındaki kelimeler için sezgisel analiz
    word_len = len(word_lower)
    
    # Sesli harf kontrolü - İngilizce'de her kelimede en az bir sesli olmalı
    vowels = set('aeiou')
    vowel_count = sum(1 for c in word_lower if c in vowels)
    consonant_count = word_len - vowel_count
    
    # Sesli harf oranı çok düşük veya yüksekse, garip kelime
    if vowel_count == 0 or (word_len >= 4 and vowel_count / word_len < 0.15):
        return 'C1'  # "qwrty" gibi kelimeler
    
    # Ardışık ünsüz kontrolü (4+ ardışık ünsüz nadir)
    max_consonants = 0
    current_consonants = 0
    for c in word_lower:
        if c not in vowels:
            current_consonants += 1
            max_consonants = max(max_consonants, current_consonants)
        else:
            current_consonants = 0
    
    if max_consonants >= 4:
        return 'C1'  # "rhythms" gibi zor kelimeler
    
    # Uzun ve karmaşık kelimeler zor
    if word_len >= 14:
        return 'C1'
    elif word_len >= 11:
        return 'B2'
    elif word_len >= 9:
        return 'B1'
    
    # Bazı önek/sonek kontrolü
    difficult_prefixes = ('un', 'dis', 'mis', 'pre', 'anti', 'super', 'ultra', 'pseudo', 'quasi', 'hyper', 'inter', 'trans', 'multi')
    difficult_suffixes = ('tion', 'sion', 'ment', 'ness', 'ity', 'ology', 'ism', 'ist', 'ive', 'ous', 'ious', 'eous', 'ical', 'ular', 'able', 'ible')
    
    has_difficult_prefix = any(word_lower.startswith(p) for p in difficult_prefixes)
    has_difficult_suffix = any(word_lower.endswith(s) for s in difficult_suffixes)
    
    if has_difficult_prefix and has_difficult_suffix:
        return 'C1' if word_len >= 10 else 'B2'
    elif has_difficult_prefix or has_difficult_suffix:
        if word_len >= 9:
            return 'B2'
        else:
            return 'B1'
    
    # Kısa ama bilinmeyen kelimeler - minimum B1 (A1/A2 değil!)
    # Çünkü A1/A2 sadece bilinen, yaygın kelimeler olmalı
    return 'B1'

def relabel_all_words():
    """Tüm kelimeleri yeniden etiketle."""
    db_path = get_db_path()
    print(f"Veritabanı: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Tüm kelimeleri al
    cursor.execute("SELECT word_id, english, pos FROM words WHERE english IS NOT NULL")
    words = cursor.fetchall()
    
    print(f"Toplam {len(words)} kelime işlenecek...")
    
    level_counts = {'A1': 0, 'A2': 0, 'B1': 0, 'B2': 0, 'C1': 0, 'C2': 0}
    batch_size = 1000
    updated = 0
    
    for i, (word_id, english, pos) in enumerate(words):
        new_level = calculate_word_difficulty(english, pos)
        
        cursor.execute("UPDATE words SET level = ? WHERE word_id = ?", (new_level, word_id))
        level_counts[new_level] = level_counts.get(new_level, 0) + 1
        updated += 1
        
        if (i + 1) % batch_size == 0:
            conn.commit()
            print(f"  {i + 1}/{len(words)} kelime işlendi...")
    
    conn.commit()
    conn.close()
    
    print(f"\n✓ {updated} kelime yeniden etiketlendi!")
    print("\nYeni seviye dağılımı:")
    for level, count in sorted(level_counts.items()):
        print(f"  {level}: {count} kelime")

if __name__ == "__main__":
    relabel_all_words()
