"""
Kelimeleri kategorilere ayıran script.
En yaygın ~5000 kelimeyi kategorize eder, geri kalanı 'other' olur.
"""

import sqlite3

# Kategori tanımları - her kategoriye ait kelimeler
CATEGORIES = {
    # A1 - Temel
    "greetings": [
        "hello", "hi", "hey", "goodbye", "bye", "good", "morning", "afternoon", 
        "evening", "night", "welcome", "greet", "greeting", "wave", "howdy",
        "farewell", "cheerio", "ciao", "adieu"
    ],
    
    "introduction": [
        "name", "my", "i", "am", "is", "are", "you", "your", "he", "she", "it",
        "we", "they", "me", "him", "her", "us", "them", "who", "what", "where",
        "old", "young", "years", "age", "from", "live", "born", "country", "city",
        "nationality", "citizen", "introduce", "myself", "yourself", "call", "called"
    ],
    
    "numbers": [
        "zero", "one", "two", "three", "four", "five", "six", "seven", "eight",
        "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
        "sixteen", "seventeen", "eighteen", "nineteen", "twenty", "thirty",
        "forty", "fifty", "sixty", "seventy", "eighty", "ninety", "hundred",
        "thousand", "million", "billion", "first", "second", "third", "fourth",
        "fifth", "number", "count", "calculate", "many", "few", "several",
        "some", "any", "more", "less", "most", "least", "half", "quarter",
        "double", "triple", "twice", "once", "pair", "dozen"
    ],
    
    "colors": [
        "color", "colour", "red", "blue", "green", "yellow", "orange", "purple",
        "pink", "brown", "black", "white", "gray", "grey", "gold", "silver",
        "bronze", "violet", "indigo", "turquoise", "beige", "cream", "maroon",
        "navy", "olive", "teal", "coral", "salmon", "lime", "aqua", "magenta",
        "crimson", "scarlet", "light", "dark", "bright", "pale", "vivid", "dull",
        "colorful", "colourful", "shade", "tone", "hue"
    ],
    
    "family": [
        "family", "mother", "mom", "mum", "father", "dad", "parent", "parents",
        "child", "children", "son", "daughter", "brother", "sister", "sibling",
        "grandmother", "grandma", "grandfather", "grandpa", "grandparent",
        "grandson", "granddaughter", "grandchild", "aunt", "uncle", "cousin",
        "nephew", "niece", "husband", "wife", "spouse", "partner", "marry",
        "married", "marriage", "wedding", "divorce", "divorced", "single",
        "relative", "relation", "baby", "infant", "toddler", "teenager", "teen",
        "adult", "elderly", "ancestor", "descendant", "twin", "twins", "orphan",
        "adopt", "adopted", "stepmother", "stepfather", "stepson", "stepdaughter",
        "half-brother", "half-sister", "in-law", "mother-in-law", "father-in-law"
    ],
    
    # A2 - Günlük Yaşam
    "daily_routine": [
        "wake", "woke", "woken", "sleep", "slept", "asleep", "awake", "dream",
        "rest", "nap", "bed", "bedroom", "pillow", "blanket", "sheet", "alarm",
        "brush", "tooth", "teeth", "toothbrush", "toothpaste", "wash", "shower",
        "bath", "bathe", "soap", "shampoo", "towel", "dress", "undress", "wear",
        "clothes", "clothing", "outfit", "breakfast", "lunch", "dinner", "meal",
        "eat", "ate", "eaten", "drink", "drank", "drunk", "cook", "cooked",
        "prepare", "morning", "noon", "afternoon", "evening", "night", "midnight",
        "daily", "routine", "schedule", "habit", "always", "usually", "often",
        "sometimes", "rarely", "never", "everyday", "weekend", "weekday"
    ],
    
    "food": [
        "food", "eat", "eating", "hungry", "hunger", "appetite", "meal", "dish",
        "breakfast", "lunch", "dinner", "supper", "snack", "dessert", "drink",
        "beverage", "water", "juice", "milk", "coffee", "tea", "soda", "beer",
        "wine", "alcohol", "bread", "toast", "butter", "cheese", "egg", "eggs",
        "meat", "beef", "pork", "chicken", "fish", "seafood", "shrimp", "lobster",
        "vegetable", "vegetables", "fruit", "fruits", "apple", "banana", "orange",
        "grape", "strawberry", "lemon", "lime", "tomato", "potato", "carrot",
        "onion", "garlic", "pepper", "salt", "sugar", "spice", "sauce", "oil",
        "rice", "pasta", "noodle", "soup", "salad", "sandwich", "burger", "pizza",
        "cake", "pie", "cookie", "chocolate", "candy", "ice", "cream", "yogurt",
        "cereal", "flour", "dough", "bake", "fry", "boil", "grill", "roast",
        "cook", "chef", "recipe", "ingredient", "taste", "flavor", "delicious",
        "yummy", "tasty", "spicy", "sweet", "sour", "bitter", "salty", "fresh",
        "raw", "cooked", "fried", "baked", "grilled", "restaurant", "cafe",
        "kitchen", "menu", "order", "serve", "waiter", "waitress", "tip"
    ],
    
    "weather": [
        "weather", "climate", "temperature", "degree", "celsius", "fahrenheit",
        "hot", "warm", "cool", "cold", "freezing", "mild", "humid", "humidity",
        "dry", "wet", "sun", "sunny", "sunshine", "cloud", "cloudy", "overcast",
        "rain", "rainy", "raining", "rainfall", "drizzle", "pour", "shower",
        "storm", "stormy", "thunder", "thunderstorm", "lightning", "wind", "windy",
        "breeze", "gust", "hurricane", "tornado", "typhoon", "cyclone", "snow",
        "snowy", "snowing", "snowfall", "blizzard", "ice", "icy", "frost", "frosty",
        "freeze", "frozen", "melt", "fog", "foggy", "mist", "misty", "haze", "hazy",
        "rainbow", "forecast", "predict", "season", "spring", "summer", "autumn",
        "fall", "winter", "seasonal"
    ],
    
    "transport": [
        "transport", "transportation", "travel", "trip", "journey", "commute",
        "car", "automobile", "vehicle", "drive", "driver", "driving", "drove",
        "bus", "coach", "train", "railway", "railroad", "metro", "subway",
        "underground", "tram", "trolley", "taxi", "cab", "uber", "ride", "rider",
        "bike", "bicycle", "cycle", "cycling", "motorcycle", "motorbike", "scooter",
        "plane", "airplane", "aircraft", "flight", "fly", "flew", "flying",
        "airport", "airline", "pilot", "boat", "ship", "ferry", "cruise", "sail",
        "sailing", "port", "harbor", "dock", "truck", "lorry", "van", "helicopter",
        "rocket", "spaceship", "ticket", "fare", "passenger", "seat", "belt",
        "luggage", "baggage", "suitcase", "passport", "visa", "departure", "arrival",
        "arrive", "depart", "leave", "board", "boarding", "terminal", "station",
        "stop", "platform", "track", "lane", "road", "street", "highway", "freeway",
        "bridge", "tunnel", "traffic", "jam", "parking", "park", "garage"
    ],
    
    "shopping": [
        "shop", "shopping", "store", "market", "supermarket", "mall", "boutique",
        "buy", "bought", "purchase", "sell", "sold", "sale", "discount", "bargain",
        "price", "cost", "expensive", "cheap", "affordable", "pay", "paid", "payment",
        "cash", "credit", "card", "debit", "money", "currency", "dollar", "euro",
        "pound", "cent", "coin", "bill", "change", "receipt", "refund", "return",
        "exchange", "customer", "client", "seller", "vendor", "merchant", "clerk",
        "cashier", "checkout", "basket", "cart", "trolley", "bag", "package",
        "wrap", "gift", "present", "order", "deliver", "delivery", "shipping",
        "online", "website", "browse", "search", "select", "choose", "size",
        "small", "medium", "large", "extra", "fit", "try", "clothes", "clothing",
        "fashion", "style", "brand", "quality", "quantity", "stock", "available"
    ],
    
    # B1 - İş ve Profesyonel
    "work": [
        "work", "job", "career", "profession", "occupation", "employment", "employ",
        "employee", "employer", "boss", "manager", "supervisor", "director", "ceo",
        "executive", "staff", "colleague", "coworker", "team", "department", "office",
        "company", "corporation", "business", "firm", "organization", "industry",
        "factory", "warehouse", "headquarters", "branch", "salary", "wage", "income",
        "earn", "earning", "pay", "paycheck", "bonus", "raise", "promotion", "promote",
        "hire", "hired", "fire", "fired", "resign", "quit", "retire", "retirement",
        "interview", "resume", "cv", "application", "apply", "candidate", "position",
        "role", "duty", "responsibility", "task", "project", "deadline", "meeting",
        "conference", "presentation", "report", "document", "file", "folder", "email",
        "schedule", "appointment", "calendar", "agenda", "professional", "experience",
        "skill", "qualification", "training", "internship", "intern", "apprentice",
        "contract", "agreement", "negotiate", "deal", "client", "customer", "partner"
    ],
    
    "health": [
        "health", "healthy", "unhealthy", "sick", "ill", "illness", "disease",
        "condition", "symptom", "pain", "painful", "ache", "hurt", "injury",
        "injured", "wound", "bleed", "bleeding", "blood", "fever", "temperature",
        "cold", "flu", "cough", "sneeze", "headache", "stomachache", "backache",
        "toothache", "sore", "throat", "infection", "virus", "bacteria", "allergy",
        "allergic", "rash", "itch", "itchy", "swollen", "swelling", "doctor",
        "physician", "nurse", "surgeon", "dentist", "therapist", "psychiatrist",
        "psychologist", "patient", "hospital", "clinic", "emergency", "ambulance",
        "medicine", "medication", "drug", "pill", "tablet", "capsule", "prescription",
        "pharmacy", "pharmacist", "treatment", "therapy", "surgery", "operation",
        "recover", "recovery", "heal", "cure", "diagnose", "diagnosis", "test",
        "examination", "checkup", "vaccine", "vaccination", "injection", "shot",
        "bandage", "cast", "wheelchair", "crutch", "exercise", "diet", "nutrition",
        "vitamin", "mineral", "protein", "calorie", "weight", "obesity", "fitness"
    ],
    
    "travel": [
        "travel", "traveling", "traveler", "tourist", "tourism", "trip", "journey",
        "voyage", "adventure", "explore", "exploration", "discover", "discovery",
        "vacation", "holiday", "getaway", "destination", "location", "place",
        "visit", "visitor", "tour", "guide", "guidebook", "map", "direction",
        "hotel", "motel", "hostel", "resort", "accommodation", "room", "suite",
        "reservation", "book", "booking", "check-in", "check-out", "reception",
        "lobby", "luggage", "suitcase", "backpack", "pack", "unpack", "passport",
        "visa", "customs", "immigration", "border", "abroad", "foreign", "domestic",
        "international", "local", "native", "culture", "tradition", "monument",
        "landmark", "attraction", "museum", "gallery", "temple", "church", "castle",
        "palace", "beach", "mountain", "island", "lake", "river", "waterfall",
        "forest", "jungle", "desert", "countryside", "village", "town", "city",
        "capital", "souvenir", "photograph", "camera", "memory", "experience"
    ],
    
    "education": [
        "education", "educate", "educated", "learn", "learning", "learner", "study",
        "studying", "student", "pupil", "scholar", "teach", "teaching", "teacher",
        "professor", "instructor", "tutor", "lecturer", "school", "college",
        "university", "academy", "institute", "institution", "class", "classroom",
        "course", "subject", "lesson", "lecture", "seminar", "workshop", "tutorial",
        "curriculum", "syllabus", "textbook", "book", "notebook", "pen", "pencil",
        "paper", "homework", "assignment", "project", "essay", "thesis", "research",
        "exam", "examination", "test", "quiz", "grade", "score", "mark", "pass",
        "fail", "graduate", "graduation", "degree", "diploma", "certificate",
        "bachelor", "master", "doctorate", "phd", "scholarship", "tuition", "fee",
        "enroll", "enrollment", "register", "registration", "semester", "term",
        "academic", "knowledge", "skill", "ability", "intelligence", "smart",
        "clever", "brilliant", "genius", "library", "laboratory", "lab"
    ],
    
    "technology": [
        "technology", "tech", "digital", "electronic", "computer", "laptop",
        "desktop", "tablet", "phone", "smartphone", "mobile", "device", "gadget",
        "screen", "monitor", "display", "keyboard", "mouse", "printer", "scanner",
        "camera", "speaker", "headphone", "microphone", "charger", "battery",
        "cable", "wire", "wireless", "bluetooth", "wifi", "internet", "web",
        "website", "webpage", "browser", "search", "google", "download", "upload",
        "install", "uninstall", "update", "upgrade", "software", "hardware",
        "application", "app", "program", "code", "coding", "programming", "developer",
        "programmer", "engineer", "data", "database", "server", "cloud", "storage",
        "file", "folder", "document", "email", "message", "text", "chat", "video",
        "audio", "stream", "streaming", "social", "media", "network", "platform",
        "account", "profile", "password", "username", "login", "logout", "security",
        "privacy", "hack", "hacker", "virus", "malware", "spam", "bug", "error",
        "crash", "freeze", "restart", "reboot", "robot", "artificial", "intelligence",
        "ai", "machine", "automation", "virtual", "reality", "vr", "ar"
    ],
    
    # B2 - İleri Konular
    "media": [
        "media", "news", "newspaper", "magazine", "journal", "article", "headline",
        "story", "report", "reporter", "journalist", "press", "publish", "publisher",
        "publication", "editor", "editorial", "column", "columnist", "interview",
        "broadcast", "broadcasting", "radio", "television", "tv", "channel", "station",
        "program", "show", "series", "episode", "documentary", "film", "movie",
        "cinema", "theater", "theatre", "drama", "comedy", "tragedy", "action",
        "horror", "thriller", "romance", "animation", "cartoon", "actor", "actress",
        "director", "producer", "celebrity", "famous", "fame", "star", "audience",
        "viewer", "listener", "reader", "subscriber", "subscription", "advertise",
        "advertisement", "ad", "commercial", "sponsor", "propaganda", "bias",
        "objective", "subjective", "opinion", "fact", "source", "reliable", "fake"
    ],
    
    "environment": [
        "environment", "environmental", "nature", "natural", "earth", "planet",
        "world", "globe", "global", "climate", "weather", "atmosphere", "air",
        "pollution", "pollute", "polluted", "clean", "dirty", "waste", "garbage",
        "trash", "rubbish", "recycle", "recycling", "reuse", "reduce", "sustainable",
        "sustainability", "renewable", "energy", "solar", "wind", "hydro", "nuclear",
        "fossil", "fuel", "oil", "gas", "coal", "carbon", "emission", "greenhouse",
        "warming", "change", "conservation", "conserve", "preserve", "protect",
        "protection", "wildlife", "animal", "species", "endangered", "extinct",
        "extinction", "habitat", "ecosystem", "biodiversity", "forest", "deforestation",
        "tree", "plant", "vegetation", "ocean", "sea", "water", "river", "lake",
        "mountain", "desert", "jungle", "rainforest", "soil", "land", "resource",
        "organic", "chemical", "pesticide", "fertilizer", "crop", "agriculture",
        "farming", "farmer", "harvest", "drought", "flood", "disaster", "earthquake"
    ],
    
    "culture": [
        "culture", "cultural", "tradition", "traditional", "custom", "customs",
        "heritage", "history", "historical", "ancient", "modern", "contemporary",
        "art", "artist", "artistic", "paint", "painting", "painter", "draw",
        "drawing", "sketch", "sculpture", "sculptor", "statue", "museum", "gallery",
        "exhibition", "exhibit", "display", "collection", "collector", "music",
        "musician", "musical", "song", "sing", "singer", "singing", "instrument",
        "piano", "guitar", "violin", "drum", "orchestra", "band", "concert",
        "performance", "perform", "performer", "dance", "dancer", "dancing",
        "ballet", "theater", "theatre", "play", "actor", "actress", "drama",
        "comedy", "tragedy", "opera", "literature", "literary", "novel", "fiction",
        "poetry", "poem", "poet", "author", "writer", "writing", "book", "story",
        "tale", "legend", "myth", "folklore", "festival", "celebration", "ceremony",
        "ritual", "religion", "religious", "belief", "faith", "spiritual", "philosophy"
    ],
    
    "economy": [
        "economy", "economic", "economics", "finance", "financial", "money", "cash",
        "currency", "dollar", "euro", "pound", "yen", "bitcoin", "cryptocurrency",
        "bank", "banking", "account", "savings", "deposit", "withdraw", "withdrawal",
        "loan", "borrow", "lend", "debt", "credit", "interest", "rate", "invest",
        "investment", "investor", "stock", "share", "bond", "market", "trade",
        "trading", "trader", "exchange", "forex", "profit", "loss", "gain",
        "revenue", "income", "expense", "cost", "budget", "tax", "taxation",
        "inflation", "deflation", "recession", "depression", "growth", "gdp",
        "wealth", "wealthy", "rich", "poor", "poverty", "inequality", "employment",
        "unemployment", "wage", "salary", "minimum", "import", "export", "tariff",
        "quota", "subsidy", "regulation", "policy", "fiscal", "monetary", "federal",
        "reserve", "central", "capitalism", "socialism", "communism", "globalization"
    ],
    
    "politics": [
        "politics", "political", "politician", "government", "govern", "state",
        "nation", "national", "country", "republic", "democracy", "democratic",
        "dictatorship", "dictator", "monarchy", "king", "queen", "prince", "princess",
        "president", "presidential", "prime", "minister", "cabinet", "congress",
        "parliament", "senate", "senator", "representative", "deputy", "mayor",
        "governor", "official", "authority", "power", "election", "elect", "vote",
        "voter", "voting", "ballot", "campaign", "candidate", "party", "liberal",
        "conservative", "left", "right", "wing", "radical", "moderate", "reform",
        "revolution", "revolutionary", "policy", "law", "legal", "illegal", "court",
        "judge", "jury", "trial", "justice", "rights", "freedom", "liberty",
        "equality", "constitution", "constitutional", "amendment", "legislation",
        "legislate", "bill", "act", "treaty", "agreement", "diplomacy", "diplomatic",
        "ambassador", "embassy", "foreign", "affairs", "international", "united",
        "nations", "nato", "eu", "european", "union", "summit", "conference"
    ],
    
    # Ek kategoriler
    "body": [
        "body", "head", "face", "hair", "eye", "eyes", "eyebrow", "eyelash",
        "ear", "ears", "nose", "mouth", "lip", "lips", "tongue", "tooth", "teeth",
        "chin", "cheek", "forehead", "neck", "throat", "shoulder", "shoulders",
        "arm", "arms", "elbow", "wrist", "hand", "hands", "finger", "fingers",
        "thumb", "nail", "nails", "chest", "breast", "stomach", "belly", "back",
        "spine", "waist", "hip", "hips", "leg", "legs", "thigh", "knee", "knees",
        "ankle", "foot", "feet", "toe", "toes", "heel", "skin", "bone", "bones",
        "muscle", "muscles", "heart", "lung", "lungs", "brain", "liver", "kidney",
        "blood", "vein", "artery", "organ"
    ],
    
    "clothing": [
        "clothes", "clothing", "wear", "dress", "shirt", "blouse", "t-shirt",
        "sweater", "sweatshirt", "hoodie", "jacket", "coat", "suit", "tie",
        "pants", "trousers", "jeans", "shorts", "skirt", "underwear", "sock",
        "socks", "shoe", "shoes", "boot", "boots", "sandal", "sandals", "sneaker",
        "sneakers", "heel", "heels", "hat", "cap", "scarf", "glove", "gloves",
        "belt", "pocket", "button", "zipper", "collar", "sleeve", "size", "fit",
        "tight", "loose", "fashion", "style", "designer", "brand", "cotton",
        "wool", "silk", "leather", "fabric", "textile", "pattern", "stripe",
        "solid", "uniform", "costume", "outfit"
    ],
    
    "house": [
        "house", "home", "apartment", "flat", "building", "floor", "story",
        "room", "bedroom", "bathroom", "kitchen", "living", "dining", "basement",
        "attic", "garage", "garden", "yard", "lawn", "fence", "gate", "door",
        "doorbell", "window", "wall", "ceiling", "roof", "stairs", "staircase",
        "elevator", "lift", "hallway", "corridor", "entrance", "exit", "balcony",
        "terrace", "patio", "furniture", "table", "chair", "sofa", "couch",
        "bed", "mattress", "pillow", "blanket", "sheet", "curtain", "carpet",
        "rug", "lamp", "light", "switch", "outlet", "plug", "appliance",
        "refrigerator", "fridge", "freezer", "oven", "stove", "microwave",
        "dishwasher", "washing", "machine", "dryer", "vacuum", "cleaner",
        "sink", "faucet", "tap", "toilet", "shower", "bathtub", "mirror",
        "closet", "wardrobe", "drawer", "shelf", "cabinet", "counter"
    ],
    
    "animals": [
        "animal", "animals", "pet", "pets", "dog", "puppy", "cat", "kitten",
        "bird", "fish", "rabbit", "hamster", "mouse", "rat", "horse", "pony",
        "cow", "bull", "pig", "sheep", "goat", "chicken", "rooster", "hen",
        "duck", "goose", "turkey", "lion", "tiger", "bear", "wolf", "fox",
        "deer", "elephant", "giraffe", "zebra", "monkey", "ape", "gorilla",
        "chimpanzee", "hippo", "rhino", "crocodile", "alligator", "snake",
        "lizard", "turtle", "tortoise", "frog", "toad", "whale", "dolphin",
        "shark", "octopus", "crab", "lobster", "shrimp", "bee", "butterfly",
        "ant", "spider", "mosquito", "fly", "worm", "snail", "pet", "wild",
        "domestic", "mammal", "reptile", "amphibian", "insect", "bird", "cage",
        "aquarium", "zoo", "farm", "barn", "stable", "kennel"
    ],
    
    "sports": [
        "sport", "sports", "game", "play", "player", "team", "match", "competition",
        "compete", "competitor", "champion", "championship", "tournament", "league",
        "season", "win", "winner", "winning", "lose", "loser", "losing", "tie",
        "draw", "score", "point", "points", "goal", "ball", "bat", "racket",
        "net", "court", "field", "pitch", "stadium", "arena", "gym", "gymnasium",
        "soccer", "football", "basketball", "baseball", "tennis", "golf", "hockey",
        "volleyball", "rugby", "cricket", "boxing", "wrestling", "martial",
        "swimming", "swim", "swimmer", "diving", "dive", "running", "run", "runner",
        "jogging", "jog", "walking", "walk", "cycling", "cycle", "cyclist",
        "skiing", "ski", "skating", "skate", "snowboarding", "surfing", "surf",
        "exercise", "workout", "training", "train", "trainer", "coach", "coaching",
        "athlete", "athletic", "fitness", "fit", "strong", "strength", "muscle"
    ],
    
    "time": [
        "time", "clock", "watch", "hour", "minute", "second", "moment", "instant",
        "now", "then", "before", "after", "during", "while", "when", "today",
        "yesterday", "tomorrow", "morning", "noon", "afternoon", "evening", "night",
        "midnight", "dawn", "dusk", "sunrise", "sunset", "day", "week", "month",
        "year", "decade", "century", "millennium", "past", "present", "future",
        "early", "late", "soon", "already", "still", "yet", "always", "never",
        "sometimes", "often", "usually", "rarely", "seldom", "ever", "forever",
        "temporary", "permanent", "brief", "long", "short", "quick", "fast",
        "slow", "schedule", "calendar", "date", "appointment", "deadline",
        "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
        "january", "february", "march", "april", "may", "june", "july", "august",
        "september", "october", "november", "december", "spring", "summer",
        "autumn", "fall", "winter", "season", "annual", "daily", "weekly", "monthly"
    ],
    
    "emotions": [
        "emotion", "emotional", "feeling", "feel", "felt", "mood", "happy",
        "happiness", "sad", "sadness", "angry", "anger", "mad", "fear", "afraid",
        "scared", "frightened", "surprise", "surprised", "shocking", "shock",
        "joy", "joyful", "pleasure", "pleased", "delight", "delighted", "excited",
        "excitement", "enthusiastic", "enthusiasm", "hope", "hopeful", "hopeless",
        "love", "loving", "hate", "hatred", "jealous", "jealousy", "envy", "envious",
        "proud", "pride", "shame", "ashamed", "embarrassed", "embarrassment",
        "guilt", "guilty", "regret", "sorry", "apologize", "forgive", "forgiveness",
        "grateful", "gratitude", "thankful", "appreciate", "appreciation", "lonely",
        "loneliness", "bored", "boring", "interested", "interesting", "curious",
        "curiosity", "confident", "confidence", "nervous", "anxiety", "anxious",
        "stress", "stressed", "relax", "relaxed", "calm", "peaceful", "content",
        "satisfied", "satisfaction", "disappointed", "disappointment", "frustrated",
        "frustration", "confused", "confusion", "worried", "worry"
    ],
    
    "communication": [
        "communicate", "communication", "speak", "speaking", "spoke", "spoken",
        "talk", "talking", "say", "said", "tell", "told", "ask", "asked",
        "answer", "answered", "question", "reply", "respond", "response",
        "discuss", "discussion", "conversation", "chat", "gossip", "rumor",
        "argue", "argument", "debate", "agree", "agreement", "disagree",
        "disagreement", "explain", "explanation", "describe", "description",
        "express", "expression", "mention", "comment", "remark", "suggest",
        "suggestion", "advise", "advice", "recommend", "recommendation", "warn",
        "warning", "promise", "swear", "lie", "lying", "truth", "honest",
        "honesty", "language", "word", "words", "vocabulary", "grammar", "sentence",
        "phrase", "pronunciation", "accent", "dialect", "translate", "translation",
        "interpreter", "interpret", "fluent", "fluency", "native", "foreign",
        "speech", "voice", "loud", "quiet", "silent", "silence", "whisper", "shout",
        "yell", "scream", "call", "phone", "telephone", "message", "text", "email"
    ],
    
    "nature": [
        "nature", "natural", "earth", "world", "land", "ground", "soil", "dirt",
        "rock", "stone", "sand", "mud", "mountain", "hill", "valley", "cliff",
        "cave", "volcano", "earthquake", "river", "stream", "creek", "lake",
        "pond", "ocean", "sea", "beach", "coast", "shore", "wave", "tide",
        "island", "peninsula", "continent", "forest", "jungle", "rainforest",
        "woods", "tree", "trees", "bush", "shrub", "grass", "lawn", "meadow",
        "field", "farm", "garden", "flower", "flowers", "plant", "plants", "leaf",
        "leaves", "branch", "trunk", "root", "roots", "seed", "seeds", "grow",
        "growing", "bloom", "blossom", "fruit", "vegetable", "crop", "harvest",
        "sky", "air", "atmosphere", "cloud", "clouds", "sun", "moon", "star",
        "stars", "planet", "space", "universe", "galaxy", "sunrise", "sunset",
        "rainbow", "horizon", "landscape", "scenery", "view", "beautiful", "beauty"
    ],
    
    "actions": [
        "do", "did", "done", "make", "made", "go", "went", "gone", "come", "came",
        "get", "got", "give", "gave", "given", "take", "took", "taken", "put",
        "keep", "kept", "let", "begin", "began", "begun", "start", "started",
        "stop", "stopped", "continue", "finish", "finished", "end", "ended",
        "try", "tried", "help", "helped", "show", "showed", "shown", "turn",
        "turned", "move", "moved", "follow", "followed", "lead", "led", "bring",
        "brought", "carry", "carried", "hold", "held", "catch", "caught", "throw",
        "threw", "thrown", "pull", "pulled", "push", "pushed", "open", "opened",
        "close", "closed", "break", "broke", "broken", "fix", "fixed", "build",
        "built", "create", "created", "destroy", "destroyed", "change", "changed",
        "use", "used", "need", "needed", "want", "wanted", "like", "liked",
        "love", "loved", "hate", "hated", "prefer", "preferred", "choose", "chose",
        "chosen", "decide", "decided", "plan", "planned", "prepare", "prepared"
    ],
    
    "descriptive": [
        "big", "large", "huge", "enormous", "giant", "massive", "small", "little",
        "tiny", "miniature", "long", "short", "tall", "high", "low", "wide",
        "narrow", "thick", "thin", "deep", "shallow", "heavy", "light", "fast",
        "quick", "rapid", "slow", "hard", "soft", "smooth", "rough", "sharp",
        "dull", "hot", "warm", "cool", "cold", "wet", "dry", "clean", "dirty",
        "new", "old", "young", "ancient", "modern", "fresh", "stale", "full",
        "empty", "open", "closed", "rich", "poor", "expensive", "cheap", "free",
        "busy", "quiet", "loud", "noisy", "silent", "dark", "bright", "light",
        "beautiful", "ugly", "pretty", "handsome", "attractive", "plain", "simple",
        "complex", "complicated", "easy", "difficult", "hard", "possible", "impossible",
        "true", "false", "real", "fake", "right", "wrong", "good", "bad", "great",
        "terrible", "wonderful", "awful", "amazing", "boring", "interesting",
        "important", "necessary", "special", "normal", "strange", "weird", "common",
        "rare", "popular", "famous", "unknown", "similar", "different", "same", "other"
    ]
}

# Ünite → Kategori eşleştirmesi
UNIT_CATEGORY_MAP = {
    # A1
    "Selamlaşma": ["greetings", "introduction"],
    "Kendini Tanıtma": ["introduction", "greetings"],
    "Sayılar": ["numbers", "time"],
    "Renkler": ["colors", "descriptive"],
    "Aile": ["family", "introduction"],
    
    # A2
    "Günlük Rutinler": ["daily_routine", "time", "actions"],
    "Yiyecek-İçecek": ["food", "shopping"],
    "Hava Durumu": ["weather", "nature", "time"],
    "Ulaşım": ["transport", "travel"],
    "Alışveriş": ["shopping", "clothing", "numbers"],
    
    # B1
    "İş Hayatı": ["work", "communication", "technology"],
    "Sağlık": ["health", "body", "emotions"],
    "Seyahat": ["travel", "transport", "culture"],
    "Eğitim": ["education", "communication", "technology"],
    "Teknoloji": ["technology", "communication", "work"],
    
    # B2
    "Medya ve Haberler": ["media", "communication", "technology"],
    "Çevre": ["environment", "nature", "animals"],
    "Kültür ve Sanat": ["culture", "emotions", "communication"],
    "Ekonomi": ["economy", "work", "politics"],
    "Politika": ["politics", "communication", "economy"],
}


def categorize_words():
    """Kelimeleri kategorilere ayır."""
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    
    # Tüm kategorilerdeki kelimeleri düz listeye çevir (kelime -> kategori)
    word_to_category = {}
    for category, words in CATEGORIES.items():
        for word in words:
            word_lower = word.lower()
            if word_lower not in word_to_category:
                word_to_category[word_lower] = category
    
    print(f"📚 Toplam {len(word_to_category)} kelime tanımlandı")
    
    # Veritabanındaki kelimeleri kategorize et
    updated = 0
    
    # Batch güncelleme için
    for category, words in CATEGORIES.items():
        if not words:
            continue
            
        # Her kelime için güncelle
        for word in words:
            cursor.execute("""
                UPDATE words 
                SET category = ? 
                WHERE LOWER(english) = ? AND (category IS NULL OR category = '')
            """, (category, word.lower()))
            updated += cursor.rowcount
    
    # Kategorize edilmemiş kelimeleri 'other' yap
    cursor.execute("""
        UPDATE words 
        SET category = 'other' 
        WHERE category IS NULL OR category = ''
    """)
    other_count = cursor.rowcount
    
    conn.commit()
    
    # İstatistikleri göster
    print(f"\n✅ {updated} kelime kategorize edildi")
    print(f"📦 {other_count} kelime 'other' kategorisine atandı")
    
    # Kategori dağılımını göster
    print("\n📊 Kategori Dağılımı:")
    cursor.execute("""
        SELECT category, COUNT(*) as cnt 
        FROM words 
        WHERE category != 'other' AND category IS NOT NULL
        GROUP BY category 
        ORDER BY cnt DESC
    """)
    
    for row in cursor.fetchall():
        print(f"   {row[0]}: {row[1]} kelime")
    
    cursor.execute("SELECT COUNT(*) FROM words WHERE category = 'other'")
    other = cursor.fetchone()[0]
    print(f"   other: {other} kelime")
    
    conn.close()
    print("\n✅ Kategorileme tamamlandı!")


if __name__ == "__main__":
    categorize_words()
