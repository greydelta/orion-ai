import json

def get_engineer_example_json():
    example = {
        "functions": [
            {
                "name": "calculate_area()",
                "parameters": [
                    { "type": "int", "name": "width" },
                    { "type": "int", "name": "height" }
                ],
                "return_type": "int",
                "description": "Calculates the area of a rectangle",
                "business_logic": "This function multiplies width and height to return the area of a rectangle.",
                "access_level": "public"
            }
        ],
        "variables": [
            {
                "name": "cnfInputInString",
                "data_type": "String",
                "access_level": "private",
                "description": "Variable to hold the input configuration in string format"
            }
        ]
    }
    return json.dumps(example, indent=2)
