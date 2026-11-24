# InsureClear – Interview Preparation

## 1. 60-Second Project Pitch

InsureClear is a GenAI-powered insurance assistant that helps users understand insurance rules and processes using official IRDAI-related information.

The main problem I wanted to solve was that insurance information is spread across different documents and circulars, making it difficult for users to find the correct information.

I developed the application using Python, FastAPI, Streamlit, ChromaDB, and Groq/Gemini LLMs. It uses Retrieval-Augmented Generation, or RAG, to retrieve relevant insurance information and generate answers based on the available records.

I also implemented input validation, response caching, latency and token logging, and prompt-injection protection. I added automated tests, Docker support, and deployed the application on Render.

The main goal of InsureClear is to make insurance information easier to understand while showing users the sources behind the answers.

## 2. Ten Likely Interview Questions

### Q1. What is InsureClear?

InsureClear is a GenAI-based insurance assistant. It helps users find answers to insurance-related questions using official insurance information instead of relying only on general LLM knowledge.

### Q2. Why did you choose this project?

Insurance rules can be difficult for ordinary users to understand. Information is available across different documents and websites. I wanted to build an application that makes this information easier to search and understand.

### Q3. What is RAG, and why did you use it?

RAG stands for Retrieval-Augmented Generation. First, the system retrieves relevant information from a knowledge base. Then, the LLM uses that information to generate an answer. I used RAG to make answers more relevant to the insurance records available in the project.

### Q4. Explain the architecture of InsureClear.

The user interacts with the Streamlit interface. The request goes to the FastAPI backend, where input validation is performed. The application retrieves relevant information through semantic search using ChromaDB. The retrieved context is passed to an LLM such as Groq or Gemini, and the generated response is returned to the user.

### Q5. Why did you use ChromaDB?

ChromaDB is a vector database. It stores vector representations of text and helps retrieve information based on semantic similarity. This allows the application to find relevant records even when the user's wording is different from the original text.

### Q6. Why did you use both Groq and Gemini?

I integrated Groq and Gemini as LLM providers so the application can work with different language models. This also gives flexibility when selecting a provider based on availability and configuration.

### Q7. What was the most difficult problem you faced?

The most difficult problem was handling insurance rules that depend on the policy type and sales channel. For example, free-look periods may differ, such as 15 or 30 days. Some older circulars may also have been superseded by newer master circulars. The challenge was to avoid mixing rules and presenting outdated information as current.

### Q8. How did you improve application performance?

I implemented an LRU cache with a maximum capacity of 128 entries. When the same question is asked again with the same prompt version, the cached response can be returned without making another LLM call. I also added request latency and token-usage logging.

### Q9. How did you test the application?

I used Pytest for automated testing and Ruff for code-quality checks. I also tested API endpoints through Swagger UI and manually checked the chat flow. I included a prompt-injection test to check that user input does not replace the system instructions.

### Q10. How did you deploy the project?

I used Docker to containerize the application and deployed it on Render. The backend provides API endpoints, and the health endpoint helps verify whether the service is running.

## 3. Hardest Problem – Interview Story

**Problem: Handling conflicting and outdated insurance rules**

One of the hardest challenges in InsureClear was handling insurance rules that change depending on the policy type and sales channel.

For example, a free-look period may be 15 days in one situation and 30 days in another. Also, some information pages refer to older circulars that may have been superseded by newer master circulars.

If the assistant retrieves information without considering these differences, it could mix two rules and give the user incorrect guidance.

My approach was to treat the policy type, sales channel, and source information as important context. The assistant should identify the applicable rule for the user's situation, show the source date, and flag guidance that may be outdated instead of presenting conflicting rules as one answer.

This taught me that building a reliable RAG application is not just about retrieving similar text. It is also about understanding the context and checking the reliability of the source.

## 4. Important Technical Terms to Revise

- **RAG:** Retrieval-Augmented Generation.
- **LLM:** Large Language Model.
- **Embedding:** Numerical representation of text.
- **ChromaDB:** Vector database used for semantic search.
- **FastAPI:** Python framework used to build APIs.
- **Streamlit:** Framework used to build the user interface.
- **LRU Cache:** Keeps recently used results and removes less recently used entries when capacity is reached.
- **Prompt Injection:** An attempt to manipulate an AI system through user input.
- **Docker:** Tool used to package an application and its dependencies.
- **Render:** Cloud platform used to deploy the application.

## 5. Project Links

- Live Application: https://genaitraining-4ihx.onrender.com
- Health Check: https://genaitraining-4ihx.onrender.com/health
- API Documentation: https://genaitraining-4ihx.onrender.com/docs
- GitHub: https://github.com/IshwariBagal05/GenAITraining