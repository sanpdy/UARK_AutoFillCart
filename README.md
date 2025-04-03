# UARK_AutoFillCart
This was started for the UArk AI Workshop with Walmart!

**Objective** 
The intent of this project is to provide an AI-powered shopping agent that attaches to the Walmart app and interprets queries from users and genereated a list of necessary items, relvant products, and substitutions. 

**Input**
The AI will be able to accept natural language prompts in the the search bar, examples include:
 -> "I want to make beef and broccoli"
 -> "What do I need for a camping trip this weekend?"
 -> "Find me the ingredients for tacos for 5"

**Output**
The AI will be able to generated curated list with features like:
 -> Smart substitutions for missing or unavailable items, similar to how OGP works at Walmart.
 -> Optional reasoning for substitutions
 -> A drafted walmart car ready for the users approval.

 **Scope**
  -> UI for cart review and substitutions
  -> NLP (Natural Language Processing) for request interpretation
  -> Rule-based, AI driven substitution logic, Eg. Substituting brand name milk with great value. 


**Team Members** 
Joshua Upshaw 
Sankalp Pandey:  
Solomon Hufford: 
Stephen Pierson: 
Cameron Eddy: DB and UI

**Architecture**
Models: Huggingface, pytorch 
  Metrics: Run time, caching (pull cache from website)
DB: SqlLite 
  Set up mock data needs
CICD: Github
  set up the file structure
  Docker: Code containerization process

Ensure we can the code run through command line interface
Once built, then set up github actions 
Deploy through: 
Streamlit API host 
