"""Question answering over a graph using ArangoDB and AQL."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from langchain.chains.base import Chain
from langchain_core.callbacks import CallbackManagerForChainRun
from langchain_core.language_models import BaseLanguageModel
from langchain_core.messages import (
    AIMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import (
    BasePromptTemplate,
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
)
from langchain_core.runnables import Runnable
from pydantic import Field

from langchain_arangodb.chains.graph_qa.prompts import (
    AQL_GENERATION_PROMPT,
    AQL_QA_PROMPT,
)
from langchain_arangodb.graphs.graph import ArangoGraph

FUNCTION_RESPONSE_SYSTEM = """You are an assistant that helps to form nice and human 
understandable answers based on the provided information from tools.
Do not add any other information that wasn't present in the tools, and use 
very concise style in interpreting results!
"""

class GraphAQLQAChain(Chain):
    graph: ArangoGraph = Field(exclude=True)
    aql_generation_chain: Runnable[Dict[str, Any], str]
    qa_chain: Runnable[Dict[str, Any], str]
    input_key: str = "query"
    output_key: str = "result"
    top_k: int = 10
    return_intermediate_steps: bool = False
    return_direct: bool = False
    use_function_response: bool = False

    @property
    def input_keys(self) -> List[str]:
        return [self.input_key]

    @property
    def output_keys(self) -> List[str]:
        return [self.output_key]

    @property
    def _chain_type(self) -> str:
        return "graph_aql_chain"

    @classmethod
    def from_llm(
        cls,
        llm: Optional[BaseLanguageModel] = None,
        *,
        qa_prompt: Optional[BasePromptTemplate] = None,
        aql_prompt: Optional[BasePromptTemplate] = None,
        qa_llm: Optional[BaseLanguageModel] = None,
        aql_llm: Optional[BaseLanguageModel] = None,
        qa_llm_kwargs: Optional[Dict[str, Any]] = None,
        aql_llm_kwargs: Optional[Dict[str, Any]] = None,
        use_function_response: bool = False,
        function_response_system: str = FUNCTION_RESPONSE_SYSTEM,
        **kwargs: Any,
    ) -> GraphAQLQAChain:

        if llm:
            qa_llm = qa_llm or llm
            aql_llm = aql_llm or llm
        elif not qa_llm or not aql_llm:
            raise ValueError("Provide either llm or both qa_llm and aql_llm")

        aql_prompt = aql_prompt or AQL_GENERATION_PROMPT
        qa_prompt = qa_prompt or AQL_QA_PROMPT

        use_qa_llm_kwargs = qa_llm_kwargs or {}
        use_aql_llm_kwargs = aql_llm_kwargs or {}

        if use_function_response:
            if not hasattr(qa_llm, "bind_tools"):
                raise ValueError("LLM does not support native tools/functions")
            qa_llm.bind_tools({})
            response_prompt = ChatPromptTemplate.from_messages([
                SystemMessage(content=function_response_system),
                HumanMessagePromptTemplate.from_template("{question}"),
                MessagesPlaceholder(variable_name="function_response"),
            ])
            qa_chain = response_prompt | qa_llm | StrOutputParser()
        else:
            qa_chain = qa_prompt | qa_llm.bind(**use_qa_llm_kwargs) | StrOutputParser()

        aql_generation_chain = (
                aql_prompt | aql_llm.bind(**use_aql_llm_kwargs) | StrOutputParser()
        )

        return cls(
            qa_chain=qa_chain,
            aql_generation_chain=aql_generation_chain,
            use_function_response=use_function_response,
            **kwargs,
        )

    def _call(
        self,
        inputs: Dict[str, Any],
        run_manager: Optional[CallbackManagerForChainRun] = None,
    ) -> Dict[str, Any]:
        _run_manager = run_manager or CallbackManagerForChainRun.get_noop_manager()
        callbacks = _run_manager.get_child()
        question = inputs[self.input_key]

        args = {"question": question}
        args.update(inputs)

        intermediate_steps = []

        aql = self.aql_generation_chain.invoke(args, callbacks=callbacks)
        _run_manager.on_text("Generated AQL:", end="\n", verbose=self.verbose)
        _run_manager.on_text(aql, color="green", end="\n", verbose=self.verbose)

        intermediate_steps.append({"aql": aql})

        context = self.graph.run_aql(aql)[: self.top_k] if aql else []

        if self.return_direct:
            result = context
        else:
            _run_manager.on_text("Full Context:", end="\n", verbose=self.verbose)
            _run_manager.on_text(str(context), color="green", end="\n", verbose=self.verbose)
            intermediate_steps.append({"context": context})

            if self.use_function_response:
                tool_id = "call_arango_tool"
                tool_messages = [
                    AIMessage(
                        content="",
                        additional_kwargs={
                            "tool_calls": [
                                {
                                    "id": tool_id,
                                    "function": {
                                        "arguments": '{"question":"' + question + '"}',
                                        "name": "GetInformation",
                                    },
                                    "type": "function",
                                }
                            ]
                        },
                    ),
                    ToolMessage(content=str(context), tool_call_id=tool_id),
                ]
                result = self.qa_chain.invoke(
                    {"question": question, "function_response": tool_messages},
                )
            else:
                result = self.qa_chain.invoke(
                    {"question": question, "context": context}, callbacks=callbacks
                )

        output = {self.output_key: result}
        if self.return_intermediate_steps:
            output["intermediate_steps"] = intermediate_steps

        return output