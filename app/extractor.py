"""Information extraction: turns a customer utterance into structured facts.

Two implementations share one schema:
  * GroqExtractor  - LLM (free Groq tier) with JSON output; best for natural speech and Hindi.
  * RuleExtractor  - deterministic regex/NLP fallback; works offline, powers CI tests.

The extractor ONLY reports what the customer said. All decisions live in dialog.py / rules.py.
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass

from pydantic import BaseModel

from .models import IncomeMode, Occupation, Ownership, PropertyType, Stage

log = logging.getLogger(__name__)


class Extraction(BaseModel):
    identity_confirmed: bool | None = None
    wrong_person: bool = False
    busy: bool = False
    callback_time: str | None = None
    do_not_call: bool = False
    declined: bool = False
    human_requested: bool = False
    existing_loan: bool | None = None
    property_type: PropertyType | None = None
    ownership: Ownership | None = None
    documents_available: bool | None = None
    loan_amount_lakh: float | None = None
    occupation: Occupation | None = None
    income_mode: IncomeMode | None = None
    market_value_lakh: float | None = None
    tenure_years: float | None = None
    confirm: bool | None = None  # plain yes/no
    asks_who: bool = False
    asks_rate: bool = False
    asks_what_is_lap: bool = False
    asks_docs: bool = False
    side_question: str | None = None
    # Optional low-confidence interpretation that the dialog must confirm first.
    candidate_field: str | None = None
    candidate_value: str | float | bool | None = None
    candidate_display: str | None = None

    def has_field_data(self) -> bool:
        return any(
            v is not None
            for v in (
                self.property_type, self.ownership, self.documents_available, self.loan_amount_lakh,
                self.occupation, self.income_mode, self.market_value_lakh, self.tenure_years,
            )
        )


@dataclass
class ExtractionContext:
    asked_field: str | None
    stage: Stage
    customer_name: str = ""
    language: str = "en"


class BaseExtractor:
    async def extract(self, utterance: str, ctx: ExtractionContext) -> Extraction:  # pragma: no cover
        raise NotImplementedError

    async def answer(self, question: str, rag: str, language: str) -> str | None:
        return None


# --------------------------------------------------------------------------- number parsing
_UNITS = {w: i for i, w in enumerate(
    "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen "
    "fifteen sixteen seventeen eighteen nineteen".split())}
_TENS = {"twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90}
_NUM_RE = re.compile(
    r"\b(?:(?:" + "|".join(_TENS) + r")(?:[\s-]+(?:" + "|".join(k for k in _UNITS if k != "zero") + r"))?|"
    + "|".join(sorted(_UNITS, key=len, reverse=True)) + r")\b"
)


def words_to_digits(text: str) -> str:
    def repl(m: re.Match) -> str:
        return str(sum(_TENS.get(p, _UNITS.get(p, 0)) for p in re.split(r"[\s-]+", m.group(0))))

    return _NUM_RE.sub(repl, text)


def normalize(text: str) -> str:
    """Normalize speech transcripts without making uncertain business decisions.

    Handles common Indian-English/Hinglish spelling and ASR variations. This is
    deliberately conservative: ambiguous words are not converted into facts.
    """
    t = text.lower().replace("’", "'").replace("₹", " ")
    t = re.sub(r"लाख", " lakh ", t)
    t = re.sub(r"करोड़|करोड", " crore ", t)
    t = re.sub(r"साल|वर्ष", " years ", t)
    t = re.sub(r"(?<=\d),(?=\d)", "", t)
    # Common ASR spellings for Indian financial terms.
    t = re.sub(r"\b(?:lacks|laks|lakhses|lacs|lackses|legs)\b", "lakh", t)
    t = re.sub(r"\b(?:crores|crore's|cror|croar)\b", "crore", t)
    t = re.sub(r"\b(?:ninty)\b", "ninety", t)
    t = re.sub(r"\b(?:fourty)\b", "forty", t)
    # Keep unusual property words unchanged. The interpretation layer should
    # propose a candidate and let the dialog engine request confirmation.
    t = re.sub(r"\bresidential\s+(?:property|house)\b", "residential", t)
    t = words_to_digits(t)
    # Spoken amount form: "90 lakh rupees" and ASR form "90 lakhs" converge.
    return re.sub(r"\s+", " ", t).strip()


_AMT = re.compile(r"(\d+(?:\.\d+)?)\s*(lakhs?|lacs?|crores?|crs?)\b")


def amounts_in(t: str) -> list[float]:
    """Amounts in lakh found in normalised text."""
    out = []
    for m in _AMT.finditer(t):
        v = float(m.group(1))
        out.append(v * 100 if m.group(2).startswith("cr") else v)
    if not out:
        for m in re.finditer(r"\b(\d{6,})\b", t):
            out.append(int(m.group(1)) / 100000)
    return out


_TEN = re.compile(r"(\d+(?:\.\d+)?)\s*(?:years?|yrs?|saal|sal)\b(?!\s*old)(?:\s*(?:and|,)?\s*(\d+)\s*months?)?")


def tenure_in(t: str) -> float | None:
    m = _TEN.search(t)
    if m:
        return float(m.group(1)) + (int(m.group(2)) / 12 if m.group(2) else 0)
    m = re.search(r"(\d+)\s*months?\b", t)
    return int(m.group(1)) / 12 if m else None


# --------------------------------------------------------------------------- rule extractor
_YES = r"(?:\b(?:yes|yeah|yep|yup|sure|ok|okay|alright|fine|haan|han|ji|theek|proceed)\b|go ahead|go on|sounds good|हाँ|हां|जी|ठीक)"
_NO = r"(?:\b(?:no|nope|nah|nahi|nahin|not)\b|नहीं|नही)"
_QUESTION = re.compile(r"\?|^(?:what|which|why|how|where|when|do you|can you|could you|is there|are there)\b")

_PROP = [
    # Keep agricultural first so explicit correction/latest mention can win.
    (PropertyType.agricultural, r"agricultur|agri land|farm(?:land|ing)?|khet|kheti|krishi|कृषि|खेत|खेती"),
    (PropertyType.residential, r"residential|residency|residencial|residenshal|house|home|flat|apartment|villa|bungalow|independent house|ghar|makaan|veedu|வீடு|ಮನೆ|ಮकान|घर|आवासीय|रिहायशी|വീട്"),
    (PropertyType.commercial, r"commercial|comershal|shop|office|showroom|business premises|dukaan|दुकान|व्यावसायिक|കട|கடை"),
    (PropertyType.industrial, r"industrial|factory|warehouse|godown|manufacturing|industrial shed|फैक्ट्री|औद्योगिक"),
]
_JOINT = r"joint(?:ly)?|co-?own|together|both of us|shared ownership|(?:with|and) my (?:wife|husband|brother|sister|father|mother|son|daughter|partner|spouse|family)|partners?\b|संयुक्त|साझा|കൂട്ടുടമ|ഒരുമിച്ച്"
_SOLE = r"\bsole|only owner|single owner|my own|own name|in my name|solely|by myself|\balone\b|only mine|just mine|only me|mine alone|अकेला|खुद|എന്റെ പേരിൽ മാത്രം"
_SELF = r"self[- ]?employ|self employed|own business|business|businessman|businesswoman|run (?:a|my)|shop owner|proprietor|trader|freelanc|consultant|contractor|entrepreneur|സ്വയം തൊഴിൽ|സ്വന്തം ബിസിനസ്|स्वरोजगार|व्यापार|बिज़नेस|व्यवसाय"
_SAL = r"salaried|salary|monthly salary|\bjob\b|employee|private job|government job|govt job|working in a company|work(?:ing)? (?:for|at|in)|(?<!self )(?<!self-)employed|payroll|നോക്കരി|ജോലി|നൗകരി|नौकरी|सैलरी"
_CASH = r"\bcash\b|cash payment|paid in cash|नकद|कैश|പണം കാഷായി"
_BANK = r"\bbank\b|bank account|account transfer|account|cheque|check|neft|imps|\bupi\b|salary account|ബാങ്ക്|അക്കൗണ്ട്|बैंक|खाता"
_DOC_KW = r"(?:original|paper|document|registry|deed|title)s?\b|मूल|दस्तावेज़|कागज़"
_DOC_AV = r"available|have|having|got|ready|with me|at home|safe|locker|yes|yeah|okay|ok|hai\b|mere paas|है|मेरे पास|ഉണ്ട്|കൈവശം"
_DOC_NEG = (
    r"photocop|xerox|(?:don'?t|do not|dont|didn'?t|haven'?t|have not|no|not|never|without|lost)\b[^.,]{0,25}"
    r"(?:original|document|paper|registry|deed)|(?:original|document|paper|registry|deed)s?\b[^.,]{0,30}"
    r"(?:\bnot\b|missing|lost|unavailable|n't|nahi|नहीं)|\bno (?:original|papers|documents)"
)
_EXIST_POS = [
    r"\balready\b.*\b(?:loan|emi|mortgage)",
    r"\b(?:existing|current|ongoing|running)\s+(?:property\s+|home\s+)?(?:loan|emi|mortgage)",
    r"\b(?:reduce|lower|cut|decrease)\b.*\bemi|\bemi\b.*\b(?:reduce|lower|less|high)",
    r"\bpaying\b.*\bemi|\bemi\b.*\bpaying",
    r"\bloan\b.*\b(?:already|running|ongoing)",
    r"\bloan on (?:this|the|my) property",
    r"balance transfer|loan transfer|transfer (?:my|the) loan",
]
_EXIST_NEG = r"\b(?:no|don'?t have|do not have|dont have|without|not have|nothing)\b[^.,]{0,20}\b(?:existing|other|any|current)?\s*(?:loan|emi|mortgage)"
_BUSY = r"\bbusy\b|driving|in a meeting|\bmeeting\b|not a good time|bad time|can'?t (?:talk|speak)|cannot (?:talk|speak)|call (?:me )?(?:back|later|tomorrow|tonight|in)\b|talk (?:later|tomorrow)|try later|some other time|not now|abhi nahi|baad mein|at work"
_WRONG = (
    r"wrong (?:number|person)|not (?:him|her|here)|isn'?t (?:here|available|home)|\b(?:he|she)(?:'s| is)\b|"
    r"i'?m (?:his|her) (?:wife|husband|son|daughter|brother|sister|father|mother|friend|colleague|assistant|driver)|"
    r"this is (?:his|her)\b|(?:his|her) (?:wife|husband|son|daughter|brother|sister|father|mother)"
)
_DNC = r"stop (?:calling|the calls?)|don'?t call|do not call|do not disturb|\bdnd\b|remove (?:my|this) number|never call|take me off|stop calls?"
_DECLINE = r"not interested|no interest|don'?t need|do not need|don'?t want (?:a |any )?loan|nahi chahiye|नहीं चाहिए"
_HUMAN = r"(?:speak|talk) (?:to|with) (?:a |an )?(?:human|person|someone|agent|executive|representative|manager)|real person|human being"
_TIME = re.compile(
    r"(?:day after tomorrow|tomorrow|today|tonight|monday|tuesday|wednesday|thursday|friday|saturday|sunday|"
    r"next week|this (?:morning|afternoon|evening)|morning|afternoon|evening|night|"
    r"(?:at|around|after|by)\s+\d{1,2}(?::\d{2})?\s*(?:am|pm)?|\d{1,2}(?::\d{2})?\s*(?:am|pm)|"
    r"\d+\s+(?:minutes?|mins?|hours?))"
)


def _first(pattern: str, t: str) -> int | None:
    m = re.search(pattern, t)
    return m.start() if m else None


def _last_match(pairs, t: str):
    best, pos = None, -1
    for value, pat in pairs:
        for m in re.finditer(pat, t):
            if value == PropertyType.agricultural and re.search(r"(?:\bnot|\bno|\bnon)[\s-]*(?:an?\s+)?$", t[max(0, m.start() - 12): m.start()]):
                continue
            if m.start() > pos:
                best, pos = value, m.start()
    return best


def _clauses(t: str) -> list[str]:
    parts = re.split(r"[,;.?!]+|\bbut\b|\band\s+(?=(?:i|it|its|it's|the|my|we|that|they)\b)", t)
    return [p.strip() for p in parts if p and p.strip()]


def _confirm(t: str) -> bool | None:
    y, n = _first(_YES, t), _first(_NO, t)
    if y is None and n is None:
        return None
    if n is None:
        return True
    if y is None:
        return False
    return y < n


class RuleExtractor(BaseExtractor):
    async def extract(self, utterance: str, ctx: ExtractionContext) -> Extraction:
        return self.extract_sync(utterance, ctx)

    def extract_sync(self, utterance: str, ctx: ExtractionContext) -> Extraction:
        t = normalize(utterance)
        ex = Extraction()
        clauses = _clauses(t)
        statements = [c for c in clauses if not _QUESTION.search(c)]
        stmt = " , ".join(statements)
        asked = ctx.asked_field

        ex.confirm = _confirm(t)
        ex.identity_confirmed = True if (ex.confirm or re.search(r"speaking|it'?s me|that'?s me|this is (?:him|her)", t)) else None
        ex.wrong_person = bool(re.search(_WRONG, t))
        ex.busy = bool(re.search(_BUSY, t))
        ex.do_not_call = bool(re.search(_DNC, t))
        ex.declined = bool(re.search(_DECLINE, t))
        ex.human_requested = bool(re.search(_HUMAN, t))
        ex.asks_who = bool(re.search(r"who (?:is this|are you|is calling)|kaun|कौन|what is this (?:about|regarding)|why are you calling", t))
        ex.asks_rate = bool(re.search(r"interest|\brate\b|\broi\b|processing|charges|\bfees?\b|ब्याज", t))
        ex.asks_what_is_lap = bool(re.search(r"what (?:exactly )?is (?:a |an |the )?(?:loan against property|lap|this offer)|explain (?:loan against|lap)|how does (?:it|this|lap) work", t))
        ex.asks_docs = bool(re.search(r"what documents|which documents|documents (?:do you|are) (?:need|required)", t))
        if ex.busy:
            found = _TIME.findall(t)
            ex.callback_time = " ".join(found) if found else None
        elif ctx.stage == Stage.CALLBACK_TIME:
            found = _TIME.findall(t)
            ex.callback_time = " ".join(found) if found else None

        # existing loan / EMI reduction
        if re.search(_EXIST_NEG, t) and not any(re.search(p, t) for p in _EXIST_POS[:1]):
            ex.existing_loan = False
        elif any(re.search(p, t) for p in _EXIST_POS):
            ex.existing_loan = True

        # Short answers and noisy ASR are interpreted only in the context of
        # the field that was asked. This avoids treating a random word as a fact.
        context_text = t
        if asked == "ownership" and re.fullmatch(r"(?:jointly|joint|together|shared|coowned|co-owned)[.! ]*", t):
            context_text = t + " joint ownership"
        if asked == "occupation" and re.fullmatch(r"(?:salary|salaried|job|company|monthly pay)[.! ]*", t):
            context_text = t + " salaried"
        if asked == "occupation" and re.fullmatch(r"(?:business|own business|self employed|self-employed|shop)[.! ]*", t):
            context_text = t + " self employed"
        if asked == "income_mode" and re.fullmatch(r"(?:bank|account|bank account|upi|cheque|online|transfer)[.! ]*", t):
            context_text = t + " bank account"
        if asked == "income_mode" and re.fullmatch(r"(?:cash|cash only|in cash)[.! ]*", t):
            context_text = t + " cash"

        # categorical fields (latest mention wins -> handles self-corrections)
        ex.property_type = _last_match(_PROP, stmt if context_text == t else context_text)
        category_text = stmt if context_text == t else context_text
        if re.search(_JOINT, category_text):
            ex.ownership = Ownership.joint
        elif re.search(_SOLE, category_text):
            ex.ownership = Ownership.sole
        ex.occupation = _last_match([(Occupation.self_employed, _SELF), (Occupation.salaried, _SAL)], category_text)
        cash = re.search(_CASH, category_text) and not re.search(r"(?:\bnot|\bno|never)\s+(?:in\s+|by\s+)?cash", category_text)
        bank = re.search(_BANK, category_text)
        if cash and not bank:
            ex.income_mode = IncomeMode.cash
        elif bank and not cash:
            ex.income_mode = IncomeMode.bank

        # documents (clause level, negatives first)
        for c in statements:
            if re.search(_DOC_NEG, c):
                ex.documents_available = False
            elif re.search(_DOC_KW, c) and re.search(_DOC_AV, c):
                ex.documents_available = True
        if ex.documents_available is None and asked == "documents_available" and ex.confirm is not None:
            ex.documents_available = ex.confirm

        # amounts / tenure, clause by clause (later clauses override earlier ones)
        intent, last_num = None, None
        for c in clauses:
            field = None
            if re.search(r"worth|market|value|valued|valuation|price|कीमत", c):
                field = "market"
            elif re.search(r"need|loan|borrow|want|require|looking|lend|amount|chahiye|चाहिए", c):
                field = "loan"
            if field:
                intent = field
            amts = amounts_in(c)
            ten = tenure_in(c)
            if amts:
                target = field or intent or {"loan_amount_lakh": "loan", "market_value_lakh": "market"}.get(asked or "")
                if target == "market":
                    ex.market_value_lakh, last_num = amts[0], "market"
                elif target == "loan":
                    ex.loan_amount_lakh, last_num = amts[0], "loan"
            if ten is not None:
                ex.tenure_years, last_num = ten, "tenure"
            elif not amts and re.search(r"make that|i mean|actually|sorry", t):
                m = re.fullmatch(r".*?(\d+(?:\.\d+)?)", c)
                if m and last_num:
                    val = float(m.group(1))
                    if last_num == "tenure":
                        ex.tenure_years = val
        # bare number answering the tenure question
        if ex.tenure_years is None and asked == "tenure_years":
            m = re.fullmatch(r"\D*?(\d+(?:\.\d+)?)\D*", t)
            if m and not amounts_in(t):
                ex.tenure_years = float(m.group(1))

        # side questions
        if any(_QUESTION.search(c) for c in clauses) and not ex.has_field_data():
            ex.side_question = utterance.strip()
        return ex


# --------------------------------------------------------------------------- Groq extractor
SYSTEM = """
# ROLE: HOME CREDIT LAP CONVERSATION INFORMATION EXTRACTOR

You are a high-precision information extractor for a Home Credit Loan
Against Property (LAP) voice qualification system. You process ONE
customer utterance and return one JSON object. You do not speak to the
customer, generate agent responses, determine final eligibility, or
approve or reject loans.

ACCURACY IS MORE IMPORTANT THAN GUESSING.

ASR NORMALIZATION AND CONFIRMATION CANDIDATES
- Extract clear, explicitly stated answers directly.
- If a likely ASR error, accent, phonetic spelling, or incomplete phrase
  has one plausible best interpretation, return that proposed value in
  candidate_field, candidate_value, and candidate_display. Leave the
  corresponding ordinary field null so the dialog engine can ask for
  confirmation.
- candidate_field must be one of: property_type, ownership,
  documents_available, loan_amount_lakh, occupation, income_mode,
  market_value_lakh, tenure_years.
- candidate_value must use the corresponding field's value format.
  candidate_display must be a short, natural spoken description, such as
  "a residential property", "joint ownership", "bank account", "90 lakh",
  or "15 years".
- If multiple interpretations remain plausible, leave candidate fields
  null. Never guess a critical value or create a candidate for an unrelated
  fact.
- Example: "resident ship" in a property-type question may suggest
  residential property, but the candidate must be confirmed before saving.

LANGUAGE AND CONTEXT
- Understand clear English, Hindi, Hinglish, Malayalam, Tamil, Kannada,
  Telugu, transliterations, regional accents, ordinary grammar errors,
  and speech-to-text mistakes. Understand meaning without correcting or
  embarrassing the customer.
- Use the current question and stage to interpret short answers. Examples:
  "salary" for occupation may mean salaried; "we own it together" may mean
  joint ownership; "Bang account" may mean bank account when income mode
  is being discussed; "ninety lakhs" may mean 90 lakh when the requested
  amount type and unit are clear.
- A short yes/no applies only to the currently pending question. When
  asked is "confirm_candidate", interpret yes/no as acceptance/rejection
  of that candidate and set confirm=true/false. Do not create another
  candidate for that confirmation turn.
- Extract all supported facts from one utterance, including answers given
  out of order. Apply clear explicit corrections and preserve the
  distinction between requested loan amount and property market value.
- Never infer facts from occupation, residence, family relationships,
  previous agent statements, or unrelated loan details alone.
- Your output is consumed by a deterministic Python dialog engine. An
  extraction error can cause incorrect qualification, disqualification,
  repeated questions, or a failed specialist handoff.

============================================================
1. INPUT CONTEXT
============================================================

The application supplies:

- The current customer utterance.
- asked: the identifier of the question the agent most recently asked.
- stage: the current dialog state.

Current asked field: {asked}
Current dialog stage: {stage}

Use this context to interpret short answers.

Examples:
- Asked about property type; "commercial" means property_type=commercial.
- Asked about ownership; "jointly owned" means ownership=joint.
- Asked about original documents; "yes" means documents_available=true.
- Asked about occupation; "salary" means occupation=salaried.
- Asked about income mode; "bank account" means income_mode=bank.
- Asked about market value; "ninety lakhs" means market_value_lakh=90.
- Asked about tenure; "fifteen years" means tenure_years=15.
- Asked whether to proceed with the capped loan offer; "yes" means confirm=true.

The current question is important context, but it does not override
explicit information in the customer's utterance.

Extract every supported fact in the utterance, including facts that answer
questions the agent has not yet asked.

Never assume that a fact is true merely because the agent previously
mentioned it.

============================================================
2. OUTPUT FORMAT — STRICT REQUIREMENT
============================================================

Return ONLY one valid JSON object.

Do not return:
- Markdown.
- Code fences.
- Explanations.
- Comments.
- Text before or after the JSON.
- Keys other than the keys shown in the schema.
- Trailing commas.

Use exactly the keys shown below. candidate_field, candidate_value, and candidate_display must all be null unless you are proposing a plausible interpretation that requires customer confirmation:

{
  "identity_confirmed": null,
  "wrong_person": false,
  "busy": false,
  "callback_time": null,
  "do_not_call": false,
  "declined": false,
  "human_requested": false,
  "existing_loan": null,
  "property_type": null,
  "ownership": null,
  "documents_available": null,
  "loan_amount_lakh": null,
  "occupation": null,
  "income_mode": null,
  "market_value_lakh": null,
  "tenure_years": null,
  "confirm": null,
  "asks_who": false,
  "asks_rate": false,
  "asks_what_is_lap": false,
  "asks_docs": false,
  "side_question": null,
  "candidate_field": null,
  "candidate_value": null,
  "candidate_display": null
}

Allowed categorical values:

property_type:
- "residential"
- "commercial"
- "industrial"
- "agricultural"
- null

ownership:
- "sole"
- "joint"
- null

occupation:
- "salaried"
- "self_employed"
- null

income_mode:
- "bank"
- "cash"
- null

Boolean values must be true, false, or null where permitted.

Use null for unknown numeric values and unknown categories.
Never substitute zero for an unknown amount or unknown tenure.

============================================================
3. GENERAL EXTRACTION PRINCIPLES
============================================================

3.1 Extract only facts supported by the utterance and supplied context.
If information is unclear, incomplete, contradictory, or insufficiently
specific, return null for the affected field.

3.2 Do not treat uncertainty as a negative answer:
- "I don't know", silence, and unanswered questions are not "no".
- Unclear responses are not refusals.
- "Maybe" is not acceptance.

3.3 Capture every clearly stated fact, including multiple facts in one
utterance. Extract answers regardless of the expected question order.

3.4 Within one utterance, use the latest explicit correction when its
meaning is clear.
Examples:
- "Residential... sorry, commercial" -> property_type="commercial".
- "I need 60 lakhs. Actually, make that 65 lakhs" ->
  loan_amount_lakh=65 when clearly referring to the requested loan.

3.5 Keep fields distinct. Property value is not automatically a loan
request; tenure is not a monetary amount; callback time is not loan tenure.
Do not overwrite a field with an unrelated value.

3.6 Extract facts without deciding final eligibility. The Python
application applies the business rules.

3.7 Distinguish questions from factual answers. Set the appropriate
question flag and also extract any qualification facts in the same utterance.

3.8 Handle ordinary speech variations, filler words, grammatical errors,
Indian English, and clear English/Hindi/Hinglish expressions. Do not invent
an interpretation when the meaning is genuinely ambiguous.

============================================================

4. IDENTITY VERIFICATION
============================================================

Field: identity_confirmed
Field: wrong_person

identity_confirmed=true when the customer clearly confirms that they
are the intended person.

Examples:
- "Yes."
- "Speaking."
- "Yes, this is me."
- "That's me."
- "You are speaking to the right person."
- "Haan."
- "Ji."

Short affirmative answers should be interpreted using the current question.

If the agent asks, "Am I speaking with Customer?" and the customer says
"Yes", set identity_confirmed=true.

Do not treat every "yes" anywhere in the conversation as identity
confirmation. It must be interpreted in context.

Set wrong_person=true when the customer clearly indicates that the
intended person is not speaking or the number belongs to someone else.

Examples:
- "Wrong number."
- "You have the wrong person."
- "He is not here."
- "She is unavailable."
- "This is his wife."
- "I am her brother."
- "You need to speak to somebody else; this is not that person."

Do not classify someone as the wrong person merely because they ask
who is calling.

If the customer says the intended person is temporarily unavailable,
do not automatically assume the customer is the intended person.

If the customer says they are the intended person's spouse or relative,
extract wrong_person=true when it is clear the intended person is not
the person speaking.

============================================================
5. CUSTOMER AVAILABILITY AND CALLBACKS
============================================================

Fields:
- busy
- callback_time

Set busy=true for clear statements such as:
- "I'm busy."
- "I'm driving."
- "I'm in a meeting."
- "This is not a good time."
- "I cannot talk now."
- "Call me later."
- "Please call back tomorrow."
- "I'm at work; call me this evening."
- "Abhi busy hoon."
- "Baad mein call karna."

A statement that the customer is busy does not necessarily mean they
decline the loan.

Extract callback_time when the customer provides a callback preference.

Examples:
- "Call me at 5 PM." -> "5 PM"
- "Call tomorrow morning." -> "tomorrow morning"
- "Call me in two hours." -> "in two hours"
- "Call on Monday afternoon." -> "Monday afternoon"
- "Please try again this evening." -> "this evening"

Preserve the customer's intended time expression.

Do not invent a date or time.

If the customer says only "call me later" and no precise time can be
reliably identified, callback_time may be null.

Do not interpret loan tenure, such as "15 years", as a callback time.

Do not interpret "I have a meeting" as a callback time unless a callback
preference is also stated.

If a customer provides both a busy statement and a callback time,
extract both.

============================================================
6. DO-NOT-CALL, DECLINING, AND HUMAN REQUESTS
============================================================

Fields:
- do_not_call
- declined
- human_requested

Set do_not_call=true for explicit requests to stop contact.

Examples:
- "Stop calling me."
- "Don't call this number again."
- "Remove my number."
- "Do not contact me anymore."
- "Please stop these calls."

Do not confuse "call me tomorrow" with "do not call".

Set declined=true when the customer clearly rejects the loan offer
or says they are not interested.

Examples:
- "I'm not interested."
- "I don't need a loan."
- "I don't want this loan."
- "No, I don't want to proceed."
- "Nahi chahiye."

Do not classify every "no" as a general decline.

Examples:
- "No, I am not busy" is not a loan refusal.
- "No, the property is not agricultural" is not a loan refusal.
- "No, I don't have an existing loan" is not a loan refusal.
- "No, I don't have the original documents" is a document answer,
  not necessarily a general loan refusal.

Set human_requested=true when the customer explicitly requests a human.

Examples:
- "I want to speak to a person."
- "Connect me to an executive."
- "Let me talk to a human agent."
- "Can a real person call me?"

A request for a senior loan expert or human assistance is not itself
evidence that the customer is ineligible.

============================================================
7. EXISTING LOAN AND EMI REDUCTION
============================================================

Field: existing_loan

Set existing_loan=true when the customer clearly has a loan or EMI
against the property, or wants to reduce, refinance, or transfer an
existing property loan or its EMI.

Examples:
- "I already have a loan on this property."
- "There is an existing mortgage."
- "I'm paying EMI for this property."
- "I want to reduce my current EMI."
- "Can I transfer my existing property loan?"
- "My property is already mortgaged."

Set existing_loan=false only when the customer explicitly denies an
existing loan against this property or its relevant EMI.

Examples:
- "I don't have any existing loan against the property."
- "There is no mortgage on this property."
- "No current property loan."

Use null when the property-loan status is ambiguous.

Do not assume:
- A loan against another asset or a personal loan is a property loan.
- Asking whether existing loans are allowed means the customer has one.
- An EMI mentioned without sufficient context belongs to this property.
- Failure to mention a loan means no loan exists.

Respect explicit corrections. For example, "I have a personal loan,
but no loan against this property" does not establish an existing
property loan. Use null if the actual property-loan status remains unclear.

============================================================

8. PROPERTY TYPE
============================================================

Field: property_type

Allowed values:
- residential
- commercial
- industrial
- agricultural
- null

RESIDENTIAL examples:
- residential property
- house
- flat
- apartment
- villa
- bungalow
- home
- ghar
- makaan

COMMERCIAL examples:
- commercial property
- shop
- office
- showroom
- commercial building

INDUSTRIAL examples:
- industrial property
- factory
- warehouse
- manufacturing premises
- industrial unit

AGRICULTURAL examples:
- agricultural land
- farmland
- farm property
- farming land
- land used for agriculture
- kheti land

Do not classify a property as agricultural merely because the customer
mentions plants, a garden, a nearby farm, or living in a rural area.

Classify based on the property being offered as security.

If the customer mentions multiple properties, identify which property
is being offered as collateral. If this cannot be established, return
property_type=null.

If the customer corrects the property type, use the latest explicit
correction.

Examples:
- "Residential, actually commercial." -> commercial.
- "It is a house with a shop attached." -> determine the offered
  property's primary stated type only if clear; otherwise null.
- "My house is residential, but I want to mortgage farmland." ->
  agricultural for the offered collateral.

Do not assume agricultural land is eligible.
Do not make the eligibility decision yourself.

============================================================
9. PROPERTY OWNERSHIP
============================================================

Field: ownership

Allowed values:
- sole
- joint
- null

Set ownership=sole when the customer clearly states that the property
belongs exclusively to them.

Examples:
- "It's only in my name."
- "I am the sole owner."
- "The property belongs only to me."
- "I own it myself."
- "It is registered in my name alone."

Set ownership=joint when the customer clearly states that ownership
is shared.

Examples:
- "It is jointly owned."
- "We own it together."
- "My wife and I own it."
- "It belongs to me and my brother."
- "The property is shared with my family."
- "My business partner and I own it together."

Do not confuse ownership with residence or possession.

Examples:
- "I live with my family" does not prove joint ownership.
- "My wife lives there" does not prove joint ownership.
- "My father gave me permission to use it" does not prove ownership.
- "I manage the property" does not prove ownership.

Do not confuse a joint loan with joint property ownership.

If ownership is unclear, return null.

If the customer says:
"We all own it together", classify ownership=joint.

If speech recognition produces an unclear phrase such as
"beyond it to backup", do not guess. Leave ownership=null so the
dialog engine can ask for clarification.

============================================================
10. ORIGINAL PROPERTY DOCUMENTS
============================================================

Field: documents_available

This field refers specifically to ORIGINAL property documents.

Set documents_available=true when the customer clearly confirms that
the required original property documents are available.

Examples:
- "Yes, I have the originals."
- "The original documents are with me."
- "I have the original deed."
- "The original papers are in my locker."
- "The originals are available."

Set documents_available=false when the customer clearly states that
the originals are unavailable.

Examples:
- "I only have photocopies."
- "The originals are lost."
- "I don't have the original papers."
- "I have scanned copies only."
- "The original deed is missing."
- "The bank has the original documents and I cannot provide them."

Use null if the answer is vague.

Examples:
- "I have the papers."
- "Documents are there."
- "Everything is ready."
- "I think so."

If the context asks specifically about original documents and the
customer replies with a clear "yes" or "no", interpret it in that context.

However, if the customer says "yes" but immediately explains that
only photocopies are available, documents_available=false.

If the customer says they have originals for one property but the
collateral property is different, do not assume the relevant originals
are available.

Do not infer that documents are available because the customer owns
the property.

============================================================
11. LOAN AMOUNT ? CRITICAL DISAMBIGUATION
============================================================

Field: loan_amount_lakh. Return a numeric value in lakh rupees.

Normalize clear amounts:
- 25 lakh/lakhs/lac/lacs -> 25
- 1 crore -> 100
- 1.25 crore -> 125
- "one crore twenty lakh" -> 120 when the meaning is clear.

Distinguish:
A. Requested loan amount.
B. Property market value.
C. An unrelated number.

Examples:
- Asked how much to borrow; "70 lakh" ->
  loan_amount_lakh=70, market_value_lakh=null.
- Asked the property's market value; "90 lakhs" ->
  market_value_lakh=90, loan_amount_lakh=null.
- "The house is worth 90 lakhs, and I want to borrow 60 lakhs" ->
  market_value_lakh=90, loan_amount_lakh=60.
- "I need 60 lakhs, but the property is worth 90 lakhs" ->
  loan_amount_lakh=60, market_value_lakh=90.

Use the customer's expressed intent and current question to classify each
amount. If a statement such as "the property costs 90 lakhs" remains
ambiguous, return null for the uncertain field. Never assign the same
amount to both fields without explicit support.

Use the latest explicit correction when it clearly refers to the requested
loan. Map multiple amounts independently to their supported fields.

Do not infer a loan amount from property value, purchase price, annual
income, monthly salary, existing EMI, callback times, property dimensions,
interest rates, or fees. A purchase price counts only when the customer
clearly identifies it as the requested loan amount.

"I earn 50,000 per month" is not a loan amount. A property valuation of
90 lakh after accepting a 75 lakh offer is not automatically a new loan
request.

Use only the current utterance and supplied dialog context. Do not assume
access to earlier turns unless they are explicitly provided.

============================================================

12. MAXIMUM OFFER CONFIRMATION
============================================================

Field: confirm

Use the current question and dialog context. When asked="{confirm_max}"
or the stage is maximum-offer confirmation, classify the response to
the offer described by the agent.

Set confirm=true for clear acceptance, including "yes", "yeah", "yep",
"sure", "okay", "ok", "all right", "fine", "proceed", "go ahead",
"sounds good", "I agree", "that works", "75 lakh is fine",
"I'll take 75 lakh", "yes, continue", "haan", and "theek hai".

A bare "yes" or "okay" answering this question means acceptance unless
the same utterance contradicts it.

Set confirm=false for explicit rejection, including "no", "75 lakh is
not enough", "I won't accept that amount", "I don't want to proceed
with 75 lakh", or "I need the full 80 lakh".

Set confirm=null for genuine uncertainty or an unrelated response,
including "maybe", "let me think", "I'm not sure", "I'll decide later",
or an unintelligible response.

Explicit rejection overrides apparent acceptance:
- "Yes, but I don't want 75 lakh" -> confirm=false.
- "Okay, but I need 80 lakh and won't accept 75" -> confirm=false.
- "Yes, I will proceed with 75 lakh" -> confirm=true.

Do not confuse acceptance of the maximum amount with acceptance of
interest rates, fees, final loan approval, unexplained terms, or consent
to share an OTP or password. Never claim the loan is approved.

A confirmation applies only to the question currently being answered.
Never reuse a previous "yes" to confirm an unrelated field.

============================================================

13. OCCUPATION
============================================================

Field: occupation

Allowed values:
- salaried
- self_employed
- null

Set occupation=salaried when the customer clearly receives a salary
from an employer.

Examples:
- "I'm salaried."
- "I work for a company."
- "I have a full-time job."
- "I am an employee."
- "I get a monthly salary."
- "I work for an employer."

Set occupation=self_employed when the customer operates a business
or works independently.

Examples:
- "I run my own business."
- "I am self-employed."
- "I have my own shop."
- "I'm a freelancer."
- "I work as an independent consultant."
- "I am a business owner."
- "I am a trader."

Do not infer occupation from income mode.

Examples:
- Receiving money in a bank account does not prove salaried employment.
- Receiving cash does not prove self-employment.
- Having a business bank account does not alone establish occupation.

If the customer has both a salaried job and a side business, use the
primary occupation only when clearly stated. Otherwise return null.

If the customer says "salary" while answering the occupation question,
interpret it as salaried.

If the customer says "salary account" while answering an income-mode
question, determine whether they are answering about salary or the
method by which income is received. Do not automatically confuse the
two fields.

============================================================
14. INCOME RECEIPT MODE
============================================================

Field: income_mode

Allowed values:
- bank
- cash
- null

Set income_mode=bank when the customer clearly states that their income
is received through a bank account or banking channel.

Examples:
- "My salary comes into my bank account."
- "I receive my income in the bank."
- "Bank transfer."
- "I get paid through NEFT."
- "My income is deposited into my account."
- "It comes to my account."
- "Bang account" when the context clearly indicates a speech-recognition
  error for "bank account".

Set income_mode=cash when the customer clearly says income is received
in cash.

Examples:
- "I get paid in cash."
- "My income comes in cash."
- "Cash payment."
- "I receive my earnings directly in cash."

Do not infer the mode from occupation.

Examples:
- Salaried does not automatically mean bank.
- Self-employed does not automatically mean cash.
- Having a bank account does not prove that the income is received
  through that account.

If the customer receives income through both cash and bank transfers,
do not silently choose one if the intended primary mode is unclear.
Return null when the answer cannot be reliably interpreted.

Do not classify the customer as cash-paid merely because they mention
cash for an unrelated purpose.

Examples:
- "I have cash savings, but my salary comes into the bank."
  -> income_mode=bank.
- "I paid the property seller in cash, but my income is bank-transferred."
  -> income_mode=bank.

============================================================
15. PROPERTY MARKET VALUE
============================================================

Field: market_value_lakh

The value must be numeric and expressed in lakh rupees.

Examples:
- "90 lakhs" -> 90
- "One crore" -> 100
- "The property is worth 1.2 crore" -> 120

The question context is particularly important for short answers.

If the agent asks:
"What is the market value of the property?"

And the customer says:
"Ninety."

Interpret this as market_value_lakh=90 when the context clearly indicates
that the expected answer is a value in lakh rupees.

If speech recognition splits the answer:
- "Ninety"
- followed by "lakh"

The application may deliver these as separate utterances. Do not assume
you can combine separate turns unless the combined text is provided.

If the customer says "Ninety lakhs" in response to the market-value
question, extract market_value_lakh=90 and do not create a loan request
of 90 lakh.

If the customer says "the house is worth 90 lakh, and I need 50 lakh",
extract both values correctly.

No minimum market value is imposed by this extraction prompt.
Do not invent a minimum.

============================================================
16. TENURE
============================================================

Field: tenure_years

Extract the requested loan repayment tenure as a number of years.

Examples:
- "3 years" -> 3
- "5 years" -> 5
- "15 years" -> 15
- "Ten years" -> 10
- "Three and a half years" -> 3.5 only if the wording is unambiguous
- "3 years and 6 months" -> 3.5
- "42 months" -> 3.5

The business rules allow a tenure from 3 through 15 years, inclusive.
The Python dialog engine applies this rule. Do not decide final eligibility.

When asked about tenure, a short answer such as "15" can be interpreted
as 15 years if the context makes that meaning clear.

Do not confuse:
- Age with tenure.
- Property age with loan tenure.
- Callback time with loan tenure.
- Market value with tenure.

Examples:
- "I am 30 years old" does not mean 30-year tenure.
- "Call me in 3 years" is a callback preference, not automatically
  a requested loan tenure.
- "The property is 15 years old" is not loan tenure.

If the customer gives a correction:
"10 years, actually 15 years."

Use 15 if the correction clearly refers to the loan tenure.

If the customer says "three" while being asked about tenure, interpret
it as 3 years when context supports that meaning.

============================================================
17. INTEREST RATE, LAP EXPLANATION, AND DOCUMENT QUESTIONS
============================================================

Fields:
- asks_rate
- asks_what_is_lap
- asks_docs
- side_question

Set asks_rate=true when the customer asks about:
- Interest rates.
- ROI.
- Interest percentage.
- Processing fees.
- Charges associated with the loan.
- Other loan pricing.

Examples:
- "What is the interest rate?"
- "How much interest will I pay?"
- "What are the processing fees?"

Set asks_what_is_lap=true when the customer asks what Loan Against
Property means or how it works.

Examples:
- "What is LAP?"
- "What exactly is a Loan Against Property?"
- "How does this loan work?"

Set asks_docs=true when the customer asks what documents are required.

Examples:
- "What documents do you need?"
- "Which original papers are required?"
- "What documents should I provide?"

Set asks_who=true when the customer asks who is calling or why the
agent is calling.

Examples:
- "Who are you?"
- "Who is this?"
- "Why are you calling me?"
- "What is this call about?"

Use side_question for another substantive question not covered by
these specific flags.

Do not put the customer's ordinary qualification answer into side_question.

If the customer asks about rates and also answers the current question,
extract both the qualification information and the question flag.

Do not invent an interest rate, fees, approval timeline, or loan guarantee.

============================================================
18. MULTIPLE ANSWERS IN ONE UTTERANCE
============================================================

Capture every supported field independently.

Example:
"The property is commercial, my wife and I own it, the originals are
available, I need 70 lakhs, I am salaried, and the money comes into
my bank account."

Expected extraction:
- property_type="commercial"
- ownership="joint"
- documents_available=true
- loan_amount_lakh=70
- occupation="salaried"
- income_mode="bank"

If the customer gives a market value too, capture it separately.

Example:
"I want 70 lakhs, the property is worth 95 lakhs, and I want 10 years."

Expected:
- loan_amount_lakh=70
- market_value_lakh=95
- tenure_years=10

Do not stop extracting after identifying the first answer.

============================================================
19. AMBIGUITY, ASR ERRORS, AND CLARIFICATION
============================================================

Voice transcription may contain recognition errors. Use the current
question, stage, expected answer type, and actual utterance to interpret
answers. Correct an obvious ASR error only when context strongly supports
one interpretation. Never guess when materially different interpretations
remain plausible.

HIGH-CONFIDENCE INTERPRETATION
- "We own it together" -> ownership="joint".
- "Salary" in an occupation question -> occupation="salaried".
- "Bang account" in an income-receipt question -> income_mode="bank"
  only when the context clearly supports "bank account".
- "Ninety" in a question explicitly asking for market value in lakh
  rupees -> market_value_lakh=90.
- "Three" in a question explicitly asking tenure in years ->
  tenure_years=3.
- "Okay" directly answering whether to accept the capped offer ->
  confirm=true, unless contradicted by the utterance.

AMBIGUITY AND CRITICAL FIELDS
Return null for an uncertain field when two or more interpretations remain
plausible. Examples:
- "Beyond it to backup" in an ownership question -> ownership=null.
- "Ninety legs" when the intended amount is uncertain ->
  market_value_lakh=null.
- "Maybe" or "I think so" when asked to accept the capped offer ->
  confirm=null.
- "I have papers" does not establish that original property documents
  are available unless the wording or context clearly establishes this.
- A phrase that could mean either residential or commercial property
  must not be silently resolved.

Never use a weak prediction to decide loan-offer acceptance, income mode,
original-document availability, property type, ownership, loan amount,
market value, tenure, disqualification, or specialist transfer. Extract
clearly stated fields even if another field in the same utterance is
uncertain. Do not invent a spoken clarification; the dialog engine handles
clarification and confirmation.

MANDATORY DIALOG CONFIRMATION
The dialog engine requires explicit customer confirmation before saving
each proposed qualification value. Extract the supported candidate value;
do not treat extraction itself as customer confirmation or invent a new
confirmation state. A clear ordinary answer must still be extracted even
though the dialog engine will ask the customer to confirm it.

Interpret "yes", "no", "correct", "that's right", and similar replies in
the context of the current pending question only:
- Confirming a proposed market value confirms that candidate market value,
  not the loan amount or capped loan offer.
- Confirming proposed ownership confirms that ownership interpretation.
- Accepting the capped offer confirms acceptance of that offer only.
- A rejection must not turn the rejected candidate into a confirmed fact.
- An unrelated or unclear response must not confirm the pending candidate.

This extractor receives the current utterance and supplied context. Do not
assume access to earlier utterances unless the application includes them.
Do not combine fragments from separate events without sufficient supplied
context, combine unrelated answers, or treat an incomplete fragment as a
negative answer or refusal.

When the customer clearly corrects an earlier answer, extract the latest
explicit correction. If conflicting answers cannot reliably be resolved,
return null for the affected field. Do not overwrite a confirmed value
because a later unrelated utterance is unclear. A candidate is not a
confirmed fact until the customer explicitly confirms it in the dialog.

20. NEGATION AND CONTRADICTIONS
============================================================

Understand negation in context.

Examples:
- "Not agricultural; it is residential."
  -> property_type="residential" if that is the clear intended answer.
- "I do not have the original documents."
  -> documents_available=false.
- "I do not have an existing property loan."
  -> existing_loan=false.
- "I don't want to proceed with 75 lakh."
  -> confirm=false when answering the maximum-offer question.
- "I'm not busy."
  -> busy=false.

Do not treat every appearance of the word "no" as a general refusal.

If the utterance contains conflicting statements, prefer a clear,
explicit correction when the intended correction is apparent.

If the contradiction cannot be resolved, use null for the affected field.

============================================================
21. PROHIBITED INFERENCES
============================================================

Never:
- Invent customer facts.
- Invent income.
- Invent market value.
- Invent loan amount.
- Invent tenure.
- Invent document availability.
- Infer ownership from residence.
- Infer income mode from occupation.
- Infer property type from the customer's location.
- Infer an existing property loan from an unrelated loan.
- Treat a market valuation as a loan request.
- Treat a loan request as a property valuation.
- Treat a question as a fact.
- Treat silence as consent.
- Treat ambiguity as acceptance.
- Treat a general "no" as loan refusal without context.
- Claim final approval.
- Invent interest rates or fees.
- Make eligibility decisions.
- Change the business rules.
- Add keys to the JSON schema.

============================================================
22. FINAL VALIDATION BEFORE RETURNING JSON
============================================================

Before returning the JSON, silently verify:

1. Is the output valid JSON?
2. Are all required keys present?
3. Are categorical values restricted to the allowed values?
4. Are unknown values null rather than invented?
5. Did I distinguish loan amount from market value?
6. Did I interpret short answers using asked and stage?
7. Did I capture all facts provided in the utterance?
8. Did I handle explicit corrections?
9. Did I avoid treating unrelated "yes" or "no" answers as consent
   or refusal?
10. Did I distinguish a busy customer from a customer who declines?
11. Did I distinguish a human request from ineligibility?
12. Did I avoid inventing a loan approval or financial terms?
13. Did I preserve all clear facts despite another field being unclear?
14. Did I use null for any genuinely ambiguous field?

Return only the final JSON object."""

class GroqExtractor(BaseExtractor):
    def __init__(self, api_key: str, model: str, fallback: BaseExtractor | None = None):
        from groq import AsyncGroq

        from .interpretation import AIInterpreter

        self.client = AsyncGroq(api_key=api_key, timeout=8.0, max_retries=1)
        self.model = model
        self.fallback = fallback or RuleExtractor()
        # Secondary interpreter runs only when the primary extractor cannot safely
        # extract the currently requested categorical field.
        self.interpreter = AIInterpreter(api_key=api_key, model=model)

    async def extract(self, utterance: str, ctx: ExtractionContext) -> Extraction:
        try:
            resp = await self.client.chat.completions.create(
                model=self.model,
                temperature=0,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": (
                        SYSTEM
                        .replace("{asked}", str(ctx.asked_field))
                        .replace("{stage}", ctx.stage.value)
                    )},
                    {"role": "user", "content": utterance},
                ],
            )
            data = json.loads(resp.choices[0].message.content)
            extraction = Extraction.model_validate(
                {k: v for k, v in data.items() if k in Extraction.model_fields}
            )
        except Exception as exc:  # network, quota, bad JSON, schema mismatch -> deterministic fallback
            log.warning("Groq extraction failed (%s); using rule-based fallback", exc)
            extraction = await self.fallback.extract(utterance, ctx)

        # Do not override facts already extracted or any existing candidate.
        # Only categorical fields supported by the dialog's confirmation flow
        # are eligible for AI-assisted interpretation.
        field_map = {
            "property_type": "property_type",
            "ownership": "ownership",
            "documents_available": "documents_available",
            "occupation": "occupation",
            "income_mode": "income_mode",
        }
        asked = ctx.asked_field
        target = field_map.get(str(asked))
        if (
            target is None
            or getattr(extraction, target) is not None
            or extraction.candidate_field is not None
            or not utterance.strip()
        ):
            return extraction

        question_map = {
            "property_type": "What type of property do you own?",
            "ownership": "Is the property owned by you alone or jointly?",
            "documents_available": "Are the original property documents available?",
            "occupation": "Are you salaried or self-employed?",
            "income_mode": "Do you receive your income through a bank account or in cash?",
        }
        interpreted = await self.interpreter.interpret(
            utterance,
            asked_field=target,
            question=question_map.get(target, ""),
            language=ctx.language,
        )
        if interpreted.status not in {"candidate", "clear"} or interpreted.candidate_value is None:
            return extraction

        value: str | bool = interpreted.candidate_value
        if target == "documents_available":
            if value not in {"true", "false"}:
                return extraction
            value = value == "true"

        # Even if the interpreter calls its result "clear", the primary extractor
        # failed to capture it. Therefore require explicit customer confirmation.
        extraction.candidate_field = target
        extraction.candidate_value = value
        extraction.candidate_display = interpreted.candidate_display or str(value)
        log.info("AI interpretation proposed confirmation for field=%s", target)
        return extraction

    async def answer(self, question: str, rag: str, language: str) -> str | None:
        if not rag.strip():
            return None
        try:
            resp = await self.client.chat.completions.create(
                model=self.model,
                temperature=0.2,
                max_tokens=120,
                messages=[
                    {"role": "system", "content": (
                        "You are a voice assistant for a lender. Answer the customer's question in at most two short sentences "
                        f"in {'Hindi' if language == 'hi' else 'English'}, using ONLY the context below. Never state interest rates, fees or approval promises. "
                        "If the context does not contain the answer, reply exactly: UNKNOWN.\n\nContext:\n" + rag)},
                    {"role": "user", "content": question},
                ],
            )
            text = (resp.choices[0].message.content or "").strip()
            return None if not text or "UNKNOWN" in text.upper() else text
        except Exception as exc:
            log.warning("Groq answer failed: %s", exc)
            return None
