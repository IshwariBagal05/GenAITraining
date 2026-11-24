# InsureClear – Interview Preparation

## 1. 60-Second Project Pitch

InsureClear is a GenAI-powered insurance information assistant. The main problem is that insurance rules, policyholder rights, deadlines and complaint procedures are spread across different official sources. Users may find it difficult to understand this information.

To solve this problem, I developed InsureClear using Python, FastAPI, Streamlit, ChromaDB and Groq/Gemini LLMs.

It uses Retrieval-Augmented Generation (RAG). When a user asks a question, the system searches for relevant insurance information and passes the retrieved context to the language model. The model then generates a simple answer based on that information.

I also implemented response caching, input validation, prompt-injection protection and latency and token monitoring.

The main goal is to make insurance information easier to understand and access.

## 2. Hardest Problem I Faced

One of the challenging problems I faced was during deployment.

After deploying InsureClear, the chat API returned a 502 error. When I checked the error response, I found that the GROQ_API_KEY environment variable was missing.

I fixed this by identifying the missing environment variable, configuring it in the deployment environment and testing the API again.

I also implemented response caching to improve response time. In my local test, the first request took 1435.61 ms, while the repeated cached request took 0.01 ms.

This experience helped me understand debugging, deployment configuration and performance measurement.

## 3. Ten Likely Interview Questions

### Q1. What is InsureClear?
InsureClear is a GenAI-powered assistant that helps users understand insurance rules, deadlines, policyholder rights and complaint procedures.

### Q2. What is RAG?
RAG stands for Retrieval-Augmented Generation. It retrieves relevant information from a knowledge source and provides that information to an LLM to generate an answer.

### Q3. Why did you use ChromaDB?
I used ChromaDB to store vector embeddings and retrieve relevant information based on the meaning of the user's question.

### Q4. What is semantic search?
Semantic search finds information based on the meaning and context of a query instead of matching only exact keywords.

### Q5. Why did you use FastAPI?
FastAPI is used to build the backend API. It handles requests from the user interface and connects the different components.

### Q6. Why did you use Streamlit?
Streamlit helps create a simple and interactive user interface using Python.

### Q7. What is an LLM?
LLM stands for Large Language Model. It understands and generates human-like text based on the input it receives.

### Q8. What is caching?
Caching stores previously generated responses. When the same question is asked again, the system can return the stored response without making another LLM call.

### Q9. How did you handle prompt injection?
I kept user questions separate from system instructions and added prompt-injection protection so that user input does not replace the system instructions.

### Q10. How did you test your project?
I used Pytest for automated testing and Ruff for code quality checks. I also tested the API endpoints and measured response latency and token usage.

## 4. Technologies Used

- Python – Main programming language
- FastAPI – Backend API
- Streamlit – User interface
- ChromaDB – Vector database
- RAG – Information retrieval and generation approach
- Groq/Gemini – LLM integration
- Pytest – Automated testing
- Ruff – Code quality checking
- Docker – Containerization
- Render – Deployment