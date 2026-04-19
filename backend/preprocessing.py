import pandas as pd

def preprocess_input(data: dict):
    """
    Handle missing values, convert categorical to numerical, and prepare for model prediction.
    data is a dictionary with keys:
    age, gender, cp, trestbps, chol, fbs, bmi, exercise_level, smoking, alcohol
    """
    # Convert dict to DataFrame for single row
    df = pd.DataFrame([data])
    
    # Fill any missing values with defaults if they exist (though pydantic should catch them)
    df.fillna({
        'age': 50,
        'gender': 1,
        'cp': 0,
        'trestbps': 120,
        'chol': 200,
        'fbs': 0,
        'bmi': 25.0,
        'exercise_level': 0,
        'smoking': 'no',
        'alcohol': 'no'
    }, inplace=True)
    
    # Convert categorical to numerical
    df['smoking'] = df['smoking'].apply(lambda x: str(x).lower()).map({'yes': 1, 'no': 0}).fillna(0)
    df['alcohol'] = df['alcohol'].apply(lambda x: str(x).lower()).map({'yes': 1, 'no': 0}).fillna(0)
    
    # Ensure exact column order as expected by the model
    columns_order = ['age', 'gender', 'cp', 'trestbps', 'chol', 'fbs', 'bmi', 'exercise_level', 'smoking', 'alcohol']
    return df[columns_order]
