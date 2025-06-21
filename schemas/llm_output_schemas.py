from typing import List, Optional

from pydantic import BaseModel

import json

class ParameterSchema(BaseModel):
    type: str
    name: str

class FunctionSchema(BaseModel):
    name: str
    parameters: List[ParameterSchema]
    return_type: str
    description: str
    business_logic: str
    access_level: str

class VariableSchema(BaseModel):
    name: str
    data_type: str
    access_level: str
    description: str

class EngineerOutputSchema(BaseModel):
    functions: List[FunctionSchema]
    variables: List[VariableSchema]


# class UserStory(BaseModel):
#     title: str
#     description: str
#     acceptance_criteria: List[str]

# class PMOutputSchema(BaseModel):
#     stories: List[UserStory]
#     summary: Optional[str]

# class QAOutputSchema(BaseModel):
#     test_cases: List[dict]