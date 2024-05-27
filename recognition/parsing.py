def parse_llm_response(text):
    """
    Parameter TEXT should have the form :
    ANIMATION;PARTICLE

    Return an array of strings [ANIMATION, PARTICLE].
    """
    tokens = text.split(';')
    length = len(tokens)

    if length != 2:
        print("ResponseParser.parse: unexpected number of tokens,",
              "expected 2, found", length)
        return None

    return tokens
