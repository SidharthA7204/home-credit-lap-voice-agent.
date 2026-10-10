# Test Results (deterministic engine, rule-based extractor)

Generated 2026-10-09 by `scripts/run_scenarios.py`. 26/26 passed.

> These are simulated text conversations against the dialog engine. Live voice-call results (recordings/links) are listed separately in `evidence/`.

| ID | Scenario | Expected | Actual | Status |
|---|---|---|---|---|
| T01 | Happy path - eligible customer | handoff | handoff | PASS |
| T02 | Agricultural property | disqualified | disqualified | PASS |
| T03 | Cash income (self-employed) | disqualified | disqualified | PASS |
| T04 | Original documents missing | disqualified | disqualified | PASS |
| T05 | Existing property loan -> transfer | transfer | transfer | PASS |
| T06 | Amount above 75L accepted at 75L, then qualifies | handoff | handoff | PASS |
| T07 | Tenure too short -> correction accepted | handoff | handoff | PASS |
| T08 | Tenure correction refused | disqualified | disqualified | PASS |
| T09 | Amount above limit, maximum rejected | disqualified | disqualified | PASS |
| T10 | Out-of-order: many facts in one sentence | handoff | handoff | PASS |
| T11 | Out-of-order: joint ownership + documents | in_progress | in_progress | PASS |
| T12 | Customer changes the amount | in_progress | in_progress | PASS |
| T13 | Vague market value accepted | handoff | handoff | PASS |
| T14 | Interest-rate question mid-flow | in_progress | in_progress | PASS |
| T15a | Busy, gives callback time immediately | callback | callback | PASS |
| T15b | Busy, agent asks for time | callback | callback | PASS |
| T16 | Wrong person - no loan details disclosed | wrong_person | wrong_person | PASS |
| T17 | Do-not-call request | do_not_call | do_not_call | PASS |
| T18 | Priority: agricultural + existing loan -> transfer | transfer | transfer | PASS |
| T19 | EMI reduction request -> transfer | transfer | transfer | PASS |
| T20 | Repeated unclear answers -> callback | unclear_callback | unclear_callback | PASS |
| T21 | Customer asks what LAP is, agent resumes | in_progress | in_progress | PASS |
| T22 | Hindi + female agent uses feminine grammar | in_progress | in_progress | PASS |
| T23 | Hindi + male agent uses masculine grammar | in_progress | in_progress | PASS |
| T24 | Contradiction: residential then agricultural (latest wins) | disqualified | disqualified | PASS |
| T25 | Customer asks for a human | human_callback | human_callback | PASS |

## Transcripts

### T01 - Happy path - eligible customer (PASS)
- **Agent:** Good morning. Am I speaking with Rahul Sharma?
- **User:** Yes, speaking
- **Agent:** Thank you. This is Riya, an AI assistant calling from Home Credit. Is now a convenient time to speak for two minutes?
- **User:** Yes sure, go ahead
- **Agent:** Thank you. As a valued Home Credit customer, you have a special pre-approved Loan Against Property offer of up to 75 lakh rupees. I'd like to ask a few quick questions to check whether it suits you. What type of property is it: residential, commercial, or industrial?
- **User:** It's a residential flat
- **Agent:** Got it. Is the property solely in your name, or jointly owned with family or partners?
- **User:** It's in my name only
- **Agent:** Okay. Do you have the original property documents available for verification?
- **User:** Yes the original documents are available
- **Agent:** Understood. How much would you like to borrow?
- **User:** I need fifty lakh
- **Agent:** Thank you. Are you salaried, or self-employed?
- **User:** I'm salaried
- **Agent:** Got it. And is your income received in your bank account, or in cash?
- **User:** It comes into my bank account
- **Agent:** Okay. Roughly what is the current market value of the property?
- **User:** About one crore
- **Agent:** Understood. Over how many years would you like to repay the loan?
- **User:** Ten years
- **Agent:** Thank you, Rahul Sharma. That's everything I needed. A senior loan expert will call you back shortly with the exact interest rates and next steps. Thank you for your time. Goodbye.

```json
{
  "call_outcome": "handoff",
  "outcome_reason": null,
  "identity_verified": true,
  "property_type": "residential",
  "ownership": "sole",
  "original_documents": true,
  "loan_amount_lakh": 50.0,
  "occupation": "salaried",
  "income_mode": "bank",
  "market_value_lakh": 100.0,
  "tenure_years": 10.0,
  "existing_loan_mentioned": false,
  "callback_time": null,
  "all_fields_complete": true
}
```

### T02 - Agricultural property (PASS)
- **Agent:** Good morning. Am I speaking with Rahul Sharma?
- **User:** Yes, speaking
- **Agent:** Thank you. This is Riya, an AI assistant calling from Home Credit. Is now a convenient time to speak for two minutes?
- **User:** Yes sure, go ahead
- **Agent:** Thank you. As a valued Home Credit customer, you have a special pre-approved Loan Against Property offer of up to 75 lakh rupees. I'd like to ask a few quick questions to check whether it suits you. What type of property is it: residential, commercial, or industrial?
- **User:** It's agricultural land
- **Agent:** Thank you for sharing that. Based on your answer, you don't meet the criteria for this specific offer at this time. Thank you for your time, and have a good day.

```json
{
  "call_outcome": "disqualified",
  "outcome_reason": "agricultural_property",
  "identity_verified": true,
  "property_type": "agricultural",
  "ownership": null,
  "original_documents": null,
  "loan_amount_lakh": null,
  "occupation": null,
  "income_mode": null,
  "market_value_lakh": null,
  "tenure_years": null,
  "existing_loan_mentioned": false,
  "callback_time": null,
  "all_fields_complete": false
}
```

### T03 - Cash income (self-employed) (PASS)
- **Agent:** Good morning. Am I speaking with Rahul Sharma?
- **User:** Yes, speaking
- **Agent:** Thank you. This is Riya, an AI assistant calling from Home Credit. Is now a convenient time to speak for two minutes?
- **User:** Yes sure, go ahead
- **Agent:** Thank you. As a valued Home Credit customer, you have a special pre-approved Loan Against Property offer of up to 75 lakh rupees. I'd like to ask a few quick questions to check whether it suits you. What type of property is it: residential, commercial, or industrial?
- **User:** Commercial shop, in my name, original documents are with me, and I need forty lakh
- **Agent:** Got it. Are you salaried, or self-employed?
- **User:** I run a business but I receive all my income in cash
- **Agent:** Thank you for sharing that. Based on your answer, you don't meet the criteria for this specific offer at this time. Thank you for your time, and have a good day.

```json
{
  "call_outcome": "disqualified",
  "outcome_reason": "cash_income",
  "identity_verified": true,
  "property_type": "commercial",
  "ownership": "sole",
  "original_documents": true,
  "loan_amount_lakh": 40.0,
  "occupation": "self_employed",
  "income_mode": "cash",
  "market_value_lakh": null,
  "tenure_years": null,
  "existing_loan_mentioned": false,
  "callback_time": null,
  "all_fields_complete": false
}
```

### T04 - Original documents missing (PASS)
- **Agent:** Good morning. Am I speaking with Rahul Sharma?
- **User:** Yes, speaking
- **Agent:** Thank you. This is Riya, an AI assistant calling from Home Credit. Is now a convenient time to speak for two minutes?
- **User:** Yes sure, go ahead
- **Agent:** Thank you. As a valued Home Credit customer, you have a special pre-approved Loan Against Property offer of up to 75 lakh rupees. I'd like to ask a few quick questions to check whether it suits you. What type of property is it: residential, commercial, or industrial?
- **User:** Residential
- **Agent:** Got it. Is the property solely in your name, or jointly owned with family or partners?
- **User:** Sole owner
- **Agent:** Okay. Do you have the original property documents available for verification?
- **User:** I only have photocopies
- **Agent:** Thank you for sharing that. Based on your answer, you don't meet the criteria for this specific offer at this time. Thank you for your time, and have a good day.

```json
{
  "call_outcome": "disqualified",
  "outcome_reason": "original_documents_unavailable",
  "identity_verified": true,
  "property_type": "residential",
  "ownership": "sole",
  "original_documents": false,
  "loan_amount_lakh": null,
  "occupation": null,
  "income_mode": null,
  "market_value_lakh": null,
  "tenure_years": null,
  "existing_loan_mentioned": false,
  "callback_time": null,
  "all_fields_complete": false
}
```

### T05 - Existing property loan -> transfer (PASS)
- **Agent:** Good morning. Am I speaking with Rahul Sharma?
- **User:** Yes, speaking
- **Agent:** Thank you. This is Riya, an AI assistant calling from Home Credit. Is now a convenient time to speak for two minutes?
- **User:** Yes sure, go ahead
- **Agent:** Thank you. As a valued Home Credit customer, you have a special pre-approved Loan Against Property offer of up to 75 lakh rupees. I'd like to ask a few quick questions to check whether it suits you. What type of property is it: residential, commercial, or industrial?
- **User:** I already have a loan on this property
- **Agent:** Thank you for letting me know. Since there is an existing loan on the property, our loan transfer specialist will contact you shortly. Thank you for your time. Goodbye.

```json
{
  "call_outcome": "transfer",
  "outcome_reason": "existing_loan",
  "identity_verified": true,
  "property_type": null,
  "ownership": null,
  "original_documents": null,
  "loan_amount_lakh": null,
  "occupation": null,
  "income_mode": null,
  "market_value_lakh": null,
  "tenure_years": null,
  "existing_loan_mentioned": true,
  "callback_time": null,
  "all_fields_complete": false
}
```

### T06 - Amount above 75L accepted at 75L, then qualifies (PASS)
- **Agent:** Good morning. Am I speaking with Rahul Sharma?
- **User:** Yes, speaking
- **Agent:** Thank you. This is Riya, an AI assistant calling from Home Credit. Is now a convenient time to speak for two minutes?
- **User:** Yes sure, go ahead
- **Agent:** Thank you. As a valued Home Credit customer, you have a special pre-approved Loan Against Property offer of up to 75 lakh rupees. I'd like to ask a few quick questions to check whether it suits you. What type of property is it: residential, commercial, or industrial?
- **User:** Residential
- **Agent:** Got it. Is the property solely in your name, or jointly owned with family or partners?
- **User:** Joint with my brother
- **Agent:** Okay. Do you have the original property documents available for verification?
- **User:** Yes the originals are available
- **Agent:** Understood. How much would you like to borrow?
- **User:** I need ninety lakh
- **Agent:** Thank you. The maximum available under this offer is 75 lakh rupees. Would you like to proceed with 75 lakh rupees?
- **User:** Yes, that's fine
- **Agent:** Got it. Are you salaried, or self-employed?
- **User:** Salaried
- **Agent:** Okay. And is your income received in your bank account, or in cash?
- **User:** Bank account
- **Agent:** Understood. Roughly what is the current market value of the property?
- **User:** 80 lakh
- **Agent:** Thank you. Over how many years would you like to repay the loan?
- **User:** Twelve years
- **Agent:** Thank you, Rahul Sharma. That's everything I needed. A senior loan expert will call you back shortly with the exact interest rates and next steps. Thank you for your time. Goodbye.

```json
{
  "call_outcome": "handoff",
  "outcome_reason": null,
  "identity_verified": true,
  "property_type": "residential",
  "ownership": "joint",
  "original_documents": true,
  "loan_amount_lakh": 75.0,
  "occupation": "salaried",
  "income_mode": "bank",
  "market_value_lakh": 80.0,
  "tenure_years": 12.0,
  "existing_loan_mentioned": false,
  "callback_time": null,
  "all_fields_complete": true
}
```

### T07 - Tenure too short -> correction accepted (PASS)
- **Agent:** Good morning. Am I speaking with Rahul Sharma?
- **User:** Yes, speaking
- **Agent:** Thank you. This is Riya, an AI assistant calling from Home Credit. Is now a convenient time to speak for two minutes?
- **User:** Yes sure, go ahead
- **Agent:** Thank you. As a valued Home Credit customer, you have a special pre-approved Loan Against Property offer of up to 75 lakh rupees. I'd like to ask a few quick questions to check whether it suits you. What type of property is it: residential, commercial, or industrial?
- **User:** Residential
- **Agent:** Got it. Is the property solely in your name, or jointly owned with family or partners?
- **User:** Sole
- **Agent:** Okay. Do you have the original property documents available for verification?
- **User:** Yes the original documents are available
- **Agent:** Understood. How much would you like to borrow?
- **User:** I need 30 lakh
- **Agent:** Thank you. Are you salaried, or self-employed?
- **User:** Salaried
- **Agent:** Got it. And is your income received in your bank account, or in cash?
- **User:** Bank
- **Agent:** Okay. Roughly what is the current market value of the property?
- **User:** One crore
- **Agent:** Understood. Over how many years would you like to repay the loan?
- **User:** I want to repay in two years
- **Agent:** Thank you. This offer allows a repayment period of 3 to 15 years. Which tenure within that range would you prefer?
- **User:** Ten years
- **Agent:** Thank you, Rahul Sharma. That's everything I needed. A senior loan expert will call you back shortly with the exact interest rates and next steps. Thank you for your time. Goodbye.

```json
{
  "call_outcome": "handoff",
  "outcome_reason": null,
  "identity_verified": true,
  "property_type": "residential",
  "ownership": "sole",
  "original_documents": true,
  "loan_amount_lakh": 30.0,
  "occupation": "salaried",
  "income_mode": "bank",
  "market_value_lakh": 100.0,
  "tenure_years": 10.0,
  "existing_loan_mentioned": false,
  "callback_time": null,
  "all_fields_complete": true
}
```

### T08 - Tenure correction refused (PASS)
- **Agent:** Good morning. Am I speaking with Rahul Sharma?
- **User:** Yes, speaking
- **Agent:** Thank you. This is Riya, an AI assistant calling from Home Credit. Is now a convenient time to speak for two minutes?
- **User:** Yes sure, go ahead
- **Agent:** Thank you. As a valued Home Credit customer, you have a special pre-approved Loan Against Property offer of up to 75 lakh rupees. I'd like to ask a few quick questions to check whether it suits you. What type of property is it: residential, commercial, or industrial?
- **User:** Residential
- **Agent:** Got it. Is the property solely in your name, or jointly owned with family or partners?
- **User:** Sole
- **Agent:** Okay. Do you have the original property documents available for verification?
- **User:** Yes the original documents are available
- **Agent:** Understood. How much would you like to borrow?
- **User:** I need 30 lakh
- **Agent:** Thank you. Are you salaried, or self-employed?
- **User:** Salaried
- **Agent:** Got it. And is your income received in your bank account, or in cash?
- **User:** Bank
- **Agent:** Okay. Roughly what is the current market value of the property?
- **User:** One crore
- **Agent:** Understood. Over how many years would you like to repay the loan?
- **User:** I want to repay in two years
- **Agent:** Thank you. This offer allows a repayment period of 3 to 15 years. Which tenure within that range would you prefer?
- **User:** No, I want two years only
- **Agent:** Thank you for sharing that. Based on your answer, you don't meet the criteria for this specific offer at this time. Thank you for your time, and have a good day.

```json
{
  "call_outcome": "disqualified",
  "outcome_reason": "tenure_outside_range_refused",
  "identity_verified": true,
  "property_type": "residential",
  "ownership": "sole",
  "original_documents": true,
  "loan_amount_lakh": 30.0,
  "occupation": "salaried",
  "income_mode": "bank",
  "market_value_lakh": 100.0,
  "tenure_years": null,
  "existing_loan_mentioned": false,
  "callback_time": null,
  "all_fields_complete": false
}
```

### T09 - Amount above limit, maximum rejected (PASS)
- **Agent:** Good morning. Am I speaking with Rahul Sharma?
- **User:** Yes, speaking
- **Agent:** Thank you. This is Riya, an AI assistant calling from Home Credit. Is now a convenient time to speak for two minutes?
- **User:** Yes sure, go ahead
- **Agent:** Thank you. As a valued Home Credit customer, you have a special pre-approved Loan Against Property offer of up to 75 lakh rupees. I'd like to ask a few quick questions to check whether it suits you. What type of property is it: residential, commercial, or industrial?
- **User:** Residential
- **Agent:** Got it. Is the property solely in your name, or jointly owned with family or partners?
- **User:** Sole
- **Agent:** Okay. Do you have the original property documents available for verification?
- **User:** Yes the original documents are available
- **Agent:** Understood. How much would you like to borrow?
- **User:** I need one crore
- **Agent:** Thank you. The maximum available under this offer is 75 lakh rupees. Would you like to proceed with 75 lakh rupees?
- **User:** No, I need the full one crore
- **Agent:** I understand. Unfortunately this offer can't go beyond 75 lakh rupees, so I won't be able to proceed. Thank you for your time, and have a good day.

```json
{
  "call_outcome": "disqualified",
  "outcome_reason": "declined_max_amount",
  "identity_verified": true,
  "property_type": "residential",
  "ownership": "sole",
  "original_documents": true,
  "loan_amount_lakh": null,
  "occupation": null,
  "income_mode": null,
  "market_value_lakh": null,
  "tenure_years": null,
  "existing_loan_mentioned": false,
  "callback_time": null,
  "all_fields_complete": false
}
```

### T10 - Out-of-order: many facts in one sentence (PASS)
- **Agent:** Good morning. Am I speaking with Rahul Sharma?
- **User:** Yes, speaking
- **Agent:** Thank you. This is Riya, an AI assistant calling from Home Credit. Is now a convenient time to speak for two minutes?
- **User:** Yes sure, go ahead
- **Agent:** Thank you. As a valued Home Credit customer, you have a special pre-approved Loan Against Property offer of up to 75 lakh rupees. I'd like to ask a few quick questions to check whether it suits you. What type of property is it: residential, commercial, or industrial?
- **User:** I'm self-employed, I have my own commercial shop, and I need forty lakh for eight years
- **Agent:** Got it. Do you have the original property documents available for verification?
- **User:** Yes the original papers are available
- **Agent:** Okay. And is your income received in your bank account, or in cash?
- **User:** The money comes into my bank account
- **Agent:** Understood. Roughly what is the current market value of the property?
- **User:** Around one crore
- **Agent:** Thank you, Rahul Sharma. That's everything I needed. A senior loan expert will call you back shortly with the exact interest rates and next steps. Thank you for your time. Goodbye.

```json
{
  "call_outcome": "handoff",
  "outcome_reason": null,
  "identity_verified": true,
  "property_type": "commercial",
  "ownership": "sole",
  "original_documents": true,
  "loan_amount_lakh": 40.0,
  "occupation": "self_employed",
  "income_mode": "bank",
  "market_value_lakh": 100.0,
  "tenure_years": 8.0,
  "existing_loan_mentioned": false,
  "callback_time": null,
  "all_fields_complete": true
}
```

### T11 - Out-of-order: joint ownership + documents (PASS)
- **Agent:** Good morning. Am I speaking with Rahul Sharma?
- **User:** Yes, speaking
- **Agent:** Thank you. This is Riya, an AI assistant calling from Home Credit. Is now a convenient time to speak for two minutes?
- **User:** Yes sure, go ahead
- **Agent:** Thank you. As a valued Home Credit customer, you have a special pre-approved Loan Against Property offer of up to 75 lakh rupees. I'd like to ask a few quick questions to check whether it suits you. What type of property is it: residential, commercial, or industrial?
- **User:** It's my residential property, jointly owned with my brother, and the original documents are available
- **Agent:** Got it. How much would you like to borrow?

```json
{
  "call_outcome": "in_progress",
  "outcome_reason": null,
  "identity_verified": true,
  "property_type": "residential",
  "ownership": "joint",
  "original_documents": true,
  "loan_amount_lakh": null,
  "occupation": null,
  "income_mode": null,
  "market_value_lakh": null,
  "tenure_years": null,
  "existing_loan_mentioned": false,
  "callback_time": null,
  "all_fields_complete": false
}
```

### T12 - Customer changes the amount (PASS)
- **Agent:** Good morning. Am I speaking with Rahul Sharma?
- **User:** Yes, speaking
- **Agent:** Thank you. This is Riya, an AI assistant calling from Home Credit. Is now a convenient time to speak for two minutes?
- **User:** Yes sure, go ahead
- **Agent:** Thank you. As a valued Home Credit customer, you have a special pre-approved Loan Against Property offer of up to 75 lakh rupees. I'd like to ask a few quick questions to check whether it suits you. What type of property is it: residential, commercial, or industrial?
- **User:** Residential
- **Agent:** Got it. Is the property solely in your name, or jointly owned with family or partners?
- **User:** Sole
- **Agent:** Okay. Do you have the original property documents available for verification?
- **User:** Original documents are available
- **Agent:** Understood. How much would you like to borrow?
- **User:** I need forty lakh. Actually, make that fifty lakh.
- **Agent:** Thank you. Are you salaried, or self-employed?

```json
{
  "call_outcome": "in_progress",
  "outcome_reason": null,
  "identity_verified": true,
  "property_type": "residential",
  "ownership": "sole",
  "original_documents": true,
  "loan_amount_lakh": 50.0,
  "occupation": null,
  "income_mode": null,
  "market_value_lakh": null,
  "tenure_years": null,
  "existing_loan_mentioned": false,
  "callback_time": null,
  "all_fields_complete": false
}
```

### T13 - Vague market value accepted (PASS)
- **Agent:** Good morning. Am I speaking with Rahul Sharma?
- **User:** Yes, speaking
- **Agent:** Thank you. This is Riya, an AI assistant calling from Home Credit. Is now a convenient time to speak for two minutes?
- **User:** Yes sure, go ahead
- **Agent:** Thank you. As a valued Home Credit customer, you have a special pre-approved Loan Against Property offer of up to 75 lakh rupees. I'd like to ask a few quick questions to check whether it suits you. What type of property is it: residential, commercial, or industrial?
- **User:** Residential house, only mine, original documents available, and I need 30 lakh
- **Agent:** Got it. Are you salaried, or self-employed?
- **User:** I'm salaried
- **Agent:** Okay. And is your income received in your bank account, or in cash?
- **User:** Yes it's credited to my bank
- **Agent:** Understood. Roughly what is the current market value of the property?
- **User:** The property is worth quite a lot, maybe somewhere around one crore.
- **Agent:** Thank you. Over how many years would you like to repay the loan?
- **User:** Ten years
- **Agent:** Thank you, Rahul Sharma. That's everything I needed. A senior loan expert will call you back shortly with the exact interest rates and next steps. Thank you for your time. Goodbye.

```json
{
  "call_outcome": "handoff",
  "outcome_reason": null,
  "identity_verified": true,
  "property_type": "residential",
  "ownership": "sole",
  "original_documents": true,
  "loan_amount_lakh": 30.0,
  "occupation": "salaried",
  "income_mode": "bank",
  "market_value_lakh": 100.0,
  "tenure_years": 10.0,
  "existing_loan_mentioned": false,
  "callback_time": null,
  "all_fields_complete": true
}
```

### T14 - Interest-rate question mid-flow (PASS)
- **Agent:** Good morning. Am I speaking with Rahul Sharma?
- **User:** Yes, speaking
- **Agent:** Thank you. This is Riya, an AI assistant calling from Home Credit. Is now a convenient time to speak for two minutes?
- **User:** Yes sure, go ahead
- **Agent:** Thank you. As a valued Home Credit customer, you have a special pre-approved Loan Against Property offer of up to 75 lakh rupees. I'd like to ask a few quick questions to check whether it suits you. What type of property is it: residential, commercial, or industrial?
- **User:** Before I answer, what interest rate will you charge?
- **Agent:** The exact interest rate will be shared by our senior loan expert after this quick check. What type of property is it: residential, commercial, or industrial?

```json
{
  "call_outcome": "in_progress",
  "outcome_reason": null,
  "identity_verified": true,
  "property_type": null,
  "ownership": null,
  "original_documents": null,
  "loan_amount_lakh": null,
  "occupation": null,
  "income_mode": null,
  "market_value_lakh": null,
  "tenure_years": null,
  "existing_loan_mentioned": false,
  "callback_time": null,
  "all_fields_complete": false
}
```

### T15a - Busy, gives callback time immediately (PASS)
- **Agent:** Good morning. Am I speaking with Rahul Sharma?
- **User:** Yes this is Rahul, but I'm driving. Call me tomorrow evening.
- **Agent:** Thank you. We'll call you back tomorrow evening. Have a great day. Goodbye.

```json
{
  "call_outcome": "callback",
  "outcome_reason": "customer_busy",
  "identity_verified": true,
  "property_type": null,
  "ownership": null,
  "original_documents": null,
  "loan_amount_lakh": null,
  "occupation": null,
  "income_mode": null,
  "market_value_lakh": null,
  "tenure_years": null,
  "existing_loan_mentioned": false,
  "callback_time": "tomorrow evening",
  "all_fields_complete": false
}
```

### T15b - Busy, agent asks for time (PASS)
- **Agent:** Good morning. Am I speaking with Rahul Sharma?
- **User:** Yes speaking
- **Agent:** Thank you. This is Riya, an AI assistant calling from Home Credit. Is now a convenient time to speak for two minutes?
- **User:** I'm in a meeting right now
- **Agent:** Certainly, I understand. What would be a convenient time for us to call you back?
- **User:** Call me at 6 pm
- **Agent:** Thank you. We'll call you back at 6 pm. Have a great day. Goodbye.

```json
{
  "call_outcome": "callback",
  "outcome_reason": "customer_busy",
  "identity_verified": true,
  "property_type": null,
  "ownership": null,
  "original_documents": null,
  "loan_amount_lakh": null,
  "occupation": null,
  "income_mode": null,
  "market_value_lakh": null,
  "tenure_years": null,
  "existing_loan_mentioned": false,
  "callback_time": "at 6 pm",
  "all_fields_complete": false
}
```

### T16 - Wrong person - no loan details disclosed (PASS)
- **Agent:** Good morning. Am I speaking with Rahul Sharma?
- **User:** I'm his wife
- **Agent:** I'm sorry for the disturbance. Thank you for your time. Goodbye.

```json
{
  "call_outcome": "wrong_person",
  "outcome_reason": "wrong_person",
  "identity_verified": false,
  "property_type": null,
  "ownership": null,
  "original_documents": null,
  "loan_amount_lakh": null,
  "occupation": null,
  "income_mode": null,
  "market_value_lakh": null,
  "tenure_years": null,
  "existing_loan_mentioned": false,
  "callback_time": null,
  "all_fields_complete": false
}
```

### T17 - Do-not-call request (PASS)
- **Agent:** Good morning. Am I speaking with Rahul Sharma?
- **User:** Yes, speaking
- **Agent:** Thank you. This is Riya, an AI assistant calling from Home Credit. Is now a convenient time to speak for two minutes?
- **User:** Yes sure, go ahead
- **Agent:** Thank you. As a valued Home Credit customer, you have a special pre-approved Loan Against Property offer of up to 75 lakh rupees. I'd like to ask a few quick questions to check whether it suits you. What type of property is it: residential, commercial, or industrial?
- **User:** Please stop calling me
- **Agent:** I understand, and I apologise for the inconvenience. I've noted your request. Goodbye.

```json
{
  "call_outcome": "do_not_call",
  "outcome_reason": "do_not_call",
  "identity_verified": true,
  "property_type": null,
  "ownership": null,
  "original_documents": null,
  "loan_amount_lakh": null,
  "occupation": null,
  "income_mode": null,
  "market_value_lakh": null,
  "tenure_years": null,
  "existing_loan_mentioned": false,
  "callback_time": null,
  "all_fields_complete": false
}
```

### T18 - Priority: agricultural + existing loan -> transfer (PASS)
- **Agent:** Good morning. Am I speaking with Rahul Sharma?
- **User:** Yes, speaking
- **Agent:** Thank you. This is Riya, an AI assistant calling from Home Credit. Is now a convenient time to speak for two minutes?
- **User:** Yes sure, go ahead
- **Agent:** Thank you. As a valued Home Credit customer, you have a special pre-approved Loan Against Property offer of up to 75 lakh rupees. I'd like to ask a few quick questions to check whether it suits you. What type of property is it: residential, commercial, or industrial?
- **User:** I have agricultural land, and I already have a loan against it
- **Agent:** Thank you for letting me know. Since there is an existing loan on the property, our loan transfer specialist will contact you shortly. Thank you for your time. Goodbye.

```json
{
  "call_outcome": "transfer",
  "outcome_reason": "existing_loan",
  "identity_verified": true,
  "property_type": null,
  "ownership": null,
  "original_documents": null,
  "loan_amount_lakh": null,
  "occupation": null,
  "income_mode": null,
  "market_value_lakh": null,
  "tenure_years": null,
  "existing_loan_mentioned": true,
  "callback_time": null,
  "all_fields_complete": false
}
```

### T19 - EMI reduction request -> transfer (PASS)
- **Agent:** Good morning. Am I speaking with Rahul Sharma?
- **User:** Yes, speaking
- **Agent:** Thank you. This is Riya, an AI assistant calling from Home Credit. Is now a convenient time to speak for two minutes?
- **User:** Yes sure, go ahead
- **Agent:** Thank you. As a valued Home Credit customer, you have a special pre-approved Loan Against Property offer of up to 75 lakh rupees. I'd like to ask a few quick questions to check whether it suits you. What type of property is it: residential, commercial, or industrial?
- **User:** I want to reduce my current EMI
- **Agent:** Thank you for letting me know. Since there is an existing loan on the property, our loan transfer specialist will contact you shortly. Thank you for your time. Goodbye.

```json
{
  "call_outcome": "transfer",
  "outcome_reason": "existing_loan",
  "identity_verified": true,
  "property_type": null,
  "ownership": null,
  "original_documents": null,
  "loan_amount_lakh": null,
  "occupation": null,
  "income_mode": null,
  "market_value_lakh": null,
  "tenure_years": null,
  "existing_loan_mentioned": true,
  "callback_time": null,
  "all_fields_complete": false
}
```

### T20 - Repeated unclear answers -> callback (PASS)
- **Agent:** Good morning. Am I speaking with Rahul Sharma?
- **User:** Yes, speaking
- **Agent:** Thank you. This is Riya, an AI assistant calling from Home Credit. Is now a convenient time to speak for two minutes?
- **User:** Yes sure, go ahead
- **Agent:** Thank you. As a valued Home Credit customer, you have a special pre-approved Loan Against Property offer of up to 75 lakh rupees. I'd like to ask a few quick questions to check whether it suits you. What type of property is it: residential, commercial, or industrial?
- **User:** Hmm... umm
- **Agent:** Sorry, I didn't quite catch that. What type of property is it: residential, commercial, or industrial?
- **User:** uh
- **Agent:** Sorry, I didn't quite catch that. What type of property is it: residential, commercial, or industrial?
- **User:** hmm
- **Agent:** I'm having trouble hearing you clearly, so I'll arrange a call back at a better time. Thank you. Goodbye.

```json
{
  "call_outcome": "unclear_callback",
  "outcome_reason": "unclear_responses",
  "identity_verified": true,
  "property_type": null,
  "ownership": null,
  "original_documents": null,
  "loan_amount_lakh": null,
  "occupation": null,
  "income_mode": null,
  "market_value_lakh": null,
  "tenure_years": null,
  "existing_loan_mentioned": false,
  "callback_time": null,
  "all_fields_complete": false
}
```

### T21 - Customer asks what LAP is, agent resumes (PASS)
- **Agent:** Good morning. Am I speaking with Rahul Sharma?
- **User:** Yes, speaking
- **Agent:** Thank you. This is Riya, an AI assistant calling from Home Credit. Is now a convenient time to speak for two minutes?
- **User:** Yes sure, go ahead
- **Agent:** Thank you. As a valued Home Credit customer, you have a special pre-approved Loan Against Property offer of up to 75 lakh rupees. I'd like to ask a few quick questions to check whether it suits you. What type of property is it: residential, commercial, or industrial?
- **User:** Wait, what exactly is a loan against property?
- **Agent:** A Loan Against Property lets you borrow by keeping your property as security, while you continue to own and use it. What type of property is it: residential, commercial, or industrial?

```json
{
  "call_outcome": "in_progress",
  "outcome_reason": null,
  "identity_verified": true,
  "property_type": null,
  "ownership": null,
  "original_documents": null,
  "loan_amount_lakh": null,
  "occupation": null,
  "income_mode": null,
  "market_value_lakh": null,
  "tenure_years": null,
  "existing_loan_mentioned": false,
  "callback_time": null,
  "all_fields_complete": false
}
```

### T22 - Hindi + female agent uses feminine grammar (PASS)
- **Agent:** नमस्कार। क्या मैं Rahul Sharma जी से बात कर रही हूँ?
- **User:** Haan ji, bol raha hoon
- **Agent:** धन्यवाद। मैं Riya, Home Credit की ओर से एक AI असिस्टेंट बोल रही हूँ। क्या अभी दो मिनट बात करने का सही समय है?
- **User:** Haan ji bataiye
- **Agent:** धन्यवाद। Home Credit के सम्मानित ग्राहक के रूप में आपके लिए 75 लाख रुपये तक का एक विशेष प्री-अप्रूव्ड लोन अगेंस्ट प्रॉपर्टी ऑफर है। यह जानने के लिए कि यह आपके लिए उपयुक्त है या नहीं, मैं कुछ छोटे सवाल पूछना चाहूँगी। आपकी प्रॉपर्टी किस प्रकार की है: रिहायशी, व्यावसायिक या औद्योगिक?

```json
{
  "call_outcome": "in_progress",
  "outcome_reason": null,
  "identity_verified": true,
  "property_type": null,
  "ownership": null,
  "original_documents": null,
  "loan_amount_lakh": null,
  "occupation": null,
  "income_mode": null,
  "market_value_lakh": null,
  "tenure_years": null,
  "existing_loan_mentioned": false,
  "callback_time": null,
  "all_fields_complete": false
}
```

### T23 - Hindi + male agent uses masculine grammar (PASS)
- **Agent:** नमस्कार। क्या मैं Rahul Sharma जी से बात कर रहा हूँ?
- **User:** Haan ji, bol raha hoon
- **Agent:** धन्यवाद। मैं Riya, Home Credit की ओर से एक AI असिस्टेंट बोल रहा हूँ। क्या अभी दो मिनट बात करने का सही समय है?
- **User:** Haan ji bataiye
- **Agent:** धन्यवाद। Home Credit के सम्मानित ग्राहक के रूप में आपके लिए 75 लाख रुपये तक का एक विशेष प्री-अप्रूव्ड लोन अगेंस्ट प्रॉपर्टी ऑफर है। यह जानने के लिए कि यह आपके लिए उपयुक्त है या नहीं, मैं कुछ छोटे सवाल पूछना चाहूँगा। आपकी प्रॉपर्टी किस प्रकार की है: रिहायशी, व्यावसायिक या औद्योगिक?

```json
{
  "call_outcome": "in_progress",
  "outcome_reason": null,
  "identity_verified": true,
  "property_type": null,
  "ownership": null,
  "original_documents": null,
  "loan_amount_lakh": null,
  "occupation": null,
  "income_mode": null,
  "market_value_lakh": null,
  "tenure_years": null,
  "existing_loan_mentioned": false,
  "callback_time": null,
  "all_fields_complete": false
}
```

### T24 - Contradiction: residential then agricultural (latest wins) (PASS)
- **Agent:** Good morning. Am I speaking with Rahul Sharma?
- **User:** Yes, speaking
- **Agent:** Thank you. This is Riya, an AI assistant calling from Home Credit. Is now a convenient time to speak for two minutes?
- **User:** Yes sure, go ahead
- **Agent:** Thank you. As a valued Home Credit customer, you have a special pre-approved Loan Against Property offer of up to 75 lakh rupees. I'd like to ask a few quick questions to check whether it suits you. What type of property is it: residential, commercial, or industrial?
- **User:** It's residential... actually no, it's agricultural land
- **Agent:** Thank you for sharing that. Based on your answer, you don't meet the criteria for this specific offer at this time. Thank you for your time, and have a good day.

```json
{
  "call_outcome": "disqualified",
  "outcome_reason": "agricultural_property",
  "identity_verified": true,
  "property_type": "agricultural",
  "ownership": null,
  "original_documents": null,
  "loan_amount_lakh": null,
  "occupation": null,
  "income_mode": null,
  "market_value_lakh": null,
  "tenure_years": null,
  "existing_loan_mentioned": false,
  "callback_time": null,
  "all_fields_complete": false
}
```

### T25 - Customer asks for a human (PASS)
- **Agent:** Good morning. Am I speaking with Rahul Sharma?
- **User:** Yes, speaking
- **Agent:** Thank you. This is Riya, an AI assistant calling from Home Credit. Is now a convenient time to speak for two minutes?
- **User:** Yes sure, go ahead
- **Agent:** Thank you. As a valued Home Credit customer, you have a special pre-approved Loan Against Property offer of up to 75 lakh rupees. I'd like to ask a few quick questions to check whether it suits you. What type of property is it: residential, commercial, or industrial?
- **User:** I'd rather speak to a human please
- **Agent:** Of course. I'll arrange for a senior loan expert to call you back shortly. Thank you for your time. Goodbye.

```json
{
  "call_outcome": "human_callback",
  "outcome_reason": "human_requested",
  "identity_verified": true,
  "property_type": null,
  "ownership": null,
  "original_documents": null,
  "loan_amount_lakh": null,
  "occupation": null,
  "income_mode": null,
  "market_value_lakh": null,
  "tenure_years": null,
  "existing_loan_mentioned": false,
  "callback_time": null,
  "all_fields_complete": false
}
```
