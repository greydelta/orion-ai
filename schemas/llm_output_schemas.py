from typing import Any, List, Optional

from pydantic import BaseModel
class ParameterSchema(BaseModel):
    data_type: str
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
    output: Optional[Any] = None


# class UserStory(BaseModel):
#     title: str
#     description: str
#     acceptance_criteria: List[str]

# class PMOutputSchema(BaseModel):
#     stories: List[UserStory]
#     summary: Optional[str]

# class QAOutputSchema(BaseModel):
#     test_cases: List[dict]