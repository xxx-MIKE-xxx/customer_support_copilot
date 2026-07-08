# Historical Support Response RAG Copilot

## 1. Project Overview

**Historical Support Response RAG Copilot** is an AI engineering project that builds a customer-support assistant using historical customer-company conversations.

The main idea is to treat previous **company responses** as approved or semi-approved reference answers. When a new customer message arrives, the system retrieves similar past customer issues and uses the corresponding company responses as context for drafting a new support reply.

This makes the project closer to a real-world AI support workflow than a generic chatbot because the system learns from historical support behavior instead of relying only on synthetic examples or manually written FAQ documents.

## 2. Core Project Idea

The project uses historical support conversations as paired examples:

```text
Customer message → Company response
```

The customer message is the input query.

The company response is used as:

1. a reference answer;
2. a retrieval document for RAG;
3. a weak evaluation target;
4. a source of response style and support behavior.

The company response should not be treated as a perfect ground-truth label. It is better described as a **historical reference response** because it may be short, brand-specific, outdated, incomplete, or dependent on private context.

## 3. Problem Statement

Customer support teams often handle many repetitive issues such as delivery problems, cancellations, refunds, payment failures, account access, and product questions.

A support agent may already have thousands or millions of historical conversations available, but searching through them manually is not practical.

The goal of this project is to build an AI copilot that can:

1. receive a new customer message;
2. classify the likely issue;
3. retrieve similar historical conversations;
4. use past company responses as examples;
5. generate a new response draft;
6. cite the retrieved historical examples;
7. recommend escalation when confidence is low.

## 4. Datasets

### 4.1 Primary Dataset: Customer Support on Twitter

The main dataset is **Customer Support on Twitter** from Kaggle. It contains over 3 million tweets and replies from major brands on Twitter/X, making it useful for studying real customer-brand support interactions.

The dataset includes fields such as tweet ID, author ID, creation time, text, and response-related IDs, which makes it possible to reconstruct customer-company conversation pairs.

This dataset is used for:

* extracting customer-message/company-response pairs;
* building the historical response retrieval corpus;
* training or evaluating response generation;
* analyzing real support conversation patterns;
* creating weak labels for issue categories.

### 4.2 Secondary Dataset: Bitext Customer Support Dataset

The secondary dataset is the **Bitext Customer Support LLM Chatbot Training Dataset**. It is a customer-service dataset designed for intent detection and chatbot training. The public Bitext description says it contains over 8,000 utterances across 27 common intents grouped into 11 major categories.

This dataset is used for:

* supervised intent classification;
* bootstrapping issue categories;
* creating synthetic evaluation cases;
* mapping historical Twitter conversations to cleaner business intents.

### 4.3 Optional Supporting Knowledge Base

A small fictional company knowledge base can be added as a secondary RAG source.

Example documents:

* refund policy;
* cancellation policy;
* delivery policy;
* payment troubleshooting guide;
* account security FAQ;
* escalation rules;
* tone-of-voice guide.

The historical company responses should be the main retrieval source. Policy documents are useful as guardrails when historical responses are too short or ambiguous.

## 5. Data Roles

| Data item                      | Role in the system                |
| ------------------------------ | --------------------------------- |
| Customer tweet/message         | Input query                       |
| Company response               | Historical reference response     |
| Similar past customer messages | Retrieval matches                 |
| Retrieved company responses    | RAG context                       |
| Bitext intent                  | Supervised intent label           |
| Generated response             | Model output                      |
| Human feedback                 | Evaluation and improvement signal |

## 6. Example Data Record

After preprocessing, each conversation pair should be stored in a structured format.

```json
{
  "conversation_id": "conv_001",
  "customer_message": "I want to cancel my order but the cancel button is missing.",
  "company_response": "Please DM us your order number so we can check the current status.",
  "brand": "example_brand",
  "channel": "twitter",
  "created_at": "2017-10-12T14:30:00",
  "intent": "cancel_order",
  "source": "customer_support_on_twitter"
}
```

## 7. Main Product Workflow

```text
New customer message
        |
        v
Text cleaning and PII masking
        |
        v
Intent classification
        |
        v
Retrieve similar historical customer messages
        |
        v
Fetch matching company responses
        |
        v
Generate response draft with LLM
        |
        v
Validate with guardrails
        |
        v
Return draft + sources + confidence + escalation recommendation
```

## 8. RAG Design

### 8.1 What Gets Indexed

Each indexed item should represent a historical support interaction.

Recommended vector database record:

```json
{
  "id": "support_pair_123",
  "text_for_embedding": "Customer issue: I cannot cancel my order. Company response: Please send us your order number so we can check the cancellation status.",
  "customer_message": "I cannot cancel my order.",
  "company_response": "Please send us your order number so we can check the cancellation status.",
  "brand": "example_brand",
  "intent": "cancel_order",
  "created_at": "2017-10-12T14:30:00",
  "metadata": {
    "channel": "twitter",
    "conversation_id": "conv_001"
  }
}
```

### 8.2 Retrieval Strategy

There are two useful retrieval approaches.

#### Option A: Embed only the customer message

```text
I cannot cancel my order.
```

This is cleaner because the system retrieves based on similarity between customer issues.

#### Option B: Embed customer message + company response

```text
Customer issue: I cannot cancel my order.
Company response: Please send us your order number so we can check the cancellation status.
```

This can improve semantic retrieval because the embedding contains both the problem and the resolution.

Recommended implementation:

1. Start with Option A.
2. Build an experiment comparing Option A and Option B.
3. Measure retrieval quality using Recall@k, MRR, and human review.
4. Keep the method that retrieves more useful response examples.

### 8.3 Retrieval Output

For a new customer message, the retriever should return similar historical examples.

```json
{
  "query": "I need to cancel my order but I cannot find the button.",
  "retrieved_examples": [
    {
      "customer_message": "I want to cancel my order but the cancel button is missing.",
      "company_response": "Please DM us your order number so we can check the current status.",
      "similarity_score": 0.89,
      "brand": "example_brand"
    },
    {
      "customer_message": "How do I cancel an order that already shipped?",
      "company_response": "Once an order has shipped, cancellation may not be available. Please send us your order details.",
      "similarity_score": 0.82,
      "brand": "example_brand"
    }
  ]
}
```

## 9. Response Generation

The LLM should use retrieved historical company responses as examples, not as facts to copy blindly.

The generated response should:

* answer the current customer message;
* follow the style of historical company responses;
* avoid inventing policies;
* avoid making unsupported promises;
* ask for missing information when needed;
* recommend escalation for risky or unclear cases.

### Prompt Template

```text
You are a customer support copilot.

Your task is to draft a response for a human support agent.

Use the retrieved historical company responses as examples.
Do not copy them word-for-word unless the wording is generic and safe.
Do not invent refund, cancellation, payment, delivery, or warranty rules.
If the retrieved examples are not relevant enough, recommend escalation.
If private information is needed, ask the customer to provide it through a secure channel.

Customer message:
{customer_message}

Detected intent:
{intent}

Retrieved historical support examples:
{retrieved_examples}

Optional company policy context:
{policy_context}

Return:
1. Draft response
2. Confidence score from 0 to 1
3. Sources used
4. Escalation recommendation
5. Short explanation for the support agent
```

## 10. Example System Output

```json
{
  "intent": "cancel_order",
  "intent_confidence": 0.91,
  "draft_response": "Hi, I’m sorry you’re having trouble canceling your order. Please send your order number through our secure support form or direct message so we can check whether the order is still eligible for cancellation.",
  "retrieved_sources": [
    {
      "customer_message": "I want to cancel my order but the cancel button is missing.",
      "company_response": "Please DM us your order number so we can check the current status.",
      "similarity_score": 0.89
    }
  ],
  "requires_human_review": false,
  "confidence": 0.84,
  "agent_note": "The retrieved examples suggest asking for the order number and checking cancellation status. No specific refund promise was made."
}
```

## 11. Key Machine Learning Components

### 11.1 Intent Classifier

The intent classifier predicts the support issue type.

Possible classes:

* cancel order;
* track order;
* refund request;
* payment issue;
* delivery issue;
* account access;
* password reset;
* product question;
* complaint;
* escalation request.

Recommended model progression:

1. TF-IDF + Logistic Regression baseline;
2. sentence embeddings + classifier;
3. fine-tuned transformer;
4. LLM-based classifier as comparison.

Metrics:

* accuracy;
* macro F1;
* per-class precision and recall;
* confusion matrix;
* calibration error.

### 11.2 Historical Response Retriever

The retriever finds similar historical support conversations.

Recommended approaches:

1. dense vector search;
2. BM25 keyword search;
3. hybrid search;
4. reranking with a cross-encoder or LLM.

Metrics:

* Recall@3;
* Recall@5;
* Mean Reciprocal Rank;
* nDCG;
* average retrieval latency;
* human relevance score.

### 11.3 Response Generator

The generator creates a draft response using the retrieved examples.

The model can be:

* hosted LLM API;
* local open-source model;
* fine-tuned model;
* smaller model with strong retrieval context.

Metrics:

* answer relevance;
* faithfulness to retrieved examples;
* tone quality;
* escalation correctness;
* hallucination rate;
* human acceptance rate.

## 12. Guardrails

The system must prevent unsafe or unsupported responses.

Guardrail checks:

1. Does the answer rely on retrieved examples?
2. Does it invent a policy?
3. Does it promise a refund, compensation, or delivery date without evidence?
4. Does it expose private information?
5. Does it ask for sensitive data in an unsafe way?
6. Is the retrieved context relevant enough?
7. Should this ticket be escalated?

Example guardrail output:

```json
{
  "passed": false,
  "issues": [
    "The generated answer promised a full refund, but no retrieved response supported that promise."
  ],
  "recommended_action": "regenerate_or_escalate"
}
```

## 13. Evaluation Strategy

### 13.1 Retrieval Evaluation

Create a test set of customer messages with known historical company responses.

For each customer message, check whether the system retrieves the original or a highly similar company response.

Metrics:

* Recall@1;
* Recall@3;
* Recall@5;
* MRR;
* nDCG.

Example:

```text
Input customer message:
"Where is my package? It says delivered but I never got it."

Expected retrieved response type:
Company asks for order number or tracking details and opens investigation.
```

### 13.2 Generation Evaluation

Compare the generated draft against the historical company response.

Important: the generated answer does not need to exactly match the original response. It should be judged on usefulness, correctness, tone, and grounding.

Metrics:

* semantic similarity to reference response;
* answer relevance;
* policy safety;
* hallucination rate;
* tone score;
* human rating.

### 13.3 Human Evaluation

Create a benchmark of 100–200 support tickets.

Human reviewers rate:

```text
1 = unusable
2 = poor
3 = acceptable with edits
4 = good
5 = ready to use
```

Review criteria:

* Is the answer helpful?
* Is it grounded in retrieved examples?
* Is the tone appropriate?
* Did it avoid unsupported promises?
* Should the ticket have been escalated?
* Would a support agent use this draft?

## 14. API Design

### POST `/tickets/analyze`

Analyzes the incoming customer message.

Input:

```json
{
  "message": "I need to cancel my order but I cannot find the cancel button.",
  "channel": "chat"
}
```

Output:

```json
{
  "intent": "cancel_order",
  "intent_confidence": 0.91,
  "priority": "medium",
  "requires_human_review": false
}
```

### POST `/tickets/retrieve-examples`

Retrieves similar historical support interactions.

Input:

```json
{
  "message": "I need to cancel my order but I cannot find the cancel button.",
  "top_k": 5
}
```

Output:

```json
{
  "retrieved_examples": [
    {
      "customer_message": "I want to cancel my order but the cancel button is missing.",
      "company_response": "Please DM us your order number so we can check the current status.",
      "similarity_score": 0.89
    }
  ]
}
```

### POST `/tickets/draft-response`

Generates a support response draft.

Input:

```json
{
  "message": "I need to cancel my order but I cannot find the cancel button.",
  "intent": "cancel_order",
  "top_k": 5
}
```

Output:

```json
{
  "draft_response": "Hi, I’m sorry you’re having trouble canceling your order. Please send your order number through our secure support form so we can check whether the order is still eligible for cancellation.",
  "confidence": 0.84,
  "requires_human_review": false,
  "sources": [
    {
      "customer_message": "I want to cancel my order but the cancel button is missing.",
      "company_response": "Please DM us your order number so we can check the current status.",
      "similarity_score": 0.89
    }
  ]
}
```

### POST `/feedback`

Collects support-agent feedback.

Input:

```json
{
  "ticket_id": "ticket_123",
  "agent_rating": 4,
  "agent_edited_response": true,
  "comment": "Useful draft, but needed a shorter tone."
}
```

## 15. User Interface

The UI should have four panels.

### Panel 1: Ticket Input

* customer message text box;
* channel selector;
* optional customer metadata;
* submit button.

### Panel 2: AI Analysis

Show:

* detected intent;
* confidence;
* priority;
* escalation flag.

### Panel 3: Retrieved Historical Examples

Show each retrieved example:

* similar customer message;
* company response;
* similarity score;
* brand or source;
* timestamp if available.

### Panel 4: Draft Response

Show:

* generated response;
* confidence score;
* cited historical examples;
* guardrail warnings;
* copy button;
* thumbs up/down feedback.

## 16. Recommended Tech Stack

| Layer               | Suggested tools                                                |
| ------------------- | -------------------------------------------------------------- |
| Backend API         | FastAPI                                                        |
| UI                  | Streamlit, Next.js, or React                                   |
| Data processing     | pandas, Polars                                                 |
| Classical ML        | scikit-learn                                                   |
| Embeddings          | SentenceTransformers, OpenAI embeddings, BGE, or E5            |
| Vector database     | Qdrant, Chroma, Weaviate, or Pinecone                          |
| Keyword search      | Elasticsearch, OpenSearch, or BM25                             |
| LLM                 | OpenAI, Anthropic, Gemini, or local Llama                      |
| Database            | PostgreSQL                                                     |
| Experiment tracking | MLflow or Weights & Biases                                     |
| Monitoring          | Prometheus, Grafana, Evidently                                 |
| Deployment          | Docker, Docker Compose, Cloud Run, Render, Fly.io, AWS, or GCP |

## 17. Data Pipeline

```text
Raw Twitter support dataset
        |
        v
Conversation reconstruction
        |
        v
Customer-company pair extraction
        |
        v
Cleaning and PII masking
        |
        v
Intent labeling
        |
        v
Embedding generation
        |
        v
Vector database indexing
        |
        v
Evaluation dataset creation
```

### 17.1 Conversation Pair Extraction

Steps:

1. Load raw Twitter support records.
2. Identify inbound customer messages.
3. Match each customer message to the company response using response IDs.
4. Remove conversations without clear customer-company pairs.
5. Remove duplicate or low-quality examples.
6. Store clean pairs in a structured format.

### 17.2 Cleaning

Apply:

* remove empty texts;
* normalize whitespace;
* mask emails;
* mask phone numbers;
* mask order IDs;
* mask usernames where needed;
* preserve important placeholders like `<ORDER_ID>` or `<EMAIL>`.

Example:

```text
Original:
My order #123456 never arrived. Email me at alex@example.com.

Cleaned:
My order <ORDER_ID> never arrived. Email me at <EMAIL>.
```

### 17.3 Intent Labeling

Use Bitext as the clean intent dataset.

For Twitter support conversations, assign weak labels using:

* keyword rules;
* embedding similarity to Bitext examples;
* zero-shot classification;
* manual validation sample.

Example:

```json
{
  "customer_message": "Where is my package? It says delivered but I never received it.",
  "weak_intent": "delivery_issue",
  "label_source": "embedding_similarity_to_bitext",
  "label_confidence": 0.78
}
```

## 18. Monitoring

Track:

* request volume;
* average latency;
* LLM cost per request;
* retrieval score distribution;
* percentage of low-confidence tickets;
* escalation rate;
* guardrail failure rate;
* agent acceptance rate;
* most common intents;
* most commonly retrieved historical responses.

Example metrics:

```text
support_copilot_request_count
support_copilot_avg_latency_seconds
retrieval_top1_similarity_avg
draft_guardrail_failure_rate
human_escalation_rate
agent_acceptance_rate
llm_cost_usd_per_day
```

## 19. Project Milestones

### Milestone 1: Dataset and Conversation Pair Extraction

Deliverables:

* raw data download instructions;
* script for loading Twitter support data;
* extracted customer-company pairs;
* cleaned dataset;
* exploratory data analysis notebook.

Success criteria:

* at least 100,000 usable customer-company pairs;
* documented data schema;
* examples of good and bad extracted pairs.

### Milestone 2: Intent Classification Baseline

Deliverables:

* Bitext-based intent classifier;
* weak labeling pipeline for Twitter conversations;
* classifier evaluation report;
* confusion matrix.

Success criteria:

* macro F1 above a majority-class baseline;
* clear explanation of weak-label limitations;
* manually reviewed sample of predictions.

### Milestone 3: Historical Response Retrieval

Deliverables:

* vector database index;
* retrieval API;
* comparison of embedding strategies;
* retrieval evaluation report.

Success criteria:

* relevant examples appear in top 5 for most test queries;
* retrieval results are shown with company responses;
* retrieval failure cases are documented.

### Milestone 4: RAG Response Drafting

Deliverables:

* prompt template;
* LLM response generator;
* source attribution;
* guardrail validation;
* generated response examples.

Success criteria:

* generated drafts use retrieved historical examples;
* unsupported policy claims are blocked;
* unclear cases are escalated.

### Milestone 5: Full Copilot Application

Deliverables:

* FastAPI backend;
* UI;
* feedback collection;
* Docker setup;
* deployment-ready configuration.

Success criteria:

* user can submit a support ticket and receive:

  * intent;
  * retrieved examples;
  * draft response;
  * confidence score;
  * escalation recommendation.

### Milestone 6: Evaluation and Portfolio Report

Deliverables:

* retrieval evaluation;
* generation evaluation;
* human review sample;
* monitoring dashboard;
* final README;
* architecture diagram;
* model card.

Success criteria:

* project is reproducible;
* metrics are clearly reported;
* failure cases and tradeoffs are documented.

## 20. Suggested Repository Structure

```text
historical-support-rag-copilot/
├── README.md
├── docker-compose.yml
├── .env.example
├── data/
│   ├── raw/
│   ├── interim/
│   ├── processed/
│   └── eval/
├── docs/
│   ├── project_documentation.md
│   ├── architecture.md
│   ├── evaluation_report.md
│   ├── model_card.md
│   └── policies/
│       ├── refund_policy.md
│       ├── cancellation_policy.md
│       ├── delivery_policy.md
│       └── escalation_rules.md
├── notebooks/
│   ├── 01_eda.ipynb
│   ├── 02_pair_extraction.ipynb
│   ├── 03_intent_baseline.ipynb
│   └── 04_retrieval_evaluation.ipynb
├── src/
│   ├── api/
│   │   ├── main.py
│   │   └── routes.py
│   ├── data/
│   │   ├── ingest_twitter.py
│   │   ├── extract_pairs.py
│   │   ├── clean_text.py
│   │   └── pii_masking.py
│   ├── labeling/
│   │   ├── intent_mapping.py
│   │   └── weak_labeling.py
│   ├── models/
│   │   ├── intent_classifier.py
│   │   └── priority_classifier.py
│   ├── retrieval/
│   │   ├── embeddings.py
│   │   ├── index_builder.py
│   │   ├── retriever.py
│   │   └── reranker.py
│   ├── generation/
│   │   ├── prompt_templates.py
│   │   └── response_generator.py
│   ├── guardrails/
│   │   └── validator.py
│   ├── evaluation/
│   │   ├── evaluate_intent.py
│   │   ├── evaluate_retrieval.py
│   │   └── evaluate_generation.py
│   └── monitoring/
│       └── metrics.py
├── tests/
│   ├── test_pair_extraction.py
│   ├── test_cleaning.py
│   ├── test_retrieval.py
│   ├── test_generation.py
│   └── test_api.py
└── frontend/
    └── app.py
```

## 21. Portfolio Presentation

The final portfolio page should include:

* project motivation;
* architecture diagram;
* dataset explanation;
* examples of extracted customer-company pairs;
* retrieval demo;
* generated response examples;
* evaluation metrics;
* failure cases;
* monitoring screenshots;
* deployment link;
* GitHub repository.

Strong portfolio points:

* uses real historical customer support conversations;
* shows practical RAG design;
* combines retrieval, classification, generation, guardrails, and evaluation;
* treats historical company responses as reference examples instead of blindly copying them;
* demonstrates human-in-the-loop support automation.

## 22. Success Metrics

### Retrieval Metrics

* Recall@3: target 0.75+
* Recall@5: target 0.85+
* MRR: target 0.65+
* average retrieval latency: below 500 ms

### Classification Metrics

* intent classifier macro F1: target 0.75+
* escalation recall for risky cases: target 0.85+

### Generation Metrics

* human response usefulness rating: target 4/5
* hallucination rate: below 5%
* unsupported policy claim rate: below 3%
* agent draft acceptance rate: target 60%+

### System Metrics

* end-to-end latency: below 5 seconds
* API uptime in demo environment: 99%+
* LLM cost per request: tracked and reported

## 23. Main Risks and Mitigations

| Risk                                            | Mitigation                                              |
| ----------------------------------------------- | ------------------------------------------------------- |
| Historical company responses are too short      | Retrieve multiple examples and add optional policy docs |
| Responses are brand-specific                    | Store brand metadata and filter by brand when needed    |
| Old responses may no longer be valid            | Add timestamp metadata and prefer newer responses       |
| LLM copies responses too directly               | Prompt against direct copying and check similarity      |
| LLM invents policy details                      | Use guardrails and optional policy context              |
| Weak intent labels are noisy                    | Manually validate a sample and report label quality     |
| Sensitive data appears in logs                  | Mask PII before indexing or logging                     |
| Retrieval finds similar wording but wrong issue | Add reranking and human evaluation                      |

## 24. Final Deliverables

The completed project should include:

1. customer-company pair extraction pipeline;
2. cleaned historical support dataset;
3. intent classifier;
4. vector database of historical support interactions;
5. retrieval API;
6. RAG response generator;
7. guardrail validator;
8. FastAPI backend;
9. simple UI;
10. evaluation scripts;
11. monitoring metrics;
12. Docker setup;
13. final README;
14. architecture diagram;
15. model card;
16. portfolio demo.

## 25. One-Sentence Portfolio Summary

Historical Support Response RAG Copilot is a production-style AI engineering project that retrieves similar historical customer support conversations and uses previous company responses as grounded examples to generate safe, useful, and reviewable support reply drafts.

