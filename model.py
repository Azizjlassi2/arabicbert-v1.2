from flask import Flask, request, jsonify, abort
import re
import json
from datetime import datetime
import uuid

app = Flask(__name__)

# Configuration
API_KEY = "YOUR_API_KEY"
MODEL_VERSION = "arabicbert-v1.2"
MAX_SEQUENCE_LENGTH = 512

TOPIC_KEYWORDS = {
  "politique": [
    "(?:حكومة|برلمان|انتخابات|سياسة|رئيس|وزير|دستور|قانون|مؤتمر|قرار|معارضة|تحالف|تظاهرة|استفتاء|حملة انتخابية|حكم|برلمان تونسي|سياسي|سياسيين|سياسة داخلية|أزمة سياسية|depute|gouvernement|vote|ministre|président)",
    "(?:politique|dawla|idara|vote|campagne|siyasah)"
  ],
  "économie": [
    "(?:اقتصاد|سوق|بنك|عملة|نمو|بطالة|تضخم|تجارة|مالية|استثمار|رأسمال|دين|ميزانية|تصدير|استيراد|سعر|أسعار|فلوس|دنانير|عملة صعبة|بيع و شراء|اقتصادي|inflation|commerce|budget|taxes|finance|recession|import|export)",
    "(?:flous|floos|dinars|investissement|economy|commerce|taxe|taux|business|economique)"
  ],
  "culture": [
    "(?:ثقافة|فن|موسيقى|مسرحية|فيلم|كتاب|أدب|تراث|مهرجان|معرض|ثقافي|عادات|تقاليد|هوية|فنانون|مؤلف|رواية|مقال|قصيدة|مسرح|heritage文化|cinéma|culturel|arts|exposition|festival)",
    "(?:culture|art|festival|concert|livre|movie|theatre|heritage|tradition|music|cinema|arts|artistic)"
  ],
  "société": [
    "(?:مجتمع|شعب|عائلة|جماعة|حقوق|عدالة|مساواة|حقوق إنسان|مرأة|طفل|نظام اجتماعي|تربية|اجتماعي|ثقافي اجتماعي|حياة اجتماعية|تقاليد|عادات|شباب|كبار|فقر|بطالة|inégalités|social|communaute|droit social)",
    "(?:societe|social|droit|égalité|justice sociale|community|population|famille|sociale)"
  ],
  "local": [
    "(?:ولاية|محافظة|مدينة|بلدية|حي|شارع|مقاطعة|تنمية محلية|خدمات|مشروع بلدي|سكان|إدارة محلية|خدمات عمومية|نظافة|طرقات|مشروع|بلدية|commune|municipalité|quartier|collectivité)",
    "(?:local|municipalité|ville|quartier|commune|local-news)"
  ],
  "international": [
    "(?:دولي|عالمي|أمم المتحدة|منظمة|اتفاق|معاهدة|دبلوماسي|سفارة|سياسة خارجية|علاقات دولية|أخبار عالمية|شرق أوسط|أوروبا|أمريكا|أفريقيا|هجرة|لاجئين|حرب|صراع|global|international|foreign relations|treaty)",
    "(?:international|global|UN|diplomatie|immigration|refugees|foreign|relations|world news)"
  ],
  "technologie": [
    "(?:تقنية|تكنولوجيا|برمجيات|تطبيق|هاتف|كمبيوتر|إنترنت|شبكة|ذكاء صناعي|معلوماتية|موبايل|اتصال|شبكات|برنامج|أمن سيبراني|ابتكار|تطوير|تقني|smartphone|software|hardware|cyber|internet|IT|innovation|tech|app|mobile)",
    "(?:tech|software|hardware|internet|AI|IT|mobile|smartphone|cyber|innovation|app)"
  ],
  "science": [
    "(?:علم|بحث علمي|دراسة|مختبر|فيزياء|كيمياء|بيولوجيا|فضاء|طبيعة|علوم|أبحاث|تجربة|علمي|مؤتمر علمي|دراسة علمية|space|biology|physics|chemistry|research|science|innovation scientifique)",
    "(?:science|research|lab|study|physics|chemistry|biology|space|innovation|research)"
  ],
  "santé": [
    "(?:صحة|مستشفى|طبيب|علاج|مرض|فيروس|وباء|دواء|طب|عيادة|صحة عامة|لقاح|تطعيم|جراحة|رعاية صحية|مرض مزمن|حالة طارئة|طب|clinic|hospital|medicine|vaccine|treatment|disease|health care|medical|santé)",
    "(?:hospital|doctor|medicine|health|virus|clinic|vaccine|treatment|disease|medical)"
  ],
  "sport": [
    "(?:رياضة|مباراة|فريق|دوري|بطولة|لاعب|كرة قدم|كرة سلة|أولمبياد|ملعب|هدف|فوز|خسارة|نادي|منافسة|كأس|score|match|league|tournament|game|goal|sport|team|player|win|lose|competition)",
    "(?:sport|match|team|goal|league|tournament|game|player|win|score|competition)"
  ],
  "loisir_divertissement": [
    "(?:مهرجان|حفلة|عرض|سينما|مسرح|حفلة موسيقية|سفر|سياحة|رحلة|مطعم|تسلية|سياحي|سفر و سياحة|مقهى|فن ترفيهي|ترفيه|ألعاب|فيديو|موسيقى|divertissement|cinema|tourism|travel|fun|restaurant|trip|vacances|tourisme)",
    "(?:cinema|tourism|travel|fun|video|games|entertainment|movie|restaurant|vacances|travel)"
  ],
  "éducation": [
    "(?:مدرسة|جامعة|تعليم|دراسة|طلاب|طالبات|مناهج|دروس|امتحان|بحث|شهادة|قبول|تسجيل|دراسة عليا|تكوين|cours|éducation|school|university|students|exam|study|training|education|enseignement|formation)",
    "(?:education|school|university|students|study|exam|course|training|formation)"
  ],
  "justice_droit": [
    "(?:قانون|محكمة|قضاء|محامي|جريمة|قضية|عدالة|تشريع|حقوق|دستور|قانون جنائي|قانون مدني|محاكمة|سجن|عقوبة|قانون و نظام|judiciaire|justice|court|law|crime|rights|legal|droit|tribunal)",
    "(?:justice|law|court|crime|rights|legal|judiciary)"
  ],
  "environnement": [
    "(?:بيئة|تلوث|مناخ|تغير مناخي|مياه|هواء|غابات|طبيعة|حياة برية|نفايات|طاقة متجددة|حماية البيئة|تربة|زراعة|طبيعي|recyclage|sustainable|pollution|nature|environnement|forest|water|air|wildlife|climate|écologie)",
    "(?:environment|nature|pollution|climate|forest|water|air|wildlife|sustainable|ecology)"
  ],
  "emploi_travail": [
    "(?:عمل|وظيفة|بطالة|أجور|راتب|شغل|صناعة|قطاع|عمال|مصنع|مقاولة|ريادة|توظيف|صناعة خفيفة|تجارة صغيرة|projet شخصي|startup|entreprise|emploi|job|salary|wage|industry|factory|labor|business|trade|crafts)",
    "(?:job|emploi|salary|business|industry|trade|startup|work|job market|employment)"
  ],
  "religion": [
    "(?:دين|إسلام|مسيحية|عبادة|مسجد|كنيسة|فتوى|عقيدة|روحانية|مؤمن|طقوس|دين محلي|holiday دينية|religion|faith|worship|church|mosque|spiritual|holy|religious|belief|praying)",
    "(?:religion|faith|worship|church|mosque|spiritual|religieux)"
  ],
  "crime_securite": [
    "(?:جريمة|عنف|شرطة|أمن|مخدرات|سرقة|قتل|خطف|إرهاب|اعتداء|قضية جنائية|محاكمة|سجن|عقوبة|crise أمنية|security|violence|crime|police|terrorism|attack|court|prison|law enforcement)",
    "(?:crime|security|police|terrorism|violence|attack|safety|law|court|prison)"
  ],
  "psychologie_bien_etre": [
    "(?:نفسية|صحة نفسية|ضغط نفسي|قلق|اكتئاب|علاج نفسي|رفاهية|راحة|علاقات|حياة نفسية|رعاية نفسية|mental health|psychologie|stress|anxiety|dépression|therapy|wellbeing|well-being|إرشاد نفسي|therapy)",
    "(?:psychology|mental health|stress|therapy|wellbeing|depression|anxiety)"
  ],
  "médias_populaires": [
    "(?:مسلسل|دراما|كليب|غناء|مشاهير|إعلام|تلفزيون|يوتيوب|فيديو|ميديا اجتماعية|مشهور|فن شعبي|فضائح|pop-culture|media|TV|clip|celebrity|youtube|social media|entertainment médiatique)",
    "(?:media|tv|series|clip|celebrity|youtube|social media|pop culture|music|video)"
  ],
  "histoire_heritage": [
    "(?:تاريخ|تراث|حضارة|آثار|موروث|حضارة|عصور قديمة|موقع أثري|heritage|civilisation|history|ancient|legacy|culture ancienne|archive|وثائق|histoire|heritage culturel)",
    "(?:history|heritage|ancient|civilization|legacy|heritage cultural)"
  ],
  "sociologie_relations": [
    "(?:علاقات إنسانية|ثقافة اجتماعية|هوية|تنوع|تعايش|جندر|جالية|مهاجر|هجرة|تواصل|جماعة|جالية|community|migration|identity|diversité|sociologie|social relations|interaction|community life)",
    "(?:sociology|identity|diversity|migration|community|relations|social|interaction)"
  ]
}


NER_PATTERNS = {
    "PER": [
        # noms prédéfinis — prénom + nom (gazetteer minimal, à enrichir)
        r"\b(قيس سعيد|الحبيب بورقيبة|محمد بن علي|أحمد بن محمد|علي عبد الله|سلمى بن خليفة|يوسف الزيات|منى التونسي|فاطمة الزهراء|محمد سلام)\b",
       
        # translittérations latines / “Arabizi” / noms latins « fréquents »
        r"\b(Mohamed|Ahmed|Ali|Said|Bourguiba|Hassan|Fateh|Salim|Youssef|Fatma|Mona)\b",
    ],
    "LOC": [
        # top-onymes connus (pays, villes, régions, lieux célèbres)
        r"\b(تونس|صفاقس|سوسة|القيروان|المنستير|دبي|القاهرة|باريس|مراكش|نابل|بنزرت|قابس|صفاقس الكبرى|وسط تونس|جربة)\b",
        # structure : nom + type de lieu (مدينة / ولاية / محافظة / منطقة / حي / قرية / شارع / ولاية / جهة ...)
        r"\b[اأإبتثجحخدذرزسشصضطظعغفقكلمنهوي]{2,20}\s+(?:مدينة|ولاية|محافظة|منطقة|قرية|حي|شارع|جهة|منطقة سياحية)\b",
        # noms de lieux latins / translittérés
        r"\b(Tunis|Sfax|Sousse|Cairo|Dubai|Paris|Marrakech|Manouba|Gafsa|Mednine|Djerba)\b",
    ],
    "ORG": [
        # organisations / institutions — gazetteer d’exemples
        r"\b(وزارة الصحة|الخطوط التونسية|البنك المركزي|جامعة تونس|اليونسكو|الفيفا|الاتحاد الأفريقي|وزارة الداخلية|وزارة التربية|نادي الترجي|نادي النجم الساحلي)\b",
        # structure : mot + « شركة / جامعة / منظمة / حزب / بنك / مؤسسة / مجلس / نادي / بنك مركزي / وزارة / هيئة / جامعة / شركة / لجنة »
        r"\b[اأإبتثجحخدذرزسشصضطظعغفقكلمنهوي]{2,20}\s+(?:شركة|جامعة|منظمة|حزب|بنك|مؤسسة|مجلس|هيئة|وزارة|نادي|لجنة)\b",
        # translittérations / english-arabizi / noms d’organisations latines
        r"\b(University|Bank|Ministry|Company|Organisation|Council|Corporation|UNICEF|WHO|Google|Microsoft)\b",
    ],
    "DATE": [
        # mois + année en arabe
        r"\b(يناير|فبراير|مارس|أبريل|مايو|ماي|يونيو|جويلية|يوليو|أغسطس|سبتمبر|أكتوبر|نوفمبر|ديسمبر)\s+\d{4}\b",
        # date format jour/mois/année ou jj-mm-aaaa ou jj/mm/aaaa
        r"\b\d{1,2}\s*(?:/|-|\-)\s*\d{1,2}\s*(?:/|-|\-)\s*\d{2,4}\b",
        # année seule (4 chiffres)
        r"\b(?:19|20)\d{2}\b",
        # jours de la semaine, expressions temporelles usuelles
        r"\b(الإثنين|الثلاثاء|الأربعاء|الخميس|الجمعة|السبت|الأحد|اليوم|غداً|غدا|أمس|قبل أمس)\b",
        # mois anglais + année, ou date anglaise — utile pour textes mixtes
        r"\b(January|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}\b",
    ],
    "MISC": [
        # événements, œuvres, titres — exemples en arabe
        r"\b(مؤتمر|مهرجان|بطولة|ألبوم|فيلم|كتاب|مشروع|برنامج|مسلسل|معرض|حفل|عرض|مسرحية|فعالية|ورشة|ندوة|جائزة)\b",
        # entités latines / en anglais — titres composés de 2 mots capitalisés, ou acronymes
        r"\b([A-Z][a-z]{2,}\s+[A-Z][a-z]{2,})\b",
        r"\b[A-Z]{2,5}\b"  # acronymes (ex: UN, EU, NATO, WHO, etc.)
    ],
   
    "NUM": [
        r"\b\d+(?:,\d+)?\b",               # nombres entiers ou décimaux
        r"\b\d+\s*(?:د.ت|DT|دينار|دينار تونسي|دنانير)\b",  # montants en dinars tunisiens
        r"\b\d+\s*(?:%)\b",              # pourcentages
    ]
    ,"TIME": [
        r"\b[01]?\d:[0-5]\d\b",  # ex 09:30, 14:05
        r"\b(صباحاً|مساءً|مساء|نهار|ليل|صباح|ظهر|عشية)\b"
    ],
    "MONEY": [
        r"\b\d+(?:,\d+)?\s*(?:د\.ت|DT|دنانير|دينار|€|\$)\b",
        r"\b(?:ريال|دينار تونسي|دولار|يورو)\b"
    ],
    "PERCENT": [
        r"\b\d+(?:,\d+)?\s*%\b"
    ],
    "NUMBER": [
        r"\b\d+(?:,\d+)?\b"
    ],
    "EVENT": [
        r"\b(مؤتمر|انتخابات|بطولة|مهرجان|قمة|اجتماع|قانون جديد|زلزال|كارثة|حادث)\b",
        r"\b([A-Z][a-z]+)\s+(Conference|Cup|Festival|Summit|Meeting)\b"
    ],
    "PRODUCT": [
        r"\b(سيارة|هاتف|موبايل|لابتوب|دواء|منتج)\s+[اأإبتثجحخدذرزسشصضطظعغفقكلمنهوي0-9]+\b",
        r"\b(iPhone|Samsung|Renault|Toyota|Paracetamol)\b"
    ],
    "WORK_OF_ART": [
        r"\b(فيلم|ألبوم|كتاب|مسلسل|رواية|مسرحية|أغنية)\b",
        r"\b([A-Z][a-z]+)\s+(Film|Album|Book|Series)\b"
    ],
    "NORP": [
        r"\b(تونسي|تونسيون|عربي|أوروبي|مسلم|مسيحي|عرب|أفارقة)\b"
    ],
    "FACILITY": [
        r"\b(مستشفى|جامعة|مدرسة|مطار|متحف|مسرح|مركز ثقافي|مركز صحي)\b"
    ]
}


# Fonctions de simulation heuristiques (mock responses basées sur exemples)
def normalize(text: str) -> str:
    # simple normalisation : ponctuation, variantes orthographiques, etc.
    text = re.sub(r'[؟!,.؛:]',' ', text)
    # remplacer hamza/variants, ya, ta marbuta etc.
    text = text.replace('أ', 'ا').replace('إ', 'ا').replace('ى', 'ي')  # etc.
    return text

def simulate_text_classification(text: str) -> dict:
    """
    Simulation de classification de texte via mots-clés enrichis.
    Retourne la catégorie avec le plus de correspondances de mots-clés.
    
    """
    t = normalize(text.lower())
    matches = {}
    for cat, patterns in TOPIC_KEYWORDS.items():
        count = sum(1 for p in patterns if re.search(p, t))
        if count > 0:
            matches[cat] = count
    if matches:
        best = max(matches.items(), key=lambda x: x[1])
        # confidence heuristique 
        confidence = min(0.5 + 0.1 * best[1], 0.99)
        return {"category": best[0], "confidence": confidence}
    # fallback
    return {"category": "general", "confidence": 0.80}

def normalize_arabic(text: str) -> str:
    """
    Normalisation basique : unifie certaines lettres/variantes
    – simplification alifs et normalisation de l’écriture.
    """
    # ex : alif hamza → alif, alef madda etc.
    text = text.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
    # remplacer ta marbuta à ha normale (optionnel selon usage)
    text = text.replace("ة", "ه")
    # compléter selon besoin (ya vs ي, alifs, kasra/fatha/hamza, etc.)
    return text

def simulate_ner(text: str) -> list[dict[str, any]]:
    """
    Simulation NER via gazetteer + regex étendus (arabe + translittérations).
    Parcours tous les patterns, renvoie toutes les entités détectées.
    """
    entities: list[dict[str, any]] = []
    t = normalize_arabic(text)
    for ent_type, patterns in NER_PATTERNS.items():
        for pattern in patterns:
            for match in re.finditer(pattern, t, flags=re.IGNORECASE):
                # récupérer l’entité telle qu’elle est dans le texte d’origine (optionnel)
                ent_text = text[match.start(): match.end()]
                entities.append({
                    "entity": ent_text,
                    "type": ent_type,
                    "start": match.start(),
                    "end": match.end()
                })
    return entities
def simulate_sentiment_analysis(text: str, language: str = "ar") -> dict:
    """Simulation d'analyse de sentiment via polarité lexicale enrichie."""
    text_lower = text.lower()
    positive_keywords = ['ممتازة', 'بهية', 'فيسع', 'أنصح', 'نرجعلو', 'رائع', 'جميل', 'مفيد', 'سعيد', 'حلو', 'برافو', 'شكرا', 'مثالي']
    negative_keywords = ['ممل', 'ما عجبنيش', 'برشا', 'سيء', 'كريه', 'مشكلة', 'فشل', 'غبي', 'مضيع', 'حقير', 'مخيب', 'غير مناسب']
    neutral_keywords = ['عادي', 'مقبول', 'متوسط', 'لا بأس', 'جيد جزئيا']
    
    pos_count = sum(1 for kw in positive_keywords if kw in text_lower)
    neg_count = sum(1 for kw in negative_keywords if kw in text_lower)
    neu_count = sum(1 for kw in neutral_keywords if kw in text_lower)
    
    total = pos_count + neg_count + neu_count
    score = 0.5
    if total > 0:
        score = (pos_count - neg_count) / total + 0.5  # Pondération simple [-1,1] normalisée [0,1]
        score = max(0.0, min(1.0, score))
    
    if pos_count > neg_count:
        return {"sentiment": "positive", "score": score if language == "tn" else score + 0.04, "label": "إيجابي"}
    elif neg_count > pos_count:
        return {"sentiment": "negative", "score": score, "label": "سلبي"}
    else:
        return {"sentiment": "neutral", "score": score, "label": "محايد"}

def simulate_question_answering(context: str, question: str) -> dict:
    """Simulation extractive QA via recherche de span enrichie."""
    question_lower = question.lower()
    # Pattern pour capitale
    if re.search(r'عاصمة\s+تونس', question_lower):
        span = re.search(r'عاصمة.*?تونس', context)
        if span:
            return {"answer": span.group().strip(), "start": span.start(), "end": span.end(), "confidence": 0.97}
    # Pattern pour indépendance
    elif re.search(r'استقلالها|استقلال\s+تونس', question_lower):
        span = re.search(r'1956', context)
        if span:
            return {"answer": span.group(), "start": span.start(), "end": span.end(), "confidence": 0.95}
    # Ajout : Pattern pour population
    elif re.search(r'عدد\s+سكانها|سكان\s+تونس', question_lower):
        span = re.search(r'12\s+مليون', context)
        if span:
            return {"answer": span.group().strip(), "start": span.start(), "end": span.end(), "confidence": 0.92}
    # Ajout : Pattern pour leader historique
    elif re.search(r'قائد\s+الاستقلال|رئيس\s+أول', question_lower):
        span = re.search(r'الحبيب\s+بورقيبة', context)
        if span:
            return {"answer": span.group().strip(), "start": span.start(), "end": span.end(), "confidence": 0.94}
    # Ajout : Pattern pour localisation
    elif re.search(r'موقع\s+تونس|أين\s+تقع', question_lower):
        span = re.search(r'شمال\s+أفريقيا', context)
        if span:
            return {"answer": span.group().strip(), "start": span.start(), "end": span.end(), "confidence": 0.96}
    return {"answer": "", "start": -1, "end": -1, "confidence": 0.0}

# Middleware d'authentification
def authenticate():
    auth_header = request.headers.get('Authorization')
    if not auth_header or auth_header != f'Bearer {API_KEY}':
        abort(401, description="Unauthorized")

# Endpoint principal
@app.route('/predict', methods=['POST'])
def predict():
   # authenticate()
    data = request.json
    if not data or 'task' not in data:
        abort(400, description="Missing 'task' field")

    task = data['task']
    text = data.get('text') or data.get('input', '')
    context = data.get('context', '')
    question = data.get('question', '')
    options = data.get('options', {})

    if len(text) > MAX_SEQUENCE_LENGTH:
        abort(413, description="Input exceeds max sequence length")

    start_time = datetime.now()
    result = {}
    tokens_used = len(text.split())

    if task == "text_classification":
        result = simulate_text_classification(text)
    elif task == "named_entity_recognition" or task == "ner":
        result = simulate_ner(text)
    elif task == "sentiment_analysis" or task == "sentiment":
        lang = options.get('language', 'ar')
        result = simulate_sentiment_analysis(text, lang)
    elif task == "question_answering" or task == "qa":
        result = simulate_question_answering(context, question)
    else:
        abort(400, description="Unsupported task")

    processing_time = (datetime.now() - start_time).total_seconds() * 1000
    language_detected = "ar" if re.search(r'[\u0600-\u06FF]', text) else "tn"

    response = {
        "model": MODEL_VERSION,
        "task": task,
        "result": result,
        "metadata": {
            "tokens_used": tokens_used,
            "language_detected": language_detected,
            "processing_time_ms": round(processing_time)
        }
    }
    return jsonify(response), 200

@app.route('/info', methods=['GET'])
def model_info():
    """
    Retourne les informations sur le modèle ArabicBERT et les endpoints disponibles.
    """
   # authenticate()  # si tu veux protéger l'info

    info = {
        "model_name": "ArabicBERT",
        "version": MODEL_VERSION,
        "description": "BERT-based model pré-entraîné sur un large corpus arabe, supporte MSA et dialecte tunisien.",
        "architecture": "BERT-base (12 couches, 12 têtes d'attention, 768 dimensions cachées)",
        "tasks_supported": [
            "text_classification",
            "named_entity_recognition",
            "sentiment_analysis",
            "question_answering"
        ],
        "endpoints": [
            {
                "path": "/predict",
                "method": "POST",
                "description": "Exécute une tâche spécifique sur le texte fourni. Paramètres: task, text/input, context (pour QA), question (pour QA), options"
            },
            {
                "path": "/info",
                "method": "GET",
                "description": "Retourne les informations sur le modèle et les endpoints disponibles."
            }
        ],
        "max_sequence_length": MAX_SEQUENCE_LENGTH,
        "author": "Equipe AI+ Platform",
        "contact": "support@ai-tunisia.com"
    }

    return jsonify(info), 200


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
    