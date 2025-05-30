# flake8: noqa
from langchain_core.prompts.prompt import PromptTemplate

AQL_GENERATION_TEMPLATE = """Task: Generate AQL query to retrieve data from an ArangoDB graph.
Instructions:
- Use only the provided attributes and collection names in the schema.
- Do not use any fields or collections not explicitly listed.
- Do not include any explanations or additional text.
- Return only a valid AQL query as output.

Schema:
{schema}

The question is:
{question}
"""

AQL_GENERATION_PROMPT = PromptTemplate(
    input_variables=["schema", "question"], template=AQL_GENERATION_TEMPLATE
)

AQL_QA_TEMPLATE = """You are an assistant that helps to form nice and human-understandable answers.
The information part contains the provided information that you must use to construct an answer.
The provided information is authoritative, you must never doubt it or try to use your internal knowledge to correct it.
Make the answer sound as a response to the question. Do not mention that you based the result on the given information.
Here is an example:

Question: Which developers worked on the AI project?
Context: [developer:Alice, developer:Bob]
Helpful Answer: Alice, Bob worked on the AI project.

Follow this example when generating answers.
If the provided information is empty, say that you don't know the answer.

Information:
{context}

Question: {question}
Helpful Answer:"""

AQL_QA_PROMPT = PromptTemplate(
    input_variables=["context", "question"], template=AQL_QA_TEMPLATE
)
