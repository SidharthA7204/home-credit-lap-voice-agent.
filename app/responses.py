"""Spoken responses (English + Hindi). Hindi strings use [female|male] markers resolved from agent_gender."""
from __future__ import annotations

import re

_GENDER = re.compile(r"\[([^|\]]+)\|([^\]]+)\]")


def fmt_amount(lakh: float, lang: str = "en") -> str:
    """Spoken-friendly Indian amount, e.g. 75 -> '75 lakh rupees', 100 -> '1 crore rupees'."""
    if lakh >= 100:
        n, unit = lakh / 100, ("करोड़" if lang == "hi" else "crore")
    else:
        n, unit = lakh, ("लाख" if lang == "hi" else "lakh")
    rupees = "रुपये" if lang == "hi" else "rupees"
    return f"{n:g} {unit} {rupees}"


def time_greeting(lang: str, hour: int | None) -> str:
    if lang == "hi":
        return "नमस्कार"
    if hour is None:
        return "Hello"
    if hour < 12:
        return "Good morning"
    if hour < 17:
        return "Good afternoon"
    return "Good evening"


EN = {
    "greet": "{greeting}. Am I speaking with {customer}?",
    "availability": "Thank you. This is {agent}, an AI assistant calling from {company}. Is now a convenient time to speak for two minutes?",
    "offer": "Thank you. As a valued {company} customer, you have a special pre-approved Loan Against Property offer of up to 75 lakh rupees. I'd like to ask a few quick questions to check whether it suits you.",
    "q_property_type": "What type of property is it: residential, commercial, or industrial?",
    "q_ownership": "Is the property solely in your name, or jointly owned with family or partners?",
    "q_documents_available": "Do you have the original property documents available for verification?",
    "q_loan_amount_lakh": "How much would you like to borrow?",
    "q_occupation": "Are you salaried, or self-employed?",
    "q_income_mode": "And is your income received in your bank account, or in cash?",
    "q_market_value_lakh": "Roughly what is the current market value of the property?",
    "q_tenure_years": "Over how many years would you like to repay the loan?",
    "amount_cap": "The maximum available under this offer is {cap}. Would you like to proceed with {cap}?",
    "tenure_range": "This offer allows a repayment period of 3 to 15 years. Which tenure within that range would you prefer?",
    "disqualified": "Thank you for sharing that. Based on your answer, you don't meet the criteria for this specific offer at this time. Thank you for your time, and have a good day.",
    "max_declined": "I understand. Unfortunately this offer can't go beyond 75 lakh rupees, so I won't be able to proceed. Thank you for your time, and have a good day.",
    "transfer": "Thank you for letting me know. Since there is an existing loan on the property, our loan transfer specialist will contact you shortly. Thank you for your time. Goodbye.",
    "handoff": "Thank you, {customer}. That's everything I needed. A senior loan expert will call you back shortly with the exact interest rates and next steps. Thank you for your time. Goodbye.",
    "callback_ask": "Certainly, I understand. What would be a convenient time for us to call you back?",
    "callback_ask_again": "Sorry, could you tell me the day and time that works best for a call back?",
    "callback_done": "Thank you. We'll call you back {when}. Have a great day. Goodbye.",
    "wrong_person": "I'm sorry for the disturbance. Thank you for your time. Goodbye.",
    "dnc": "I understand, and I apologise for the inconvenience. I've noted your request. Goodbye.",
    "declined": "Understood, no problem at all. Thank you for your time, and have a great day.",
    "human": "Of course. I'll arrange for a senior loan expert to call you back shortly. Thank you for your time. Goodbye.",
    "unclear_end": "I'm having trouble hearing you clearly, so I'll arrange a call back at a better time. Thank you. Goodbye.",
    "who_are_you": "This is {agent}, an AI assistant calling from {company} for {customer}. Am I speaking with {customer}?",
    "verify_retry": "Sorry, I didn't catch that. Am I speaking with {customer}?",
    "sorry": "Sorry, I didn't quite catch that.",
    "confirm_retry": "Sorry, I didn't catch that. Please say yes or no.",
    "rate_defer": "The exact interest rate will be shared by our senior loan expert after this quick check.",
    "what_is_lap": "A Loan Against Property lets you borrow by keeping your property as security, while you continue to own and use it.",
    "docs_needed": "You'll need the original property documents available for verification.",
    "expert_defer": "I don't have those details with me, but our senior loan expert will be happy to help with that.",
}
EN_ACKS = ["Thank you.", "Got it.", "Okay.", "Understood."]

HI = {
    "greet": "{greeting}। क्या मैं {customer} जी से बात कर [रही|रहा] हूँ?",
    "availability": "धन्यवाद। मैं {agent}, {company} की ओर से एक AI असिस्टेंट बोल [रही|रहा] हूँ। क्या अभी दो मिनट बात करने का सही समय है?",
    "offer": "धन्यवाद। {company} के सम्मानित ग्राहक के रूप में आपके लिए 75 लाख रुपये तक का एक विशेष प्री-अप्रूव्ड लोन अगेंस्ट प्रॉपर्टी ऑफर है। यह जानने के लिए कि यह आपके लिए उपयुक्त है या नहीं, मैं कुछ छोटे सवाल पूछना चाहूँ[गी|गा]।",
    "q_property_type": "आपकी प्रॉपर्टी किस प्रकार की है: रिहायशी, व्यावसायिक या औद्योगिक?",
    "q_ownership": "क्या प्रॉपर्टी सिर्फ आपके नाम पर है, या परिवार या पार्टनर के साथ संयुक्त है?",
    "q_documents_available": "क्या प्रॉपर्टी के मूल दस्तावेज़ सत्यापन के लिए आपके पास उपलब्ध हैं?",
    "q_loan_amount_lakh": "आप कितनी राशि का लोन लेना चाहते हैं?",
    "q_occupation": "क्या आप नौकरीपेशा हैं या अपना व्यवसाय करते हैं?",
    "q_income_mode": "और आपकी आय बैंक खाते में आती है या नकद में मिलती है?",
    "q_market_value_lakh": "आपकी प्रॉपर्टी की मौजूदा बाज़ार कीमत लगभग कितनी होगी?",
    "q_tenure_years": "आप लोन कितने सालों में चुकाना चाहेंगे?",
    "amount_cap": "इस ऑफर के तहत अधिकतम राशि {cap} है। क्या आप {cap} के साथ आगे बढ़ना चाहेंगे?",
    "tenure_range": "इस ऑफर में चुकौती अवधि 3 से 15 साल के बीच होनी चाहिए। आप इस दायरे में कितने साल चुनना चाहेंगे?",
    "disqualified": "यह बताने के लिए धन्यवाद। आपके उत्तर के अनुसार आप फिलहाल इस विशेष ऑफर के मानदंड पूरे नहीं करते। आपके समय के लिए धन्यवाद, आपका दिन शुभ हो।",
    "max_declined": "मैं समझ [सकती|सकता] हूँ। यह ऑफर 75 लाख रुपये से अधिक नहीं हो सकता, इसलिए मैं आगे नहीं बढ़ पाऊँ[गी|गा]। आपके समय के लिए धन्यवाद।",
    "transfer": "बताने के लिए धन्यवाद। चूँकि प्रॉपर्टी पर पहले से लोन है, हमारे लोन ट्रांसफर विशेषज्ञ जल्द ही आपसे संपर्क करेंगे। आपके समय के लिए धन्यवाद। नमस्कार।",
    "handoff": "धन्यवाद {customer} जी। मुझे जो जानकारी चाहिए थी वह मिल गई। हमारे वरिष्ठ लोन विशेषज्ञ जल्द ही आपको कॉल करके सटीक ब्याज दरें और अगले कदम बताएँगे। आपके समय के लिए धन्यवाद। नमस्कार।",
    "callback_ask": "जी बिल्कुल, मैं समझ [सकती|सकता] हूँ। हम आपको किस समय दोबारा कॉल करें?",
    "callback_ask_again": "माफ़ कीजिए, कृपया बताइए कि हम किस दिन और समय पर कॉल करें?",
    "callback_done": "धन्यवाद। हम आपको {when} कॉल करेंगे। आपका दिन शुभ हो। नमस्कार।",
    "wrong_person": "असुविधा के लिए खेद है। आपके समय के लिए धन्यवाद। नमस्कार।",
    "dnc": "मैं समझ [सकती|सकता] हूँ, असुविधा के लिए क्षमा चाह[ती|ता] हूँ। आपका अनुरोध दर्ज कर लिया गया है। नमस्कार।",
    "declined": "ठीक है, कोई बात नहीं। आपके समय के लिए धन्यवाद। आपका दिन शुभ हो।",
    "human": "जी बिल्कुल। मैं हमारे वरिष्ठ लोन विशेषज्ञ से जल्द ही आपको कॉल करवाऊँ[गी|गा]। धन्यवाद। नमस्कार।",
    "unclear_end": "आवाज़ साफ़ नहीं आ रही है, इसलिए मैं किसी और समय के लिए कॉलबैक की व्यवस्था करूँ[गी|गा]। धन्यवाद। नमस्कार।",
    "who_are_you": "मैं {agent}, {company} की ओर से {customer} जी के लिए कॉल कर [रही|रहा] हूँ। क्या मैं {customer} जी से बात कर [रही|रहा] हूँ?",
    "verify_retry": "माफ़ कीजिए, मैं समझ नहीं [पाई|पाया]। क्या मैं {customer} जी से बात कर [रही|रहा] हूँ?",
    "sorry": "माफ़ कीजिए, मैं ठीक से समझ नहीं [पाई|पाया]।",
    "confirm_retry": "माफ़ कीजिए, कृपया हाँ या ना में बताइए।",
    "rate_defer": "सटीक ब्याज दर हमारे वरिष्ठ लोन विशेषज्ञ इस जाँच के बाद बताएँगे।",
    "what_is_lap": "लोन अगेंस्ट प्रॉपर्टी में आप अपनी प्रॉपर्टी को गिरवी रखकर लोन लेते हैं, और प्रॉपर्टी आपके ही पास रहती है।",
    "docs_needed": "सत्यापन के लिए आपके पास प्रॉपर्टी के मूल दस्तावेज़ उपलब्ध होने चाहिए।",
    "expert_defer": "यह जानकारी अभी मेरे पास नहीं है, लेकिन हमारे वरिष्ठ लोन विशेषज्ञ इसमें आपकी मदद करेंगे।",
}
HI_ACKS = ["धन्यवाद।", "ठीक है।", "जी, समझ [गई|गया]।"]

_TABLE = {"en": EN, "hi": HI}
ACKS = {"en": EN_ACKS, "hi": HI_ACKS}


def resolve_gender(text: str, gender: str) -> str:
    female = gender.strip().lower() == "female"
    return _GENDER.sub(lambda m: m.group(1) if female else m.group(2), text)


def say(key: str, lang: str, gender: str, **kw) -> str:
    table = _TABLE.get(lang, EN)
    return resolve_gender(table[key].format(**kw), gender)


def ack(lang: str, gender: str, n: int) -> str:
    items = ACKS.get(lang, EN_ACKS)
    return resolve_gender(items[n % len(items)], gender)
