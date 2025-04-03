# UARK_AutoFillCart

This was started for the UArk AI Workshop with Walmart!

---

## **Objective**
The intent of this project is to provide an **AI-powered shopping agent** that attaches to the Walmart app and interprets queries from users to generate a list of necessary items, relevant products, and substitutions.

---

## **Input**
The AI will be able to accept natural language prompts in the search bar. Examples include:

- `"I want to make beef and broccoli"`
- `"What do I need for a camping trip this weekend?"`
- `"Find me the ingredients for tacos for 5"`

---

## **Output**
The AI will be able to generate curated lists with features like:

- Smart substitutions for missing or unavailable items, similar to how OGP works at Walmart
- Optional reasoning for substitutions
- A drafted Walmart cart ready for the user's approval

---

## **Scope**

- UI for cart review and substitutions  
- NLP (Natural Language Processing) for request interpretation  
- Rule-based, AI-driven substitution logic  
  - e.g. Substituting brand name milk with Great Value

---

## **Team Members**

- Joshua Upshaw  
- Sankalp Pandey  
- Solomon Hufford  
- Stephen Pierson  
- Cameron Eddy: DB and UI

---

## **Architecture**

**Models:**  
- Huggingface  
- PyTorch  

**Metrics:**  
- Run time  
- Caching (pull cache from website)  

**Database:**  
- SQLite  
- Set up mock data needs  

**CI/CD:**  
- GitHub (set up the file structure)  
- Docker: Code containerization process  

---

## **Deployment Notes**

- Ensure we can run the code through the command line interface
- Once built, set up GitHub Actions
- Deploy through: **Streamlit API host**
