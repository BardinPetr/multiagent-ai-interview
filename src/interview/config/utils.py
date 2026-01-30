def kickoff(crew, inputs: dict, repeats: int = 5):
    if repeats < 0: return None
    try:
        return crew.crew().kickoff(inputs=inputs).pydantic
    except Exception as e:
        print(e)
        return kickoff(crew, inputs, repeats=repeats - 1)
