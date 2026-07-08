# Project Documentation: Reference-Answer RAG Customer Support Copilot

## 1. Project Overview

This project builds a **Customer Support Copilot** that helps support agents answer customer messages by retrieving similar historical support conversations and using official company responses as reference answers.

Instead of treating the dataset only as raw chat text, the project treats each historical **company response** as a supervised reference label. For a new customer message, the system retrieves similar past customer issues, fetches the corresponding company responses, and uses those examples as grounding context for an LLM-generated draft.

The main idea is:

> “Given a new customer complaint or question, find similar past customer messages and official company replies, then generate a high-quality answer that follows the company’s historical support style.”

The primary dataset is **Customer Support on Twitter**, which contains over 3 million tweets and replies from major brands on Twitter/X. The dataset contains fields such as `tweet_id`, `author_id`, `created_at`, `text`, `inbound`, `response_tweet_id`, and `in_response_to_tweet_id`, which makes it possible to reconstruct customer-company conversation pairs.

## 2. Business Problem

Customer support teams often receive many repeated questions:

* delivery delays,
* refund requests,
* account access issues,
* app bugs,
* billing complaints,
* service outages,
* product availability questions.

A human support agent usually needs to search internal documentation or previous tickets before replying. This is slow and inconsistent.

This project solves that by building an AI assistant that:

1. classifies the customer’s issue,
2. retrieves similar historical support cases,
3. shows official historical company replies,
4. generates a suggested response,
5. explains which past cases influenced the answer,
6. flags low-confidence cases for human review.

The final system should behave like an internal support tool, not a public-facing autonomous chatbot.

## 3. Core Project Idea

The key modification is to use **company responses as labels**.

In a standard RAG system, the retrieved documents are usually documentation pages, FAQs, or knowledge base articles.

In this project, the retrieved documents are **historical solved support cases**:

```text
Customer message → Company response
```

The customer message becomes the retrieval query candidate.

The company response becomes the reference label.

For training and evaluation, the system learns:

```text
Given this customer message,
can the system retrieve similar past cases
and generate an answer close to the real company response?
```

This turns the project into a hybrid of:

* retrieval-based customer support,
* supervised response modeling,
* RAG evaluation,
* customer service workflow automation.

## 4. Dataset

### Primary Dataset

**Customer Support on Twitter**

The dataset contains customer support interactions between customers and company support accounts. It includes inbound customer tweets and outbound company replies.

Relevant fields:

| Field                     | Meaning                                           |
| ------------------------- | ------------------------------------------------- |
| `tweet_id`                | Unique anonymized tweet ID                        |
| `author_id`               | Anonymized author or company support account      |
| `inbound`                 | Whether the tweet is from a customer to a company |
| `created_at`              | Timestamp                                         |
| `text`                    | Tweet content                                     |
| `response_tweet_id`       | ID or IDs of replies to this tweet                |
| `in_response_to_tweet_id` | ID of the tweet this tweet replied to             |

### Optional Secondary Dataset

**Bitext Customer Support LLM Chatbot Training Dataset**

This dataset can be used as an auxiliary dataset for intent classification, issue categorization, or prompt testing. Bitext describes the dataset as a customer support dataset with over 8,000 utterances, 27 common intents, and 11 major categories.

Use it only as a supporting dataset, not as the main source of truth, because the main goal is to learn from real historical company responses.

## 5. Target Users

The target users are:

* customer support agents,
* support team leads,
* QA reviewers,
* customer experience analysts.

The system does not replace support agents. It helps them respond faster and more consistently.

## 6. Main Features

### 6.1 Customer Message Intake

The user enters a customer message, for example:

```text
My order says delivered but I never received it. Can someone help?
```

The system should:

* clean the message,
* detect language if needed,
* classify the issue,
* retrieve similar historical cases,
* generate a draft reply.

### 6.2 Similar Case Retrieval

The system embeds the new customer message and searches a vector database for similar historical customer messages.

Each retrieved case should include:

```text
Customer message
Official company response
Brand/company
Timestamp
Conversation ID
Similarity score
```

The retrieved company responses are used as reference examples.

### 6.3 Reference-Aware Answer Generation

The LLM receives:

* the new customer message,
* top-k similar historical customer messages,
* their official company responses,
* response style rules,
* safety rules,
* escalation rules.

The output should be a draft response, not an automatically sent message.

Example output:

```text
I’m sorry this happened. Please send us a private message with your order number and delivery address so we can look into this for you.
```

The response should be grounded in retrieved examples and should not invent policies.

### 6.4 Evidence Panel

The UI should show the retrieved reference cases used by the system.

For each retrieved case:

```text
Similarity: 0.87
Customer: My package says delivered but it’s not here.
Company: Sorry about that. Please DM us your order number and delivery address so we can check this with the carrier.
```

This makes the project stronger because it shows explainability, not just generation.

### 6.5 Confidence and Escalation

The system should estimate whether it is safe to suggest an answer.

Escalate to human review when:

* retrieval similarity is low,
* retrieved examples disagree with each other,
* customer message contains legal, medical, financial, or safety-sensitive content,
* customer is angry or threatening,
* the model tries to answer without evidence,
* no similar reference cases are found.

## 7. Machine Learning Tasks

This project includes several AI engineering tasks.

### Task 1: Conversation Reconstruction

Use `tweet_id`, `response_tweet_id`, and `in_response_to_tweet_id` to reconstruct pairs:

```text
customer_message → company_response
```

Start with single-turn examples before supporting multi-turn conversations.

Minimum useful training row:

```json
{
  "customer_text": "...",
  "company_response": "...",
  "company": "...",
  "created_at": "...",
  "conversation_id": "...",
  "intent": "...",
  "sentiment": "..."
}
```

### Task 2: Label Creation

Treat `company_response` as the gold label.

For each customer message:

```text
Input: customer_text
Label: company_response
```

This allows several evaluation tasks:

* Can retrieval find similar labeled examples?
* Can the generated answer match the style and intent of the label?
* Can the system recommend the correct type of response?
* Can the system avoid hallucinating unsupported policies?

### Task 3: Intent Classification

Train or prompt an intent classifier.

Possible intents:

* refund request,
* delivery issue,
* account access,
* payment issue,
* technical bug,
* service outage,
* cancellation,
* complaint,
* general question,
* escalation required.

The Bitext dataset can help bootstrap intent labels because it contains customer support utterances grouped into common intents and categories.

### Task 4: Retrieval Model

Build a vector search index over historical customer messages.

Recommended embedding options:

* OpenAI embeddings,
* Cohere embeddings,
* Sentence Transformers,
* BGE embeddings.

Recommended vector databases:

* Qdrant,
* Weaviate,
* Pinecone,
* Chroma for local development.

Each vector record should store:

```json
{
  "customer_text": "...",
  "company_response": "...",
  "company": "...",
  "intent": "...",
  "created_at": "...",
  "conversation_id": "..."
}
```

### Task 5: RAG Generation

Build a prompt that uses retrieved references.

The model should not simply copy one historical reply. It should synthesize a new response from multiple relevant company responses.

Prompt structure:

```text
You are a customer support assistant helping a human agent.

New customer message:
{customer_message}

Retrieved historical support cases:
1. Customer: ...
   Official company response: ...

2. Customer: ...
   Official company response: ...

Instructions:
- Use the historical company responses as reference answers.
- Do not invent policies.
- If the references are not relevant, say that human review is needed.
- Keep the answer short, helpful, and professional.
- Do not claim actions were completed unless the references support it.

Draft response:
```

## 8. System Architecture

```text
                  ┌────────────────────┐
                  │ Customer Message    │
                  └─────────┬──────────┘
                            │
                            v
                  ┌────────────────────┐
                  │ Preprocessing       │
                  │ cleaning, language  │
                  │ detection, PII mask │
                  └─────────┬──────────┘
                            │
                            v
                  ┌────────────────────┐
                  │ Intent Classifier   │
                  └─────────┬──────────┘
                            │
                            v
                  ┌────────────────────┐
                  │ Embedding Model     │
                  └─────────┬──────────┘
                            │
                            v
                  ┌────────────────────┐
                  │ Vector Database     │
                  │ similar cases       │
                  └─────────┬──────────┘
                            │
                            v
                  ┌────────────────────┐
                  │ RAG Prompt Builder  │
                  └─────────┬──────────┘
                            │
                            v
                  ┌────────────────────┐
                  │ LLM Draft Generator │
                  └─────────┬──────────┘
                            │
                            v
                  ┌────────────────────┐
                  │ Guardrails + Eval   │
                  └─────────┬──────────┘
                            │
                            v
                  ┌────────────────────┐
                  │ Agent UI / API      │
                  └────────────────────┘
```

## 9. Backend API

Build the backend with FastAPI.

### Endpoint: `POST /suggest-response`

Request:

```json
{
  "customer_message": "My order says delivered but I never got it.",
  "company": "AmazonHelp",
  "top_k": 5
}
```

Response:

```json
{
  "draft_response": "I’m sorry this happened. Please send us a private message with your order number and delivery address so we can look into this.",
  "intent": "delivery_issue",
  "confidence": 0.84,
  "needs_human_review": false,
  "retrieved_cases": [
    {
      "customer_text": "My package says delivered but I never received it.",
      "company_response": "Sorry about that. Please DM us your order number and delivery address so we can check this with the carrier.",
      "similarity": 0.89
    }
  ]
}
```

### Endpoint: `POST /evaluate`

Evaluate generated answers against historical labels.

Request:

```json
{
  "customer_message": "...",
  "gold_company_response": "...",
  "generated_response": "..."
}
```

Response:

```json
{
  "semantic_similarity": 0.82,
  "retrieval_hit": true,
  "faithfulness_score": 0.91,
  "toxicity_flag": false,
  "policy_hallucination_flag": false
}
```

## 10. Frontend

Build a simple dashboard using Streamlit, Next.js, or React.

The UI should contain:

1. customer message input,
2. selected company or brand,
3. generated draft response,
4. retrieved reference cases,
5. confidence score,
6. human review warning,
7. feedback buttons:

   * good answer,
   * wrong intent,
   * unsafe answer,
   * not enough evidence.

This feedback can later be stored for evaluation and improvement.

## 11. Evaluation Plan

The project should not rely only on “the answer looks good.”

Use offline and qualitative evaluation.

### 11.1 Retrieval Evaluation

Split historical data into train/test.

For each test customer message:

1. hide the real company response,
2. retrieve similar cases from the training set,
3. check whether retrieved cases have similar intent or response style.

Metrics:

* Recall@k,
* MRR,
* cosine similarity,
* intent match rate,
* company match rate.

### 11.2 Generation Evaluation

Compare the generated response to the real company response label.

Metrics:

* semantic similarity,
* BERTScore,
* ROUGE as a weak baseline,
* LLM-as-judge score,
* human review score.

Important: the generated response does not need to match the label word-for-word. It should match the intent, policy, tone, and action.

### 11.3 RAG Faithfulness Evaluation

Check whether the answer is supported by retrieved company responses.

Questions:

* Did the model invent a refund policy?
* Did it ask for information that similar company responses asked for?
* Did it claim an action was completed without evidence?
* Did it contradict retrieved examples?

### 11.4 Safety Evaluation

Flag responses that:

* request sensitive personal information unnecessarily,
* include offensive language,
* make legal or financial promises,
* reveal private information,
* over-apologize without solving the issue,
* pretend to be a human agent.

## 12. Suggested Tech Stack

### Data Processing

* Python
* pandas
* Polars for larger files
* Jupyter notebooks
* Great Expectations or Pandera for data validation

### Machine Learning

* scikit-learn for baselines
* Sentence Transformers or OpenAI embeddings
* LightGBM for intent classification baseline
* optional fine-tuning later

### RAG

* Qdrant or Weaviate
* LangChain or LlamaIndex
* OpenAI, Anthropic, or local Llama model
* reranker model for better retrieval quality

### Backend

* FastAPI
* Pydantic
* PostgreSQL
* Redis cache
* Docker

### Frontend

* Streamlit for fast portfolio demo
* or Next.js for a more polished product demo

### MLOps

* MLflow for experiment tracking
* Docker Compose
* GitHub Actions
* Evidently AI for drift monitoring
* pytest for testing

## 13. Development Milestones

### Milestone 1: Data Understanding

Deliverables:

* load dataset,
* inspect schema,
* count inbound and outbound messages,
* identify company support accounts,
* reconstruct simple customer-response pairs,
* create cleaned dataset.

Success criteria:

* at least 100,000 clean customer-response pairs,
* each pair has customer text and company response,
* missing or broken threads removed.

### Milestone 2: Baseline Retrieval

Deliverables:

* create embeddings for customer messages,
* store vectors in Qdrant or Chroma,
* retrieve top-k similar cases,
* display retrieved company responses.

Success criteria:

* retrieval returns relevant cases for common support issues,
* simple command-line demo works.

### Milestone 3: Label-Based Evaluation

Deliverables:

* split dataset into train/test,
* treat company responses as labels,
* evaluate retrieval quality,
* create baseline response generator.

Success criteria:

* report Recall@5 and semantic similarity,
* show examples where retrieval works and fails.

### Milestone 4: RAG Draft Generator

Deliverables:

* prompt builder,
* LLM integration,
* generated response with references,
* confidence scoring.

Success criteria:

* generated responses are grounded in retrieved examples,
* system refuses or escalates weak retrieval cases.

### Milestone 5: Support Agent UI

Deliverables:

* web UI,
* input box,
* draft answer,
* retrieved evidence panel,
* feedback buttons.

Success criteria:

* user can test the system end-to-end from browser.

### Milestone 6: Productionization

Deliverables:

* FastAPI backend,
* Docker Compose setup,
* tests,
* logging,
* monitoring dashboard,
* README,
* architecture diagram.

Success criteria:

* one-command local startup,
* reproducible evaluation,
* demo video or screenshots.

## 14. Repository Structure

```text
reference-answer-rag-support-copilot/
│
├── README.md
├── docker-compose.yml
├── requirements.txt
├── .env.example
│
├── data/
│   ├── raw/
│   ├── interim/
│   └── processed/
│
├── notebooks/
│   ├── 01_data_exploration.ipynb
│   ├── 02_conversation_reconstruction.ipynb
│   ├── 03_retrieval_baseline.ipynb
│   └── 04_evaluation.ipynb
│
├── src/
│   ├── data/
│   │   ├── load_data.py
│   │   ├── clean_text.py
│   │   └── build_pairs.py
│   │
│   ├── retrieval/
│   │   ├── embed.py
│   │   ├── vector_store.py
│   │   └── retrieve_cases.py
│   │
│   ├── generation/
│   │   ├── prompt_builder.py
│   │   ├── llm_client.py
│   │   └── guardrails.py
│   │
│   ├── evaluation/
│   │   ├── retrieval_metrics.py
│   │   ├── generation_metrics.py
│   │   └── rag_faithfulness.py
│   │
│   └── api/
│       ├── main.py
│       ├── schemas.py
│       └── routes.py
│
├── app/
│   └── streamlit_app.py
│
├── tests/
│   ├── test_pair_builder.py
│   ├── test_retrieval.py
│   └── test_api.py
│
└── reports/
    ├── model_card.md
    ├── evaluation_report.md
    └── architecture.md
```

## 15. Portfolio Presentation

The final portfolio project should include:

* GitHub repository,
* clean README,
* architecture diagram,
* short demo video,
* screenshots of the UI,
* evaluation report,
* examples of retrieved reference responses,
* failure analysis,
* deployment instructions.

The project should clearly explain that the system is not just a chatbot. It is a **reference-answer RAG system** that learns from historical official company replies.

## 16. Example README Summary

```text
Reference-Answer RAG Customer Support Copilot is an AI assistant for support agents.

The system uses historical customer support conversations from Twitter/X. Customer messages are used as retrieval queries, while official company replies are treated as gold reference answers.

For a new customer issue, the system retrieves similar historical cases, shows the official replies used as evidence, and generates a grounded draft response for a human support agent to review.

The project demonstrates real-world AI engineering skills: data preprocessing, conversation reconstruction, embeddings, vector search, RAG, LLM prompting, evaluation, FastAPI deployment, Docker, and monitoring.
```

## 17. Why This Project Is Portfolio-Worthy

This project is stronger than a simple chatbot because it includes:

* real-world noisy data,
* weak supervision from historical company responses,
* retrieval over solved cases,
* label-based evaluation,
* LLM generation,
* confidence scoring,
* explainability,
* human-in-the-loop workflow,
* production-style API and UI.

It demonstrates practical AI engineering, not only model training.

## 18. Main Risks and How to Handle Them

### Risk 1: Noisy Twitter Conversations

Tweets can be short, sarcastic, incomplete, or multi-turn.

Solution:

* start with single-turn pairs,
* filter very short messages,
* remove broken threads,
* later add multi-turn reconstruction.

### Risk 2: Company Responses Are Not Always Ideal Labels

Some company replies may be generic, outdated, or unhelpful.

Solution:

* filter generic replies,
* group by company,
* score response usefulness,
* keep low-quality labels out of evaluation.

### Risk 3: RAG May Retrieve Similar Words but Wrong Policy

A delivery issue for one company may not apply to another company.

Solution:

* filter retrieval by company when possible,
* include company metadata,
* add reranking,
* require confidence threshold.

### Risk 4: LLM Hallucination

The model may invent policies or actions.

Solution:

* force citation to retrieved cases,
* add guardrails,
* add “not enough evidence” fallback,
* log hallucination examples.

## 19. Final Success Criteria

The project is successful when:

1. a user can enter a new customer support message,
2. the system retrieves relevant historical support cases,
3. the system displays official company responses as references,
4. the LLM generates a useful draft reply,
5. the system gives a confidence score,
6. weak or unsafe cases are escalated,
7. the project includes reproducible evaluation,
8. the whole system can run locally with Docker.

The final result should feel like a realistic internal AI tool that a support team could test in a pilot.
